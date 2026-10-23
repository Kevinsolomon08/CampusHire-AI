# tests/test_scoring_api.py
# Integration tests for AI scoring endpoints, match analysis, and ranking defaults.

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
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


@pytest.fixture(scope="module")
def scoring_api_fixture():
    """Setup test company, recruiter, students with resumes, job, and applications."""
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    # 1. Company and Recruiter
    company = Company(
        name=f"AI Scoring Corp {suffix}",
        website="https://aiscoring.example.com",
        industry="Technology",
    )
    db.add(company)
    db.flush()

    recruiter_user = User(
        email=f"recruiter_score_{suffix}@test.com",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.RECRUITER,
        full_name="Score Recruiter",
        is_active=True,
    )
    db.add(recruiter_user)
    db.flush()

    recruiter = Recruiter(
        user_id=recruiter_user.id,
        company_id=company.id,
        designation="Lead AI Talent Partner",
    )
    db.add(recruiter)
    db.flush()

    # 2. Job posting
    job = Job(
        company_id=company.id,
        created_by=recruiter_user.id,
        title=f"Senior Python Engineer {suffix}",
        description="Looking for an experienced Python and FastAPI backend developer with PostgreSQL skills.",
        requirements=["3+ years experience", "Strong Python knowledge"],
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        preferred_skills=["Docker", "AWS"],
        min_cgpa=7.0,
        allowed_branches=["Computer Science", "Information Technology"],
        maximum_backlogs=1,
        eligible_batch=2025,
        experience_requirement="2 years",
        status=JobStatus.OPEN,
    )
    db.add(job)
    db.flush()

    # 3. Student 1 (Top Match: has all skills, 9.0 CGPA, CS branch)
    user_s1 = User(
        email=f"alice_top_{suffix}@test.com",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.STUDENT,
        full_name="Alice Top Match",
        is_active=True,
    )
    db.add(user_s1)
    db.flush()

    student_1 = Student(
        user_id=user_s1.id,
        roll_number=f"TOP_{suffix}",
        branch="Computer Science",
        year=2025,
        cgpa=9.2,
        backlog_count=0,
        skills=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
    )
    db.add(student_1)
    db.flush()

    resume_1 = Resume(
        student_id=student_1.id,
        file_path=f"uploads/alice_{suffix}.pdf",
        extracted_text="Senior Python developer with 3 years experience building FastAPI backends and PostgreSQL databases with Docker and AWS.",
        parsed_data={
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
            "experience": [{"role": "Python Dev", "company": "Alpha Corp", "duration": "2 years"}],
            "education": [{"degree": "B.Tech in Computer Science", "institution": "Top Tech", "year": 2025}],
        },
        parsing_status="success",
    )
    db.add(resume_1)
    db.flush()

    app_1 = Application(
        student_id=student_1.id,
        job_id=job.id,
        resume_id=resume_1.id,
        status=ApplicationStatus.ELIGIBILITY_VERIFIED,
        applied_at=datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc),
    )
    db.add(app_1)

    # 4. Student 2 (Partial Match: Python only, no FastAPI/PostgreSQL, 7.5 CGPA)
    user_s2 = User(
        email=f"bob_mid_{suffix}@test.com",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.STUDENT,
        full_name="Bob Mid Match",
        is_active=True,
    )
    db.add(user_s2)
    db.flush()

    student_2 = Student(
        user_id=user_s2.id,
        roll_number=f"MID_{suffix}",
        branch="Computer Science",
        year=2025,
        cgpa=7.5,
        backlog_count=0,
        skills=["Python", "Django"],
    )
    db.add(student_2)
    db.flush()

    resume_2 = Resume(
        student_id=student_2.id,
        file_path=f"uploads/bob_{suffix}.pdf",
        extracted_text="Junior developer with Python and Django knowledge.",
        parsed_data={
            "skills": ["Python", "Django"],
            "experience": [{"role": "Intern", "company": "Beta Corp", "duration": "6 months"}],
            "education": [{"degree": "B.Tech in Computer Science", "institution": "City College", "year": 2025}],
        },
        parsing_status="success",
    )
    db.add(resume_2)
    db.flush()

    app_2 = Application(
        student_id=student_2.id,
        job_id=job.id,
        resume_id=resume_2.id,
        status=ApplicationStatus.ELIGIBILITY_VERIFIED,
        applied_at=datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    db.add(app_2)

    db.commit()

    recruiter_token = create_access_token(subject=str(recruiter_user.id), role="RECRUITER")
    student_1_token = create_access_token(subject=str(user_s1.id), role="STUDENT")
    student_2_token = create_access_token(subject=str(user_s2.id), role="STUDENT")

    yield {
        "job_id": job.id,
        "app_1_id": app_1.id,
        "app_2_id": app_2.id,
        "recruiter_token": recruiter_token,
        "student_1_token": student_1_token,
        "student_2_token": student_2_token,
    }


def test_get_job_applicants_auto_scores_and_ranks_default(scoring_api_fixture):
    """
    GET /jobs/{job_id}/applications auto-scores unscored applicants and returns
    them sorted by rank (rank 1 first).
    """
    job_id = scoring_api_fixture["job_id"]
    token = scoring_api_fixture["recruiter_token"]

    response = client.get(
        f"/applications/jobs/{job_id}/applications",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    items = body["data"]["items"]
    assert len(items) == 2

    # Verify rank 1 is first and has higher AI score
    first = items[0]
    second = items[1]

    assert first["rank"] == 1
    assert second["rank"] == 2
    assert first["ai_score"] >= second["ai_score"]
    assert first["skill_score"] is not None
    assert first["student_name"] == "Alice Top Match"


def test_get_job_applicants_min_ai_score_filter(scoring_api_fixture):
    """
    GET /jobs/{job_id}/applications with min_ai_score filter filters out lower-scoring candidates.
    """
    job_id = scoring_api_fixture["job_id"]
    token = scoring_api_fixture["recruiter_token"]

    # Filter for high scores (e.g. >= 70)
    response = client.get(
        f"/applications/jobs/{job_id}/applications?min_ai_score=70.0",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    items = body["data"]["items"]

    # Only candidates with ai_score >= 70.0 should be returned
    for item in items:
        assert item["ai_score"] >= 70.0


def test_post_recalculate_job_scores(scoring_api_fixture):
    """
    POST /jobs/{job_id}/recalculate-scores manually triggers rescoring and returns success.
    """
    job_id = scoring_api_fixture["job_id"]
    token = scoring_api_fixture["recruiter_token"]

    response = client.post(
        f"/applications/jobs/{job_id}/recalculate-scores",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["scored_count"] == 2
    assert body["data"]["job_id"] == job_id


def test_get_application_match_analysis_success(scoring_api_fixture):
    """
    GET /applications/{id}/match-analysis returns full breakdown:
    overall_score, semantic_similarity, skill_match_percentage, experience_relevance,
    education_relevance, matching_skills, missing_required_skills, rank, eligibility result.
    """
    app_1_id = scoring_api_fixture["app_1_id"]
    token = scoring_api_fixture["recruiter_token"]

    response = client.get(
        f"/applications/{app_1_id}/match-analysis",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    data = body["data"]
    assert data["application_id"] == app_1_id
    assert data["overall_score"] is not None
    assert data["semantic_similarity"] is not None
    assert data["skill_match_percentage"] is not None
    assert data["experience_relevance"] is not None
    assert data["education_relevance"] is not None

    # Matching skills for Student 1
    assert "Python" in data["matching_skills"]
    assert "FastAPI" in data["matching_skills"]
    assert "PostgreSQL" in data["matching_skills"]
    assert data["missing_required_skills"] == []
    assert "Docker" in data["matching_preferred_skills"]

    # Rank and Eligibility
    assert data["rank"] == 1
    assert data["eligibility"]["eligible"] is True

    # Disclaimer text is present
    assert "screening aid" in data["disclaimer"].lower()


def test_get_application_match_analysis_student_view_own(scoring_api_fixture):
    """Student can view match analysis for their own application."""
    app_1_id = scoring_api_fixture["app_1_id"]
    student_token = scoring_api_fixture["student_1_token"]

    response = client.get(
        f"/applications/{app_1_id}/match-analysis",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_get_application_match_analysis_forbidden_for_other_student(scoring_api_fixture):
    """Student cannot view match analysis for another student's application."""
    app_1_id = scoring_api_fixture["app_1_id"]
    student_2_token = scoring_api_fixture["student_2_token"]

    response = client.get(
        f"/applications/{app_1_id}/match-analysis",
        headers={"Authorization": f"Bearer {student_2_token}"},
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"


# ===========================================================================
# CSV Export Tests
# ===========================================================================

def test_export_job_applicants_csv_top_k(scoring_api_fixture):
    """
    GET /jobs/{job_id}/applications/export?top_k=1&format=csv returns CSV file
    with correct headers and top 1 candidate.
    """
    job_id = scoring_api_fixture["job_id"]
    token = scoring_api_fixture["recruiter_token"]

    response = client.get(
        f"/applications/jobs/{job_id}/applications/export?top_k=1&format=csv",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert "attachment" in response.headers.get("content-disposition", "")
    assert "_top_1_candidates.csv" in response.headers.get("content-disposition", "")

    content = response.text
    lines = [line.strip() for line in content.strip().split("\n") if line.strip()]

    # Header + 1 row
    assert len(lines) == 2

    # Check exact column headers
    header_cols = [c.strip() for c in lines[0].split(",")]
    expected_headers = [
        "Rank",
        "Candidate Name",
        "Email",
        "Phone",
        "Department",
        "Batch",
        "CGPA",
        "Backlogs",
        "AI Score",
        "Semantic Similarity",
        "Skill Match %",
        "Matching Skills",
        "Missing Required Skills",
        "Application Status",
        "Applied Date",
    ]
    assert header_cols == expected_headers

    # Top candidate row (Alice)
    assert "Alice Top Match" in lines[1]
    assert "1" in lines[1]  # Rank 1


def test_export_job_applicants_csv_all(scoring_api_fixture):
    """
    GET /jobs/{job_id}/applications/export?format=csv without top_k exports all
    eligible applicants ordered by rank.
    """
    job_id = scoring_api_fixture["job_id"]
    token = scoring_api_fixture["recruiter_token"]

    response = client.get(
        f"/applications/jobs/{job_id}/applications/export?format=csv",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert "_top_all_candidates.csv" in response.headers.get("content-disposition", "")

    content = response.text
    lines = [line.strip() for line in content.strip().split("\n") if line.strip()]

    # Header + 2 candidate rows
    assert len(lines) == 3
    assert "Alice Top Match" in lines[1]
    assert "Bob Mid Match" in lines[2]


def test_export_job_applicants_csv_top_k_exceeds(scoring_api_fixture):
    """
    top_k exceeding applicant count exports all available applicants without error.
    """
    job_id = scoring_api_fixture["job_id"]
    token = scoring_api_fixture["recruiter_token"]

    response = client.get(
        f"/applications/jobs/{job_id}/applications/export?top_k=100&format=csv",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    lines = [line.strip() for line in response.text.strip().split("\n") if line.strip()]
    assert len(lines) == 3


def test_export_job_applicants_csv_forbidden_for_other_recruiter(scoring_api_fixture):
    """A recruiter from a different company cannot export another company's job applicants."""
    job_id = scoring_api_fixture["job_id"]

    db = SessionLocal()
    suffix = uuid.uuid4().hex[:6]
    other_company = Company(name=f"Other Corp {suffix}", website="https://other.com")
    db.add(other_company)
    db.flush()

    other_user = User(
        email=f"other_rec_{suffix}@test.com",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.RECRUITER,
        full_name="Other Recruiter",
        is_active=True,
    )
    db.add(other_user)
    db.flush()

    other_rec = Recruiter(user_id=other_user.id, company_id=other_company.id)
    db.add(other_rec)
    db.commit()

    other_token = create_access_token(subject=str(other_user.id), role="RECRUITER")
    db.close()

    response = client.get(
        f"/applications/jobs/{job_id}/applications/export?format=csv",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"


def test_export_job_applicants_csv_no_applicants_error(scoring_api_fixture):
    """Exporting a job with 0 applicants returns 400 error instead of broken CSV."""
    token = scoring_api_fixture["recruiter_token"]
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    # Find the company id for the recruiter
    job_obj = db.query(Job).filter(Job.id == scoring_api_fixture["job_id"]).first()

    empty_job = Job(
        company_id=job_obj.company_id,
        title=f"Empty Job {suffix}",
        description="No applications yet",
        status=JobStatus.OPEN,
    )
    db.add(empty_job)
    db.commit()
    db.refresh(empty_job)
    empty_job_id = empty_job.id
    db.close()

    response = client.get(
        f"/applications/jobs/{empty_job_id}/applications/export?format=csv",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "No scored applicants available" in response.json()["message"]
