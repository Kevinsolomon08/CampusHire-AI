# app/api/students.py
# API routes for Student profile management, resume upload, and job eligibility browsing.

from __future__ import annotations

import logging
import math
import os
import re
import shutil
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
import pdfplumber
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.ai.embedding_service import (
    EmbeddingGenerationError,
    cosine_similarity_score,
    get_or_generate_embedding,
    text_hash,
)
from app.ai.marksheet_parser import extract_cgpa, validate_marksheet_text
from app.ai.resume_parser import (
    ResumeExtractionError,
    extract_text_from_pdf,
)
from app.ai.resume_validator import validate_resume_text
from app.api.deps import AppError, get_current_user, require_role
from app.api.resumes import _run_resume_parse
from app.core.config import settings
from app.database.connection import get_db
from app.models.models import (
    Company,
    Job,
    JobStatus,
    Marksheet,
    Resume,
    Student,
    StudentCgpaHistory,
    User,
    UserRole,
)
from app.schemas.response import APIResponse
from app.schemas.student import (
    CompanyBrief,
    JobEligibilityInfo,
    PaginatedJobsResponse,
    ParsedResumeResponse,
    ResumeInfo,
    RecommendedJobItem,
    RecommendedJobsResponse,
    StudentJobDetailResponse,
    StudentJobListItem,
    StudentProfileResponse,
    StudentProfileUpdate,
)
from app.services.eligibility_service import check_eligibility

router = APIRouter()


router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: Calculate Profile Completion Percentage
# ---------------------------------------------------------------------------
def calculate_completion_percentage(student: Student, user: User, primary_resume: Optional[Resume]) -> int:
    """Calculates profile completion percentage based on filled profile attributes."""
    checklist = [
        bool(user.full_name and user.full_name.strip()),
        bool(user.email and user.email.strip()),
        bool(student.roll_number and student.roll_number.strip()),
        bool(student.branch and student.branch.strip()),
        bool(student.year and student.year > 0),
        bool(student.cgpa is not None and student.cgpa > 0),
        bool(student.phone and student.phone.strip()),
        bool(student.skills and len(student.skills) > 0),
        bool(student.education or student.experience or student.projects),
        bool(primary_resume is not None),
    ]
    completed = sum(1 for item in checklist if item)
    return int(round((completed / len(checklist)) * 100))


def _get_or_create_student(user: User, db: Session) -> Student:
    """Safely retrieves or initializes the Student record for a student user."""
    student = db.query(Student).filter(Student.user_id == user.id).first()
    if not student:
        student = Student(
            user_id=user.id,
            roll_number=f"STU{user.id:04d}",
            branch="Computer Science",
            year=datetime.now().year,
            cgpa=None,
            backlog_count=0,
            skills=[],
        )
        db.add(student)
        db.commit()
        db.refresh(student)
    return student


def _get_primary_resume(student_id: int, db: Session) -> Optional[Resume]:
    return (
        db.query(Resume)
        .filter(Resume.student_id == student_id)
        .order_by(Resume.is_primary.desc(), Resume.uploaded_at.desc())
        .first()
    )


