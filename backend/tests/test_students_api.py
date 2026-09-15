# tests/test_students_api.py
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.database.connection import SessionLocal
from app.models.models import User, Student, Job, JobStatus, Company, UserRole
from app.core.security import hash_password

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_test_data():
    db = SessionLocal()
    # Create or retrieve test student
    student_user = db.query(User).filter(User.email == "test_student@example.com").first()
    if not student_user:
        student_user = User(
            email="test_student@example.com",
            hashed_password=hash_password("Password123!"),
            role=UserRole.STUDENT,
            full_name="Alex River",
            is_active=True,
        )
        db.add(student_user)
        db.commit()
        db.refresh(student_user)

    student = db.query(Student).filter(Student.user_id == student_user.id).first()
    if not student:
        student = Student(
            user_id=student_user.id,
            roll_number="TEST_STU_001",
            branch="Computer Science",
            year=2025,
            cgpa=8.5,
            backlog_count=0,
            skills=["Python", "FastAPI"],
        )
        db.add(student)
        db.commit()
        db.refresh(student)
    else:
        student.branch = "Computer Science"
        student.year = 2025
        student.cgpa = 8.5
        student.backlog_count = 0
        db.commit()

    token = create_access_token(subject=str(student_user.id), role="STUDENT")
    db.close()
    return {"token": token, "user_id": student_user.id}


def test_get_student_profile(setup_test_data):
    token = setup_test_data["token"]
    response = client.get("/students/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "test_student@example.com"
    assert data["data"]["cgpa"] == 8.5
    assert data["data"]["department"] == "Computer Science"
    assert "profile_completion_pct" in data["data"]


def test_update_student_profile_valid(setup_test_data):
    token = setup_test_data["token"]
    update_payload = {
        "department": "Information Technology",
        "batch": 2025,
        "cgpa": 9.1,
        "backlog_count": 0,
        "phone": "+91 9876543210",
        "skills": ["Python", "React", "Docker"],
        "education": [{"degree": "B.Tech", "institution": "Tech University", "year": 2025}],
        "full_name": "Alex River Updated",
    }
    response = client.put("/students/me", json=update_payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["cgpa"] == 9.1
    assert data["data"]["department"] == "Information Technology"
    assert data["data"]["name"] == "Alex River Updated"
    assert data["data"]["phone"] == "+91 9876543210"
    assert "React" in data["data"]["skills"]


def test_update_student_profile_invalid_cgpa(setup_test_data):
    token = setup_test_data["token"]
    payload = {"cgpa": 11.5}
    response = client.put("/students/me", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "VALIDATION_ERROR"


def test_update_student_profile_invalid_backlogs(setup_test_data):
    token = setup_test_data["token"]
    payload = {"backlog_count": -2}
    response = client.put("/students/me", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "VALIDATION_ERROR"


def test_upload_resume_reject_non_pdf(setup_test_data):
    token = setup_test_data["token"]
    fake_file = io.BytesIO(b"this is plain text, not a pdf")
    response = client.post(
        "/students/resume",
        files={"file": ("resume.txt", fake_file, "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False


def test_upload_resume_reject_corrupt_pdf(setup_test_data):
    token = setup_test_data["token"]
    fake_file = io.BytesIO(b"corrupt non-pdf header content")
    response = client.post(
        "/students/resume",
        files={"file": ("resume.pdf", fake_file, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "CORRUPTED_PDF"


def test_upload_resume_valid_pdf(setup_test_data):
    token = setup_test_data["token"]
    valid_pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (Test Resume) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    pdf_file = io.BytesIO(valid_pdf_content)
    response = client.post(
        "/students/resume",
        files={"file": ("alex_river_resume.pdf", pdf_file, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["filename"] == "alex_river_resume.pdf"
    assert data["data"]["is_primary"] is True


def test_get_student_jobs_with_eligibility(setup_test_data):
    token = setup_test_data["token"]
    response = client.get("/students/jobs?page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "items" in data["data"]
    assert len(data["data"]["items"]) > 0

    first_job = data["data"]["items"][0]
    assert "eligibility" in first_job
    assert "eligible" in first_job["eligibility"]
    assert isinstance(first_job["eligibility"]["reasons"], list)


def test_get_student_job_detail(setup_test_data):
    token = setup_test_data["token"]
    # Get first job id
    jobs_resp = client.get("/students/jobs?page=1&page_size=1", headers={"Authorization": f"Bearer {token}"})
    job_id = jobs_resp.json()["data"]["items"][0]["id"]

    response = client.get(f"/students/jobs/{job_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == job_id
    assert "eligibility" in data["data"]
    assert "eligible" in data["data"]["eligibility"]
    assert "reasons" in data["data"]["eligibility"]
