# tests/test_resumes_api.py
# Integration tests for resume upload, parsing endpoints, and student prefill flows.

import io
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token, hash_password
from app.database.connection import SessionLocal
from app.models.models import Resume, Student, User, UserRole
from app.ai.resume_parser import ResumeExtractionError

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_resume_test_data():
    db = SessionLocal()

    # Create Student A
    student_user_a = db.query(User).filter(User.email == "student_resume_a@example.com").first()
    if not student_user_a:
        student_user_a = User(
            email="student_resume_a@example.com",
            hashed_password=hash_password("Password123!"),
            role=UserRole.STUDENT,
            full_name="Alice Parse",
            is_active=True,
        )
        db.add(student_user_a)
        db.commit()
        db.refresh(student_user_a)

    student_a = db.query(Student).filter(Student.user_id == student_user_a.id).first()
    if not student_a:
        student_a = Student(
            user_id=student_user_a.id,
            roll_number="PARSE_STU_001",
            branch="Computer Science",
            year=2025,
            cgpa=9.0,
            backlog_count=0,
            skills=["Python"],
        )
        db.add(student_a)
        db.commit()
        db.refresh(student_a)

    # Create Student B (for cross-tenant tests)
    student_user_b = db.query(User).filter(User.email == "student_resume_b@example.com").first()
    if not student_user_b:
        student_user_b = User(
            email="student_resume_b@example.com",
            hashed_password=hash_password("Password123!"),
            role=UserRole.STUDENT,
            full_name="Bob Other",
            is_active=True,
        )
        db.add(student_user_b)
        db.commit()
        db.refresh(student_user_b)

    student_b = db.query(Student).filter(Student.user_id == student_user_b.id).first()
    if not student_b:
        student_b = Student(
            user_id=student_user_b.id,
            roll_number="PARSE_STU_002",
            branch="Mechanical",
            year=2025,
            cgpa=8.0,
            backlog_count=0,
        )
        db.add(student_b)
        db.commit()
        db.refresh(student_b)

    # Create Recruiter (for role tests)
    recruiter_user = db.query(User).filter(User.email == "recruiter_resume_test@example.com").first()
    if not recruiter_user:
        recruiter_user = User(
            email="recruiter_resume_test@example.com",
            hashed_password=hash_password("Password123!"),
            role=UserRole.RECRUITER,
            full_name="Recruiter Tester",
            is_active=True,
        )
        db.add(recruiter_user)
        db.commit()
        db.refresh(recruiter_user)

    token_a = create_access_token(subject=str(student_user_a.id), role="STUDENT")
    token_b = create_access_token(subject=str(student_user_b.id), role="STUDENT")
    token_recruiter = create_access_token(subject=str(recruiter_user.id), role="RECRUITER")

    db.close()

    return {
        "token_a": token_a,
        "token_b": token_b,
        "token_recruiter": token_recruiter,
        "student_a_id": student_a.id,
        "student_b_id": student_b.id,
    }


def test_upload_resume_with_inline_parsing(setup_resume_test_data):
    token_a = setup_resume_test_data["token_a"]

    # Mock PDF extraction to return sample text
    sample_text = """
    Alice Parse
    Email: alice.parse@example.com | Phone: +1 555 123 4567
    
    Education
    B.Tech in Computer Science, Stanford University, 2025, CGPA: 9.2
    
    Skills
    Python, FastAPI, React, PostgreSQL, Docker, Machine Learning
    
    Experience
    Software Engineering Intern at Google
    Jun 2024 - Aug 2024
    Built scalable microservices and REST APIs using FastAPI and Redis.
    
    Projects
    Campus Placement Portal
    Engineered full-stack portal with React and Python.
    """

    valid_pdf_content = b"%PDF-1.4\nMock PDF stream content for testing.\n%%EOF"
    pdf_file = io.BytesIO(valid_pdf_content)

    with patch("app.api.resumes.extract_text_from_pdf", return_value=sample_text):
        response = client.post(
            "/students/resume",
            files={"file": ("alice_resume.pdf", pdf_file, "application/pdf")},
            headers={"Authorization": f"Bearer {token_a}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["parsing_status"] == "success"
    assert data["data"]["parsed_data"] is not None
    assert "Python" in data["data"]["parsed_data"]["skills"]
    assert "FastAPI" in data["data"]["parsed_data"]["skills"]


def test_get_parsed_resume_endpoint(setup_resume_test_data):
    token_a = setup_resume_test_data["token_a"]

    response = client.get(
        "/students/me/parsed-resume",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["parsing_status"] == "success"
    assert data["data"]["parsed_data"] is not None
    assert "skills" in data["data"]["parsed_data"]


def test_post_resume_reparse_success(setup_resume_test_data):
    token_a = setup_resume_test_data["token_a"]

    # First get primary resume id
    res_resp = client.get("/students/resume", headers={"Authorization": f"Bearer {token_a}"})
    resume_id = res_resp.json()["data"]["id"]

    sample_text = """
    Alice Parse
    alice.parse@example.com
    Skills: Python, TypeScript, GraphQL, AWS
    """

    with patch("app.api.resumes.extract_text_from_pdf", return_value=sample_text):
        response = client.post(
            f"/resumes/{resume_id}/parse",
            headers={"Authorization": f"Bearer {token_a}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["parsing_status"] == "success"
    assert "Python" in data["data"]["parsed_data"]["skills"]
    assert "TypeScript" in data["data"]["parsed_data"]["skills"]


def test_post_resume_reparse_failure_fallback(setup_resume_test_data):
    token_a = setup_resume_test_data["token_a"]

    res_resp = client.get("/students/resume", headers={"Authorization": f"Bearer {token_a}"})
    resume_id = res_resp.json()["data"]["id"]

    # Force extraction error (e.g. scanned image)
    with patch(
        "app.api.resumes.extract_text_from_pdf",
        side_effect=ResumeExtractionError("Unable to extract text"),
    ):
        response = client.post(
            f"/resumes/{resume_id}/parse",
            headers={"Authorization": f"Bearer {token_a}"},
        )

    # Must return 200 with success=True and parsing_status="failed", never 500
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["parsing_status"] == "failed"
    assert data["data"]["parsed_data"] is None
    assert "Manual" in data["message"] or "manual" in data["message"]


def test_cross_student_resume_parse_forbidden(setup_resume_test_data):
    token_b = setup_resume_test_data["token_b"]
    token_a = setup_resume_test_data["token_a"]

    # Get student A's resume id
    res_resp = client.get("/students/resume", headers={"Authorization": f"Bearer {token_a}"})
    resume_id_a = res_resp.json()["data"]["id"]

    # Student B attempts to parse Student A's resume
    response = client.post(
        f"/resumes/{resume_id_a}/parse",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "RESUME_NOT_FOUND"


def test_recruiter_cannot_call_resume_parse(setup_resume_test_data):
    token_recruiter = setup_resume_test_data["token_recruiter"]

    response = client.post(
        "/resumes/1/parse",
        headers={"Authorization": f"Bearer {token_recruiter}"},
    )
    assert response.status_code == 403