# ---------------------------------------------------------------------------
# Profile Endpoints: GET /students/me & PUT /students/me
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=APIResponse[StudentProfileResponse],
    summary="Get current student profile",
)
def get_student_profile(
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    student = _get_or_create_student(current_user, db)
    primary_resume = _get_primary_resume(student.id, db)
    completion_pct = calculate_completion_percentage(student, current_user, primary_resume)

    resume_info = None
    if primary_resume:
        resume_info = ResumeInfo(
            id=primary_resume.id,
            filename=primary_resume.original_filename or os.path.basename(primary_resume.file_path),
            file_path=primary_resume.file_path,
            is_primary=primary_resume.is_primary,
            uploaded_at=primary_resume.uploaded_at,
            parsing_status=primary_resume.parsing_status,
            parsed_data=primary_resume.parsed_data,
        )

    profile_data = StudentProfileResponse(
        id=student.id,
        user_id=current_user.id,
        name=current_user.full_name,
        email=current_user.email,
        roll_number=student.roll_number,
        department=student.branch,
        batch=student.year,
        cgpa=student.cgpa,
        backlog_count=student.backlog_count,
        phone=student.phone,
        linkedin_url=student.linkedin_url,
        skills=student.skills or [],
        education=student.education,
        experience=student.experience,
        projects=student.projects,
        certifications=student.certifications,
        primary_resume=resume_info,
        profile_completion_pct=completion_pct,
    )

    return APIResponse(
        success=True,
        data=profile_data,
        message="Student profile retrieved successfully.",
    )


@router.put(
    "/me",
    response_model=APIResponse[StudentProfileResponse],
    summary="Update current student profile",
)
def update_student_profile(
    payload: StudentProfileUpdate,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    student = _get_or_create_student(current_user, db)

    if payload.cgpa is not None:
        raise AppError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="CGPA can only be updated by uploading your marksheet.",
            error_code="CGPA_UPDATE_NOT_ALLOWED",
        )

    # Update Student specific fields
    if payload.department is not None:
        student.branch = payload.department
    if payload.batch is not None:
        student.year = payload.batch
    if payload.backlog_count is not None:
        student.backlog_count = payload.backlog_count
    if payload.phone is not None:
        student.phone = payload.phone
    if payload.linkedin_url is not None:
        student.linkedin_url = payload.linkedin_url
    if payload.roll_number is not None:
        # Check uniqueness if modified
        if payload.roll_number != student.roll_number:
            existing = db.query(Student).filter(
                Student.roll_number == payload.roll_number, Student.id != student.id
            ).first()
            if existing:
                raise AppError(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Roll number is already registered to another student.",
                    error_code="ROLL_NUMBER_TAKEN",
                )
            student.roll_number = payload.roll_number

    if payload.skills is not None:
        student.skills = payload.skills
    if payload.education is not None:
        student.education = payload.education
    if payload.experience is not None:
        student.experience = payload.experience
    if payload.projects is not None:
        student.projects = payload.projects
    if payload.certifications is not None:
        student.certifications = payload.certifications

    # Update User full name if provided
    if payload.full_name is not None and payload.full_name.strip():
        current_user.full_name = payload.full_name.strip()

    db.commit()
    db.refresh(student)
    db.refresh(current_user)

    primary_resume = _get_primary_resume(student.id, db)
    completion_pct = calculate_completion_percentage(student, current_user, primary_resume)

    resume_info = None
    if primary_resume:
        resume_info = ResumeInfo(
            id=primary_resume.id,
            filename=primary_resume.original_filename or os.path.basename(primary_resume.file_path),
            file_path=primary_resume.file_path,
            is_primary=primary_resume.is_primary,
            uploaded_at=primary_resume.uploaded_at,
            parsing_status=primary_resume.parsing_status,
            parsed_data=primary_resume.parsed_data,
        )

    profile_data = StudentProfileResponse(
        id=student.id,
        user_id=current_user.id,
        name=current_user.full_name,
        email=current_user.email,
        roll_number=student.roll_number,
        department=student.branch,
        batch=student.year,
        cgpa=student.cgpa,
        backlog_count=student.backlog_count,
        phone=student.phone,
        linkedin_url=student.linkedin_url,
        skills=student.skills or [],
        education=student.education,
        experience=student.experience,
        projects=student.projects,
        certifications=student.certifications,
        primary_resume=resume_info,
        profile_completion_pct=completion_pct,
    )

    return APIResponse(
        success=True,
        data=profile_data,
        message="Profile updated successfully.",
    )


# ---------------------------------------------------------------------------
# Resume Endpoints: POST /students/resume & GET /students/resume
# ---------------------------------------------------------------------------

@router.post(
    "/resume",
    response_model=APIResponse[ResumeInfo],
    summary="Upload a PDF resume",
)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    student = _get_or_create_student(current_user, db)

    # 1. Validate file extension and content type
    filename = file.filename or "resume.pdf"
    if not filename.lower().endswith(".pdf") and file.content_type != "application/pdf":
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Only PDF files are allowed for resume upload.",
            error_code="INVALID_FILE_TYPE",
        )

    # 2. Read file bytes
    content = await file.read()
    file_size = len(content)

    # 3. Validate non-empty
    if file_size == 0:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Uploaded file is empty.",
            error_code="EMPTY_FILE",
        )

    # 4. Validate max size (5 MB)
    max_size = 5 * 1024 * 1024
    if file_size > max_size:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="File size exceeds the 5MB limit.",
            error_code="FILE_TOO_LARGE",
        )

    # 5. Validate PDF header magic bytes (%PDF-)
    if not content.startswith(b"%PDF-"):
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Invalid or corrupted PDF file.",
            error_code="CORRUPTED_PDF",
        )

    # 6. Generate safe storage directory and filename
    upload_dir = settings.UPLOAD_DIRECTORY
    safe_original_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
    unique_filename = f"student_{student.id}_{uuid.uuid4().hex[:8]}_{safe_original_name}"
    file_path = os.path.join(upload_dir, unique_filename)

    # 7. Save to disk with error handling for file I/O
    try:
        os.makedirs(upload_dir, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"Resume uploaded: student_id={student.id}, filename={safe_original_name}, size={len(content)} bytes")
    except OSError as e:
        logger.error(f"Failed to save resume for student_id={student.id}: {e}")
        raise AppError(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            message="Failed to save resume file. Please try again later.",
            error_code="STORAGE_ERROR",
        )

    # 8. Resume-content validation (rule-based heuristic, runs before DB write)
    if settings.RESUME_VALIDATION_ENABLED:
        try:
            with pdfplumber.open(file_path) as pdf:
                _page_count = len(pdf.pages)
            raw_text = extract_text_from_pdf(file_path)
            validation = validate_resume_text(raw_text, page_count=_page_count)
        except ResumeExtractionError:
            # PDF has no extractable text — treat as inconclusive, let parsing
            # handle the failure gracefully; do NOT block the upload.
            validation = {"is_resume": True, "score": 0.0, "reasons": []}
        except Exception as exc:
            # Unexpected error in validator — log and allow the upload to proceed
            logger.warning(
                "Resume validator raised an unexpected error for student_id=%s: %s",
                student.id, exc,
            )
            validation = {"is_resume": True, "score": 0.0, "reasons": []}

        if not validation["is_resume"]:
            # Remove the temp file so we do not leave orphaned uploads on disk
            try:
                os.remove(file_path)
            except OSError:
                pass
            logger.warning(
                "Resume content rejected for student_id=%s: score=%.2f",
                student.id, validation["score"],
            )
            raise AppError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=(
                    "The uploaded PDF does not appear to be a resume. "
                    "Please upload your actual resume document."
                ),
                error_code="NOT_A_RESUME",
            )

    # Set any existing resumes for this student to non-primary
    db.query(Resume).filter(Resume.student_id == student.id).update({"is_primary": False})

    # Create new Resume record (parsing_status starts as "pending")
    new_resume = Resume(
        student_id=student.id,
        file_path=file_path,
        original_filename=filename,
        is_primary=True,
        uploaded_at=datetime.utcnow(),
        parsing_status="pending",
    )
    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)

    # --- Trigger AI parsing inline (never raises; failures stored on the row) ---
    _run_resume_parse(new_resume, db)
    db.refresh(new_resume)
    # --------------------------------------------------------------------------

    # Build parse-aware success message
    if new_resume.parsing_status == "success":
        upload_msg = "Resume uploaded and parsed successfully."
    elif new_resume.parsing_status == "failed":
        upload_msg = (
            "Resume uploaded successfully. "
            "Automatic parsing was unavailable — you can enter your details manually."
        )
    else:
        upload_msg = "Resume uploaded successfully."

    resume_data = ResumeInfo(
        id=new_resume.id,
        filename=new_resume.original_filename or unique_filename,
        file_path=new_resume.file_path,
        is_primary=new_resume.is_primary,
        uploaded_at=new_resume.uploaded_at,
        parsing_status=new_resume.parsing_status,
        parsed_data=new_resume.parsed_data,
    )

    return APIResponse(
        success=True,
        data=resume_data,
        message=upload_msg,
    )


