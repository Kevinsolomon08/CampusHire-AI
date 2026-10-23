# app/api/applications.py
# Application workflow and interview management endpoints.

from __future__ import annotations

import csv
import io
import logging
import math
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import and_, case, or_
from sqlalchemy.orm import Session, joinedload

from app.ai.scoring_engine import (
    calculate_education_relevance,
    calculate_experience_relevance,
    calculate_skill_match,
    score_and_rank_job_applicants,
)
from app.api.deps import AppError, get_current_user, require_role
from app.database.connection import get_db
from app.models.models import (
    Application,
    ApplicationStatus,
    ApplicationStatusHistory,
    Interview,
    InterviewResult,
    Job,
    JobStatus,
    Notification,
    Recruiter,
    Resume,
    Student,
    User,
    UserRole,
)
from app.schemas.application import (
    ApplicantListItem,
    ApplicationCreate,
    ApplicationDetailResponse,
    ApplicationListItem,
    ApplicationMatchAnalysisResponse,
    ApplicationStatusHistoryItem,
    ApplicationStatusUpdateRequest,
    InterviewCreate,
    InterviewDetail,
    InterviewUpdate,
    JobBriefForApplication,
    PaginatedApplicantsResponse,
    PaginatedInterviewsResponse,
)
from app.schemas.response import APIResponse
from app.services.application_service import (
    build_status_history_entry,
    validate_status_transition,
)
from app.services.eligibility_service import check_eligibility
from app.services.notification_service import create_notification

router = APIRouter()
logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
) -> Notification:
    """Create a notification row (delegates to notification_service)."""
    return create_notification(db, user_id, title, message)


def _format_application_detail(
    app: Application, db: Session
) -> ApplicationDetailResponse:
    """Format an Application ORM object into the response schema."""
    job_brief = JobBriefForApplication(
        id=app.job.id,
        title=app.job.title,
        company_name=app.job.company.name if app.job.company else "Unknown",
        package_lpa=app.job.package_lpa,
        location=app.job.location,
        deadline=app.job.deadline,
    )

    status_history_items = []
    for sh in app.status_history:
        status_history_items.append(
            ApplicationStatusHistoryItem(
                id=sh.id,
                old_status=sh.old_status.value if sh.old_status else None,
                new_status=sh.new_status.value if sh.new_status else str(sh.new_status),
                changed_by_name=sh.changed_by_user.full_name if sh.changed_by_user else None,
                changed_by_role=sh.changed_by_user.role.value if sh.changed_by_user else None,
                remarks=sh.remarks,
                changed_at=sh.changed_at,
            )
        )

    return ApplicationDetailResponse(
        id=app.id,
        student_id=app.student_id,
        job_id=app.job_id,
        resume_id=app.resume_id,
        status=app.status.value if hasattr(app.status, "value") else str(app.status),
        applied_at=app.applied_at,
        updated_at=app.updated_at,
        ai_score=app.ai_score,
        semantic_score=app.semantic_score,
        skill_score=app.skill_score,
        experience_score=app.experience_score,
        education_score=app.education_score,
        rank=app.rank,
        job=job_brief,
        status_history=status_history_items,
    )


# ---------------------------------------------------------------------------
# 1. POST /applications/{job_id}/apply — Student Apply
# ---------------------------------------------------------------------------

