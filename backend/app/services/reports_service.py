# app/services/reports_service.py
"""
CampusHire Reports Service.

Generates placement reports with various breakdowns (company-wise, department-wise, batch-wise)
and supports filtering and CSV export.
"""

from typing import Optional
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.models import (
    Application,
    ApplicationStatus,
    Company,
    Interview,
    Job,
    Student,
    User,
)


def get_placement_report(
    db: Session,
    batch: Optional[int] = None,
    department: Optional[str] = None,
    company_id: Optional[int] = None,
    job_id: Optional[int] = None,
) -> dict:
    """
    Generate a comprehensive placement report with various breakdowns.
    """
    # Base query
    base_query = (
        db.query(Application)
        .join(Student, Application.student_id == Student.id)
        .join(User, Student.user_id == User.id)
        .join(Job, Application.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
    )

    # Apply filters
    if batch:
        base_query = base_query.filter(Student.year == batch)
    if department:
        base_query = base_query.filter(Student.branch == department)
    if company_id:
        base_query = base_query.filter(Company.id == company_id)
    if job_id:
        base_query = base_query.filter(Job.id == job_id)

    # Summary totals
    total_apps = base_query.count()
    total_shortlisted = (
        base_query.filter(
            Application.status.in_([
                ApplicationStatus.SHORTLISTED,
                ApplicationStatus.INTERVIEW_SCHEDULED,
                ApplicationStatus.INTERVIEW,
                ApplicationStatus.SELECTED,
                ApplicationStatus.REJECTED,
            ])
        ).count()
    )
    total_interviewed = (
        base_query.filter(
            Application.status.in_([
                ApplicationStatus.INTERVIEW,
                ApplicationStatus.SELECTED,
                ApplicationStatus.REJECTED,
            ])
        ).count()
    )
    total_selected = (
        base_query.filter(Application.status == ApplicationStatus.SELECTED).count()
    )
    total_rejected = (
        base_query.filter(Application.status == ApplicationStatus.REJECTED).count()
    )

    selection_rate = (
        ((total_selected / total_apps) * 100) if total_apps > 0 else 0
    )

    # Company breakdown
    company_breakdown = []
    company_data = (
        db.query(
            Company.id,
            Company.name,
            func.count(Application.id).label("total"),
            func.sum(
                case((Application.status == ApplicationStatus.SELECTED, 1), else_=0)
            ).label("selected"),
            func.sum(
                case((Application.status == ApplicationStatus.REJECTED, 1), else_=0)
            ).label("rejected"),
        )
        .select_from(Company)
        .join(Job, Company.id == Job.company_id)
        .join(Application, Job.id == Application.job_id)
        .join(Student, Application.student_id == Student.id)
    )

    if batch:
        company_data = company_data.filter(Student.year == batch)
    if department:
        company_data = company_data.filter(Student.branch == department)
    if company_id:
        company_data = company_data.filter(Company.id == company_id)
    if job_id:
        company_data = company_data.filter(Job.id == job_id)

    company_data = company_data.group_by(Company.id, Company.name).all()

    for cid, cname, total, selected, rejected in company_data:
        sel_count = selected or 0
        rej_count = rejected or 0
        tot_count = total or 0
        rate = ((sel_count / tot_count) * 100) if tot_count > 0 else 0
        company_breakdown.append(
            {
                "company_id": cid,
                "company_name": cname,
                "applications": tot_count,
                "selected": sel_count,
                "rejected": rej_count,
                "selection_rate": round(rate, 2),
            }
        )

    # Department breakdown
    dept_breakdown = []
    dept_data = (
        db.query(
            Student.branch,
            func.count(Application.id).label("total"),
            func.sum(
                case((Application.status == ApplicationStatus.SELECTED, 1), else_=0)
            ).label("selected"),
            func.sum(
                case((Application.status == ApplicationStatus.REJECTED, 1), else_=0)
            ).label("rejected"),
        )
        .select_from(Student)
        .join(Application, Student.id == Application.student_id)
        .join(Job, Application.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
    )

    if batch:
        dept_data = dept_data.filter(Student.year == batch)
    if department:
        dept_data = dept_data.filter(Student.branch == department)
    if company_id:
        dept_data = dept_data.filter(Company.id == company_id)
    if job_id:
        dept_data = dept_data.filter(Job.id == job_id)

    dept_data = dept_data.group_by(Student.branch).all()

    for dept, total, selected, rejected in dept_data:
        sel_count = selected or 0
        rej_count = rejected or 0
        tot_count = total or 0
        rate = ((sel_count / tot_count) * 100) if tot_count > 0 else 0
        dept_breakdown.append(
            {
                "department": dept,
                "applications": tot_count,
                "selected": sel_count,
                "rejected": rej_count,
                "selection_rate": round(rate, 2),
            }
        )

    # Batch breakdown
    batch_breakdown = []
    batch_data = (
        db.query(
            Student.year,
            func.count(Application.id).label("total"),
            func.sum(
                case((Application.status == ApplicationStatus.SELECTED, 1), else_=0)
            ).label("selected"),
            func.sum(
                case((Application.status == ApplicationStatus.REJECTED, 1), else_=0)
            ).label("rejected"),
        )
        .select_from(Student)
        .join(Application, Student.id == Application.student_id)
        .join(Job, Application.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
    )

    if batch:
        batch_data = batch_data.filter(Student.year == batch)
    if department:
        batch_data = batch_data.filter(Student.branch == department)
    if company_id:
        batch_data = batch_data.filter(Company.id == company_id)
    if job_id:
        batch_data = batch_data.filter(Job.id == job_id)

    batch_data = batch_data.group_by(Student.year).order_by(Student.year.desc()).all()

    for b, total, selected, rejected in batch_data:
        sel_count = selected or 0
        rej_count = rejected or 0
        tot_count = total or 0
        rate = ((sel_count / tot_count) * 100) if tot_count > 0 else 0
        batch_breakdown.append(
            {
                "batch": b,
                "applications": tot_count,
                "selected": sel_count,
                "rejected": rej_count,
                "selection_rate": round(rate, 2),
            }
        )

    return {
        "summary": {
            "total_applications": total_apps,
            "total_shortlisted": total_shortlisted,
            "total_interviewed": total_interviewed,
            "total_selected": total_selected,
            "total_rejected": total_rejected,
            "selection_rate": round(selection_rate, 2),
        },
        "company_breakdown": company_breakdown,
        "department_breakdown": dept_breakdown,
        "batch_breakdown": batch_breakdown,
    }


def generate_csv_report(report_data: dict) -> str:
    """
    Generate CSV format of the placement report.

    Returns: CSV string
    """
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)

    # Summary section
    writer.writerow(["PLACEMENT REPORT SUMMARY"])
    writer.writerow([])
    summary = report_data.get("summary", {})
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Applications", summary.get("total_applications", 0)])
    writer.writerow(["Total Shortlisted", summary.get("total_shortlisted", 0)])
    writer.writerow(["Total Interviewed", summary.get("total_interviewed", 0)])
    writer.writerow(["Total Selected", summary.get("total_selected", 0)])
    writer.writerow(["Total Rejected", summary.get("total_rejected", 0)])
    writer.writerow(["Selection Rate (%)", summary.get("selection_rate", 0)])
    writer.writerow([])

    # Company breakdown
    writer.writerow(["COMPANY-WISE BREAKDOWN"])
    writer.writerow([])
    writer.writerow(["Company", "Applications", "Selected", "Rejected", "Selection Rate (%)"])
    for company in report_data.get("company_breakdown", []):
        writer.writerow([
            company["company_name"],
            company["applications"],
            company["selected"],
            company["rejected"],
            company["selection_rate"],
        ])
    writer.writerow([])

    # Department breakdown
    writer.writerow(["DEPARTMENT-WISE BREAKDOWN"])
    writer.writerow([])
    writer.writerow(["Department", "Applications", "Selected", "Rejected", "Selection Rate (%)"])
    for dept in report_data.get("department_breakdown", []):
        writer.writerow([
            dept["department"],
            dept["applications"],
            dept["selected"],
            dept["rejected"],
            dept["selection_rate"],
        ])
    writer.writerow([])

    # Batch breakdown
    writer.writerow(["BATCH-WISE BREAKDOWN"])
    writer.writerow([])
    writer.writerow(["Batch", "Applications", "Selected", "Rejected", "Selection Rate (%)"])
    for b in report_data.get("batch_breakdown", []):
        writer.writerow([
            b["batch"],
            b["applications"],
            b["selected"],
            b["rejected"],
            b["selection_rate"],
        ])

    return output.getvalue()
