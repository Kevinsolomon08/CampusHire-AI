# app/models/__init__.py
# Re-export all models so alembic env.py only needs: from app.models import *

from app.models.models import (  # noqa: F401
    Application,
    ApplicationStatus,
    ApplicationStatusHistory,
    Company,
    Interview,
    InterviewMode,
    Job,
    JobStatus,
    Notification,
    Recruiter,
    Resume,
    Student,
    User,
    UserRole,
)

__all__ = [
    "User",
    "UserRole",
    "Student",
    "Company",
    "Recruiter",
    "Job",
    "JobStatus",
    "Resume",
    "Application",
    "ApplicationStatus",
    "ApplicationStatusHistory",
    "Interview",
    "InterviewMode",
    "Notification",
]