@router.post(
    "/{job_id}/apply",
    response_model=APIResponse[ApplicationDetailResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Apply for a job posting",
)
def apply_for_job(
    job_id: int,
    payload: ApplicationCreate,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    # Validate job exists and is OPEN
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

    if job.status != JobStatus.OPEN:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="This job posting is not currently open for applications.",
            error_code="JOB_NOT_OPEN",
        )

    # Check deadline
    now = datetime.now(timezone.utc)
    deadline_utc = (
        job.deadline
        if job.deadline and job.deadline.tzinfo
        else (job.deadline.replace(tzinfo=timezone.utc) if job.deadline else None)
    )
    if deadline_utc and deadline_utc <= now:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="This application deadline has passed.",
            error_code="DEADLINE_PASSED",
        )

    # Get student
    student = (
        db.query(Student)
        .filter(Student.user_id == current_user.id)
        .first()
    )
    if not student:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Student profile not found.",
            error_code="STUDENT_NOT_FOUND",
        )

    # Check eligibility
    eligibility_result = check_eligibility(student, job)
    if not eligibility_result.get("eligible", False):
        reasons_str = "; ".join(eligibility_result.get("reasons", []))
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"You are not eligible for this job because: {reasons_str}",
            error_code="NOT_ELIGIBLE",
        )

    # Check duplicate application
    existing_app = (
        db.query(Application)
        .filter(
            and_(
                Application.student_id == student.id,
                Application.job_id == job_id,
            )
        )
        .first()
    )
    if existing_app:
        logger.warning(f"Duplicate application attempt: student_id={student.id}, job_id={job_id}")
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            message="You have already applied for this job.",
            error_code="DUPLICATE_APPLICATION",
        )

    # Determine resume_id
    resume_id = payload.resume_id
    if not resume_id:
        # Use primary resume
        primary_resume = (
            db.query(Resume)
            .filter(
                and_(
                    Resume.student_id == student.id,
                    Resume.is_primary == True,
                )
            )
            .first()
        )
        if primary_resume:
            resume_id = primary_resume.id

    # Create Application with status APPLIED
    new_app = Application(
        student_id=student.id,
        job_id=job_id,
        resume_id=resume_id,
        status=ApplicationStatus.APPLIED,
    )
    db.add(new_app)
    db.flush()
    
    logger.info(f"Application created: student_id={student.id}, job_id={job_id}, application_id={new_app.id}")

    # Create first status history: APPLIED (no old_status)
    entry_1 = build_status_history_entry(
        application_id=new_app.id,
        old_status=None,
        new_status="APPLIED",
        changed_by_user_id=current_user.id,
        remarks="Student application submitted",
    )
    history_1 = ApplicationStatusHistory(
        application_id=new_app.id,
        old_status=None,
        new_status=ApplicationStatus.APPLIED,
        changed_by=current_user.id,
        remarks=entry_1["remarks"],
        changed_at=entry_1["changed_at"],
    )
    db.add(history_1)
    db.flush()

    # Immediately transition to ELIGIBILITY_VERIFIED
    transition_result = validate_status_transition(
        current_status="APPLIED",
        new_status="ELIGIBILITY_VERIFIED",
        actor_role="SYSTEM",  # System auto-transition
    )
    if transition_result["allowed"]:
        new_app.status = ApplicationStatus.ELIGIBILITY_VERIFIED
        new_app.updated_at = datetime.now(timezone.utc)
        db.add(new_app)
        db.flush()

        entry_2 = build_status_history_entry(
            application_id=new_app.id,
            old_status="APPLIED",
            new_status="ELIGIBILITY_VERIFIED",
            changed_by_user_id=current_user.id,
            remarks="Automatic eligibility verification on application submission",
        )
        history_2 = ApplicationStatusHistory(
            application_id=new_app.id,
            old_status=ApplicationStatus.APPLIED,
            new_status=ApplicationStatus.ELIGIBILITY_VERIFIED,
            changed_by=current_user.id,
            remarks=entry_2["remarks"],
            changed_at=entry_2["changed_at"],
        )
        db.add(history_2)

        # Notify student
        _create_notification(
            db,
            user_id=current_user.id,
            title="Application Verified",
            message=f"Your application for {job.title} at {job.company.name} has been verified and is now under review.",
        )

    db.commit()
    db.refresh(new_app)

    return APIResponse(
        success=True,
        data=_format_application_detail(new_app, db),
        message="Application submitted successfully.",
    )


# ---------------------------------------------------------------------------
# 2. GET /applications — Student's Applications List
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=APIResponse[list[ApplicationListItem]],
    summary="Get student's applications",
)
def get_student_applications(
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        return APIResponse(
            success=True,
            data=[],
            message="No applications found.",
        )

    applications = (
        db.query(Application)
        .options(
            joinedload(Application.job).joinedload(Job.company),
        )
        .filter(Application.student_id == student.id)
        .order_by(Application.applied_at.desc())
        .all()
    )

    items = []
    for app in applications:
        job_brief = JobBriefForApplication(
            id=app.job.id,
            title=app.job.title,
            company_name=app.job.company.name if app.job.company else "Unknown",
            package_lpa=app.job.package_lpa,
            location=app.job.location,
            deadline=app.job.deadline,
        )
        items.append(
            ApplicationListItem(
                id=app.id,
                job=job_brief,
                status=app.status.value if hasattr(app.status, "value") else str(app.status),
                applied_at=app.applied_at,
                updated_at=app.updated_at,
                ai_score=app.ai_score,
                rank=app.rank,
            )
        )

    return APIResponse(
        success=True,
        data=items,
        message="Applications retrieved successfully.",
    )


# ---------------------------------------------------------------------------
# 3. GET /applications/{id} — Application Detail with Timeline
# ---------------------------------------------------------------------------

@router.get(
    "/{id}",
    response_model=APIResponse[ApplicationDetailResponse],
    summary="Get application detail with status history timeline",
)
def get_application_detail(
    id: int,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    app = (
        db.query(Application)
        .options(
            joinedload(Application.job).joinedload(Job.company),
            joinedload(Application.status_history).joinedload(ApplicationStatusHistory.changed_by_user),
            joinedload(Application.student),
        )
        .filter(Application.id == id)
        .first()
    )

    if not app:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Application not found.",
            error_code="APPLICATION_NOT_FOUND",
        )

    # Scoped: student can only view their own applications
    if app.student_id != current_user.id:
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You are not authorized to view this application.",
            error_code="FORBIDDEN",
        )

    return APIResponse(
        success=True,
        data=_format_application_detail(app, db),
        message="Application detail retrieved successfully.",
    )


