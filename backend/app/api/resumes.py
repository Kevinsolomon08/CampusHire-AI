# app/api/resumes.py
# Resume parsing API endpoint.
#
# POST /resumes/{resume_id}/parse
#   Fetches the Resume row, runs extract_text_from_pdf + parse_resume,
#   and stores the results back on the Resume record.
#   On any failure, stores parsing_status = "failed" with a short error
#   message but always returns success: True so the upload flow is
#   never interrupted.

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.ai.resume_parser import (
    ResumeExtractionError,
    ResumeParsingError,
    extract_text_from_pdf,
    parse_resume,
)
from app.api.deps import AppError, require_role
from app.database.connection import get_db
from app.models.models import Resume, Student, User, UserRole
from app.schemas.response import APIResponse
from app.schemas.student import ParsedResumeResponse

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helper — reusable by students.py upload route
# ---------------------------------------------------------------------------

def _run_resume_parse(resume: Resume, db: Session) -> None:
    """
    Run extract_text_from_pdf + parse_resume on *resume* and persist the results.

    This function NEVER raises — all exceptions are caught and stored as
    parsing_status = "failed" so the calling upload flow is always unaffected.

    Parameters
    ----------
    resume : Resume
        The Resume ORM instance to parse (must already be committed with a file_path).
    db : Session
        An open SQLAlchemy session.
    """
    try:
        # Step 1 — extract text from PDF
        text = extract_text_from_pdf(resume.file_path)

        # Step 2 — parse structured data from text
        parsed = parse_resume(text)

        # Step 3 — persist success
        resume.extracted_text = text
        resume.parsed_data = parsed
        resume.parsing_status = "success"
        resume.parsing_error = None
        db.commit()
        logger.info(
            "Resume parsed successfully: resume_id=%s, skills_found=%d",
            resume.id,
            len(parsed.get("skills", [])),
        )

    except ResumeExtractionError as exc:
        _store_parse_failure(
            resume,
            db,
            f"Unable to extract text from this resume. It may be a scanned image or corrupted file.",
        )
        logger.warning("ResumeExtractionError for resume_id=%s: %s", resume.id, exc)

    except ResumeParsingError as exc:
        # Persist any partial data that was extracted before the failure
        partial = getattr(exc, "partial_data", None)
        resume.extracted_text = None
        resume.parsed_data = partial if partial else None
        resume.parsing_status = "failed"
        resume.parsing_error = str(exc)[:500]
        db.commit()
        logger.warning("ResumeParsingError for resume_id=%s: %s", resume.id, exc)

    except Exception as exc:
        _store_parse_failure(
            resume,
            db,
            "An unexpected error occurred during parsing.",
        )
        logger.error(
            "Unexpected error parsing resume_id=%s: %s", resume.id, exc, exc_info=True
        )


def _store_parse_failure(resume: Resume, db: Session, message: str) -> None:
    """Persist a failed parsing attempt."""
    try:
        resume.parsed_data = None
        resume.parsing_status = "failed"
        resume.parsing_error = message[:500]
        db.commit()
    except Exception:
        db.rollback()


# ---------------------------------------------------------------------------
# POST /resumes/{resume_id}/parse
# ---------------------------------------------------------------------------

@router.post(
    "/{resume_id}/parse",
    response_model=APIResponse[ParsedResumeResponse],
    summary="Parse a stored resume PDF and extract structured data",
)
def parse_resume_endpoint(
    resume_id: int,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    """
    Trigger AI parsing of a stored resume.

    - Fetches the Resume row (must belong to the authenticated student).
    - Runs extract_text_from_pdf → parse_resume.
    - Stores parsed_data / extracted_text / parsing_status back on the Resume row.
    - Always returns success: True — even if parsing fails, the file is safe.

    Returns
    -------
    ParsedResumeResponse with parsing_status and parsed_data (or null on failure).
    """
    # Resolve the student for this user
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Student profile not found.",
            error_code="STUDENT_NOT_FOUND",
        )

    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.student_id == student.id)
        .first()
    )
    if not resume:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Resume not found or does not belong to this account.",
            error_code="RESUME_NOT_FOUND",
        )

    # Run parsing (never raises)
    _run_resume_parse(resume, db)
    db.refresh(resume)

    # Build message based on outcome
    if resume.parsing_status == "success":
        msg = "Resume parsed successfully."
    else:
        msg = (
            "Resume uploaded successfully. Automatic parsing was unavailable — "
            "you can enter your details manually."
        )

    return APIResponse(
        success=True,
        data=ParsedResumeResponse(
            resume_id=resume.id,
            parsing_status=resume.parsing_status,
            parsing_error=resume.parsing_error,
            parsed_data=resume.parsed_data,
        ),
        message=msg,
    )
