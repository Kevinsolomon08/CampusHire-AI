# app/services/admin_service.py
"""
CampusHire Admin Service.

Provides query helpers for the Placement Officer dashboard, including:
- Student queries (with filters: department, batch, name)
- Company queries (with filters: name)
- Job queries (with filters: company, status)
- Application queries (with filters: status, company, department)
- Interview queries (with filters: status, company, department)
- Dashboard aggregate counts
- Statistics for charting (applications by company, selections by company, etc.)
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.models import (
    Application,
    ApplicationStatus,
    ApplicationStatusHistory,
    Company,
    Interview,
    InterviewResult,
    Job,
    JobStatus,
    Student,
    User,
    UserRole,
)


# ---------------------------------------------------------------------------
# Student Queries
# ---------------------------------------------------------------------------

def get_students_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
    department: Optional[str] = None,
    batch: Optional[int] = None,
) -> tuple[list, int]:
    """
    Get paginated list of students with optional filters.

    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Items per page
        search: Search by name or email
        department: Filter by department (branch)
        batch: Filter by batch year (year)

    Returns:
        (list of student dicts, total count)
    """
    query = db.query(Student).join(User, Student.user_id == User.id)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                Student.roll_number.ilike(search_term),
            )
        )

    if department:
        query = query.filter(Student.branch == department)

    if batch:
        query = query.filter(Student.year == batch)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    students = query.offset(offset).limit(page_size).all()

    # Format results
    result = []
    for s in students:
        result.append(
            {
                "id": s.id,
                "user_id": s.user_id,
                "name": s.user.full_name if s.user else "Unknown",
                "email": s.user.email if s.user else "Unknown",
                "department": s.branch,
                "batch": s.year,
                "cgpa": s.cgpa,
                "backlogs": s.backlog_count,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
        )

    return result, total


# ---------------------------------------------------------------------------
# Company Queries
# ---------------------------------------------------------------------------

def get_companies_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
) -> tuple[list, int]:
    """
    Get paginated list of companies with optional search.

    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Items per page
        search: Search by company name or industry

    Returns:
        (list of company dicts, total count)
    """
    query = db.query(Company)

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Company.name.ilike(search_term),
                Company.industry.ilike(search_term),
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    companies = query.offset(offset).limit(page_size).all()

    # Format results
    result = []
    for c in companies:
        result.append(
            {
                "id": c.id,
                "name": c.name,
                "industry": c.industry,
                "website": c.website,
                "location": c.address,
                "hrContact": c.contact_email,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
        )

    return result, total


# ---------------------------------------------------------------------------
# Job Queries
# ---------------------------------------------------------------------------

def get_jobs_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
    company_id: Optional[int] = None,
    status: Optional[str] = None,
) -> tuple[list, int]:
    """
    Get paginated list of jobs with optional filters.

    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Items per page
        search: Search by job title or description
        company_id: Filter by company
        status: Filter by job status (OPEN, CLOSED, DRAFT)

    Returns:
        (list of job dicts, total count)
    """
    query = db.query(Job).join(Company, Job.company_id == Company.id)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Job.title.ilike(search_term),
                Job.description.ilike(search_term),
                Company.name.ilike(search_term),
            )
        )

    if company_id:
        query = query.filter(Job.company_id == company_id)

    if status:
        query = query.filter(Job.status == status)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    jobs = query.offset(offset).limit(page_size).all()

    # Format results
    result = []
    for j in jobs:
        status_val = j.status.value if hasattr(j.status, "value") else str(j.status)
        result.append(
            {
                "id": j.id,
                "title": j.title,
                "company_id": j.company_id,
                "company_name": j.company.name if j.company else "Unknown",
                "description": j.description,
                "package_lpa": j.package_lpa,
                "location": j.location,
                "status": status_val,
                "deadline": j.deadline.isoformat() if j.deadline else None,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
        )

    return result, total


# ---------------------------------------------------------------------------
# Application Queries
# ---------------------------------------------------------------------------

def get_applications_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
    app_status: Optional[str] = None,
    company_id: Optional[int] = None,
    department: Optional[str] = None,
) -> tuple[list, int]:
    """
    Get paginated list of applications with optional filters.

    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Items per page
        search: Search by student name or email
        app_status: Filter by application status
        company_id: Filter by company
        department: Filter by student department (branch)

    Returns:
        (list of application dicts, total count)
    """
    query = (
        db.query(Application)
        .join(Student, Application.student_id == Student.id)
        .join(User, Student.user_id == User.id)
        .join(Job, Application.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
    )

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                Student.roll_number.ilike(search_term),
                Job.title.ilike(search_term),
            )
        )

    if app_status:
        query = query.filter(Application.status == app_status)

    if company_id:
        query = query.filter(Company.id == company_id)

    if department:
        query = query.filter(Student.branch == department)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    applications = query.offset(offset).limit(page_size).all()

    # Format results
    result = []
    for app in applications:
        status_val = app.status.value if hasattr(app.status, "value") else str(app.status)
        result.append(
            {
                "id": app.id,
                "student_name": app.student.user.full_name if (app.student and app.student.user) else "Unknown",
                "student_email": app.student.user.email if (app.student and app.student.user) else "Unknown",
                "student_department": app.student.branch if app.student else "Unknown",
                "job_title": app.job.title if app.job else "Unknown",
                "company_name": app.job.company.name if (app.job and app.job.company) else "Unknown",
                "status": status_val,
                "created_at": app.applied_at.isoformat() if app.applied_at else None,
            }
        )

    return result, total


# ---------------------------------------------------------------------------
# Interview Queries
# ---------------------------------------------------------------------------

def get_interviews_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
    result_status: Optional[str] = None,
    company_id: Optional[int] = None,
    department: Optional[str] = None,
) -> tuple[list, int]:
    """
    Get paginated list of interviews with optional filters.

    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Items per page
        search: Search by student name or email
        result_status: Filter by interview result (PENDING, PASSED, FAILED, NO_SHOW)
        company_id: Filter by company
        department: Filter by student department

    Returns:
        (list of interview dicts, total count)
    """
    query = (
        db.query(Interview)
        .join(Application, Interview.application_id == Application.id)
        .join(Student, Application.student_id == Student.id)
        .join(User, Student.user_id == User.id)
        .join(Job, Application.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
    )

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                Job.title.ilike(search_term),
            )
        )

    if result_status:
        query = query.filter(Interview.result == result_status)

    if company_id:
        query = query.filter(Company.id == company_id)

    if department:
        query = query.filter(Student.branch == department)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    interviews = query.offset(offset).limit(page_size).all()

    # Format results
    result = []
    for interview in interviews:
        res_val = interview.result.value if hasattr(interview.result, "value") else str(interview.result)
        round_val = interview.round.value if hasattr(interview.round, "value") else str(interview.round)
        student_name = "Unknown"
        student_email = "Unknown"
        job_title = "Unknown"
        company_name = "Unknown"

        if interview.application:
            if interview.application.student and interview.application.student.user:
                student_name = interview.application.student.user.full_name
                student_email = interview.application.student.user.email
            if interview.application.job:
                job_title = interview.application.job.title
                if interview.application.job.company:
                    company_name = interview.application.job.company.name

        result.append(
            {
                "id": interview.id,
                "student_name": student_name,
                "student_email": student_email,
                "job_title": job_title,
                "company_name": company_name,
                "scheduled_at": interview.scheduled_at.isoformat() if interview.scheduled_at else None,
                "result": res_val,
                "round": round_val,
                "created_at": interview.created_at.isoformat() if interview.created_at else None,
            }
        )

    return result, total


# ---------------------------------------------------------------------------
# Dashboard Aggregate Counts
# ---------------------------------------------------------------------------

def get_dashboard_counts(db: Session) -> dict:
    """
    Get aggregate counts for the placement officer dashboard.

    Returns:
        {
            "total_students": int,
            "total_companies": int,
            "active_recruitment_drives": int,
            "total_job_postings": int,
            "total_applications": int,
            "applications_shortlisted": int,
            "total_interviews": int,
            "applications_selected": int,
            "applications_rejected": int,
            "placement_percentage": float,
        }
    """
    total_students = db.query(func.count(Student.id)).scalar() or 0
    total_companies = db.query(func.count(Company.id)).scalar() or 0
    active_drives = (
        db.query(func.count(Job.id))
        .filter(Job.status == JobStatus.OPEN)
        .scalar()
        or 0
    )
    total_jobs = db.query(func.count(Job.id)).scalar() or 0
    total_apps = db.query(func.count(Application.id)).scalar() or 0
    apps_shortlisted = (
        db.query(func.count(Application.id))
        .filter(Application.status == ApplicationStatus.SHORTLISTED)
        .scalar()
        or 0
    )
    total_interviews = db.query(func.count(Interview.id)).scalar() or 0
    apps_selected = (
        db.query(func.count(Application.id))
        .filter(Application.status == ApplicationStatus.SELECTED)
        .scalar()
        or 0
    )
    apps_rejected = (
        db.query(func.count(Application.id))
        .filter(Application.status == ApplicationStatus.REJECTED)
        .scalar()
        or 0
    )

    placement_percentage = (
        ((apps_selected / total_apps) * 100) if total_apps > 0 else 0
    )

    return {
        "total_students": total_students,
        "total_companies": total_companies,
        "active_recruitment_drives": active_drives,
        "total_job_postings": total_jobs,
        "total_applications": total_apps,
        "applications_shortlisted": apps_shortlisted,
        "total_interviews": total_interviews,
        "applications_selected": apps_selected,
        "applications_rejected": apps_rejected,
        "placement_percentage": round(placement_percentage, 2),
    }


# ---------------------------------------------------------------------------
# Statistics for Charting
# ---------------------------------------------------------------------------

def get_statistics(db: Session) -> dict:
    """
    Get statistics data for dashboard charts.
    """
    # Applications by company
    apps_by_company = (
        db.query(Company.name, func.count(Application.id).label("count"))
        .select_from(Company)
        .join(Job, Company.id == Job.company_id)
        .join(Application, Job.id == Application.job_id)
        .group_by(Company.id, Company.name)
        .all()
    )
    apps_by_company_list = [
        {"company": row[0], "count": row[1]} for row in apps_by_company
    ]

    # Selections by company
    selections_by_company = (
        db.query(Company.name, func.count(Application.id).label("count"))
        .select_from(Company)
        .join(Job, Company.id == Job.company_id)
        .join(Application, Job.id == Application.job_id)
        .filter(Application.status == ApplicationStatus.SELECTED)
        .group_by(Company.id, Company.name)
        .all()
    )
    selections_by_company_list = [
        {"company": row[0], "count": row[1]} for row in selections_by_company
    ]

    # Applications by department
    apps_by_dept = (
        db.query(Student.branch, func.count(Application.id).label("count"))
        .select_from(Student)
        .join(Application, Student.id == Application.student_id)
        .group_by(Student.branch)
        .all()
    )
    apps_by_dept_list = [
        {"department": row[0], "count": row[1]} for row in apps_by_dept
    ]

    # Selection rate by department
    selection_rate_by_dept = []
    for dept, app_count in apps_by_dept:
        selected_count = (
            db.query(func.count(Application.id))
            .select_from(Student)
            .join(Application, Student.id == Application.student_id)
            .filter(
                Student.branch == dept,
                Application.status == ApplicationStatus.SELECTED,
            )
            .scalar()
            or 0
        )
        rate = ((selected_count / app_count) * 100) if app_count > 0 else 0
        selection_rate_by_dept.append(
            {"department": dept, "rate": round(rate, 2)}
        )

    # Recruitment drive status
    job_statuses = (
        db.query(Job.status, func.count(Job.id).label("count"))
        .group_by(Job.status)
        .all()
    )
    drive_status_list = []
    for row in job_statuses:
        st_val = row[0].value if hasattr(row[0], "value") else str(row[0])
        drive_status_list.append({"status": st_val, "count": row[1]})

    # Application funnel
    total_apps = db.query(func.count(Application.id)).scalar() or 0
    eligible = (
        db.query(func.count(Application.id))
        .filter(Application.status.in_([
            ApplicationStatus.ELIGIBILITY_VERIFIED,
            ApplicationStatus.SHORTLISTED,
            ApplicationStatus.INTERVIEW_SCHEDULED,
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.SELECTED,
            ApplicationStatus.REJECTED,
        ]))
        .scalar()
        or 0
    )
    shortlisted = (
        db.query(func.count(Application.id))
        .filter(Application.status.in_([
            ApplicationStatus.SHORTLISTED,
            ApplicationStatus.INTERVIEW_SCHEDULED,
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.SELECTED,
            ApplicationStatus.REJECTED,
        ]))
        .scalar()
        or 0
    )
    interviewed = (
        db.query(func.count(Application.id))
        .filter(Application.status.in_([
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.SELECTED,
            ApplicationStatus.REJECTED,
        ]))
        .scalar()
        or 0
    )
    selected = (
        db.query(func.count(Application.id))
        .filter(Application.status == ApplicationStatus.SELECTED)
        .scalar()
        or 0
    )

    funnel = [
        {"stage": "Applications", "count": total_apps},
        {"stage": "Eligible", "count": eligible},
        {"stage": "Shortlisted", "count": shortlisted},
        {"stage": "Interviewed", "count": interviewed},
        {"stage": "Selected", "count": selected},
    ]

    return {
        "applications_by_company": apps_by_company_list,
        "selections_by_company": selections_by_company_list,
        "applications_by_department": apps_by_dept_list,
        "selection_rate_by_department": selection_rate_by_dept,
        "recruitment_drive_status": drive_status_list,
        "application_funnel": funnel,
    }