# ---------------------------------------------------------------------------
# 4. GET /jobs/{job_id}/applications — Recruiter's Applicants List
# ---------------------------------------------------------------------------

@router.get(
    "/jobs/{job_id}/applications",
    response_model=APIResponse[PaginatedApplicantsResponse],
    summary="Get paginated applicants for a job (recruiter view)",
)
def get_job_applicants(
    job_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    branch: Optional[str] = Query(None, description="Filter by branch"),
    min_cgpa: Optional[float] = Query(None, description="Minimum CGPA"),
    max_backlogs: Optional[int] = Query(None, description="Maximum backlogs"),
    batch: Optional[int] = Query(None, description="Graduating batch"),
    status: Optional[str] = Query(None, description="Filter by application status"),
    min_ai_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum AI score"),
    sort_by: str = Query("rank", pattern="^(rank|applied_at|cgpa|name)$"),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
    db: Session = Depends(get_db),
):
    # Verify recruiter owns the job
    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
    if not recruiter:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Recruiter profile not found.",
            error_code="RECRUITER_NOT_FOUND",
        )

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Job posting not found.",
            error_code="JOB_NOT_FOUND",
        )

    if job.company_id != recruiter.company_id:
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You are not authorized to view applicants for this job.",
            error_code="FORBIDDEN",
        )

    # Automatically score and rank applicants if any eligible applicant has not been scored yet
    unscored_count = (
        db.query(Application)
        .filter(
            Application.job_id == job_id,
            Application.ai_score.is_(None),
        )
        .count()
    )
    if unscored_count > 0:
        try:
            score_and_rank_job_applicants(job_id=job_id, db_session=db)
        except Exception as exc:
            logger.warning("Automatic scoring for job %s failed: %s", job_id, exc)

    # Build query for applications with filters
    query = (
        db.query(Application)
        .options(
            joinedload(Application.student).joinedload(Student.user),
            joinedload(Application.job),
        )
        .filter(Application.job_id == job_id)
    )

    if status:
        query = query.filter(Application.status == status)

    if branch:
        query = query.join(Student).filter(Student.branch == branch)

    if min_cgpa is not None:
        query = query.join(Student).filter(Student.cgpa >= min_cgpa)

    if max_backlogs is not None:
        query = query.join(Student).filter(Student.backlog_count <= max_backlogs)

    if batch:
        query = query.join(Student).filter(Student.year == batch)

    if min_ai_score is not None:
        query = query.filter(Application.ai_score >= min_ai_score)

    # Sort
    if sort_by == "rank":
        # Rank 1 first; null ranks last, then tie-break by applied_at desc
        query = query.order_by(
            case((Application.rank.is_(None), 1), else_=0),
            Application.rank.asc(),
            Application.applied_at.desc(),
        )
    elif sort_by == "cgpa":
        query = query.join(Student).order_by(Student.cgpa.desc())
    elif sort_by == "name":
        query = query.join(Student).join(User).order_by(User.full_name.asc())
    else:  # applied_at
        query = query.order_by(Application.applied_at.desc())

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    applications = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for app in applications:
        items.append(
            ApplicantListItem(
                application_id=app.id,
                student_id=app.student_id,
                student_name=app.student.user.full_name if app.student and app.student.user else "Unknown",
                student_email=app.student.user.email if app.student and app.student.user else "",
                roll_number=app.student.roll_number if app.student else "",
                branch=app.student.branch if app.student else "",
                cgpa=app.student.cgpa if app.student else None,
                backlog_count=app.student.backlog_count if app.student else 0,
                status=app.status.value if hasattr(app.status, "value") else str(app.status),
                applied_at=app.applied_at,
                ai_score=app.ai_score,
                semantic_score=app.semantic_score,
                skill_score=app.skill_score,
                experience_score=app.experience_score,
                education_score=app.education_score,
                rank=app.rank,
            )
        )

    return APIResponse(
        success=True,
        data=PaginatedApplicantsResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
        message="Applicants retrieved successfully.",
    )


