# tests/test_ai_pipeline_integration.py
# End-to-end integration tests for the full Phase 2 AI pipeline:
# Parsing -> Embedding -> Scoring -> Ranking -> Match Analysis -> CSV Export -> Recommendations.

import io
import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ai.scoring_engine import score_and_rank_job_applicants
from app.core.security import create_access_token, hash_password
from app.database.connection import SessionLocal
from app.models.models import (
    Application,
    ApplicationStatus,
    Company,
    Job,
    JobStatus,
    Recruiter,
    Resume,
    Student,
    User,
    UserRole,
)

client = TestClient(app)


SAMPLE_RESUME_TEXT = """
ALEX RIVERA
Software Engineer | Full Stack Developer
Email: alex.rivera@example.com | Phone: +1 555-019-2834
GitHub: github.com/alexrivera | LinkedIn: linkedin.com/in/alexrivera

SUMMARY
Motivated Software Engineer with 2+ years of experience in backend development,
distributed systems, and cloud architectures. Proficient in Python, FastAPI, PostgreSQL,
Docker, and AWS. Passionate about writing scalable, test-driven microservices.

TECHNICAL SKILLS
- Languages: Python, JavaScript, TypeScript, SQL
- Frameworks & Libraries: FastAPI, Django, Flask, React
- Databases: PostgreSQL, Redis, MongoDB
- DevOps & Cloud: Docker, Kubernetes, AWS (EC2, S3, RDS), CI/CD pipelines
- Tools: Git, Linux, Pytest, Postman

EXPERIENCE
Backend Software Engineer | CloudScale Tech (2023 - Present) - 2 years
- Architected and deployed RESTful APIs in FastAPI and PostgreSQL serving 100k+ daily users.
- Designed caching layer using Redis reducing 95th percentile response latency by 45%.
- Containerized microservices with Docker and managed deployment on AWS ECS.

Software Engineering Intern | NextGen Systems (2022 - 2023) - 1 year
- Developed core authentication modules and background worker queues using Python and Celery.
- Wrote extensive unit and integration tests achieving 90%+ code coverage.

EDUCATION
Bachelor of Technology in Computer Science and Engineering
Apex Institute of Technology, 2021 - 2025
CGPA: 8.8 / 10.0

PROJECTS
- Real-time Analytics Dashboard: Built with FastAPI, PostgreSQL, and React.
- Task Orchestration Engine: Distributed queue worker implemented in Python.
"""


