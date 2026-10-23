"""
tests/test_resume_upload_validation.py
=======================================
API-level integration tests for resume content validation.

These tests call POST /students/resume with mocked PDF text extraction
so that no real PDFs need to exist on disk.  The validation logic
is exercised through the full FastAPI request-response cycle.
"""

from __future__ import annotations

import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token, hash_password
from app.database.connection import SessionLocal
from app.models.models import User, Student, UserRole

client = TestClient(app)

# ---------------------------------------------------------------------------
# Synthetic text samples
# ---------------------------------------------------------------------------

RESUME_TEXT = """
Alice Johnson
alice@example.com | +91 9876543210 | github.com/alice

Education
B.Tech in Computer Science | Tech University | 2020-2024

Skills
Python, FastAPI, React, PostgreSQL, Docker, AWS

Experience
Software Engineer Intern — StartupX | June 2023 - Aug 2023
Developed REST APIs using Python and FastAPI.
Deployed containers with Docker on AWS.
Built React dashboards integrated with PostgreSQL.

Projects
Job Portal — Python, FastAPI, React, PostgreSQL
Designed and implemented a full-stack recruitment platform.
""".strip()


INVOICE_TEXT = """
INVOICE #INV-2024-001

Bill To: Acme Corp
Item Description    Quantity    Unit Price    Total
Software License    1           $500.00       $500.00
Support Services    5           $100.00       $500.00

Subtotal: $1,000.00
Tax (GST): $180.00
Total Amount Due: $1,180.00
Payment Due: 2024-01-30
Transaction ID: TXN-987654321
""".strip()


# Minimal valid PDF bytes (passes the %PDF- header check)
FAKE_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Title (Test) >>\nendobj\n%%EOF"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def student_token():
    db = SessionLocal()
    user = db.query(User).filter(User.email == "val_test_student@example.com").first()
    if not user:
        user = User(
            email="val_test_student@example.com",
            hashed_password=hash_password("Password123!"),
            role=UserRole.STUDENT,
            full_name="Validation Tester",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    student = db.query(Student).filter(Student.user_id == user.id).first()
    if not student:
        student = Student(
            user_id=user.id,
            roll_number="VAL_TEST_001",
            branch="Computer Science",
            year=2025,
            cgpa=8.5,
            backlog_count=0,
            skills=["Python"],
        )
        db.add(student)
        db.commit()

    token = create_access_token(subject=str(user.id), role="STUDENT")
    db.close()
    return token


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestResumeValidationAPI:
    """Tests for POST /students/resume content validation."""

    def test_invoice_upload_returns_422(self, student_token):
        """Uploading a PDF whose text looks like an invoice should be rejected."""
        with (
            patch(
                "app.api.students.extract_text_from_pdf",
                return_value=INVOICE_TEXT,
            ),
            patch(
                "app.api.students.pdfplumber.open",
                return_value=MagicMock(
                    __enter__=lambda s, *a: MagicMock(pages=[MagicMock()]),
                    __exit__=lambda s, *a: None,
                ),
            ),
        ):
            response = client.post(
                "/students/resume",
                files={"file": ("invoice.pdf", io.BytesIO(FAKE_PDF_BYTES), "application/pdf")},
                headers={"Authorization": f"Bearer {student_token}"},
            )

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "NOT_A_RESUME"
        assert "resume" in data["message"].lower()

    def test_resume_upload_accepted(self, student_token):
        """Uploading a well-formed resume PDF should succeed."""
        with (
            patch(
                "app.api.students.extract_text_from_pdf",
                return_value=RESUME_TEXT,
            ),
            patch(
                "app.api.students.pdfplumber.open",
                return_value=MagicMock(
                    __enter__=lambda s, *a: MagicMock(pages=[MagicMock(), MagicMock()]),
                    __exit__=lambda s, *a: None,
                ),
            ),
            # Also mock the parse step so we do not need spaCy in tests
            patch("app.api.resumes._run_resume_parse", return_value=None),
        ):
            response = client.post(
                "/students/resume",
                files={"file": ("resume.pdf", io.BytesIO(FAKE_PDF_BYTES), "application/pdf")},
                headers={"Authorization": f"Bearer {student_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["filename"] == "resume.pdf"

    def test_disabled_validation_allows_invoice(self, student_token):
        """When RESUME_VALIDATION_ENABLED=False the invoice should pass through."""
        with (
            patch(
                "app.api.students.extract_text_from_pdf",
                return_value=INVOICE_TEXT,
            ),
            patch(
                "app.api.students.pdfplumber.open",
                return_value=MagicMock(
                    __enter__=lambda s, *a: MagicMock(pages=[MagicMock()]),
                    __exit__=lambda s, *a: None,
                ),
            ),
            patch("app.api.students.settings") as mock_settings,
            patch("app.api.resumes._run_resume_parse", return_value=None),
        ):
            mock_settings.RESUME_VALIDATION_ENABLED = False
            mock_settings.UPLOAD_DIRECTORY = "uploads"

            response = client.post(
                "/students/resume",
                files={"file": ("invoice.pdf", io.BytesIO(FAKE_PDF_BYTES), "application/pdf")},
                headers={"Authorization": f"Bearer {student_token}"},
            )

        # With validation disabled it should proceed (200 or any non-422 success)
        assert response.status_code != 422

    def test_validation_error_has_correct_error_code(self, student_token):
        """The error_code in the response must be exactly NOT_A_RESUME."""
        with (
            patch(
                "app.api.students.extract_text_from_pdf",
                return_value=INVOICE_TEXT,
            ),
            patch(
                "app.api.students.pdfplumber.open",
                return_value=MagicMock(
                    __enter__=lambda s, *a: MagicMock(pages=[MagicMock()]),
                    __exit__=lambda s, *a: None,
                ),
            ),
        ):
            response = client.post(
                "/students/resume",
                files={"file": ("invoice.pdf", io.BytesIO(FAKE_PDF_BYTES), "application/pdf")},
                headers={"Authorization": f"Bearer {student_token}"},
            )

        data = response.json()
        assert data.get("error_code") == "NOT_A_RESUME"

    def test_unreadable_pdf_still_uploads(self, student_token):
        """If the PDF cannot be text-extracted the upload must not be blocked."""
        from app.ai.resume_parser import ResumeExtractionError

        with (
            patch(
                "app.api.students.extract_text_from_pdf",
                side_effect=ResumeExtractionError("No text"),
            ),
            patch(
                "app.api.students.pdfplumber.open",
                return_value=MagicMock(
                    __enter__=lambda s, *a: MagicMock(pages=[MagicMock()]),
                    __exit__=lambda s, *a: None,
                ),
            ),
            patch("app.api.resumes._run_resume_parse", return_value=None),
        ):
            response = client.post(
                "/students/resume",
                files={"file": ("scanned.pdf", io.BytesIO(FAKE_PDF_BYTES), "application/pdf")},
                headers={"Authorization": f"Bearer {student_token}"},
            )

        # Should succeed — scanned/image PDFs must not be blocked by content validation
        assert response.status_code == 200
