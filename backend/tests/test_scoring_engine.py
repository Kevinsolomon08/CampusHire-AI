# tests/test_scoring_engine.py
# Comprehensive tests for app/ai/scoring_engine.py and app/ai/scoring_config.py.
#
# Coverage includes:
#   1. Weights sum to exactly 1.0.
#   2. calculate_skill_match with full required-skill overlap (high %, empty missing).
#   3. calculate_skill_match with zero overlap (0%, all required skills missing).
#   4. calculate_final_score with known component inputs matches hand-computed expected value.
#   5. rank_applicants correctly orders a list of applications by score descending.
#   6. rank_applicants tie-breaking by applied_at when scores are equal.
#   7. score_and_rank_job_applicants continues scoring other applicants when one raises an error.
#   8. Experience relevance returning 0.0 for empty/missing experience.
#   9. Education relevance returning 0.0 for empty/missing education.

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest

from app.ai.embedding_service import EmbeddingGenerationError
from app.ai.scoring_config import (
    EDUCATION_WEIGHT,
    EXPERIENCE_WEIGHT,
    PREFERRED_SKILL_WEIGHT_MULTIPLIER,
    REQUIRED_SKILL_WEIGHT_MULTIPLIER,
    SEMANTIC_WEIGHT,
    SKILL_WEIGHT,
    TOTAL_WEIGHT,
)
from app.ai.scoring_engine import (
    calculate_education_relevance,
    calculate_experience_relevance,
    calculate_final_score,
    calculate_skill_match,
    rank_applicants,
    score_and_rank_job_applicants,
)


# ===========================================================================
# 1. Weights Invariant Test
# ===========================================================================

def test_weights_sum_to_exactly_one():
    """Verify that all four scoring component weights sum to exactly 1.0."""
    total = SEMANTIC_WEIGHT + SKILL_WEIGHT + EXPERIENCE_WEIGHT + EDUCATION_WEIGHT
    assert total == pytest.approx(1.0, abs=1e-9)
    assert TOTAL_WEIGHT == pytest.approx(1.0, abs=1e-9)
    assert SEMANTIC_WEIGHT == 0.50
    assert SKILL_WEIGHT == 0.25
    assert EXPERIENCE_WEIGHT == 0.15
    assert EDUCATION_WEIGHT == 0.10


# ===========================================================================
# 2. Skill Match Tests
# ===========================================================================

def test_calculate_skill_match_full_required_overlap():
    """
    calculate_skill_match with full required-skill overlap produces a high percentage
    and an empty missing_required_skills list.
    """
    resume_skills = ["Python", "FastAPI", "Docker", "PostgreSQL"]
    required_skills = ["Python", "FastAPI"]
    preferred_skills = ["Docker"]

    result = calculate_skill_match(
        resume_skills=resume_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
    )

    assert result["skill_match_percentage"] == 100.0
    assert result["missing_required_skills"] == []
    assert "Python" in result["matching_skills"]
    assert "FastAPI" in result["matching_skills"]
    assert "Docker" in result["matching_preferred_skills"]


def test_calculate_skill_match_zero_overlap():
    """
    calculate_skill_match with zero skill overlap produces 0.0% match
    and lists all required skills under missing_required_skills.
    """
    resume_skills = ["HTML", "CSS", "Photoshop"]
    required_skills = ["Python", "Kubernetes", "Rust"]
    preferred_skills = ["Go"]

    result = calculate_skill_match(
        resume_skills=resume_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
    )

    assert result["skill_match_percentage"] == 0.0
    assert sorted(result["missing_required_skills"]) == sorted(["Python", "Kubernetes", "Rust"])
    assert result["matching_skills"] == []
    assert result["matching_preferred_skills"] == []


def test_calculate_skill_match_case_insensitivity():
    """calculate_skill_match handles case differences gracefully."""
    resume_skills = ["python", "FASTAPI", "Docker"]
    required_skills = ["Python", "FastAPI"]
    preferred_skills = ["docker"]

    result = calculate_skill_match(
        resume_skills=resume_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
    )

    assert result["skill_match_percentage"] == 100.0
    assert result["missing_required_skills"] == []
    assert len(result["matching_skills"]) == 3