@router.post(
    "/jobs/{job_id}/recalculate-scores",
    response_model=APIResponse[dict],
    summary="Trigger recalculation of AI scores and ranking for a job",
)
def recalculate_job_scores(
    job_id: int,
    current_user: User = Depends(require_role(UserRole.RECRUITER, UserRole.PLACEMENT_OFFICER)),
    db: Session = Depends(get_db),
):
    # Verify recruiter owns the job if recruiter
    if current_user.role == UserRole.RECRUITER:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not recruiter:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Recruiter profile not found.",
                error_code="RECRUITER_NOT_FOUND",
            )
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Job posting not found.",
                error_code="JOB_NOT_FOUND",
            )
        if job.company_id != recruiter.company_id:
            raise AppError(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You are not authorized to recalculate scores for this job.",
                error_code="FORBIDDEN",
            )
    else:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Job posting not found.",
                error_code="JOB_NOT_FOUND",
            )

    ranked = score_and_rank_job_applicants(job_id=job_id, db_session=db)
    return APIResponse(
        success=True,
        data={"scored_count": len(ranked), "job_id": job_id},
        message="Applicant scores and rankings recalculated successfully.",
    )


@router.get(
    "/jobs/{job_id}/applications/export",
    summary="Export top-k or all eligible applicants for a job as CSV",
)
@router.get(
    "/jobs/{job_id}/export",
    summary="Export top-k or all eligible applicants for a job as CSV (short alias)",
)
def export_job_applicants_csv(
    job_id: int,
    top_k: Optional[int] = Query(None, ge=1, description="Number of top candidates to export"),
    format: str = Query("csv", pattern="^csv$", description="Export format (csv)"),
    current_user: User = Depends(require_role(UserRole.RECRUITER, UserRole.PLACEMENT_OFFICER)),
    db: Session = Depends(get_db),
):
    # Verify recruiter owns the job if recruiter
    if current_user.role == UserRole.RECRUITER:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not recruiter:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Recruiter profile not found.",
                error_code="RECRUITER_NOT_FOUND",
            )
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Job posting not found.",
                error_code="JOB_NOT_FOUND",
            )
        if job.company_id != recruiter.company_id:
            raise AppError(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You are not authorized to export applicants for this job.",
                error_code="FORBIDDEN",
            )
    else:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Job posting not found.",
                error_code="JOB_NOT_FOUND",
            )

    # Automatically score and rank applicants if any eligible applicant has not been scored yet
    unscored_count = (
        db.query(Application)
        .filter(
            Application.job_id == job_id,
            Application.ai_score.is_(None),
        )
        .count()
    )
    if unscored_count > 0:
        try:
            score_and_rank_job_applicants(job_id=job_id, db_session=db)
        except Exception as exc:
            logger.warning("Automatic scoring for export on job %s failed: %s", job_id, exc)

    # Query applicants sorted by rank ascending (best first), nulls last, then applied_at desc
    query = (
        db.query(Application)
        .options(
            joinedload(Application.student).joinedload(Student.user),
            joinedload(Application.resume),
            joinedload(Application.job),
        )
        .filter(Application.job_id == job_id)
        .order_by(
            case((Application.rank.is_(None), 1), else_=0),
            Application.rank.asc(),
            Application.applied_at.desc(),
        )
    )

    if top_k is not None:
        applications = query.limit(top_k).all()
    else:
        applications = query.all()

    # If the job has zero eligible/scored applicants yet, return a clear error
    if not applications:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="No scored applicants available to export yet.",
            error_code="NO_APPLICANTS_TO_EXPORT",
        )

    # Prepare CSV output
    output = io.StringIO()
    writer = csv.writer(output)

    # CSV headers in exact required order
    writer.writerow([
        "Rank",
        "Candidate Name",
        "Email",
        "Phone",
        "Department",
        "Batch",
        "CGPA",
        "Backlogs",
        "AI Score",
        "Semantic Similarity",
        "Skill Match %",
        "Matching Skills",
        "Missing Required Skills",
        "Application Status",
        "Applied Date",
    ])

    req_skills = job.required_skills if isinstance(job.required_skills, list) else []
    pref_skills = job.preferred_skills if isinstance(job.preferred_skills, list) else []

    for app in applications:
        student = app.student
        user = student.user if student else None
        resume = app.resume
        parsed_data = (resume.parsed_data if resume and isinstance(resume.parsed_data, dict) else {}) or {}

        # Candidate skills for matching/missing lists
        cand_skills = parsed_data.get("skills")
        if not cand_skills and student and student.skills:
            cand_skills = student.skills if isinstance(student.skills, list) else []
        cand_skills = cand_skills or []

        skill_res = calculate_skill_match(cand_skills, req_skills, pref_skills)
        matching_skills_str = "; ".join(skill_res["matching_skills"])
        missing_skills_str = "; ".join(skill_res["missing_required_skills"])

        # Candidate phone
        phone = ""
        if parsed_data.get("personal_info") and isinstance(parsed_data["personal_info"], dict):
            phone = parsed_data["personal_info"].get("phone") or ""
        if not phone and user and hasattr(user, "phone"):
            phone = getattr(user, "phone") or ""

        writer.writerow([
            str(app.rank) if app.rank is not None else "",
            user.full_name if user else "Unknown",
            user.email if user else "",
            phone,
            student.branch if student else "",
            str(student.year) if student and student.year else "",
            f"{student.cgpa:.2f}" if student and student.cgpa is not None else "",
            str(student.backlog_count) if student and student.backlog_count is not None else "0",
            f"{app.ai_score:.1f}%" if app.ai_score is not None else "",
            f"{app.semantic_score:.1f}%" if app.semantic_score is not None else "",
            f"{app.skill_score:.1f}%" if app.skill_score is not None else (f"{skill_res['skill_match_percentage']:.1f}%" if skill_res else ""),
            matching_skills_str,
            missing_skills_str,
            app.status.value if hasattr(app.status, "value") else str(app.status),
            app.applied_at.strftime("%Y-%m-%d %H:%M:%S") if app.applied_at else "",
        ])

    csv_content = output.getvalue()

    # Sanitize job title for safe filename
    sanitized_title = re.sub(r"[^a-zA-Z0-9_-]", "_", job.title.strip().lower())
    top_str = str(top_k) if top_k else "all"
    filename = f"{sanitized_title}_top_{top_str}_candidates.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/csv; charset=utf-8",
        },
    )


