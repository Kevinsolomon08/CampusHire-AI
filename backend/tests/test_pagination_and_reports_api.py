# tests/test_pagination_and_reports_api.py
"""
Test suite covering:
1. Pagination behavior on Admin list endpoints (/admin/students, /admin/jobs, /admin/applications)
2. Reports generation endpoint (/admin/reports) in JSON format with breakdowns
3. Reports CSV export streaming response with attachment headers
4. Placement statistics endpoint (/admin/statistics)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.security import create_access_token, hash_password
from app.database.connection import SessionLocal
from app.models.models import User, UserRole

client = TestClient(app)


@pytest.fixture(scope="module")
def admin_token():
    """Sets up a placement officer user and returns JWT token."""
    db = SessionLocal()
    officer = db.query(User).filter(User.role == UserRole.PLACEMENT_OFFICER).first()
    if not officer:
        officer = User(
            email="admin_test_officer@campushire.demo",
            hashed_password=hash_password("Pass123!"),
            role=UserRole.PLACEMENT_OFFICER,
            full_name="Admin Test Officer",
            is_active=True,
        )
        db.add(officer)
        db.commit()
        db.refresh(officer)

    token = create_access_token(subject=str(officer.id), role="PLACEMENT_OFFICER")
    db.close()
    return token


def test_admin_students_pagination(admin_token):
    """GET /admin/students respects page and page_size query parameters."""
    res = client.get(
        "/admin/students?page=1&page_size=3",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "items" in data["data"]
    assert "total" in data["data"]
    assert "page" in data["data"]
    assert "page_size" in data["data"]
    assert data["data"]["page"] == 1
    assert data["data"]["page_size"] == 3
    assert len(data["data"]["items"]) <= 3


def test_admin_jobs_pagination(admin_token):
    """GET /admin/jobs returns paginated job listings."""
    res = client.get(
        "/admin/jobs?page=1&page_size=5",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "items" in data["data"]
    assert data["data"]["page"] == 1


def test_admin_applications_pagination(admin_token):
    """GET /admin/applications returns paginated applications."""
    res = client.get(
        "/admin/applications?page=1&page_size=5",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "items" in data["data"]


def test_admin_reports_json(admin_token):
    """GET /admin/reports returns aggregated KPI summary and company/department/batch breakdowns."""
    res = client.get(
        "/admin/reports",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    report = data["data"]
    assert "summary" in report
    assert "total_applications" in report["summary"]
    assert "total_selected" in report["summary"]
    assert "selection_rate" in report["summary"]
    assert "company_breakdown" in report
    assert "department_breakdown" in report
    assert "batch_breakdown" in report


def test_admin_reports_csv_download(admin_token):
    """GET /admin/reports?format=csv returns downloadable CSV stream."""
    res = client.get(
        "/admin/reports?format=csv",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert "text/csv" in res.headers.get("content-type", "")
    assert "placement_report.csv" in res.headers.get("content-disposition", "")
    assert len(res.text) > 0
    assert "SUMMARY" in res.text or "Total Applications" in res.text or "Applications" in res.text


def test_admin_statistics_endpoint(admin_token):
    """GET /admin/statistics returns data for frontend dashboard charts."""
    res = client.get(
        "/admin/statistics",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    stats = data["data"]
    assert "application_funnel" in stats
    assert "recruitment_drive_status" in stats
    assert "applications_by_company" in stats
    assert "applications_by_department" in stats
    assert "selections_by_company" in stats
    assert "selection_rate_by_department" in stats
