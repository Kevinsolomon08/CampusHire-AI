# app/api/jobs.py
# API routes for Job CRUD, publishing, and closing with strict recruiter company ownership enforcement.

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import AppError, get_current_user, require_role
from app.database.connection import get_db
from app.models.models import Application, Company, Job, JobStatus, Recruiter, User, UserRole
from app.schemas.recruiter import CompanyOut, JobCreate, JobDetailResponse, JobUpdate
from app.schemas.response import APIResponse

router = APIRouter()


def _format_job_detail(job: Job, db: Session) -> JobDetailResponse:
    company_out = None
    if job.company:
        company_out = CompanyOut(
            id=job.company.id,
            name=job.company.name,
            website=job.company.website,
            industry=job.company.industry,
            description=job.company.description,
            logo_url=job.company.logo_url,
            contact_email=job.company.contact_email,
            contact_phone=job.company.contact_phone,
            address=job.company.address,
            created_at=job.company.created_at,
        )

    total_applicants = (
        db.query(Application).filter(Application.job_id == job.id).count()
    )

    return JobDetailResponse(
        id=job.id,
        company_id=job.company_id,
        company=company_out,
        created_by=job.created_by,
        title=job.title,
        description=job.description,
        requirements=job.requirements,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
        min_cgpa=job.min_cgpa,
        allowed_branches=job.allowed_branches,
        maximum_backlogs=job.maximum_backlogs,
        eligible_batch=job.eligible_batch,
        experience_requirement=job.experience_requirement,
        employment_type=job.employment_type or "FULL_TIME",
        location=job.location,
        package_lpa=job.package_lpa,
        status=job.status.value if hasattr(job.status, "value") else str(job.status),
        deadline=job.deadline,
        total_applicants=total_applicants,
        eligible_applicants=0,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _get_recruiter_and_verify_job_ownership(job_id: int, user: User, db: Session) -> tuple[Recruiter, Job]:
    """Retrieves job and verifies that current recruiter's company owns it."""
    recruiter = db.query(Recruiter).filter(Recruiter.user_id == user.id).first()
    if not recruiter:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Recruiter profile not found.",
            error_code="RECRUITER_NOT_FOUND",
        )

    job = db.query(Job).options(joinedload(Job.company)).filter(Job.id == job_id).first()
    if not job:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Job posting not found.",
            error_code="JOB_NOT_FOUND",
        )

    # Strict ownership check: Recruiter cannot edit or manage another recruiter's / company's job
    if job.company_id != recruiter.company_id:
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You are not authorized to perform this action.",
            error_code="FORBIDDEN",
        )

    return recruiter, job


