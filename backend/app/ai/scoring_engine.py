"""
app/ai/scoring_engine.py
========================
Isolated scoring and ranking engine for CampusHire applicant evaluation.

Components:
  1. Configurable weights imported centrally from app.ai.scoring_config.
  2. calculate_skill_match(resume_skills, required_skills, preferred_skills) -> dict
  3. calculate_experience_relevance(student_experience, job_experience_requirement) -> float
  4. calculate_education_relevance(student_education, job) -> float
  5. calculate_final_score(semantic_similarity, skill_match_pct, experience_relevance, education_relevance) -> float
  6. rank_applicants(applications) -> list[Application]
  7. score_and_rank_job_applicants(job_id, db_session) -> list[Application]

This module is isolated from API routes.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.ai.embedding_service import (
    EmbeddingGenerationError,
    cosine_similarity_score,
    generate_embedding,
    get_or_generate_embedding,
    text_hash,
)
from app.ai.scoring_config import (
    EDUCATION_WEIGHT,
    EXPERIENCE_WEIGHT,
    PREFERRED_SKILL_WEIGHT_MULTIPLIER,
    REQUIRED_SKILL_WEIGHT_MULTIPLIER,
    SEMANTIC_WEIGHT,
    SKILL_WEIGHT,
)

logger = logging.getLogger(__name__)


# ===========================================================================
# 1. Skill Match Calculation
# ===========================================================================

def calculate_skill_match(
    resume_skills: Optional[List[str]],
    required_skills: Optional[List[str]],
    preferred_skills: Optional[List[str]],
) -> Dict[str, Any]:
    """
    Calculate the skill match percentage and identify matching/missing skills.

    Weighting Rule:
    ---------------
    Required skills are weighted more heavily than preferred skills in the
    percentage calculation. Specifically:
      - Each matched REQUIRED skill contributes REQUIRED_SKILL_WEIGHT_MULTIPLIER (default 2.0).
      - Each matched PREFERRED skill contributes PREFERRED_SKILL_WEIGHT_MULTIPLIER (default 1.0).
    This ensures that failing to meet mandatory job requirements penalises the candidate
    twice as much as missing optional/preferred competencies.

    Matching is case-insensitive and whitespace-tolerant.

    Parameters
    ----------
    resume_skills : list[str] | None
        List of skills extracted from candidate resume or student profile.
    required_skills : list[str] | None
        List of mandatory skills specified in the job posting.
    preferred_skills : list[str] | None
        List of nice-to-have skills specified in the job posting.

    Returns
    -------
    dict
        {
            "skill_match_percentage": float,      # 0.0 to 100.0
            "matching_skills": list[str],          # All matching skill names
            "missing_required_skills": list[str],  # Required skills not found in resume
            "matching_preferred_skills": list[str] # Preferred skills found in resume
        }
    """
    resume_skills = resume_skills or []
    required_skills = required_skills or []
    preferred_skills = preferred_skills or []

    # Normalise candidate skills into a lowercase set for O(1) case-insensitive lookup
    resume_set = {s.strip().lower() for s in resume_skills if s and s.strip()}

    matching_required: List[str] = []
    missing_required: List[str] = []

    for req in required_skills:
        if not req or not req.strip():
            continue
        cleaned = req.strip()
        if cleaned.lower() in resume_set:
            matching_required.append(cleaned)
        else:
            missing_required.append(cleaned)

    matching_preferred: List[str] = []
    for pref in preferred_skills:
        if not pref or not pref.strip():
            continue
        cleaned = pref.strip()
        if cleaned.lower() in resume_set:
            matching_preferred.append(cleaned)

    # Combined list of all matching skills (preserving uniqueness)
    all_matching_skills: List[str] = list(
        dict.fromkeys(matching_required + matching_preferred)
    )

    # Weighted score calculation
    req_weight = REQUIRED_SKILL_WEIGHT_MULTIPLIER
    pref_weight = PREFERRED_SKILL_WEIGHT_MULTIPLIER

    total_possible = (len(required_skills) * req_weight) + (len(preferred_skills) * pref_weight)

    if total_possible == 0:
        # If the job has no skill criteria specified, treat as 100% satisfied
        skill_match_percentage = 100.0
    else:
        earned = (len(matching_required) * req_weight) + (len(matching_preferred) * pref_weight)
        skill_match_percentage = round((earned / total_possible) * 100.0, 2)

    return {
        "skill_match_percentage": float(min(100.0, max(0.0, skill_match_percentage))),
        "matching_skills": all_matching_skills,
        "missing_required_skills": missing_required,
        "matching_preferred_skills": matching_preferred,
    }


# ===========================================================================
# 2. Experience Relevance Calculation
# ===========================================================================

def _parse_duration_to_years(duration_str: str) -> float:
    """
    Helper to convert duration strings like '6 months', '2 years', '1.5 yrs'
    into a float number of years.
    """
    if not duration_str or not isinstance(duration_str, str):
        return 0.5  # default estimate for an internship/entry with unspecified duration

    duration_str = duration_str.lower().strip()

    # Match patterns like "2 years", "18 months", "1.5 yrs"
    match = re.search(r"(\d+(?:\.\d+)?)\s*(year|yr|month|mo)", duration_str)
    if match:
        val = float(match.group(1))
        unit = match.group(2)
        if "month" in unit or "mo" in unit:
            return val / 12.0
        return val

    # Match single standalone number (e.g. "2")
    num_match = re.search(r"(\d+(?:\.\d+)?)", duration_str)
    if num_match:
        val = float(num_match.group(1))
        return val if val <= 10 else val / 12.0

    return 0.5


def calculate_experience_relevance(
    student_experience: Optional[List[Dict[str, Any]]],
    job_experience_requirement: Optional[str],
) -> float:
    """
    Calculate the relevance and sufficiency of candidate experience.

    Heuristic Rules:
    ----------------
    1. If the student has no experience entries (None or empty list), returns exactly 0.0.
       Missing information is honestly reflected as 0 rather than a fabricated middling score.
    2. If the job requires 0 years / 'fresher' / has no requirement, any valid candidate
       experience earns a full 100.0 score.
    3. If the job specifies required years (e.g. '2+ years', '1-3 years'), candidate duration
       is parsed and compared against the requirement:
         score = min(100.0, (candidate_years / required_years) * 100.0)

    Parameters
    ----------
    student_experience : list[dict] | None
        List of experience dicts (e.g. [{"role": "...", "duration": "...", ...}]).
    job_experience_requirement : str | None
        Requirement string from job posting (e.g. "2+ years", "Fresher", "1 year").

    Returns
    -------
    float
        Experience relevance score in [0.0, 100.0].
    """
    # Strict rule: no experience data -> return 0.0
    if not student_experience or not isinstance(student_experience, list) or len(student_experience) == 0:
        return 0.0

    # Clean valid entries
    valid_entries = [e for e in student_experience if isinstance(e, dict) and any(e.values())]
    if not valid_entries:
        return 0.0

    # Calculate candidate's total accumulated experience in years
    total_candidate_years = 0.0
    for entry in valid_entries:
        duration_val = entry.get("duration", "")
        # Also check description if duration field is empty
        if not duration_val and "description" in entry:
            desc_match = re.search(r"(\d+(?:\.\d+)?)\s*(year|yr|month|mo)", str(entry.get("description", "")).lower())
            if desc_match:
                duration_val = desc_match.group(0)

        total_candidate_years += _parse_duration_to_years(str(duration_val))

    # At least 0.5 years per valid entry (internship heuristic)
    total_candidate_years = max(total_candidate_years, len(valid_entries) * 0.5)

    # Parse job requirement
    req_str = str(job_experience_requirement or "").strip().lower()

    if not req_str or "fresher" in req_str or "0" in req_str or "entry" in req_str or "intern" in req_str:
        # Candidate has experience for an entry-level/fresher position -> full score
        return 100.0

    req_num_match = re.search(r"(\d+(?:\.\d+)?)", req_str)
    if req_num_match:
        required_years = float(req_num_match.group(1))
        if required_years <= 0.0:
            return 100.0
        score = (total_candidate_years / required_years) * 100.0
        return round(min(100.0, max(0.0, score)), 1)

    # If requirement text is non-empty but has no digits (e.g. "Experienced", "Prior internship required")
    # Candidate with at least 1 entry receives a high score (80.0)
    return 80.0


# ===========================================================================
# 3. Education Relevance Calculation
# ===========================================================================

def calculate_education_relevance(
    student_education: Optional[List[Dict[str, Any]]],
    job: Any,
) -> float:
    """
    Calculate education alignment between candidate and job profile.

    Heuristic Rules:
    ----------------
    1. If candidate has no education entries (None or empty list), returns exactly 0.0.
       Missing information is honestly reflected as 0 rather than guessing.
    2. Having valid higher education (e.g. degree / institution) starts with a base score of 50.0.
    3. Alignment with job's allowed_branches or tech department keywords adds +30.0 points.
    4. Recognised degree qualifications (e.g. B.Tech, B.E., M.Tech, MCA, B.Sc, M.S.) add +20.0 points.
    5. Score is clamped to [0.0, 100.0].

    Parameters
    ----------
    student_education : list[dict] | None
        List of education dicts (e.g. [{"degree": "...", "institution": "...", ...}]).
    job : Job | dict | Any
        Job object or dict containing title, description, and allowed_branches.

    Returns
    -------
    float
        Education relevance score in [0.0, 100.0].
    """
    # Strict rule: no education data -> return 0.0
    if not student_education or not isinstance(student_education, list) or len(student_education) == 0:
        return 0.0

    valid_entries = [e for e in student_education if isinstance(e, dict) and any(e.values())]
    if not valid_entries:
        return 0.0

    # Extract job criteria
    allowed_branches: List[str] = []
    job_title = ""
    job_desc = ""

    if isinstance(job, dict):
        allowed = job.get("allowed_branches")
        if isinstance(allowed, list):
            allowed_branches = [str(b).lower().strip() for b in allowed if b]
        elif isinstance(allowed, str):
            allowed_branches = [b.lower().strip() for b in allowed.split(",") if b.strip()]
        job_title = str(job.get("title", "")).lower()
        job_desc = str(job.get("description", "")).lower()
    elif job is not None:
        allowed = getattr(job, "allowed_branches", None)
        if isinstance(allowed, list):
            allowed_branches = [str(b).lower().strip() for b in allowed if b]
        elif isinstance(allowed, str):
            allowed_branches = [b.lower().strip() for b in allowed.split(",") if b.strip()]
        job_title = str(getattr(job, "title", "") or "").lower()
        job_desc = str(getattr(job, "description", "") or "").lower()

    # Aggregate candidate education text
    edu_texts: List[str] = []
    for edu in valid_entries:
        for k in ("degree", "institution", "branch", "department", "field"):
            v = edu.get(k)
            if v:
                edu_texts.append(str(v).lower())

    combined_edu_str = " ".join(edu_texts)

    # Base score for having valid verified education
    score = 50.0

    # Branch / Field Alignment Check (+30 points)
    branch_matched = False
    if allowed_branches:
        for branch in allowed_branches:
            if branch in combined_edu_str:
                branch_matched = True
                break
    else:
        # Tech / Engineering keyword alignment if no specific allowed_branches set
        tech_keywords = [
            "computer science", "cse", "it", "information technology",
            "software", "electronics", "ece", "electrical", "data science",
            "artificial intelligence", "ai", "engineering", "mca", "bca"
        ]
        for kw in tech_keywords:
            if kw in combined_edu_str and (kw in job_title or kw in job_desc or "engineer" in job_title or "developer" in job_title):
                branch_matched = True
                break

    if branch_matched:
        score += 30.0

    # Degree Qualification Check (+20 points)
    degree_keywords = [
        "b.tech", "btech", "b.e", "be", "m.tech", "mtech", "mca", "bca",
        "b.sc", "bsc", "m.sc", "msc", "bachelor", "master", "ph.d", "phd", "b.s", "m.s"
    ]
    for deg in degree_keywords:
        if deg in combined_edu_str:
            score += 20.0
            break

    return round(min(100.0, max(0.0, score)), 1)


# ===========================================================================
# 4. Final Score Calculation
# ===========================================================================

def calculate_final_score(
    semantic_similarity: float,
    skill_match_pct: float,
    experience_relevance: float,
    education_relevance: float,
) -> float:
    """
    Compute the overall composite AI score from the four weighted sub-scores.

    Weights (from app.ai.scoring_config):
      - SEMANTIC_WEIGHT   : 0.50
      - SKILL_WEIGHT      : 0.25
      - EXPERIENCE_WEIGHT : 0.15
      - EDUCATION_WEIGHT  : 0.10

    Returns
    -------
    float
        Final score in [0.0, 100.0] rounded to 1 decimal place.
    """
    sem = max(0.0, min(100.0, float(semantic_similarity or 0.0)))
    skl = max(0.0, min(100.0, float(skill_match_pct or 0.0)))
    exp = max(0.0, min(100.0, float(experience_relevance or 0.0)))
    edu = max(0.0, min(100.0, float(education_relevance or 0.0)))

    composite = (
        (sem * SEMANTIC_WEIGHT)
        + (skl * SKILL_WEIGHT)
        + (exp * EXPERIENCE_WEIGHT)
        + (edu * EDUCATION_WEIGHT)
    )

    return round(composite, 1)


# ===========================================================================
# 5. Applicant Ranking
# ===========================================================================

def rank_applicants(applications: List[Any]) -> List[Any]:
    """
    Rank a list of Application objects descending by composite ai_score.

    Tie-breaking Rule:
    ------------------
    When two or more applications have identical ai_score, ties are broken by
    earlier applied_at timestamp first (the applicant who applied earlier gets
    the better / lower numerical rank).

    Assigns `rank = 1, 2, 3...` in place on each Application object and returns
    the sorted list.

    Parameters
    ----------
    applications : list[Application]
        List of application ORM objects or test doubles with ai_score and applied_at.

    Returns
    -------
    list[Application]
        The sorted list of applications with updated .rank attributes.
    """
    if not applications:
        return []

    # Sort key helper:
    # 1. Scored applications before unscored (ai_score is not None -> 0, else 1)
    # 2. Higher ai_score first (-score)
    # 3. Earlier applied_at timestamp first (tie-breaking)
    def _sort_key(app: Any) -> Tuple[int, float, datetime]:
        score = getattr(app, "ai_score", None)
        applied_at = getattr(app, "applied_at", None) or datetime.max

        if score is None:
            return (1, 0.0, applied_at)
        return (0, -float(score), applied_at)

    sorted_apps = sorted(applications, key=_sort_key)

    # Assign ranks in place
    current_rank = 1
    for app in sorted_apps:
        if getattr(app, "ai_score", None) is not None:
            app.rank = current_rank
            current_rank += 1
        else:
            app.rank = None

    return sorted_apps


# ===========================================================================
# 6. Full Pipeline Orchestration
# ===========================================================================

def score_and_rank_job_applicants(job_id: int, db_session: Any) -> List[Any]:
    """
    Full scoring and ranking pipeline orchestration for a job posting.

    Workflow:
    ---------
    1. Fetches the Job and all eligible applications.
    2. Generates or reuses the Job embedding.
    3. For each applicant:
       - Extracts resume/profile text, skills, experience, and education.
       - Generates/reuses candidate embedding.
       - Calculates semantic, skill, experience, and education scores.
       - Computes final ai_score.
       - Resilient error handling: if any individual applicant fails (e.g. embedding error),
         sets their scores to None with a failure note, ensuring one bad resume never
         blocks ranking the rest of the applicant pool.
    4. Ranks all successfully scored applicants by ai_score (breaking ties by applied_at).
    5. Persists scores and ranks to the database session and commits.

    Parameters
    ----------
    job_id : int
        Primary key of the Job.
    db_session : Session
        SQLAlchemy database session.

    Returns
    -------
    list[Application]
        List of all processed applications for the job.
    """
    from app.models.models import Application, Job, Resume, Student

    job = db_session.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError(f"Job with id {job_id} not found.")

    # 1. Prepare Job Embedding
    job_text = f"{job.title}\n\n{job.description or ''}\n\nRequirements:\n{job.requirements or ''}"
    current_job_hash = text_hash(job_text)

    job_embedding, job_recomputed = get_or_generate_embedding(
        text=job_text,
        cached_embedding=job.embedding,
        cached_text_hash=job.embedding_hash,
        current_text_hash=current_job_hash,
    )

    if job_recomputed:
        job.embedding = job_embedding
        job.embedding_hash = current_job_hash
        logger.info("Generated new job embedding for job_id=%s (hash=%s)", job_id, current_job_hash[:8])
    else:
        logger.debug("Reused cached job embedding for job_id=%s (hash=%s)", job_id, current_job_hash[:8])

    # 2. Fetch all applications for this job
    applications: List[Application] = (
        db_session.query(Application)
        .filter(Application.job_id == job_id)
        .all()
    )

    if not applications:
        db_session.commit()
        return []

    logger.info("Scoring and ranking %d application(s) for job_id=%s", len(applications), job_id)

    # 3. Score each applicant independently with per-applicant resilience
    for app in applications:
        try:
            student = app.student
            resume = app.resume

            # Extract parsed resume data or fallback to student profile
            parsed_data = (resume.parsed_data if resume and isinstance(resume.parsed_data, dict) else {}) or {}

            # Candidate Skills
            cand_skills = parsed_data.get("skills")
            if not cand_skills and student and student.skills:
                cand_skills = student.skills if isinstance(student.skills, list) else []
            cand_skills = cand_skills or []

            # Candidate Experience
            cand_exp = parsed_data.get("experience")
            if not cand_exp and student and student.experience:
                cand_exp = student.experience if isinstance(student.experience, list) else []
            cand_exp = cand_exp or []

            # Candidate Education
            cand_edu = parsed_data.get("education")
            if not cand_edu and student:
                if student.education and isinstance(student.education, list):
                    cand_edu = student.education
                elif student.branch:
                    cand_edu = [{
                        "degree": f"Bachelor of Technology in {student.branch}",
                        "institution": "Campus",
                        "year": student.year,
                        "score": f"{student.cgpa} CGPA" if student.cgpa else None,
                    }]
            cand_edu = cand_edu or []

            # Candidate Text for Embedding
            cand_text = ""
            if resume and resume.extracted_text and resume.extracted_text.strip():
                cand_text = resume.extracted_text.strip()
            elif cand_skills or cand_exp or cand_edu:
                cand_text = (
                    f"Skills: {', '.join(cand_skills)}\n"
                    f"Experience: {cand_exp}\n"
                    f"Education: {cand_edu}"
                )
            elif student and (student.branch or student.year or student.cgpa):
                parts = []
                if student.branch:
                    parts.append(f"Branch: {student.branch}")
                if student.year:
                    parts.append(f"Year: {student.year}")
                if student.cgpa:
                    parts.append(f"CGPA: {student.cgpa}")
                cand_text = "Student profile: " + ", ".join(parts)

            if not cand_text or not cand_text.strip():
                raise EmbeddingGenerationError("No usable resume text or student profile data found to embed.")

            # Candidate Embedding
            if resume:
                cand_hash = text_hash(cand_text)
                cand_embedding, resume_recomputed = get_or_generate_embedding(
                    text=cand_text,
                    cached_embedding=resume.embedding,
                    cached_text_hash=resume.embedding_hash,
                    current_text_hash=cand_hash,
                )
                if resume_recomputed:
                    resume.embedding = cand_embedding
                    resume.embedding_hash = cand_hash
                    logger.debug(
                        "Generated fresh candidate embedding for resume_id=%s (hash=%s)",
                        resume.id,
                        cand_hash[:8],
                    )
                else:
                    logger.debug(
                        "Reused cached candidate embedding for resume_id=%s (hash=%s)",
                        resume.id,
                        cand_hash[:8],
                    )
            else:
                cand_embedding = generate_embedding(cand_text)

            # 4. Calculate Individual Component Scores
            semantic_score = cosine_similarity_score(job_embedding, cand_embedding)

            req_skills = job.required_skills if isinstance(job.required_skills, list) else []
            pref_skills = job.preferred_skills if isinstance(job.preferred_skills, list) else []
            skill_res = calculate_skill_match(cand_skills, req_skills, pref_skills)
            skill_score = skill_res["skill_match_percentage"]

            exp_score = calculate_experience_relevance(cand_exp, job.experience_requirement)
            edu_score = calculate_education_relevance(cand_edu, job)

            ai_score = calculate_final_score(
                semantic_similarity=semantic_score,
                skill_match_pct=skill_score,
                experience_relevance=exp_score,
                education_relevance=edu_score,
            )

            # Persist scores on Application row
            app.semantic_score = semantic_score
            app.skill_score = skill_score
            app.experience_score = exp_score
            app.education_score = edu_score
            app.ai_score = ai_score

        except Exception as exc:
            logger.warning(
                "AI scoring failed for application %s (student_id=%s): %s",
                getattr(app, "id", "unknown"),
                getattr(app, "student_id", "unknown"),
                exc,
                exc_info=True,
            )
            # Resilient fallback: reset scores to null and attach error note
            app.semantic_score = None
            app.skill_score = None
            app.experience_score = None
            app.education_score = None
            app.ai_score = None
            app.rank = None
            if hasattr(app, "notes"):
                app.notes = f"Scoring error: {exc}"

    # 5. Rank all applicants
    ranked_applications = rank_applicants(applications)

    # 6. Commit all changes to database
    db_session.commit()

    return ranked_applications
