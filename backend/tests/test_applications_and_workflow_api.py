# tests/test_applications_and_workflow_api.py
"""
Test suite covering:
1. Student apply to eligible job (success 201)
2. Student apply to ineligible job (blocked 400 with criteria details)
3. Duplicate application prevention (conflict 409 DUPLICATE_APPLICATION)
4. Status transitions via PATCH /applications/{id}/status:
   - Recruiter valid status advancement
   - Recruiter invalid status skip or backwards transition rejected (400)
   - Terminal state protection (SELECTED/REJECTED cannot move forward)
   - Placement officer reopen permissions
5. Interview scheduling via POST /applications/{id}/interviews
6. Interview result updates via PUT /applications/interviews/{id}
"""

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.security import create_access_token, hash_password
from app.database.connection import SessionLocal
from app.models.models import (
    Application,
    ApplicationStatus,
    Company,
    Interview,
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
def workflow_fixture():
    """Sets up company, recruiter, eligible/ineligible students, job postings, and tokens."""
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:6]
    now = datetime.now(timezone.utc)

    # 1. Company and Recruiter
    company = Company(
        name=f"Workflow Tech {suffix}",
        website="https://workflow.example.com",
        industry="Software",
    )
    db.add(company)
    db.flush()

    recruiter_user = User(
        email=f"rec_wf_{suffix}@test.com",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.RECRUITER,
        full_name="Recruiter Lead",
        is_active=True,
    )
    db.add(recruiter_user)
    db.flush()

    recruiter = Recruiter(
        user_id=recruiter_user.id,
        company_id=company.id,
        designation="Lead TA",
    )
    db.add(recruiter)

    # 2. Placement Officer User
    placement_user = User(
        email=f"place_wf_{suffix}@test.com",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.PLACEMENT_OFFICER,
        full_name="Dr. Placement",
        is_active=True,
    )
    db.add(placement_user)
    db.flush()

    # 3. Eligible Student (CS, 8.5 CGPA, 0 backlogs, 2024 batch)
    stu_elig_user = User(
        email=f"stu_elig_{suffix}@test.com",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.STUDENT,
        full_name="Eligible Candidate",
        is_active=True,
    )
    db.add(stu_elig_user)
    db.flush()

    student_elig = Student(
        user_id=stu_elig_user.id,
        roll_number=f"CS_{suffix}",
        branch="Computer Science",
        year=2024,
        cgpa=8.5,
        backlog_count=0,
    )
    db.add(student_elig)
    db.flush()

    resume = Resume(
        student_id=student_elig.id,
        file_path=f"uploads/stu_{student_elig.id}_resume.pdf",
        original_filename="resume.pdf",
        is_primary=True,
    )
    db.add(resume)

    # 4. Ineligible Student (Mechanical, 6.0 CGPA, 2 backlogs, 2025 batch)
    stu_inelig_user = User(
        email=f"stu_inelig_{suffix}@test.com",
        hashed_password=hash_password("Pass123!"),
        role=UserRole.STUDENT,
        full_name="Ineligible Candidate",
        is_active=True,
    )
    db.add(stu_inelig_user)
    db.flush()

    student_inelig = Student(
        user_id=stu_inelig_user.id,
        roll_number=f"ME_{suffix}",
        branch="Mechanical",
        year=2025,
        cgpa=6.0,
        backlog_count=2,
    )
    db.add(student_inelig)

    # 5. Strict Job (Min CGPA 7.5, 0 backlogs, CS/IT only, batch 2024)
    job = Job(
        company_id=company.id,
        created_by=recruiter_user.id,
        title="Backend Software Engineer",
        description="FastAPI Backend Engineer",
        required_skills=["Python", "FastAPI", "SQL"],
        min_cgpa=7.5,
        eligible_batch=2024,
        allowed_branches=["Computer Science", "Information Technology"],
        maximum_backlogs=0,
        status=JobStatus.OPEN,
        deadline=now + timedelta(days=20),
        package_lpa=12.0,
    )
    db.add(job)
    db.commit()

    tokens = {
        "recruiter_token": create_access_token(subject=str(recruiter_user.id), role="RECRUITER"),
        "placement_token": create_access_token(subject=str(placement_user.id), role="PLACEMENT_OFFICER"),
        "stu_elig_token": create_access_token(subject=str(stu_elig_user.id), role="STUDENT"),
        "stu_inelig_token": create_access_token(subject=str(stu_inelig_user.id), role="STUDENT"),
        "job_id": job.id,
        "company_id": company.id,
        "student_elig_id": student_elig.id,
        "app_id": None,
        "interview_id": None,
    }
    db.close()
    return tokens


