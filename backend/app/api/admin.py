# app/api/admin.py
# Admin/Placement Officer management endpoints.

from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database.connection import get_db
from app.models.models import User, UserRole
from app.schemas.response import APIResponse
from app.services.admin_service import (
    get_applications_paginated,
    get_companies_paginated,
    get_dashboard_counts,
    get_interviews_paginated,
    get_jobs_paginated,
    get_statistics,
    get_students_paginated,
)
from app.services.reports_service import get_placement_report, generate_csv_report

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper: Require Placement Officer Role
# ---------------------------------------------------------------------------

async def require_placement_officer(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to ensure only placement officers can access admin endpoints."""
    if current_user.role != UserRole.PLACEMENT_OFFICER:
        from app.api.deps import AppError
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Only placement officers can access admin endpoints",
            error_code="FORBIDDEN",
        )
    return current_user


# ---------------------------------------------------------------------------
# Students Endpoint
# ---------------------------------------------------------------------------


@router.get("/students", response_model=dict, tags=["Admin"], summary="Get paginated list of students with filters")
async def get_students(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    department: Optional[str] = Query(None, description="Filter by department"),
    batch: Optional[int] = Query(None, description="Filter by batch year"),
    current_user: User = Depends(require_placement_officer),
    db: Session = Depends(get_db),
) -> APIResponse:
    """
    Get paginated list of students (Placement Officer only).

    Query Parameters:
    - page: Page number (1-indexed), default 1
    - page_size: Items per page, default 10, max 100
    - search: Search by student name or email
    - department: Filter by department (e.g., "CSE", "ECE")
    - batch: Filter by batch year (e.g., 2024)

    Returns:
        {
            "success": true,
            "data": {
                "items": [
                    {
                        "id": int,
                        "user_id": int,
                        "name": str,
                        "email": str,
                        "department": str,
                        "batch": int,
                        "cgpa": float,
                        "backlogs": int,
                        "created_at": ISO 8601 datetime
                    },
                    ...
                ],
                "total": int,
                "page": int,
                "page_size": int,
                "total_pages": int
            }
        }
    """
    items, total = get_students_paginated(
        db,
        page=page,
        page_size=page_size,
        search=search,
        department=department,
        batch=batch,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
    }


# ---------------------------------------------------------------------------
# Companies Endpoint
# ---------------------------------------------------------------------------


@router.get("/companies", response_model=dict, tags=["Admin"], summary="Get paginated list of registered companies")
async def get_companies(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by company name or industry"),
    current_user: User = Depends(require_placement_officer),
    db: Session = Depends(get_db),
) -> APIResponse:
    """
    Get paginated list of companies (Placement Officer only).

    Query Parameters:
    - page: Page number (1-indexed), default 1
    - page_size: Items per page, default 10, max 100
    - search: Search by company name or industry

    Returns:
        {
            "success": true,
            "data": {
                "items": [
                    {
                        "id": int,
                        "name": str,
                        "industry": str,
                        "website": str,
                        "location": str,
                        "hrContact": str,
                        "created_at": ISO 8601 datetime
                    },
                    ...
                ],
                "total": int,
                "page": int,
                "page_size": int,
                "total_pages": int
            }
        }
    """
    items, total = get_companies_paginated(
        db,
        page=page,
        page_size=page_size,
        search=search,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
    }


# ---------------------------------------------------------------------------
# Jobs Endpoint
# ---------------------------------------------------------------------------


@router.get("/jobs", response_model=dict, tags=["Admin"], summary="Get paginated list of job postings across all companies")
async def get_jobs(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by job title or description"),
    company_id: Optional[int] = Query(None, description="Filter by company"),
    status: Optional[str] = Query(None, description="Filter by job status (OPEN, CLOSED, DRAFT, PUBLISHED)"),
    current_user: User = Depends(require_placement_officer),
    db: Session = Depends(get_db),
) -> APIResponse:
    """
    Get paginated list of jobs (Placement Officer only).

    Query Parameters:
    - page: Page number (1-indexed), default 1
    - page_size: Items per page, default 10, max 100
    - search: Search by job title or description
    - company_id: Filter by company ID
    - status: Filter by job status (OPEN, CLOSED, DRAFT, PUBLISHED)

    Returns:
        {
            "success": true,
            "data": {
                "items": [
                    {
                        "id": int,
                        "title": str,
                        "company_id": int,
                        "company_name": str,
                        "description": str,
                        "package_lpa": float,
                        "location": str,
                        "status": str,
                        "deadline": ISO 8601 datetime,
                        "created_at": ISO 8601 datetime
                    },
                    ...
                ],
                "total": int,
                "page": int,
                "page_size": int,
                "total_pages": int
            }
        }
    """
    items, total = get_jobs_paginated(
        db,
        page=page,
        page_size=page_size,
        search=search,
        company_id=company_id,
        status=status,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
    }


# ---------------------------------------------------------------------------
# Applications Endpoint
# ---------------------------------------------------------------------------


@router.get("/applications", response_model=dict, tags=["Admin"], summary="Get paginated list of all candidate applications")
async def get_applications(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by student name or email"),
    app_status: Optional[str] = Query(None, description="Filter by application status"),
    company_id: Optional[int] = Query(None, description="Filter by company"),
    department: Optional[str] = Query(None, description="Filter by student department"),
    current_user: User = Depends(require_placement_officer),
    db: Session = Depends(get_db),
) -> APIResponse:
    """
    Get paginated list of applications (Placement Officer only).

    Query Parameters:
    - page: Page number (1-indexed), default 1
    - page_size: Items per page, default 10, max 100
    - search: Search by student name or email
    - app_status: Filter by application status (APPLIED, ELIGIBILITY_VERIFIED, SHORTLISTED, INTERVIEW_SCHEDULED, INTERVIEW, SELECTED, REJECTED)
    - company_id: Filter by company ID
    - department: Filter by student department

    Returns:
        {
            "success": true,
            "data": {
                "items": [
                    {
                        "id": int,
                        "student_name": str,
                        "student_email": str,
                        "student_department": str,
                        "job_title": str,
                        "company_name": str,
                        "status": str,
                        "created_at": ISO 8601 datetime
                    },
                    ...
                ],
                "total": int,
                "page": int,
                "page_size": int,
                "total_pages": int
            }
        }
    """
    items, total = get_applications_paginated(
        db,
        page=page,
        page_size=page_size,
        search=search,
        app_status=app_status,
        company_id=company_id,
        department=department,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
    }


# ---------------------------------------------------------------------------
# Interviews Endpoint
# ---------------------------------------------------------------------------


@router.get("/interviews", response_model=dict, tags=["Admin"], summary="Get paginated list of scheduled interviews")
async def get_interviews(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by student name or email"),
    result_status: Optional[str] = Query(None, description="Filter by interview result (PENDING, PASSED, FAILED, NO_SHOW)"),
    company_id: Optional[int] = Query(None, description="Filter by company"),
    department: Optional[str] = Query(None, description="Filter by student department"),
    current_user: User = Depends(require_placement_officer),
    db: Session = Depends(get_db),
) -> APIResponse:
    """
    Get paginated list of interviews (Placement Officer only).

    Query Parameters:
    - page: Page number (1-indexed), default 1
    - page_size: Items per page, default 10, max 100
    - search: Search by student name or email
    - result_status: Filter by interview result (PENDING, PASSED, FAILED, NO_SHOW)
    - company_id: Filter by company ID
    - department: Filter by student department

    Returns:
        {
            "success": true,
            "data": {
                "items": [
                    {
                        "id": int,
                        "student_name": str,
                        "student_email": str,
                        "job_title": str,
                        "company_name": str,
                        "scheduled_at": ISO 8601 datetime,
                        "result": str,
                        "round": str,
                        "created_at": ISO 8601 datetime
                    },
                    ...
                ],
                "total": int,
                "page": int,
                "page_size": int,
                "total_pages": int
            }
        }
    """
    items, total = get_interviews_paginated(
        db,
        page=page,
        page_size=page_size,
        search=search,
        result_status=result_status,
        company_id=company_id,
        department=department,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
    }


# ---------------------------------------------------------------------------
# Dashboard Endpoint
# ---------------------------------------------------------------------------


@router.get("/dashboard", response_model=dict, tags=["Admin"], summary="Get placement officer dashboard KPI metrics")
async def get_dashboard(
    current_user: User = Depends(require_placement_officer),
    db: Session = Depends(get_db),
) -> APIResponse:
    """
    Get dashboard aggregate counts (Placement Officer only).

    Returns:
        {
            "success": true,
            "data": {
                "total_students": int,
                "total_companies": int,
                "active_recruitment_drives": int,
                "total_job_postings": int,
                "total_applications": int,
                "applications_shortlisted": int,
                "total_interviews": int,
                "applications_selected": int,
                "applications_rejected": int,
                "placement_percentage": float
            }
        }
    """
    counts = get_dashboard_counts(db)
    return {
        "success": True,
        "data": counts,
    }


# ---------------------------------------------------------------------------
# Statistics Endpoint (for Charts)
# ---------------------------------------------------------------------------


@router.get("/statistics", response_model=dict, tags=["Admin"], summary="Get charts and placement statistics data")
async def get_admin_statistics(
    current_user: User = Depends(require_placement_officer),
    db: Session = Depends(get_db),
) -> APIResponse:
    """
    Get statistics data for dashboard charts (Placement Officer only).

    Returns:
        {
            "success": true,
            "data": {
                "applications_by_company": [
                    {"company": str, "count": int},
                    ...
                ],
                "selections_by_company": [
                    {"company": str, "count": int},
                    ...
                ],
                "applications_by_department": [
                    {"department": str, "count": int},
                    ...
                ],
                "selection_rate_by_department": [
                    {"department": str, "rate": float},
                    ...
                ],
                "recruitment_drive_status": [
                    {"status": str, "count": int},
                    ...
                ],
                "application_funnel": [
                    {"stage": str, "count": int},
                    ...
                ]
            }
        }
    """
    stats = get_statistics(db)
    return {
        "success": True,
        "data": stats,
    }


# ---------------------------------------------------------------------------
# Reports Endpoint
# ---------------------------------------------------------------------------


@router.get("/reports", response_model=dict, tags=["Admin"], summary="Generate comprehensive placement report with JSON or CSV export")
async def get_reports(
    batch: Optional[int] = Query(None, description="Filter by student batch year"),
    department: Optional[str] = Query(None, description="Filter by student department"),
    company_id: Optional[int] = Query(None, description="Filter by company"),
    job_id: Optional[int] = Query(None, description="Filter by job"),
    format: str = Query("json", pattern="^(json|csv)$", description="Export format: json or csv"),
    current_user: User = Depends(require_placement_officer),
    db: Session = Depends(get_db),
) -> APIResponse:
    """
    Generate a comprehensive placement report with various breakdowns (Placement Officer only).

    Query Parameters:
    - batch: Filter by student batch year (e.g., 2024)
    - department: Filter by student department (e.g., "CSE")
    - company_id: Filter by company ID
    - job_id: Filter by job ID
    - format: Export format - "json" (default) or "csv"

    Returns (JSON):
        {
            "success": true,
            "data": {
                "summary": {
                    "total_applications": int,
                    "total_shortlisted": int,
                    "total_interviewed": int,
                    "total_selected": int,
                    "total_rejected": int,
                    "selection_rate": float
                },
                "company_breakdown": [
                    {
                        "company_id": int,
                        "company_name": str,
                        "applications": int,
                        "selected": int,
                        "rejected": int,
                        "selection_rate": float
                    },
                    ...
                ],
                "department_breakdown": [...],
                "batch_breakdown": [...]
            }
        }

    Returns (CSV): CSV file with summary, company-wise, department-wise, and batch-wise breakdowns
    """
    from fastapi.responses import StreamingResponse
    import io

    report_data = get_placement_report(
        db,
        batch=batch,
        department=department,
        company_id=company_id,
        job_id=job_id,
    )

    if format == "csv":
        csv_content = generate_csv_report(report_data)
        # Return CSV as downloadable file
        output = io.BytesIO()
        output.write(csv_content.encode('utf-8'))
        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=placement_report.csv"
            },
        )

    # Default: JSON
    return {
        "success": True,
        "data": report_data,
    }
