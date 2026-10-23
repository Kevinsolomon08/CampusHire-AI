# tests/test_marksheet_upload.py
"""
Tests for marksheet-based CGPA upload, extraction, and invariants.
"""

from __future__ import annotations

import io
import os
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token, hash_password
from app.database.connection import SessionLocal
from app.models.models import User, Student, Marksheet, StudentCgpaHistory, Notification, UserRole
from app.ai.marksheet_parser import validate_marksheet_text, extract_cgpa

client = TestClient(app)

# Minimal valid PDF bytes that pdfplumber can open
VALID_MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
    b"xref\n0 4\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"trailer\n<< /Size 4 /Root 1 0 R >>\n"
    b"startxref\n190\n%%EOF"
)


@pytest.fixture(scope="module")
def marksheet_test_student():
    db = SessionLocal()
    email = "marksheet_student@example.com"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password=hash_password("Password123!"),
            role=UserRole.STUDENT,
            full_name="Marksheet Test Student",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    student = db.query(Student).filter(Student.user_id == user.id).first()
    if not student:
        student = Student(
            user_id=user.id,
            roll_number="MS_STU_001",
            branch="Computer Science",
            year=2025,
            cgpa=None,
            cgpa_source=None,
            backlog_count=0,
            skills=["Python"],
        )
        db.add(student)
        db.commit()
        db.refresh(student)
    else:
        student.cgpa = None
        student.cgpa_source = None
        student.cgpa_verified_at = None
        student.current_marksheet_id = None
        db.commit()

    token = create_access_token(subject=str(user.id), role="STUDENT")
    user_id = user.id
    student_id = student.id
    db.close()
    return {"token": token, "user_id": user_id, "student_id": student_id}


def test_registration_rejects_cgpa():
    payload = {
        "name": "New Student",
        "email": "new_student_cgpa_reject@example.com",
        "password": "Password123!",
        "role": "STUDENT",
        "cgpa": 8.75,
        "roll_number": "STU_REJECT_001",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "CGPA_UPDATE_NOT_ALLOWED"
    assert "CGPA can only be updated by uploading your marksheet" in data["message"]


def test_put_student_me_rejects_cgpa(marksheet_test_student):
    token = marksheet_test_student["token"]
    payload = {"cgpa": 8.5}
    response = client.put("/students/me", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "CGPA_UPDATE_NOT_ALLOWED"


def test_marksheet_parser_extract_cgpa_cumulative_only():
    text = """
    ANNA UNIVERSITY CHENNAI
    SEMESTER GRADE REPORT / MARKSHEET
    Semester: 6  Branch: B.E. Computer Science and Engineering
    Course Credits Grade
    CS8601 Mobile Computing 3 A+
    CS8602 Compiler Design 4 O
    Total Credits Registered: 24  Earned: 24
    Semester GPA (SGPA): 8.42
    Cumulative Grade Point Average (CGPA): 8.85
    Result: PASSED
    """
    res = extract_cgpa(text)
    assert res["error_code"] is None
    assert float(res["cgpa"]) == 8.85


def test_marksheet_parser_rejects_sgpa_only():
    text = """
    UNIVERSITY EXAMINATIONS
    PROVISIONAL MARKSHEET
    Semester 4
    Subject Grade
    Mathematics-IV A
    Operating Systems A+
    Semester SGPA: 8.12
    Total Credits: 22
    Result: Pass
    """
    res = extract_cgpa(text)
    assert res["error_code"] == "SGPA_ONLY"
    assert res["cgpa"] is None


def test_marksheet_parser_rejects_unsupported_scale():
    text = """
    GLOBAL TECHNICAL UNIVERSITY
    ACADEMIC TRANSCRIPT / MARKSHEET
    Bachelor of Science
    Overall Cumulative GPA: 3.8 / 4.0 scale
    Total Credits: 120
    Status: Degree Conferred
    """
    res = extract_cgpa(text)
    assert res["error_code"] == "UNSUPPORTED_SCALE"


def test_marksheet_parser_rejects_ambiguous_cgpa():
    text = """
    STATE INSTITUTE OF TECHNOLOGY
    STUDENT MARKSHEET
    CGPA Semester 1: 7.50
    CGPA Semester 2: 8.50
    Credits Earned: 45
    """
    res = extract_cgpa(text)
    assert res["error_code"] == "CGPA_AMBIGUOUS"


def test_marksheet_parser_rejects_scanned_image_text():
    text = "   "  # less than 50 printable characters
    res = validate_marksheet_text(text)
    assert res["is_valid"] is False
    assert res["error_code"] == "SCANNED_MARKSHEET"


def test_marksheet_parser_rejects_non_marksheet():
    text = """
    INVOICE #INV-2024-998
    Vendor: Office Supplies Pvt Ltd
    Item Description: 10 reams of A4 paper
    Subtotal: $50.00
    Tax: $5.00
    Total Paid: $55.00
    Thank you for your business!
    """
    res = validate_marksheet_text(text)
    assert res["is_valid"] is False
    assert res["error_code"] == "NOT_A_MARKSHEET"


def test_successful_marksheet_upload(marksheet_test_student):
    token = marksheet_test_student["token"]
    student_id = marksheet_test_student["student_id"]
    user_id = marksheet_test_student["user_id"]

    sample_marksheet_text = """
    ANNA UNIVERSITY CHENNAI
    CONSOLIDATED GRADE SHEET / MARKSHEET
    Branch: Information Technology
    Graduating Year: 2025
    Credits Completed: 160
    SGPA Sem 8: 9.10
    Cumulative Grade Point Average (CGPA): 8.92
    Classification: First Class with Distinction
    """

    with patch("app.api.students.extract_text_from_pdf", return_value=sample_marksheet_text):
        files = {"file": ("marksheet.pdf", VALID_MINIMAL_PDF, "application/pdf")}
        response = client.post(
            "/students/marksheet",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["cgpa"] == 8.92
    assert data["data"]["source"] == "MARKSHEET"

    # Verify Database Invariants
    db = SessionLocal()
    updated_student = db.query(Student).filter(Student.id == student_id).first()
    assert updated_student.cgpa == 8.92
    assert str(updated_student.cgpa_source).endswith("MARKSHEET")
    assert updated_student.cgpa_verified_at is not None
    assert updated_student.current_marksheet_id is not None

    # Check History Row
    history_rows = (
        db.query(StudentCgpaHistory)
        .filter(StudentCgpaHistory.student_id == student_id)
        .all()
    )
    assert len(history_rows) >= 1
    latest_history = history_rows[-1]
    assert latest_history.new_cgpa == 8.92
    assert latest_history.source == "MARKSHEET"

    # Check Notification Created
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.title == "CGPA Verified")
        .all()
    )
    assert len(notifications) >= 1
    assert "8.92" in notifications[-1].message

    db.close()


def test_failed_marksheet_upload_rejects_non_pdf(marksheet_test_student):
    token = marksheet_test_student["token"]
    files = {"file": ("marksheet.txt", b"plain text", "text/plain")}
    response = client.post(
        "/students/marksheet",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "NOT_A_MARKSHEET"