@router.post(
    "",
    response_model=APIResponse[JobDetailResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job (scoped to recruiter's company)",
)
def create_job(
    payload: JobCreate,
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
    db: Session = Depends(get_db),
):
    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
    if not recruiter:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Recruiter profile not found.",
            error_code="RECRUITER_NOT_FOUND",
        )

    initial_status = JobStatus.DRAFT
    if payload.status:
        try:
            initial_status = JobStatus(payload.status.upper())
        except ValueError:
            initial_status = JobStatus.DRAFT

    # If creating directly in OPEN status, validate deadline
    if initial_status == JobStatus.OPEN:
        if not payload.deadline:
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Application deadline is required to publish a job.",
                error_code="DEADLINE_REQUIRED",
            )
        now = datetime.now(timezone.utc)
        deadline_utc = payload.deadline if payload.deadline.tzinfo else payload.deadline.replace(tzinfo=timezone.utc)
        if deadline_utc <= now:
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Job deadline must be in the future to publish.",
                error_code="INVALID_DEADLINE",
            )

    cgpa_val = payload.minimum_cgpa if payload.minimum_cgpa is not None else payload.min_cgpa

    new_job = Job(
        company_id=recruiter.company_id,
        created_by=current_user.id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        requirements=payload.requirements or [],
        required_skills=payload.required_skills or [],
        preferred_skills=payload.preferred_skills or [],
        min_cgpa=cgpa_val,
        allowed_branches=payload.allowed_branches or [],
        maximum_backlogs=payload.maximum_backlogs,
        eligible_batch=payload.eligible_batch,
        experience_requirement=payload.experience_requirement.strip() if payload.experience_requirement else None,
        employment_type=payload.employment_type or "FULL_TIME",
        location=payload.location.strip() if payload.location else None,
        package_lpa=payload.package_lpa,
        status=initial_status,
        deadline=payload.deadline,
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return APIResponse(
        success=True,
        data=_format_job_detail(new_job, db),
        message="Job created successfully.",
    )


@router.get(
    "/{job_id}",
    response_model=APIResponse[JobDetailResponse],
    summary="Get Job details by ID",
)
def get_job_by_id(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.query(Job).options(joinedload(Job.company)).filter(Job.id == job_id).first()
    if not job:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Job posting not found.",
            error_code="JOB_NOT_FOUND",
        )

    return APIResponse(
        success=True,
        data=_format_job_detail(job, db),
        message="Job details retrieved successfully.",
    )


@router.put(
    "/{job_id}",
    response_model=APIResponse[JobDetailResponse],
    summary="Update a Job (Scoped to owning recruiter only)",
)
def update_job(
    job_id: int,
    payload: JobUpdate,
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
    db: Session = Depends(get_db),
):
    _, job = _get_recruiter_and_verify_job_ownership(job_id, current_user, db)

    if payload.title is not None and payload.title.strip():
        job.title = payload.title.strip()
    if payload.description is not None and payload.description.strip():
        job.description = payload.description.strip()
    if payload.requirements is not None:
        job.requirements = payload.requirements
    if payload.required_skills is not None:
        job.required_skills = payload.required_skills
    if payload.preferred_skills is not None:
        job.preferred_skills = payload.preferred_skills

    cgpa_val = payload.minimum_cgpa if payload.minimum_cgpa is not None else payload.min_cgpa
    if cgpa_val is not None:
        job.min_cgpa = cgpa_val

    if payload.allowed_branches is not None:
        job.allowed_branches = payload.allowed_branches
    if payload.maximum_backlogs is not None:
        job.maximum_backlogs = payload.maximum_backlogs
    if payload.eligible_batch is not None:
        job.eligible_batch = payload.eligible_batch
    if payload.experience_requirement is not None:
        job.experience_requirement = payload.experience_requirement.strip() if payload.experience_requirement else None
    if payload.employment_type is not None:
        job.employment_type = payload.employment_type
    if payload.location is not None:
        job.location = payload.location.strip() if payload.location else None
    if payload.package_lpa is not None:
        job.package_lpa = payload.package_lpa

    if payload.deadline is not None:
        job.deadline = payload.deadline

    if payload.status is not None:
        try:
            job.status = JobStatus(payload.status.upper())
        except ValueError:
            pass

    db.commit()
    db.refresh(job)

    return APIResponse(
        success=True,
        data=_format_job_detail(job, db),
        message="Job updated successfully.",
    )


@router.delete(
    "/{job_id}",
    response_model=APIResponse[dict],
    summary="Delete a Job (Scoped to owning recruiter only)",
)
def delete_job(
    job_id: int,
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
    db: Session = Depends(get_db),
):
    _, job = _get_recruiter_and_verify_job_ownership(job_id, current_user, db)

    db.delete(job)
    db.commit()

    return APIResponse(
        success=True,
        data={"deleted_job_id": job_id},
        message="Job deleted successfully.",
    )


@router.post(
    "/{job_id}/publish",
    response_model=APIResponse[JobDetailResponse],
    summary="Publish Job: DRAFT -> OPEN (Requires future deadline)",
)
def publish_job(
    job_id: int,
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
    db: Session = Depends(get_db),
):
    _, job = _get_recruiter_and_verify_job_ownership(job_id, current_user, db)

    # Validate deadline
    if not job.deadline:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Application deadline is required to publish a job.",
            error_code="DEADLINE_REQUIRED",
        )

    now = datetime.now(timezone.utc)
    deadline_utc = job.deadline if job.deadline.tzinfo else job.deadline.replace(tzinfo=timezone.utc)
    if deadline_utc <= now:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Job deadline must be in the future to publish.",
            error_code="INVALID_DEADLINE",
        )

    job.status = JobStatus.OPEN
    db.commit()
    db.refresh(job)

    return APIResponse(
        success=True,
        data=_format_job_detail(job, db),
        message="Job published successfully.",
    )


@router.post(
    "/{job_id}/close",
    response_model=APIResponse[JobDetailResponse],
    summary="Close Job: OPEN -> CLOSED",
)
def close_job(
    job_id: int,
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
    db: Session = Depends(get_db),
):
    _, job = _get_recruiter_and_verify_job_ownership(job_id, current_user, db)

    job.status = JobStatus.CLOSED
    db.commit()
    db.refresh(job)

    return APIResponse(
        success=True,
        data=_format_job_detail(job, db),
        message="Job closed successfully.",
    )
