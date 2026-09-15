# tests/test_auth_and_roles_api.py
"""
Test suite covering:
1. User registration across all roles (STUDENT, RECRUITER, PLACEMENT_OFFICER)
2. Duplicate email rejection
3. Credential authentication, password verification, and JWT issuance
4. /auth/me profile retrieval
5. Role authorization boundaries (Student -> Admin blocked 403, Recruiter -> Admin blocked 403, Placement Officer allowed)
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.security import create_access_token, hash_password
from app.database.connection import SessionLocal
from app.models.models import User, UserRole, Student, Recruiter, Company

client = TestClient(app)


@pytest.fixture(scope="module")
def auth_fixture_users():
    """Sets up fixture users with known roles and generated JWT tokens."""
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    # 1. Student User
    student_user = User(
        email=f"stu_auth_{suffix}@test.com",
        hashed_password=hash_password("ValidPass123!"),
        role=UserRole.STUDENT,
        full_name="Auth Test Student",
        is_active=True,
    )
    db.add(student_user)
    db.flush()

    student_profile = Student(
        user_id=student_user.id,
        roll_number=f"ROLL_{suffix}",
        branch="Computer Science",
        year=2024,
        cgpa=8.2,
        backlog_count=0,
    )
    db.add(student_profile)

    # 2. Recruiter User & Company
    comp = Company(
        name=f"Auth Test Corp {suffix}",
        website="https://authtest.com",
        industry="Technology",
    )
    db.add(comp)
    db.flush()

    recruiter_user = User(
        email=f"rec_auth_{suffix}@test.com",
        hashed_password=hash_password("ValidPass123!"),
        role=UserRole.RECRUITER,
        full_name="Auth Test Recruiter",
        is_active=True,
    )
    db.add(recruiter_user)
    db.flush()

    recruiter_profile = Recruiter(
        user_id=recruiter_user.id,
        company_id=comp.id,
        designation="Lead Recruiter",
    )
    db.add(recruiter_profile)

    # 3. Placement Officer User
    placement_user = User(
        email=f"place_auth_{suffix}@test.com",
        hashed_password=hash_password("ValidPass123!"),
        role=UserRole.PLACEMENT_OFFICER,
        full_name="Auth Test Officer",
        is_active=True,
    )
    db.add(placement_user)
    db.commit()

    student_token = create_access_token(subject=str(student_user.id), role="STUDENT")
    recruiter_token = create_access_token(subject=str(recruiter_user.id), role="RECRUITER")
    placement_token = create_access_token(subject=str(placement_user.id), role="PLACEMENT_OFFICER")

    db_data = {
        "student_user": student_user,
        "recruiter_user": recruiter_user,
        "placement_user": placement_user,
        "student_token": student_token,
        "recruiter_token": recruiter_token,
        "placement_token": placement_token,
    }
    db.close()
    return db_data


def test_register_student_success():
    """Registering a new student creates user and student profile."""
    unique_email = f"new_stu_{uuid.uuid4().hex[:6]}@test.com"
    payload = {
        "email": unique_email,
        "password": "Password123!",
        "name": "Jane Student",
        "role": "STUDENT",
        "roll_number": f"ROLL_{uuid.uuid4().hex[:6]}",
        "branch": "Information Technology",
        "year": 2024,
    }
    res = client.post("/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["data"]["email"] == unique_email.lower()
    assert data["data"]["role"] == "STUDENT"
    assert data["data"]["student_profile"]["branch"] == "Information Technology"


def test_register_recruiter_success():
    """Registering a new recruiter creates company and recruiter link."""
    unique_email = f"new_rec_{uuid.uuid4().hex[:6]}@test.com"
    payload = {
        "email": unique_email,
        "password": "Password123!",
        "name": "Bob Recruiter",
        "role": "RECRUITER",
        "company_name": f"New Acme Corp {uuid.uuid4().hex[:4]}",
        "designation": "Director of HR",
    }
    res = client.post("/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["data"]["email"] == unique_email.lower()
    assert data["data"]["role"] == "RECRUITER"
    assert data["data"]["recruiter_profile"] is not None


def test_register_duplicate_email_rejected(auth_fixture_users):
    """Registering with an already existing email returns 400 error."""
    existing_email = auth_fixture_users["student_user"].email
    payload = {
        "email": existing_email,
        "password": "Password123!",
        "name": "Duplicate Student",
        "role": "STUDENT",
    }
    res = client.post("/auth/register", json=payload)
    assert res.status_code == 400
    assert "already registered" in res.json().get("message", "").lower()


def test_login_valid_credentials(auth_fixture_users):
    """Valid login credentials yield JWT access token and user metadata."""
    email = auth_fixture_users["student_user"].email
    res = client.post("/auth/login", json={"email": email, "password": "ValidPass123!"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"
    assert data["data"]["user"]["email"] == email


def test_login_invalid_password(auth_fixture_users):
    """Invalid password returns 401 Unauthorized."""
    email = auth_fixture_users["student_user"].email
    res = client.post("/auth/login", json={"email": email, "password": "WrongPassword999!"})
    assert res.status_code == 401
    assert "invalid" in res.json().get("message", "").lower()


def test_login_nonexistent_user():
    """Non-existent email login returns 401 Unauthorized."""
    res = client.post("/auth/login", json={"email": "nobody_exists@unknown.com", "password": "Password123!"})
    assert res.status_code == 401


def test_get_current_user_me(auth_fixture_users):
    """GET /auth/me returns the authenticated user profile."""
    token = auth_fixture_users["student_token"]
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["email"] == auth_fixture_users["student_user"].email


def test_role_authorization_student_cannot_access_admin(auth_fixture_users):
    """Student cannot access Placement Officer /admin routes (403 Forbidden)."""
    token = auth_fixture_users["student_token"]
    res = client.get("/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_role_authorization_recruiter_cannot_access_admin(auth_fixture_users):
    """Recruiter cannot access Placement Officer /admin routes (403 Forbidden)."""
    token = auth_fixture_users["recruiter_token"]
    res = client.get("/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_role_authorization_placement_officer_can_access_admin(auth_fixture_users):
    """Placement officer can access /admin routes."""
    token = auth_fixture_users["placement_token"]
    res = client.get("/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "total_students" in data["data"]