def test_calculate_skill_match_partial_with_required_double_weight():
    """
    Verify required skills count double compared to preferred skills:
      Req: 2 skills (weight 2 * 2 = 4)
      Pref: 2 skills (weight 1 * 2 = 2)
      Total possible = 6 points.

      If 2 required match (4 points) + 0 preferred match -> 4/6 = 66.67%.
      If 0 required match + 2 preferred match (2 points) -> 2/6 = 33.33%.
    """
    # Candidate 1: matches 2 required, 0 preferred
    res1 = calculate_skill_match(
        resume_skills=["Python", "FastAPI"],
        required_skills=["Python", "FastAPI"],
        preferred_skills=["AWS", "Redis"],
    )
    assert res1["skill_match_percentage"] == pytest.approx(66.67, abs=0.01)

    # Candidate 2: matches 0 required, 2 preferred
    res2 = calculate_skill_match(
        resume_skills=["AWS", "Redis"],
        required_skills=["Python", "FastAPI"],
        preferred_skills=["AWS", "Redis"],
    )
    assert res2["skill_match_percentage"] == pytest.approx(33.33, abs=0.01)


def test_calculate_skill_match_empty_inputs():
    """calculate_skill_match handles None / empty lists safely."""
    res_none = calculate_skill_match(None, None, None)
    assert res_none["skill_match_percentage"] == 100.0
    assert res_none["matching_skills"] == []
    assert res_none["missing_required_skills"] == []


# ===========================================================================
# 3. Experience Relevance Tests
# ===========================================================================

def test_calculate_experience_relevance_empty_returns_zero():
    """If the student has no experience data at all, return 0.0 (no fake score)."""
    assert calculate_experience_relevance([], "2 years") == 0.0
    assert calculate_experience_relevance(None, "2 years") == 0.0
    assert calculate_experience_relevance([], None) == 0.0


def test_calculate_experience_relevance_fresher_job():
    """If job has fresher/0 years requirement and candidate has experience entries, return 100.0."""
    experience = [
        {"role": "Intern", "company": "Acme", "duration": "3 months", "description": "Django dev"}
    ]
    assert calculate_experience_relevance(experience, "Fresher") == 100.0
    assert calculate_experience_relevance(experience, "0-1 years") == 100.0
    assert calculate_experience_relevance(experience, None) == 100.0


def test_calculate_experience_relevance_proportional():
    """Experience score is proportional to duration vs requirement."""
    experience = [
        {"role": "Software Engineer", "company": "Beta Corp", "duration": "1 year", "description": "Backend"}
    ]
    # 1 year candidate for 2 years requirement -> 50%
    score = calculate_experience_relevance(experience, "2 years")
    assert score == pytest.approx(50.0, abs=1.0)


# ===========================================================================
# 4. Education Relevance Tests
# ===========================================================================

def test_calculate_education_relevance_empty_returns_zero():
    """If candidate has no education entries, return 0.0."""
    assert calculate_education_relevance([], {"title": "Software Engineer"}) == 0.0
    assert calculate_education_relevance(None, {"title": "Software Engineer"}) == 0.0


def test_calculate_education_relevance_aligned():
    """Candidate with B.Tech in Computer Science matching job profile."""
    education = [
        {"degree": "Bachelor of Technology", "branch": "Computer Science", "institution": "Tech University"}
    ]
    job = {
        "title": "Software Engineer",
        "description": "Python backend engineer",
        "allowed_branches": ["Computer Science", "Information Technology"],
    }
    score = calculate_education_relevance(education, job)
    # Base 50 + Branch match 30 + Degree keyword 20 = 100.0
    assert score == 100.0


# ===========================================================================
# 5. Hand-Computed Final Score Verification
# ===========================================================================

def test_calculate_final_score_hand_computed_check():
    """
    calculate_final_score with known component inputs produces the exact
    expected weighted output.

    Hand calculation:
      semantic_similarity  = 80.0  * 0.50 = 40.0
      skill_match_pct      = 70.0  * 0.25 = 17.5
      experience_relevance = 60.0  * 0.15 =  9.0
      education_relevance  = 90.0  * 0.10 =  9.0
      Total                = 40.0 + 17.5 + 9.0 + 9.0 = 75.5
    """
    final = calculate_final_score(
        semantic_similarity=80.0,
        skill_match_pct=70.0,
        experience_relevance=60.0,
        education_relevance=90.0,
    )
    assert final == 75.5


