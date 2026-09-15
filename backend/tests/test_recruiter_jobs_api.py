# tests/test_recruiter_jobs_api.py
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, hash_password
from app.database.connection import SessionLocal
from app.models.models import Company, Job, JobStatus, Recruiter, User, UserRole

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_recruiters_data():
    db = SessionLocal()

    # Recruiter A & Company A
    user_a = db.query(User).filter(User.email == "recruiter_a@corp.com").first()
    if not user_a:
        user_a = User(
            email="recruiter_a@corp.com",
            hashed_password=hash_password("Password123!"),
            role=UserRole.RECRUITER,
            full_name="Alice Recruiter",
            is_active=True,
        )
        db.add(user_a)
        db.flush()

    comp_a = db.query(Company).filter(Company.name == "Company Alpha").first()
    if not comp_a:
        comp_a = Company(
            name="Company Alpha",
            website="https://alpha.corp",
            industry="Technology",
            description="Alpha technology solutions",
        )
        db.add(comp_a)
        db.flush()

    rec_a = db.query(Recruiter).filter(Recruiter.user_id == user_a.id).first()
    if not rec_a:
        rec_a = Recruiter(
            user_id=user_a.id,
            company_id=comp_a.id,
            designation="Senior Technical Recruiter",
        )
        db.add(rec_a)
    else:
        rec_a.company_id = comp_a.id

    # Recruiter B & Company B (for testing ownership restrictions)
    user_b = db.query(User).filter(User.email == "recruiter_b@corp.com").first()
    if not user_b:
        user_b = User(
            email="recruiter_b@corp.com",
            hashed_password=hash_password("Password123!"),
            role=UserRole.RECRUITER,
            full_name="Bob Recruiter",
            is_active=True,
        )
        db.add(user_b)
        db.flush()

    comp_b = db.query(Company).filter(Company.name == "Company Beta").first()
    if not comp_b:
        comp_b = Company(
            name="Company Beta",
            website="https://beta.corp",
            industry="Finance",
            description="Beta financial services",
        )
        db.add(comp_b)
        db.flush()

    rec_b = db.query(Recruiter).filter(Recruiter.user_id == user_b.id).first()
    if not rec_b:
        rec_b = Recruiter(
            user_id=user_b.id,
            company_id=comp_b.id,
            designation="HR Manager",
        )
        db.add(rec_b)
    else:
        rec_b.company_id = comp_b.id

    db.commit()

    token_a = create_access_token(subject=str(user_a.id), role="RECRUITER")
    token_b = create_access_token(subject=str(user_b.id), role="RECRUITER")

    comp_a_id = comp_a.id
    comp_b_id = comp_b.id
    db.close()

    return {
        "token_a": token_a,
        "token_b": token_b,
        "comp_a_id": comp_a_id,
        "comp_b_id": comp_b_id,
    }


def test_get_recruiter_me(setup_recruiters_data):
    token = setup_recruiters_data["token_a"]
    res = client.get("/recruiters/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Alice Recruiter"
    assert data["data"]["company"]["name"] == "Company Alpha"
    assert "total_jobs" in data["data"]
    assert "active_jobs" in data["data"]


def test_update_company_profile_success(setup_recruiters_data):
    token = setup_recruiters_data["token_a"]
    comp_id = setup_recruiters_data["comp_a_id"]
    payload = {
        "name": "Company Alpha Global",
        "website": "https://alphaglobal.corp",
        "description": "Leading AI platform",
    }
    res = client.put(
        f"/companies/{comp_id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Company Alpha Global"
    assert data["data"]["website"] == "https://alphaglobal.corp"


def test_update_other_company_forbidden(setup_recruiters_data):
    # Recruiter B tries to update Company A
    token_b = setup_recruiters_data["token_b"]
    comp_a_id = setup_recruiters_data["comp_a_id"]
    payload = {"name": "Hacked Name"}
    res = client.put(
        f"/companies/{comp_a_id}",
        json=payload,
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res.status_code == 403
    data = res.json()
    assert data["success"] is False
    assert data["message"] == "You are not authorized to perform this action."


def test_create_job_validation(setup_recruiters_data):
    token = setup_recruiters_data["token_a"]

    # Invalid CGPA > 10
    res = client.post(
        "/jobs",
        json={"title": "Software Dev", "description": "Desc", "minimum_cgpa": 12.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422

    # Invalid negative backlogs
    res = client.post(
        "/jobs",
        json={"title": "Software Dev", "description": "Desc", "maximum_backlogs": -3},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422


def test_job_crud_lifecycle_and_ownership(setup_recruiters_data):
    token_a = setup_recruiters_data["token_a"]
    token_b = setup_recruiters_data["token_b"]

    future_deadline = (datetime.now(timezone.utc) + timedelta(days=20)).isoformat()

    # 1. Recruiter A creates a DRAFT job
    create_payload = {
        "title": "Backend Systems Engineer",
        "description": "Build high-throughput distributed microservices.",
        "location": "Bengaluru, India",
        "package_lpa": 26.0,
        "minimum_cgpa": 7.5,
        "maximum_backlogs": 0,
        "eligible_batch": 2025,
        "allowed_branches": ["Computer Science", "Information Technology"],
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "deadline": future_deadline,
        "status": "DRAFT",
    }
    create_res = client.post(
        "/jobs", json=create_payload, headers={"Authorization": f"Bearer {token_a}"}
    )
    assert create_res.status_code == 201
    job_a = create_res.json()["data"]
    job_id = job_a["id"]
    assert job_a["status"] == "DRAFT"
    assert job_a["package_lpa"] == 26.0

    # 2. Recruiter B tries to edit Recruiter A's job -> 403 Forbidden
    edit_res_b = client.put(
        f"/jobs/{job_id}",
        json={"title": "Unauthorized Title Change"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert edit_res_b.status_code == 403
    assert edit_res_b.json()["message"] == "You are not authorized to perform this action."

    # 3. Recruiter B tries to publish Recruiter A's job -> 403 Forbidden
    pub_res_b = client.post(
        f"/jobs/{job_id}/publish",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert pub_res_b.status_code == 403
    assert pub_res_b.json()["message"] == "You are not authorized to perform this action."

    # 4. Recruiter B tries to delete Recruiter A's job -> 403 Forbidden
    del_res_b = client.delete(
        f"/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_res_b.status_code == 403
    assert del_res_b.json()["message"] == "You are not authorized to perform this action."

    # 5. Recruiter A publishes their own job: DRAFT -> OPEN
    pub_res_a = client.post(
        f"/jobs/{job_id}/publish",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert pub_res_a.status_code == 200
    assert pub_res_a.json()["data"]["status"] == "OPEN"

    # 6. Recruiter A closes their own job: OPEN -> CLOSED
    close_res_a = client.post(
        f"/jobs/{job_id}/close",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert close_res_a.status_code == 200
    assert close_res_a.json()["data"]["status"] == "CLOSED"

    # 7. Recruiter A views their job list -> should contain this job
    list_res_a = client.get(
        "/recruiters/jobs",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert list_res_a.status_code == 200
    items = list_res_a.json()["data"]["items"]
    assert any(j["id"] == job_id for j in items)

    # 8. Recruiter B views their job list -> should NOT contain Recruiter A's job
    list_res_b = client.get(
        "/recruiters/jobs",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert list_res_b.status_code == 200
    items_b = list_res_b.json()["data"]["items"]
    assert not any(j["id"] == job_id for j in items_b)

    # 9. Recruiter A deletes the job
    del_res_a = client.delete(
        f"/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert del_res_a.status_code == 200
    assert del_res_a.json()["success"] is True