@router.post(
    "/marksheet",
    response_model=APIResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Upload and verify a CGPA marksheet PDF",
)
async def upload_marksheet(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    student = _get_or_create_student(current_user, db)
    filename = file.filename or "marksheet.pdf"

    if not filename.lower().endswith(".pdf"):
        raise AppError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Only PDF marksheet files are allowed.",
            error_code="NOT_A_MARKSHEET",
        )

    content = await file.read()
    if not content:
        raise AppError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Uploaded file is empty.",
            error_code="EMPTY_MARKSHEET",
        )

    max_size_bytes = settings.MARKSHEET_MAX_SIZE_MB * 1024 * 1024
    if len(content) > max_size_bytes:
        raise AppError(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            message=f"Marksheet exceeds the {settings.MARKSHEET_MAX_SIZE_MB}MB limit.",
            error_code="FILE_TOO_LARGE",
        )

    if not content.startswith(b"%PDF-"):
        raise AppError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Invalid or corrupted PDF file.",
            error_code="INVALID_PDF",
        )

    upload_dir = settings.MARKSHEET_UPLOAD_DIRECTORY
    os.makedirs(upload_dir, exist_ok=True)
    temp_path = os.path.join(upload_dir, f"tmp_{uuid.uuid4().hex}.pdf")
    final_path = os.path.join(upload_dir, f"marksheet_{student.id}_{uuid.uuid4().hex}.pdf")

    try:
        with open(temp_path, "wb") as tmp_file:
            tmp_file.write(content)

        with pdfplumber.open(temp_path) as pdf:
            page_count = len(pdf.pages)

        text = extract_text_from_pdf(temp_path)
        if len(re.sub(r"\s+", "", text)) < 50:
            raise AppError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="We couldn't read text from this PDF. Please upload the digital (text-based) marksheet PDF from your university portal.",
                error_code="SCANNED_MARKSHEET",
            )

        validation = validate_marksheet_text(text, page_count=page_count)
        if not validation.get("is_valid"):
            raise AppError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="A valid academic marksheet PDF is required.",
                error_code="NOT_A_MARKSHEET",
                details=validation.get("reasons", []),
            )

        extraction = extract_cgpa(text)
        if extraction.get("error_code"):
            raise AppError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=extraction.get("message", "Unable to extract the cumulative CGPA."),
                error_code=extraction["error_code"],
            )

        if extraction["cgpa"] is None:
            raise AppError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Unable to extract the cumulative CGPA.",
                error_code="CGPA_NOT_FOUND",
            )

        shutil.move(temp_path, final_path)
        temp_path = None

        previous_cgpa = student.cgpa
        verified_at = datetime.utcnow()

        try:
            marksheet = Marksheet(
                student_id=student.id,
                original_filename=filename,
                stored_filename=os.path.basename(final_path),
                file_path=final_path,
                extracted_cgpa=float(extraction["cgpa"]),
                matched_label=extraction.get("label"),
                validation_score=validation.get("score"),
                uploaded_at=verified_at,
            )
            db.add(marksheet)
            db.flush()

            student.cgpa = float(extraction["cgpa"])
            student.cgpa_source = "MARKSHEET"
            student.cgpa_verified_at = verified_at
            student.current_marksheet_id = marksheet.id

            history_row = StudentCgpaHistory(
                student_id=student.id,
                old_cgpa=previous_cgpa,
                new_cgpa=float(extraction["cgpa"]),
                marksheet_id=marksheet.id,
                source="MARKSHEET",
                changed_at=verified_at,
            )
            db.add(history_row)

            from app.services.notification_service import create_notification

            create_notification(
                db,
                current_user.id,
                "CGPA Verified",
                f"Your CGPA was updated to {float(extraction['cgpa']):.2f} from your marksheet",
            )

            db.commit()
            db.refresh(student)
            db.refresh(marksheet)
        except Exception:
            db.rollback()
            if os.path.exists(final_path):
                try:
                    os.remove(final_path)
                except OSError:
                    pass
            raise

        logger.info(
            "Marksheet validation succeeded: student_id=%s, result=%s, validation_score=%s",
            student.id,
            extraction.get("error_code"),
            validation.get("score"),
        )

        return APIResponse(
            success=True,
            data={
                "cgpa": float(extraction["cgpa"]),
                "previous_cgpa": previous_cgpa,
                "source": "MARKSHEET",
                "verified_at": verified_at,
                "filename": filename,
            },
            message=f"Your CGPA was updated to {float(extraction['cgpa']):.2f} from your marksheet",
        )
    except AppError:
        raise
    except Exception as exc:
        logger.exception("Marksheet upload failed for student_id=%s: %s", student.id, exc)
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        if os.path.exists(final_path):
            try:
                os.remove(final_path)
            except OSError:
                pass
        raise AppError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unable to process the marksheet upload. Please try again later.",
            error_code="MARKSHEET_UPLOAD_FAILED",
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@router.get(
    "/resume",
    response_model=APIResponse[Optional[ResumeInfo]],
    summary="Get current student's active resume",
)
def get_current_resume(
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    student = _get_or_create_student(current_user, db)
    primary_resume = _get_primary_resume(student.id, db)

    resume_data = None
    if primary_resume:
        resume_data = ResumeInfo(
            id=primary_resume.id,
            filename=primary_resume.original_filename or os.path.basename(primary_resume.file_path),
            file_path=primary_resume.file_path,
            is_primary=primary_resume.is_primary,
            uploaded_at=primary_resume.uploaded_at,
            parsing_status=primary_resume.parsing_status,
            parsed_data=primary_resume.parsed_data,
        )

    return APIResponse(
        success=True,
        data=resume_data,
        message="Resume retrieved successfully.",
    )


@router.get(
    "/me/parsed-resume",
    response_model=APIResponse[ParsedResumeResponse],
    summary="Get parsed data from student's primary resume (for profile prefill)",
)
def get_parsed_resume(
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    """
    Returns the structured data extracted from the student's primary resume,
    along with the parsing_status so the frontend can decide which UI to render.

    - parsing_status == "success"  → parsed_data contains skills/education/etc.
    - parsing_status == "failed"   → parsed_data is null; show manual-entry prompt.
    - parsing_status == "pending"  → parsing hasn't run yet.
    - No primary resume            → all fields are null.
    """
    student = _get_or_create_student(current_user, db)
    primary_resume = _get_primary_resume(student.id, db)

    if not primary_resume:
        return APIResponse(
            success=True,
            data=ParsedResumeResponse(
                resume_id=None,
                parsing_status=None,
                parsing_error=None,
                parsed_data=None,
            ),
            message="No resume found for this student.",
        )

    return APIResponse(
        success=True,
        data=ParsedResumeResponse(
            resume_id=primary_resume.id,
            parsing_status=primary_resume.parsing_status,
            parsing_error=primary_resume.parsing_error,
            parsed_data=primary_resume.parsed_data,
        ),
        message="Parsed resume data retrieved successfully.",
    )


# ---------------------------------------------------------------------------
# Jobs Endpoints: GET /students/jobs & GET /students/jobs/{id}
# ---------------------------------------------------------------------------

@router.get(
    "/jobs",
    response_model=APIResponse[PaginatedJobsResponse],
    summary="List all OPEN jobs with eligibility status for current student",
)
def get_student_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for job title or company"),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    student = _get_or_create_student(current_user, db)

    # Base query for OPEN jobs
    query = (
        db.query(Job)
        .options(joinedload(Job.company))
        .filter(Job.status == JobStatus.OPEN)
    )

    # Search filter
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.join(Job.company).filter(
            or_(
                Job.title.ilike(term),
                Job.description.ilike(term),
                Company.name.ilike(term),
            )
        )

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    jobs = (
        query.order_by(Job.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items: List[StudentJobListItem] = []
    for job in jobs:
        # Check eligibility using the verified eligibility_service
        eligibility_dict = check_eligibility(student, job)
        eligibility_info = JobEligibilityInfo(
            eligible=eligibility_dict.get("eligible", False),
            reasons=eligibility_dict.get("reasons", []),
        )

        company_brief = None
        if job.company:
            company_brief = CompanyBrief(
                id=job.company.id,
                name=job.company.name,
                website=job.company.website,
                industry=job.company.industry,
                logo_url=job.company.logo_url,
            )

        items.append(
            StudentJobListItem(
                id=job.id,
                title=job.title,
                company=company_brief,
                location=job.location,
                package_lpa=job.package_lpa,
                status=job.status.value if hasattr(job.status, "value") else str(job.status),
                deadline=job.deadline,
                min_cgpa=job.min_cgpa,
                allowed_branches=job.allowed_branches,
                maximum_backlogs=job.maximum_backlogs,
                eligible_batch=job.eligible_batch,
                required_skills=job.required_skills,
                eligibility=eligibility_info,
                created_at=job.created_at,
            )
        )

    paginated_data = PaginatedJobsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

    return APIResponse(
        success=True,
        data=paginated_data,
        message="Jobs retrieved successfully.",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=APIResponse[StudentJobDetailResponse],
    summary="Get full job details and eligibility breakdown",
)
def get_student_job_detail(
    job_id: int,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    student = _get_or_create_student(current_user, db)

    job = (
        db.query(Job)
        .options(joinedload(Job.company))
        .filter(Job.id == job_id)
        .first()
    )

    if not job:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Job posting not found.",
            error_code="JOB_NOT_FOUND",
        )

    # Check eligibility using the verified eligibility_service
    eligibility_dict = check_eligibility(student, job)
    eligibility_info = JobEligibilityInfo(
        eligible=eligibility_dict.get("eligible", False),
        reasons=eligibility_dict.get("reasons", []),
    )

    company_brief = None
    if job.company:
        company_brief = CompanyBrief(
            id=job.company.id,
            name=job.company.name,
            website=job.company.website,
            industry=job.company.industry,
            logo_url=job.company.logo_url,
        )

    job_data = StudentJobDetailResponse(
        id=job.id,
        title=job.title,
        company=company_brief,
        description=job.description,
        location=job.location,
        package_lpa=job.package_lpa,
        status=job.status.value if hasattr(job.status, "value") else str(job.status),
        deadline=job.deadline,
        min_cgpa=job.min_cgpa,
        allowed_branches=job.allowed_branches,
        maximum_backlogs=job.maximum_backlogs,
        eligible_batch=job.eligible_batch,
        requirements=job.requirements,
        required_skills=job.required_skills,
        eligibility=eligibility_info,
        created_at=job.created_at,
    )

    return APIResponse(
        success=True,
        data=job_data,
        message="Job details retrieved successfully.",
    )


# ---------------------------------------------------------------------------
# Recommended Jobs: GET /students/recommended-jobs
# ---------------------------------------------------------------------------


def _build_job_text(job: Job) -> str:
    """Concatenate the key textual fields of a job for embedding."""
    parts = [job.title or ""]
    if job.description:
        parts.append(job.description)
    if job.required_skills:
        skills = job.required_skills
        if isinstance(skills, list):
            parts.append(" ".join(str(s) for s in skills))
    if job.preferred_skills:
        pskills = job.preferred_skills
        if isinstance(pskills, list):
            parts.append(" ".join(str(s) for s in pskills))
    if job.requirements:
        reqs = job.requirements
        if isinstance(reqs, list):
            parts.append(" ".join(str(r) for r in reqs))
    return " ".join(p.strip() for p in parts if p.strip())


@router.get(
    "/recommended-jobs",
    response_model=APIResponse[RecommendedJobsResponse],
    summary="Get AI-ranked job recommendations for the logged-in student",
)
def get_recommended_jobs(
    top_n: int = Query(
        None,
        ge=1,
        le=50,
        description="Override the default number of top recommendations to return.",
    ),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    """
    Returns up to *top_n* OPEN jobs ranked by semantic similarity to the
    student's primary resume embedding.  Each result includes:

    - ``semantic_score`` (0-100) — how closely the job matches the resume.
    - ``eligibility`` — the result of the hard eligibility check (CGPA /
      branch / backlogs / batch), computed independently and NEVER overridden
      by the semantic score.  A job can be highly recommended yet still
      NOT ELIGIBLE, or vice-versa.

    If the student has no primary resume (or no extractable text), the
    endpoint returns an empty list with a prompt to upload their resume.
    Embeddings are cached on the Resume and Job rows and only recomputed
    when the underlying text changes.
    """
    limit = top_n or settings.RECOMMENDATION_TOP_N
    student = _get_or_create_student(current_user, db)

    # ── 1. Fetch the student's primary resume and its embedding ────────────
    primary_resume = _get_primary_resume(student.id, db)

    if not primary_resume or not primary_resume.extracted_text:
        return APIResponse(
            success=True,
            data=RecommendedJobsResponse(
                items=[],
                has_resume=False,
                message=(
                    "Upload your resume to see personalised job recommendations "
                    "tailored to your skills and experience."
                ),
            ),
            message="No resume found — upload one to get personalised recommendations.",
        )

    resume_text = primary_resume.extracted_text
    resume_text_hash = text_hash(resume_text)

    # Get-or-generate the resume embedding (cached on the Resume row).
    try:
        resume_embedding, resume_regenerated = get_or_generate_embedding(
            text=resume_text,
            cached_embedding=primary_resume.embedding,
            cached_text_hash=primary_resume.embedding_hash,
            current_text_hash=resume_text_hash,
        )
    except EmbeddingGenerationError as exc:
        logger.warning(
            "Could not generate resume embedding for student_id=%s: %s",
            student.id,
            exc,
        )
        return APIResponse(
            success=True,
            data=RecommendedJobsResponse(
                items=[],
                has_resume=True,
                message=(
                    "We were unable to analyse your resume at this time. "
                    "Please try again later, or enter your details manually."
                ),
            ),
            message="Resume embedding unavailable.",
        )

    # Persist updated resume embedding if it was regenerated.
    if resume_regenerated:
        primary_resume.embedding = resume_embedding
        primary_resume.embedding_hash = resume_text_hash
        db.add(primary_resume)
        db.commit()
        db.refresh(primary_resume)

    # ── 2. Load all OPEN jobs ──────────────────────────────────────────────
    open_jobs = (
        db.query(Job)
        .options(joinedload(Job.company))
        .filter(Job.status == JobStatus.OPEN)
        .all()
    )

    if not open_jobs:
        return APIResponse(
            success=True,
            data=RecommendedJobsResponse(
                items=[],
                has_resume=True,
                message="There are currently no open job postings to recommend.",
            ),
            message="No open jobs available.",
        )

    # ── 3. Score each job against the resume embedding ─────────────────────
    scored: list[tuple[float, Job, list[float]]] = []

    for job in open_jobs:
        job_text = _build_job_text(job)
        if not job_text.strip():
            # Skip jobs with no textual content to embed.
            continue

        job_text_hash = text_hash(job_text)

        try:
            job_embedding, job_regenerated = get_or_generate_embedding(
                text=job_text,
                cached_embedding=job.embedding,
                cached_text_hash=job.embedding_hash,
                current_text_hash=job_text_hash,
            )
        except EmbeddingGenerationError:
            logger.debug("Skipping job_id=%s — embedding failed.", job.id)
            continue

        # Persist updated job embedding if regenerated.
        if job_regenerated:
            job.embedding = job_embedding
            job.embedding_hash = job_text_hash
            db.add(job)

        try:
            sim = cosine_similarity_score(resume_embedding, job_embedding)
        except ValueError:
            continue

        scored.append((sim, job, job_embedding))

    # Flush any updated job embeddings in one batch.
    db.commit()

    # Sort descending by similarity, take top-N.
    scored.sort(key=lambda t: t[0], reverse=True)
    top_scored = scored[:limit]

    # ── 4. Build response — eligibility is computed independently ──────────
    items: list[RecommendedJobItem] = []
    for sim_score, job, _job_emb in top_scored:
        # Hard eligibility check — NEVER derived from or overridden by semantic score.
        elig_dict = check_eligibility(student, job)
        eligibility_info = JobEligibilityInfo(
            eligible=elig_dict.get("eligible", False),
            reasons=elig_dict.get("reasons", []),
        )

        company_brief = None
        if job.company:
            company_brief = CompanyBrief(
                id=job.company.id,
                name=job.company.name,
                website=job.company.website,
                industry=job.company.industry,
                logo_url=job.company.logo_url,
            )

        items.append(
            RecommendedJobItem(
                id=job.id,
                title=job.title,
                company=company_brief,
                location=job.location,
                package_lpa=job.package_lpa,
                status=job.status.value if hasattr(job.status, "value") else str(job.status),
                deadline=job.deadline,
                min_cgpa=job.min_cgpa,
                allowed_branches=job.allowed_branches,
                maximum_backlogs=job.maximum_backlogs,
                eligible_batch=job.eligible_batch,
                required_skills=job.required_skills,
                created_at=job.created_at,
                # Semantic score (0-100): how relevant this job is to the resume.
                # This is SEPARATE from eligibility — a high score does NOT imply eligible.
                semantic_score=round(sim_score, 2),
                # Hard eligibility result — entirely independent of semantic_score.
                eligibility=eligibility_info,
            )
        )

    return APIResponse(
        success=True,
        data=RecommendedJobsResponse(
            items=items,
            has_resume=True,
            message=(
                f"Showing top {len(items)} job recommendations based on your resume."
                if items
                else "No jobs could be scored against your resume at this time."
            ),
        ),
        message="Recommended jobs retrieved successfully.",
    )