def test_calculate_final_score_second_hand_computed():
    """
    Second hand-computed test vector:
      semantic_similarity  = 92.4 * 0.50 = 46.20
      skill_match_pct      = 85.0 * 0.25 = 21.25
      experience_relevance = 40.0 * 0.15 =  6.00
      education_relevance  = 100.0 * 0.10 = 10.00
      Total                = 46.20 + 21.25 + 6.00 + 10.00 = 83.45 -> round to 1 decimal: 83.5
    """
    final = calculate_final_score(
        semantic_similarity=92.4,
        skill_match_pct=85.0,
        experience_relevance=40.0,
        education_relevance=100.0,
    )
    assert final == 73.5 or final == 83.5  # 83.45 rounds to 83.5
    assert final == pytest.approx(83.5, abs=0.1)


# ===========================================================================
# 6. Applicant Ranking & Tie-breaking Tests
# ===========================================================================

class MockApplication:
    """Lightweight test double for Application ORM model."""
    def __init__(self, id: int, ai_score: float | None, applied_at: datetime):
        self.id = id
        self.ai_score = ai_score
        self.applied_at = applied_at
        self.rank: int | None = None

    def __repr__(self):
        return f"<MockApp id={self.id} score={self.ai_score} rank={self.rank} applied_at={self.applied_at}>"


def test_rank_applicants_descending_order():
    """rank_applicants correctly orders a list of applications by score descending."""
    now = datetime.now(timezone.utc)
    app1 = MockApplication(id=1, ai_score=75.0, applied_at=now)
    app2 = MockApplication(id=2, ai_score=92.5, applied_at=now)
    app3 = MockApplication(id=3, ai_score=83.0, applied_at=now)

    ranked = rank_applicants([app1, app2, app3])

    assert ranked[0].id == 2  # score 92.5
    assert ranked[0].rank == 1

    assert ranked[1].id == 3  # score 83.0
    assert ranked[1].rank == 2

    assert ranked[2].id == 1  # score 75.0
    assert ranked[2].rank == 3


def test_rank_applicants_tie_breaking_by_applied_at():
    """
    When two scores are equal, break ties by earlier applied_at timestamp first
    (earlier application gets the better rank, i.e. rank 1 before rank 2).
    """
    t0 = datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 1, 11, 0, 0, tzinfo=timezone.utc)

    # app_early applied at 9:00 with score 85.0
    app_early = MockApplication(id=1, ai_score=85.0, applied_at=t0)
    # app_late applied at 11:00 with score 85.0
    app_late = MockApplication(id=2, ai_score=85.0, applied_at=t2)
    # app_mid applied at 10:00 with score 85.0
    app_mid = MockApplication(id=3, ai_score=85.0, applied_at=t1)

    # Pass in scrambled order
    ranked = rank_applicants([app_late, app_early, app_mid])

    # Earliest applicant gets rank 1
    assert ranked[0].id == 1
    assert ranked[0].rank == 1

    # Second earliest applicant gets rank 2
    assert ranked[1].id == 3
    assert ranked[1].rank == 2

    # Latest applicant gets rank 3
    assert ranked[2].id == 2
    assert ranked[2].rank == 3


def test_rank_applicants_with_unscored_applicant():
    """Unscored applicants (ai_score=None) are placed at the end with rank=None."""
    now = datetime.now(timezone.utc)
    app1 = MockApplication(id=1, ai_score=90.0, applied_at=now)
    app2 = MockApplication(id=2, ai_score=None, applied_at=now)
    app3 = MockApplication(id=3, ai_score=80.0, applied_at=now)

    ranked = rank_applicants([app1, app2, app3])

    assert ranked[0].id == 1
    assert ranked[0].rank == 1

    assert ranked[1].id == 3
    assert ranked[1].rank == 2

    assert ranked[2].id == 2
    assert ranked[2].rank is None


# ===========================================================================
# 7. Orchestration & Resilience (Partial Failure Test)
# ===========================================================================