@pytest.fixture(scope="module")
def ai_pipeline_fixture():
    """Seed users, recruiter, job, students, resumes and applications for full E2E pipeline tests."""
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    # 1. Company and Recruiter
    company = Company(
        name=f"E2E Tech Labs {suffix}",
        website="https://e2e.example.com",
        industry="Software",
    )
    db.add(company)
    db.flush()

    recruiter_user = User(
        email=f"recruiter_e2e_{suffix}@example.com",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.RECRUITER,
        full_name="E2E Recruiter Lead",
        is_active=True,
    )
    db.add(recruiter_user)
    db.flush()

    recruiter = Recruiter(
        user_id=recruiter_user.id,
        company_id=company.id,
        designation="Lead Hiring Manager",
    )
    db.add(recruiter)
    db.flush()

    # 2. Target Job
    job = Job(
        company_id=company.id,
        created_by=recruiter_user.id,
        title=f"Backend Python Engineer {suffix}",
        description="Seeking an exceptional backend engineer with expertise in Python, FastAPI, PostgreSQL, and AWS.",
        requirements=["2+ years backend experience", "Strong knowledge of Python and microservices"],
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        preferred_skills=["Docker", "AWS", "Redis"],
        min_cgpa=7.5,
        allowed_branches=["Computer Science", "Information Technology"],
        maximum_backlogs=0,
        eligible_batch=2025,
        experience_requirement="2 years",
        status=JobStatus.OPEN,
    )
    db.add(job)
    db.flush()

    # 3. Valid Student 1 (Alex - strong match)
    user_alex = User(
        email=f"alex_{suffix}@example.com",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.STUDENT,
        full_name="Alex Rivera",
        is_active=True,
    )
    db.add(user_alex)
    db.flush()

    student_alex = Student(
        user_id=user_alex.id,
        roll_number=f"ALEX_{suffix}",
        branch="Computer Science",
        year=2025,
        cgpa=8.8,
        backlog_count=0,
        skills=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
    )
    db.add(student_alex)
    db.flush()

    resume_alex = Resume(
        student_id=student_alex.id,
        file_path="mock/path/alex_resume.pdf",
        original_filename="alex_rivera_resume.pdf",
        is_primary=True,
        parsing_status="success",
        extracted_text=SAMPLE_RESUME_TEXT,
        parsed_data={
            "personal_info": {"name": "Alex Rivera", "email": user_alex.email, "phone": "+1 555-019-2834"},
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Redis"],
            "education": [{"degree": "Bachelor of Technology in Computer Science", "institution": "Apex Institute", "year": 2025}],
            "experience": [{"role": "Backend Software Engineer", "duration": "2 years", "company": "CloudScale Tech"}],
        },
    )
    db.add(resume_alex)
    db.flush()

    app_alex = Application(
        student_id=student_alex.id,
        job_id=job.id,
        resume_id=resume_alex.id,
        status=ApplicationStatus.ELIGIBILITY_VERIFIED,
        applied_at=datetime(2025, 1, 10, 10, 0, tzinfo=timezone.utc),
    )
    db.add(app_alex)
    db.flush()

    # 4. Valid Student 2 (Beth - partial match)
    user_beth = User(
        email=f"beth_{suffix}@example.com",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.STUDENT,
        full_name="Beth Harmon",
        is_active=True,
    )
    db.add(user_beth)
    db.flush()

    student_beth = Student(
        user_id=user_beth.id,
        roll_number=f"BETH_{suffix}",
        branch="Information Technology",
        year=2025,
        cgpa=7.9,
        backlog_count=0,
        skills=["Python", "SQL"],
    )
    db.add(student_beth)
    db.flush()

    resume_beth = Resume(
        student_id=student_beth.id,
        file_path="mock/path/beth_resume.pdf",
        original_filename="beth_harmon_resume.pdf",
        is_primary=True,
        parsing_status="success",
        extracted_text="BETH HARMON\nJunior Developer\nSkills: Python, SQL\nEducation: B.Tech IT\nExperience: 6 months internship.",
        parsed_data={
            "personal_info": {"name": "Beth Harmon", "email": user_beth.email, "phone": "+1 555-987-6543"},
            "skills": ["Python", "SQL"],
            "education": [{"degree": "B.Tech in Information Technology", "institution": "Apex Institute", "year": 2025}],
            "experience": [{"role": "Intern", "duration": "6 months"}],
        },
    )
    db.add(resume_beth)
    db.flush()

    app_beth = Application(
        student_id=student_beth.id,
        job_id=job.id,
        resume_id=resume_beth.id,
        status=ApplicationStatus.ELIGIBILITY_VERIFIED,
        applied_at=datetime(2025, 1, 11, 10, 0, tzinfo=timezone.utc),
    )
    db.add(app_beth)
    db.flush()

    # 5. Corrupted Resume Student 3 (Charlie - corrupted resume)
    user_charlie = User(
        email=f"charlie_corrupt_{suffix}@example.com",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.STUDENT,
        full_name="Charlie Corrupt",
        is_active=True,
    )
    db.add(user_charlie)
    db.flush()

    student_charlie = Student(
        user_id=user_charlie.id,
        roll_number=f"CHARLIE_{suffix}",
        branch="Mechanical",
        year=2025,
        cgpa=6.0,
        backlog_count=2,
        skills=[],
    )
    db.add(student_charlie)
    db.flush()

    resume_charlie = Resume(
        student_id=student_charlie.id,
        file_path="mock/path/charlie_corrupt.pdf",
        original_filename="corrupted_file.pdf",
        is_primary=True,
        parsing_status="failed",
        parsing_error="Unable to extract text from this resume. It may be a scanned image or corrupted file.",
        extracted_text=None,
        parsed_data=None,
    )
    db.add(resume_charlie)
    db.flush()

    app_charlie = Application(
        student_id=student_charlie.id,
        job_id=job.id,
        resume_id=resume_charlie.id,
        status=ApplicationStatus.APPLIED,
        applied_at=datetime(2025, 1, 12, 10, 0, tzinfo=timezone.utc),
    )
    db.add(app_charlie)
    db.flush()

    db.commit()

    recruiter_token = create_access_token(subject=str(recruiter_user.id), role=recruiter_user.role.value)
    alex_token = create_access_token(subject=str(user_alex.id), role=user_alex.role.value)
    beth_token = create_access_token(subject=str(user_beth.id), role=user_beth.role.value)
    charlie_token = create_access_token(subject=str(user_charlie.id), role=user_charlie.role.value)

    data = {
        "job_id": job.id,
        "company_id": company.id,
        "recruiter_id": recruiter.id,
        "recruiter_user_id": recruiter_user.id,
        "recruiter_token": recruiter_token,
        "alex_token": alex_token,
        "beth_token": beth_token,
        "charlie_token": charlie_token,
        "app_alex_id": app_alex.id,
        "app_beth_id": app_beth.id,
        "app_charlie_id": app_charlie.id,
        "student_alex_id": student_alex.id,
        "student_charlie_id": student_charlie.id,
        "resume_alex_id": resume_alex.id,
    }
    db.close()
    return data