@router.get(
    "/{id}/match-analysis",
    response_model=APIResponse[ApplicationMatchAnalysisResponse],
    summary="Get detailed AI match analysis breakdown for an applicant",
)
def get_application_match_analysis(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = (
        db.query(Application)
        .options(
            joinedload(Application.student).joinedload(Student.user),
            joinedload(Application.job).joinedload(Job.company),
            joinedload(Application.resume),
        )
        .filter(Application.id == id)
        .first()
    )
    if not app:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Application not found.",
            error_code="APPLICATION_NOT_FOUND",
        )

    # Authorization
    if current_user.role == UserRole.STUDENT:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student or app.student_id != student.id:
            raise AppError(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You are not authorized to view this analysis.",
                error_code="FORBIDDEN",
            )
    elif current_user.role == UserRole.RECRUITER:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not recruiter or app.job.company_id != recruiter.company_id:
            raise AppError(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You are not authorized to view this analysis.",
                error_code="FORBIDDEN",
            )

    # Check eligibility
    eligibility_result = check_eligibility(app.student, app.job)

    # Candidate skills & breakdown
    resume = app.resume
    student = app.student
    job = app.job

    parsed_data = (resume.parsed_data if resume and isinstance(resume.parsed_data, dict) else {}) or {}

    cand_skills = parsed_data.get("skills")
    if not cand_skills and student and student.skills:
        cand_skills = student.skills if isinstance(student.skills, list) else []
    cand_skills = cand_skills or []

    req_skills = job.required_skills if isinstance(job.required_skills, list) else []
    pref_skills = job.preferred_skills if isinstance(job.preferred_skills, list) else []
    skill_res = calculate_skill_match(cand_skills, req_skills, pref_skills)

    scoring_available = app.ai_score is not None

    return APIResponse(
        success=True,
        data=ApplicationMatchAnalysisResponse(
            application_id=app.id,
            student_id=app.student_id,
            candidate_name=app.student.user.full_name if app.student and app.student.user else "Unknown",
            candidate_email=app.student.user.email if app.student and app.student.user else "",
            roll_number=app.student.roll_number if app.student else "",
            branch=app.student.branch if app.student else "",
            cgpa=app.student.cgpa if app.student else None,
            job_id=job.id,
            job_title=job.title,
            overall_score=app.ai_score,
            semantic_similarity=app.semantic_score,
            skill_match_percentage=app.skill_score if app.skill_score is not None else skill_res["skill_match_percentage"],
            experience_relevance=app.experience_score,
            education_relevance=app.education_score,
            matching_skills=skill_res["matching_skills"],
            missing_required_skills=skill_res["missing_required_skills"],
            matching_preferred_skills=skill_res["matching_preferred_skills"],
            rank=app.rank,
            eligibility=eligibility_result,
            status=app.status.value if hasattr(app.status, "value") else str(app.status),
            scoring_available=scoring_available,
        ),
        message="Match analysis retrieved successfully.",
    )