def test_score_and_rank_job_applicants_partial_failure_resilience():
    """
    score_and_rank_job_applicants continues successfully scoring other applicants
    when one raises an embedding error (mock this).
    One bad resume must not block ranking everyone else.
    """
    # Create mock Job
    mock_job = MagicMock()
    mock_job.id = 101
    mock_job.title = "Backend Engineer"
    mock_job.description = "Python and FastAPI developer"
    mock_job.requirements = ["Python", "REST API"]
    mock_job.required_skills = ["Python", "FastAPI"]
    mock_job.preferred_skills = ["Docker"]
    mock_job.experience_requirement = "1 year"
    mock_job.allowed_branches = ["Computer Science"]
    mock_job.embedding = [0.1] * 384
    mock_job.embedding_hash = "job_hash_123"

    # Create 3 Mock Applications
    # Applicant A: Valid resume -> Should succeed
    mock_app_a = MagicMock()
    mock_app_a.id = 1
    mock_app_a.student_id = 11
    mock_app_a.job_id = 101
    mock_app_a.applied_at = datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc)
    mock_app_a.student = MagicMock(skills=["Python", "FastAPI"], experience=[], education=[], branch="Computer Science", year=2025, cgpa=8.5)
    mock_app_a.resume = MagicMock(
        extracted_text="Experienced Python FastAPI developer",
        parsed_data={"skills": ["Python", "FastAPI"], "experience": [], "education": []},
        embedding=[0.2] * 384,
        embedding_hash="hash_a",
    )
    mock_app_a.notes = None

    # Applicant B: Corrupted/bad resume that raises EmbeddingGenerationError
    mock_app_b = MagicMock()
    mock_app_b.id = 2
    mock_app_b.student_id = 12
    mock_app_b.job_id = 101
    mock_app_b.applied_at = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    mock_app_b.student = MagicMock(skills=[], experience=[], education=[], branch="Mechanical", year=2025, cgpa=7.0)
    mock_app_b.resume = MagicMock(
        extracted_text="corrupted text that causes error",
        parsed_data={},
        embedding=None,
        embedding_hash=None,
    )
    mock_app_b.notes = None

    # Applicant C: Valid resume -> Should succeed
    mock_app_c = MagicMock()
    mock_app_c.id = 3
    mock_app_c.student_id = 13
    mock_app_c.job_id = 101
    mock_app_c.applied_at = datetime(2026, 9, 1, 11, 0, 0, tzinfo=timezone.utc)
    mock_app_c.student = MagicMock(skills=["Python", "Docker"], experience=[], education=[], branch="Computer Science", year=2025, cgpa=9.0)
    mock_app_c.resume = MagicMock(
        extracted_text="Python and Docker engineer",
        parsed_data={"skills": ["Python", "Docker"], "experience": [], "education": []},
        embedding=[0.3] * 384,
        embedding_hash="hash_c",
    )
    mock_app_c.notes = None

    # Mock DB session
    mock_db = MagicMock()
    
    def mock_filter(condition):
        # We simulate job query or applications query
        mock_query_obj = MagicMock()
        # If querying Job
        mock_query_obj.first.return_value = mock_job
        # If querying Applications
        mock_query_obj.all.return_value = [mock_app_a, mock_app_b, mock_app_c]
        return mock_query_obj

    mock_db.query.return_value.filter = mock_filter

    # Patch get_or_generate_embedding to raise on App B's text
    def side_effect_embedding(text, cached_embedding=None, cached_text_hash=None, current_text_hash=None):
        if "corrupted" in text:
            raise EmbeddingGenerationError("Simulated embedding generation failure for corrupted resume.")
        return ([0.1] * 384, False)

    with patch("app.ai.scoring_engine.get_or_generate_embedding", side_effect=side_effect_embedding), \
         patch("app.ai.scoring_engine.cosine_similarity_score", return_value=85.0):

        results = score_and_rank_job_applicants(job_id=101, db_session=mock_db)

        # Database transaction was committed
        mock_db.commit.assert_called_once()

        # All 3 applications are returned
        assert len(results) == 3

        # Applicant B failed gracefully without crashing the whole batch
        assert mock_app_b.ai_score is None
        assert mock_app_b.rank is None
        assert "Scoring error" in str(mock_app_b.notes)

        # Applicant A and C were scored and ranked successfully
        assert mock_app_a.ai_score is not None
        assert mock_app_a.rank in (1, 2)

        assert mock_app_c.ai_score is not None
        assert mock_app_c.rank in (1, 2)
