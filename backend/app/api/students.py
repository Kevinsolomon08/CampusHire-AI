# app/api/students.py
# API routes for Student profile management, resume upload, and job eligibility browsing.

from __future__ import annotations

import logging
import math
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import AppError, get_current_user, require_role
from app.core.config import settings
from app.database.connection import get_db
from app.models.models import Company, Job, JobStatus, Resume, Student, User, UserRole
from app.schemas.response import APIResponse
from app.schemas.student import (
    CompanyBrief,
    JobEligibilityInfo,
    PaginatedJobsResponse,
    ResumeInfo,
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

    # Update Student specific fields
    if payload.department is not None:
        student.branch = payload.department
    if payload.batch is not None:
        student.year = payload.batch
    if payload.cgpa is not None:
        student.cgpa = payload.cgpa
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

    # Set any existing resumes for this student to non-primary
    db.query(Resume).filter(Resume.student_id == student.id).update({"is_primary": False})

    # Create new Resume record
    new_resume = Resume(
        student_id=student.id,
        file_path=file_path,
        original_filename=filename,
        is_primary=True,
        uploaded_at=datetime.utcnow(),
    )
    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)

    resume_data = ResumeInfo(
        id=new_resume.id,
        filename=new_resume.original_filename or unique_filename,
        file_path=new_resume.file_path,
        is_primary=new_resume.is_primary,
        uploaded_at=new_resume.uploaded_at,
    )

    return APIResponse(
        success=True,
        data=resume_data,
        message="Resume uploaded successfully.",
    )


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
        )

    return APIResponse(
        success=True,
        data=resume_data,
        message="Resume retrieved successfully.",
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