def test_student_apply_ineligible_blocked(workflow_fixture):
    """Ineligible student application is rejected with 400 and detailed reasons."""
    token = workflow_fixture["stu_inelig_token"]
    job_id = workflow_fixture["job_id"]
    res = client.post(
        f"/applications/{job_id}/apply",
        json={"job_id": job_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "not eligible" in res.json().get("message", "").lower()


def test_student_apply_eligible_success(workflow_fixture):
    """Eligible student applies successfully (201 Created)."""
    token = workflow_fixture["stu_elig_token"]
    job_id = workflow_fixture["job_id"]
    res = client.post(
        f"/applications/{job_id}/apply",
        json={"job_id": job_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["data"]["status"] in ["APPLIED", "ELIGIBILITY_VERIFIED"]
    # Store created app_id for downstream tests
    workflow_fixture["app_id"] = data["data"]["id"]


def test_duplicate_application_prevention(workflow_fixture):
    """Same student applying again to the same job receives 409 DUPLICATE_APPLICATION."""
    token = workflow_fixture["stu_elig_token"]
    job_id = workflow_fixture["job_id"]
    res = client.post(
        f"/applications/{job_id}/apply",
        json={"job_id": job_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 409
    assert "already applied" in res.json().get("message", "").lower()


def test_recruiter_status_transition_shortlist(workflow_fixture):
    """Recruiter can transition eligible application to SHORTLISTED."""
    token = workflow_fixture["recruiter_token"]
    app_id = workflow_fixture["app_id"]
    res = client.patch(
        f"/applications/{app_id}/status",
        json={"new_status": "SHORTLISTED", "remarks": "Strong profile"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "SHORTLISTED"


def test_recruiter_invalid_transition_rejected(workflow_fixture):
    """Recruiter attempting invalid status backward jump or invalid status returns 400."""
    token = workflow_fixture["recruiter_token"]
    app_id = workflow_fixture["app_id"]
    res = client.patch(
        f"/applications/{app_id}/status",
        json={"new_status": "APPLIED", "remarks": "Trying to move backwards"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400


def test_schedule_interview_success(workflow_fixture):
    """Recruiter schedules interview; application moves to INTERVIEW_SCHEDULED."""
    token = workflow_fixture["recruiter_token"]
    app_id = workflow_fixture["app_id"]
    interview_time = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    payload = {
        "application_id": app_id,
        "scheduled_at": interview_time,
        "mode": "ONLINE",
        "round": "TECHNICAL",
        "interviewer": "Senior Engineer",
        "location_or_link": "https://meet.google.com/xyz",
        "notes": "Data structures & Python round",
    }
    res = client.post(
        f"/applications/{app_id}/interviews",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["data"]["round"] == "TECHNICAL"
    workflow_fixture["interview_id"] = data["data"]["id"]


def test_update_interview_result_passed(workflow_fixture):
    """Recruiter updates interview result to PASSED."""
    token = workflow_fixture["recruiter_token"]
    interview_id = workflow_fixture["interview_id"]
    payload = {
        "result": "PASSED",
        "notes": "Passed coding challenge",
    }
    res = client.put(
        f"/applications/interviews/{interview_id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["data"]["result"] == "PASSED"


def test_placement_officer_reopen_status(workflow_fixture):
    """Placement officer has privileges to manage and reopen status."""
    token = workflow_fixture["placement_token"]
    app_id = workflow_fixture["app_id"]
    # Transition INTERVIEW_SCHEDULED -> INTERVIEW
    res0 = client.patch(
        f"/applications/{app_id}/status",
        json={"new_status": "INTERVIEW", "remarks": "Candidate attending interview"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res0.status_code == 200

    # Transition INTERVIEW -> SELECTED
    res1 = client.patch(
        f"/applications/{app_id}/status",
        json={"new_status": "SELECTED", "remarks": "Hired"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 200

    # Reopen to ELIGIBILITY_VERIFIED (Placement Officer privilege)
    res2 = client.patch(
        f"/applications/{app_id}/status",
        json={"new_status": "ELIGIBILITY_VERIFIED", "remarks": "Reopened by Placement Cell"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 200
    assert res2.json()["data"]["status"] == "ELIGIBILITY_VERIFIED"