# ---------------------------------------------------------------------------
# 5. PATCH /applications/{id}/status — Update Application Status
# ---------------------------------------------------------------------------

@router.patch(
    "/{id}/status",
    response_model=APIResponse[ApplicationDetailResponse],
    summary="Update application status (recruiter/placement officer)",
)
def update_application_status(
    id: int,
    payload: ApplicationStatusUpdateRequest,
    current_user: User = Depends(require_role(UserRole.RECRUITER, UserRole.PLACEMENT_OFFICER)),
    db: Session = Depends(get_db),
):
    app = (
        db.query(Application)
        .options(
            joinedload(Application.job).joinedload(Job.company),
            joinedload(Application.student).joinedload(Student.user),
            joinedload(Application.status_history).joinedload(ApplicationStatusHistory.changed_by_user),
        )
        .filter(Application.id == id)
        .first()
    )

    if not app:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Application not found.",
            error_code="APPLICATION_NOT_FOUND",
        )

    # Verify ownership if recruiter
    if current_user.role == UserRole.RECRUITER:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not recruiter or app.job.company_id != recruiter.company_id:
            raise AppError(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You are not authorized to update this application.",
                error_code="FORBIDDEN",
            )

    # Validate transition
    actor_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    transition = validate_status_transition(
        current_status=app.status.value if hasattr(app.status, "value") else str(app.status),
        new_status=payload.new_status.upper(),
        actor_role=actor_role,
    )

    if not transition["allowed"]:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=transition.get("reason", "This transition is not permitted."),
            error_code="INVALID_TRANSITION",
        )

    old_status_str = app.status.value if hasattr(app.status, "value") else str(app.status)
    new_status_str = payload.new_status.upper()

    # Update application
    app.status = ApplicationStatus[new_status_str]
    app.updated_at = datetime.now(timezone.utc)
    db.add(app)
    db.flush()
    
    logger.info(f"Application status updated: application_id={app.id}, student_id={app.student_id}, job_id={app.job_id}, old_status={old_status_str}, new_status={new_status_str}, changed_by={current_user.email}")

    # Write status history
    entry = build_status_history_entry(
        application_id=app.id,
        old_status=old_status_str,
        new_status=new_status_str,
        changed_by_user_id=current_user.id,
        remarks=payload.remarks or (transition.get("reason") if transition.get("reason") else None),
    )
    history = ApplicationStatusHistory(
        application_id=app.id,
        old_status=ApplicationStatus[old_status_str] if old_status_str != "None" else None,
        new_status=ApplicationStatus[new_status_str],
        changed_by=current_user.id,
        remarks=entry["remarks"],
        changed_at=entry["changed_at"],
    )
    db.add(history)

    # Notify student
    status_messages = {
        "SHORTLISTED": f"Great news! You have been shortlisted for {app.job.title} at {app.job.company.name}.",
        "INTERVIEW_SCHEDULED": f"Your interview for {app.job.title} has been scheduled.",
        "SELECTED": f"Congratulations! You have been selected for {app.job.title} at {app.job.company.name}.",
        "REJECTED": f"Unfortunately, you were not selected for {app.job.title}. Thank you for applying.",
    }
    if new_status_str in status_messages:
        _create_notification(
            db,
            user_id=app.student.user_id,
            title=f"Application Status Update: {new_status_str.replace('_', ' ')}",
            message=status_messages[new_status_str],
        )

    db.commit()
    db.refresh(app)

    return APIResponse(
        success=True,
        data=_format_application_detail(app, db),
        message=f"Application status updated to {new_status_str}.",
    )


# ---------------------------------------------------------------------------
# 6. POST /applications/{id}/interviews — Schedule Interview
# ---------------------------------------------------------------------------

