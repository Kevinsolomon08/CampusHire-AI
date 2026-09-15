# app/api/recruiters.py
# API routes for Recruiter profile and recruiter-scoped job listing.

from __future__ import annotations

import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import AppError, get_current_user, require_role
from app.database.connection import get_db
from app.models.models import Application, Company, Job, JobStatus, Recruiter, User, UserRole
from app.schemas.recruiter import (
    CompanyOut,
    PaginatedRecruiterJobsResponse,
    RecruiterJobListItem,
    RecruiterProfileResponse,
)
from app.schemas.response import APIResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=APIResponse[RecruiterProfileResponse],
    summary="Get current Recruiter profile and linked company metrics",
)
def get_recruiter_profile(
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
    db: Session = Depends(get_db),
):
    recruiter = (
        db.query(Recruiter)
        .options(joinedload(Recruiter.company))
        .filter(Recruiter.user_id == current_user.id)
        .first()
    )

    if not recruiter:
        # Create a default recruiter record with a company if none exists
        company = Company(name=f"{current_user.full_name}'s Company")
        db.add(company)
        db.flush()

        recruiter = Recruiter(
            user_id=current_user.id,
            company_id=company.id,
            designation="Talent Acquisition Lead",
        )
        db.add(recruiter)
        db.commit()
        db.refresh(recruiter)

    # Real counts for this recruiter's company
    total_jobs = db.query(Job).filter(Job.company_id == recruiter.company_id).count()
    active_jobs = (
        db.query(Job)
        .filter(Job.company_id == recruiter.company_id, Job.status == JobStatus.OPEN)
        .count()
    )

    company_out = None
    if recruiter.company:
        company_out = CompanyOut(
            id=recruiter.company.id,
            name=recruiter.company.name,
            website=recruiter.company.website,
            industry=recruiter.company.industry,
            description=recruiter.company.description,
            logo_url=recruiter.company.logo_url,
            contact_email=recruiter.company.contact_email,
            contact_phone=recruiter.company.contact_phone,
            address=recruiter.company.address,
            created_at=recruiter.company.created_at,
        )

    profile_data = RecruiterProfileResponse(
        id=recruiter.id,
        user_id=current_user.id,
        name=current_user.full_name,
        email=current_user.email,
        designation=recruiter.designation,
        phone=recruiter.phone,
        company=company_out,
        total_jobs=total_jobs,
        active_jobs=active_jobs,
    )

    return APIResponse(
        success=True,
        data=profile_data,
        message="Recruiter profile retrieved successfully.",
    )


@router.get(
    "/jobs",
    response_model=APIResponse[PaginatedRecruiterJobsResponse],
    summary="List recruiter's own company jobs (paginated with applicant counts)",
)
def get_recruiter_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
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

    query = (
        db.query(Job)
        .options(joinedload(Job.company))
        .filter(Job.company_id == recruiter.company_id)
    )

    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(Job.status == status_filter.upper())

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(term),
                Job.description.ilike(term),
                Job.location.ilike(term),
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

    items: List[RecruiterJobListItem] = []
    for job in jobs:
        # Count applicants in DB (will be >0 once Prompt 5 applications exist)
        total_applicants = (
            db.query(Application).filter(Application.job_id == job.id).count()
        )

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

        items.append(
            RecruiterJobListItem(
                id=job.id,
                company_id=job.company_id,
                company=company_out,
                title=job.title,
                location=job.location,
                package_lpa=job.package_lpa,
                status=job.status.value if hasattr(job.status, "value") else str(job.status),
                deadline=job.deadline,
                min_cgpa=job.min_cgpa,
                allowed_branches=job.allowed_branches,
                maximum_backlogs=job.maximum_backlogs,
                eligible_batch=job.eligible_batch,
                required_skills=job.required_skills,
                employment_type=job.employment_type or "FULL_TIME",
                total_applicants=total_applicants,
                eligible_applicants=0,
                created_at=job.created_at,
            )
        )

    paginated_data = PaginatedRecruiterJobsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

    return APIResponse(
        success=True,
        data=paginated_data,
        message="Recruiter jobs retrieved successfully.",
    )