def test_e2e_full_pipeline_parse_embed_score_rank(ai_pipeline_fixture):
    """
    E2E Integration Test:
    Runs the full AI pipeline (parse -> embed -> score -> rank) and verifies
    non-null scores, correct relative ranking, and graceful DB persistence.
    """
    job_id = ai_pipeline_fixture["job_id"]
    recruiter_token = ai_pipeline_fixture["recruiter_token"]

    db = SessionLocal()
    try:
        # Run scoring & ranking pipeline
        ranked_apps = score_and_rank_job_applicants(job_id=job_id, db_session=db)
        assert len(ranked_apps) == 3

        # Alex should be top ranked (rank 1) with high non-null score
        alex_app = next(a for a in ranked_apps if a.id == ai_pipeline_fixture["app_alex_id"])
        assert alex_app.ai_score is not None
        assert alex_app.ai_score >= 70.0
        assert alex_app.semantic_score is not None
        assert alex_app.semantic_score > 0
        assert alex_app.skill_score is not None
        assert alex_app.skill_score == 100.0  # has Python, FastAPI, PostgreSQL, Docker, AWS
        assert alex_app.experience_score is not None
        assert alex_app.education_score is not None
        assert alex_app.rank == 1

        # Beth should have rank 2 with lower score than Alex
        beth_app = next(a for a in ranked_apps if a.id == ai_pipeline_fixture["app_beth_id"])
        assert beth_app.ai_score is not None
        assert beth_app.ai_score < alex_app.ai_score
        assert beth_app.rank == 2

    finally:
        db.close()

    # Recruiter views the ranked applicants via API
    resp = client.get(
        f"/applications/jobs/{job_id}/applications",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert resp.status_code == 200
    res_data = resp.json()["data"]
    assert res_data["total"] == 3
    items = res_data["items"]
    # First item should be rank 1 (Alex)
    assert items[0]["application_id"] == ai_pipeline_fixture["app_alex_id"]
    assert items[0]["rank"] == 1
    assert items[0]["ai_score"] is not None
    assert items[0]["student_name"] == "Alex Rivera"


def test_corrupted_resume_does_not_block_applicant_pool(ai_pipeline_fixture, monkeypatch):
    """
    Test that an applicant with a corrupted/unparseable resume does NOT prevent
    the rest of the applicant pool from being scored and ranked.
    Also tests that runtime AI exception on one candidate fails gracefully to None
    without crashing the request or losing the application record.
    """
    job_id = ai_pipeline_fixture["job_id"]
    recruiter_token = ai_pipeline_fixture["recruiter_token"]

    db = SessionLocal()
    try:
        ranked_apps = score_and_rank_job_applicants(job_id=job_id, db_session=db)
        assert len(ranked_apps) == 3

        # Top applicants (Alex & Beth) are correctly scored and ranked
        alex_app = next(a for a in ranked_apps if a.id == ai_pipeline_fixture["app_alex_id"])
        beth_app = next(a for a in ranked_apps if a.id == ai_pipeline_fixture["app_beth_id"])
        charlie_app = next(a for a in ranked_apps if a.id == ai_pipeline_fixture["app_charlie_id"])

        assert alex_app.rank == 1
        assert alex_app.ai_score > beth_app.ai_score
        assert beth_app.rank == 2
        # Charlie (corrupted resume) has fallback score / rank and never crashes
        assert charlie_app.rank == 3
        assert charlie_app.ai_score < beth_app.ai_score
    finally:
        db.close()

    # Now simulate a catastrophic embedding error specifically for Charlie
    # to verify total resilience when an exception occurs inside the candidate scoring loop
    from app.ai import scoring_engine

    orig_get_or_gen = scoring_engine.get_or_generate_embedding

    def faulty_get_or_generate(text, cached_embedding, cached_text_hash=None, current_text_hash=None):
        if "Charlie" in text or "Mechanical" in text:
            raise scoring_engine.EmbeddingGenerationError("Simulated model failure on corrupted candidate")
        return orig_get_or_gen(text, cached_embedding, cached_text_hash, current_text_hash)

    monkeypatch.setattr(scoring_engine, "get_or_generate_embedding", faulty_get_or_generate)

    db2 = SessionLocal()
    try:
        resilient_apps = scoring_engine.score_and_rank_job_applicants(job_id=job_id, db_session=db2)
        assert len(resilient_apps) == 3

        # Charlie should have null scores and null rank due to the exception
        charlie_failed = next(a for a in resilient_apps if a.id == ai_pipeline_fixture["app_charlie_id"])
        assert charlie_failed.ai_score is None
        assert charlie_failed.rank is None

        # Alex and Beth still scored and ranked 1 & 2
        alex_ok = next(a for a in resilient_apps if a.id == ai_pipeline_fixture["app_alex_id"])
        beth_ok = next(a for a in resilient_apps if a.id == ai_pipeline_fixture["app_beth_id"])
        assert alex_ok.rank == 1
        assert beth_ok.rank == 2
        assert alex_ok.ai_score is not None
        assert beth_ok.ai_score is not None
    finally:
        db2.close()

    # API returns all applicants gracefully without 500 error
    resp = client.get(
        f"/applications/jobs/{job_id}/applications",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) == 3


def test_embedding_and_score_cache_reuse(ai_pipeline_fixture):
    """
    Test that second pass scoring reuses cached embeddings and doesn't crash or recompute.
    """
    job_id = ai_pipeline_fixture["job_id"]
    db = SessionLocal()
    try:
        # First pass
        score_and_rank_job_applicants(job_id=job_id, db_session=db)

        job = db.query(Job).filter(Job.id == job_id).first()
        resume_alex = db.query(Resume).filter(Resume.id == ai_pipeline_fixture["resume_alex_id"]).first()

        orig_job_hash = job.embedding_hash
        orig_resume_hash = resume_alex.embedding_hash
        assert orig_job_hash is not None
        assert orig_resume_hash is not None

        # Second pass
        ranked_apps = score_and_rank_job_applicants(job_id=job_id, db_session=db)
        assert len(ranked_apps) == 3

        db.refresh(job)
        db.refresh(resume_alex)
        assert job.embedding_hash == orig_job_hash
        assert resume_alex.embedding_hash == orig_resume_hash
    finally:
        db.close()


def test_match_analysis_endpoint_detailed_breakdown(ai_pipeline_fixture):
    """
    Test GET /applications/{id}/match-analysis returns full transparent scoring breakdown.
    """
    app_alex_id = ai_pipeline_fixture["app_alex_id"]
    recruiter_token = ai_pipeline_fixture["recruiter_token"]
    alex_token = ai_pipeline_fixture["alex_token"]

    # Recruiter view
    resp = client.get(
        f"/applications/{app_alex_id}/match-analysis",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["application_id"] == app_alex_id
    assert data["overall_score"] is not None
    assert data["semantic_similarity"] is not None
    assert data["skill_match_percentage"] == 100.0
    assert "Python" in data["matching_skills"]
    assert "FastAPI" in data["matching_skills"]
    assert "PostgreSQL" in data["matching_skills"]
    assert data["scoring_available"] is True
    assert data["eligibility"]["eligible"] is True

    # Student own view
    resp_student = client.get(
        f"/applications/{app_alex_id}/match-analysis",
        headers={"Authorization": f"Bearer {alex_token}"},
    )
    assert resp_student.status_code == 200
    assert resp_student.json()["data"]["candidate_name"] == "Alex Rivera"


def test_recommended_jobs_endpoint_independent_eligibility(ai_pipeline_fixture):
    """
    Test GET /students/recommended-jobs provides semantic score and independent eligibility.
    """
    alex_token = ai_pipeline_fixture["alex_token"]

    resp = client.get(
        "/students/recommended-jobs",
        headers={"Authorization": f"Bearer {alex_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["has_resume"] is True
    assert len(data["items"]) > 0
    first_job = data["items"][0]
    assert first_job["semantic_score"] is not None
    assert first_job["semantic_score"] > 0
    assert "eligibility" in first_job
    assert isinstance(first_job["eligibility"]["eligible"], bool)


def test_export_ranked_applicants_csv(ai_pipeline_fixture):
    """
    Test GET /jobs/{job_id}/applications/export produces a well-formed CSV
    with all required columns and valid values (no blank or corrupted output).
    """
    job_id = ai_pipeline_fixture["job_id"]
    recruiter_token = ai_pipeline_fixture["recruiter_token"]

    resp = client.get(
        f"/applications/jobs/{job_id}/applications/export?top_k=5&format=csv",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "attachment; filename=" in resp.headers["content-disposition"]

    csv_text = resp.text
    lines = csv_text.strip().split("\r\n") if "\r\n" in csv_text else csv_text.strip().split("\n")
    assert len(lines) >= 3  # Header + at least 2 scored/ranked candidates

    header = lines[0]
    assert "Rank" in header
    assert "Candidate Name" in header
    assert "Email" in header
    assert "Phone" in header
    assert "Department" in header
    assert "AI Score" in header
    assert "Semantic Similarity" in header
    assert "Skill Match %" in header
    assert "Matching Skills" in header
    assert "Missing Required Skills" in header

    # Alex should be in the first row
    assert "Alex Rivera" in lines[1]
    assert "Python" in lines[1]