@router.post(
    "/{id}/interviews",
    response_model=APIResponse[InterviewDetail],
    status_code=status.HTTP_201_CREATED,
    summary="Schedule an interview for an application",
)
def schedule_interview(
    id: int,
    payload: InterviewCreate,
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
    db: Session = Depends(get_db),
):
    app = (
        db.query(Application)
        .options(
            joinedload(Application.job).joinedload(Job.company),
            joinedload(Application.student).joinedload(Student.user),
        )
        .filter(Application.id == id)
        .first()
    )

    if not app:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Application not found.",
            error_code="APPLICATION_NOT_FOUND",
        )

    # Verify ownership
    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
    if not recruiter or app.job.company_id != recruiter.company_id:
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You are not authorized to schedule interviews for this application.",
            error_code="FORBIDDEN",
        )

    # Transition application to INTERVIEW_SCHEDULED
    current_status_str = app.status.value if hasattr(app.status, "value") else str(app.status)
    transition = validate_status_transition(
        current_status=current_status_str,
        new_status="INTERVIEW_SCHEDULED",
        actor_role="RECRUITER",
    )

    if not transition["allowed"]:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=transition.get("reason", "Cannot schedule interview in current application status."),
            error_code="INVALID_TRANSITION",
        )

    # Create interview
    new_interview = Interview(
        application_id=app.id,
        scheduled_at=payload.scheduled_at,
        mode=payload.mode.upper(),
        round=payload.round.upper() if payload.round else "TECHNICAL",
        interviewer=payload.interviewer,
        location_or_link=payload.location_or_link,
        notes=payload.notes,
        result="PENDING",
    )
    db.add(new_interview)
    db.flush()

    # Update application status
    app.status = ApplicationStatus.INTERVIEW_SCHEDULED
    app.updated_at = datetime.now(timezone.utc)
    db.add(app)
    db.flush()

    # Write status history
    entry = build_status_history_entry(
        application_id=app.id,
        old_status=current_status_str,
        new_status="INTERVIEW_SCHEDULED",
        changed_by_user_id=current_user.id,
        remarks="Interview scheduled",
    )
    history = ApplicationStatusHistory(
        application_id=app.id,
        old_status=ApplicationStatus[current_status_str] if current_status_str != "None" else None,
        new_status=ApplicationStatus.INTERVIEW_SCHEDULED,
        changed_by=current_user.id,
        remarks=entry["remarks"],
        changed_at=entry["changed_at"],
    )
    db.add(history)

    # Notify student
    scheduled_date = payload.scheduled_at.strftime("%B %d, %Y at %I:%M %p")
    _create_notification(
        db,
        user_id=app.student.user_id,
        title="Interview Scheduled",
        message=f"Your {payload.round.upper()} interview for {app.job.title} is scheduled for {scheduled_date}.",
    )

    db.commit()
    db.refresh(new_interview)

    interview_detail = InterviewDetail(
        id=new_interview.id,
        application_id=new_interview.application_id,
        scheduled_at=new_interview.scheduled_at,
        mode=new_interview.mode,
        round=new_interview.round,
        interviewer=new_interview.interviewer,
        location_or_link=new_interview.location_or_link,
        result=new_interview.result,
        notes=new_interview.notes,
        created_at=new_interview.created_at,
        updated_at=new_interview.updated_at,
        student_name=app.student.user.full_name,
        job_title=app.job.title,
        company_name=app.job.company.name if app.job.company else "Unknown",
    )

    return APIResponse(
        success=True,
        data=interview_detail,
        message="Interview scheduled successfully.",
    )


# ---------------------------------------------------------------------------
# 7. PUT /interviews/{id} — Update Interview Details/Result
# ---------------------------------------------------------------------------

@router.put(
    "/interviews/{id}",
    response_model=APIResponse[InterviewDetail],
    summary="Update interview details or result",
)
def update_interview(
    id: int,
    payload: InterviewUpdate,
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
    db: Session = Depends(get_db),
):
    interview = (
        db.query(Interview)
        .options(
            joinedload(Interview.application).joinedload(Application.job).joinedload(Job.company),
            joinedload(Interview.application).joinedload(Application.student).joinedload(Student.user),
        )
        .filter(Interview.id == id)
        .first()
    )

    if not interview:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Interview not found.",
            error_code="INTERVIEW_NOT_FOUND",
        )

    # Verify ownership
    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
    if not recruiter or interview.application.job.company_id != recruiter.company_id:
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You are not authorized to update this interview.",
            error_code="FORBIDDEN",
        )

    # Update fields
    if payload.scheduled_at is not None:
        interview.scheduled_at = payload.scheduled_at
    if payload.mode is not None:
        interview.mode = payload.mode.upper()
    if payload.round is not None:
        interview.round = payload.round.upper()
    if payload.interviewer is not None:
        interview.interviewer = payload.interviewer
    if payload.location_or_link is not None:
        interview.location_or_link = payload.location_or_link
    if payload.result is not None:
        old_result = interview.result
        interview.result = payload.result.upper()

        # If result changed to PASSED/FAILED, potentially update application status
        if payload.result.upper() in ("PASSED", "FAILED"):
            if interview.application.status == ApplicationStatus.INTERVIEW:
                new_app_status = (
                    ApplicationStatus.SELECTED
                    if payload.result.upper() == "PASSED"
                    else ApplicationStatus.REJECTED
                )
                interview.application.status = new_app_status
                interview.application.updated_at = datetime.now(timezone.utc)
                db.add(interview.application)
                db.flush()

                # Write status history
                entry = build_status_history_entry(
                    application_id=interview.application.id,
                    old_status="INTERVIEW",
                    new_status=new_app_status.value,
                    changed_by_user_id=current_user.id,
                    remarks=f"Interview result: {payload.result.upper()}",
                )
                history = ApplicationStatusHistory(
                    application_id=interview.application.id,
                    old_status=ApplicationStatus.INTERVIEW,
                    new_status=new_app_status,
                    changed_by=current_user.id,
                    remarks=entry["remarks"],
                    changed_at=entry["changed_at"],
                )
                db.add(history)

                # Notify student
                if new_app_status == ApplicationStatus.SELECTED:
                    _create_notification(
                        db,
                        user_id=interview.application.student.user_id,
                        title="Interview Passed",
                        message=f"Congratulations! You passed the interview for {interview.application.job.title}.",
                    )
                else:
                    _create_notification(
                        db,
                        user_id=interview.application.student.user_id,
                        title="Interview Result",
                        message=f"Unfortunately, you did not pass the interview for {interview.application.job.title}.",
                    )

    if payload.notes is not None:
        interview.notes = payload.notes

    interview.updated_at = datetime.now(timezone.utc)
    db.add(interview)
    db.commit()
    db.refresh(interview)

    interview_detail = InterviewDetail(
        id=interview.id,
        application_id=interview.application_id,
        scheduled_at=interview.scheduled_at,
        mode=interview.mode,
        round=interview.round,
        interviewer=interview.interviewer,
        location_or_link=interview.location_or_link,
        result=interview.result,
        notes=interview.notes,
        created_at=interview.created_at,
        updated_at=interview.updated_at,
        student_name=interview.application.student.user.full_name,
        job_title=interview.application.job.title,
        company_name=(
            interview.application.job.company.name
            if interview.application.job.company
            else "Unknown"
        ),
    )

    return APIResponse(
        success=True,
        data=interview_detail,
        message="Interview updated successfully.",
    )


# ---------------------------------------------------------------------------
# 8. GET /interviews — List Interviews (Student/Recruiter/PO)
# ---------------------------------------------------------------------------

@router.get(
    "/interviews",
    response_model=APIResponse[PaginatedInterviewsResponse],
    summary="List interviews scoped by role",
)
def get_interviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Interview).options(
        joinedload(Interview.application).joinedload(Application.job),
        joinedload(Interview.application).joinedload(Application.student).joinedload(Student.user),
    )

    if current_user.role == UserRole.STUDENT:
        # Student sees their own interviews
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return APIResponse(
                success=True,
                data=PaginatedInterviewsResponse(
                    items=[], total=0, page=1, page_size=page_size, total_pages=1
                ),
                message="No interviews found.",
            )
        query = query.join(Application).filter(Application.student_id == student.id)

    elif current_user.role == UserRole.RECRUITER:
        # Recruiter sees interviews for their company's jobs
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not recruiter:
            return APIResponse(
                success=True,
                data=PaginatedInterviewsResponse(
                    items=[], total=0, page=1, page_size=page_size, total_pages=1
                ),
                message="No interviews found.",
            )
        query = query.join(Application).join(Job).filter(Job.company_id == recruiter.company_id)

    # else: PLACEMENT_OFFICER sees all

    query = query.order_by(Interview.scheduled_at.desc())
    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    interviews = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for interview in interviews:
        items.append(
            InterviewDetail(
                id=interview.id,
                application_id=interview.application_id,
                scheduled_at=interview.scheduled_at,
                mode=interview.mode,
                round=interview.round,
                interviewer=interview.interviewer,
                location_or_link=interview.location_or_link,
                result=interview.result,
                notes=interview.notes,
                created_at=interview.created_at,
                updated_at=interview.updated_at,
                student_name=interview.application.student.user.full_name,
                job_title=interview.application.job.title,
                company_name=(
                    interview.application.job.company.name
                    if interview.application.job.company
                    else "Unknown"
                ),
            )
        )

    return APIResponse(
        success=True,
        data=PaginatedInterviewsResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
        message="Interviews retrieved successfully.",
    )
