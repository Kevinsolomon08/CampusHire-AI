
# app/models/models.py
# All SQLAlchemy ORM models for CampusHire.
#
# Models:
#   User, Student, Company, Recruiter, Job, Resume,
#   Application, ApplicationStatusHistory, Interview, Notification
#
# Enums:
#   UserRole          — STUDENT | RECRUITER | PLACEMENT_OFFICER
#   JobStatus         — DRAFT | OPEN | CLOSED | COMPLETED
#   ApplicationStatus — APPLIED | ELIGIBILITY_VERIFIED | SHORTLISTED |
#                       INTERVIEW_SCHEDULED | INTERVIEW | SELECTED | REJECTED

from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# forward-declare enums used as column types below (populated after enum classes)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    RECRUITER = "RECRUITER"
    PLACEMENT_OFFICER = "PLACEMENT_OFFICER"


class JobStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    COMPLETED = "COMPLETED"


class ApplicationStatus(str, enum.Enum):
    APPLIED = "APPLIED"
    ELIGIBILITY_VERIFIED = "ELIGIBILITY_VERIFIED"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    INTERVIEW = "INTERVIEW"
    SELECTED = "SELECTED"
    REJECTED = "REJECTED"


class InterviewMode(str, enum.Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class InterviewRound(str, enum.Enum):
    TECHNICAL = "TECHNICAL"
    HR = "HR"
    MANAGERIAL = "MANAGERIAL"
    ASSESSMENT = "ASSESSMENT"
    OTHER = "OTHER"


class InterviewResult(str, enum.Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    NO_SHOW = "NO_SHOW"


# ---------------------------------------------------------------------------
# 1. User
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="userrole"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    student: Mapped[Optional["Student"]] = relationship(
        "Student", back_populates="user", uselist=False
    )
    recruiter: Mapped[Optional["Recruiter"]] = relationship(
        "Recruiter", back_populates="user", uselist=False
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user"
    )
    status_changes_made: Mapped[List["ApplicationStatusHistory"]] = relationship(
        "ApplicationStatusHistory", back_populates="changed_by_user"
    )
    jobs_created: Mapped[List["Job"]] = relationship(
        "Job", back_populates="created_by_user"
    )

    __table_args__ = (
        Index("ix_users_email", "email"),
    )


# ---------------------------------------------------------------------------
# 2. Student
# ---------------------------------------------------------------------------

class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    roll_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    branch: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    cgpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    backlog_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Stored as a JSON array of skill strings, e.g. ["Python", "SQL"]
    skills: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Stored as JSON structures for rich profile sections
    education: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    experience: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    projects: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    certifications: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="student")
    resumes: Mapped[List["Resume"]] = relationship("Resume", back_populates="student")
    applications: Mapped[List["Application"]] = relationship(
        "Application", back_populates="student"
    )

    @property
    def department(self) -> str:
        return self.branch

    @department.setter
    def department(self, value: str):
        self.branch = value

    @property
    def batch(self) -> int:
        return self.year

    @batch.setter
    def batch(self, value: int):
        self.year = value

    __table_args__ = (
        Index("ix_students_student_id", "id"),
        Index("ix_students_user_id", "user_id"),
    )


# ---------------------------------------------------------------------------
# 3. Company
# ---------------------------------------------------------------------------

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    recruiters: Mapped[List["Recruiter"]] = relationship(
        "Recruiter", back_populates="company"
    )
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="company")

    __table_args__ = (
        Index("ix_companies_company_id", "id"),
    )


# ---------------------------------------------------------------------------
# 4. Recruiter
# ---------------------------------------------------------------------------

class Recruiter(Base):
    __tablename__ = "recruiters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="recruiter")
    company: Mapped["Company"] = relationship("Company", back_populates="recruiters")

    __table_args__ = (
        Index("ix_recruiters_user_id", "user_id"),
        Index("ix_recruiters_company_id", "company_id"),
    )


# ---------------------------------------------------------------------------
# 5. Job
# ---------------------------------------------------------------------------

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # JSON array of requirement strings
    requirements: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # JSON array of skill strings
    required_skills: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    preferred_skills: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    min_cgpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Eligibility criteria
    allowed_branches: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    maximum_backlogs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    eligible_batch: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    experience_requirement: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    employment_type: Mapped[str] = mapped_column(String(50), default="FULL_TIME", nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    package_lpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, name="jobstatus"),
        default=JobStatus.DRAFT,
        nullable=False,
    )
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="jobs")
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="jobs_created"
    )
    applications: Mapped[List["Application"]] = relationship(
        "Application", back_populates="job"
    )

    @property
    def minimum_cgpa(self) -> Optional[float]:
        return self.min_cgpa

    @minimum_cgpa.setter
    def minimum_cgpa(self, value: Optional[float]):
        self.min_cgpa = value

    __table_args__ = (
        Index("ix_jobs_company_id", "company_id"),
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_deadline", "deadline"),
    )


# ---------------------------------------------------------------------------
# 6. Resume
# ---------------------------------------------------------------------------

class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="resumes")
    applications: Mapped[List["Application"]] = relationship(
        "Application", back_populates="resume"
    )

    __table_args__ = (
        Index("ix_resumes_student_id", "student_id"),
    )


# ---------------------------------------------------------------------------
# 7. Application
# ---------------------------------------------------------------------------

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    resume_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus, name="applicationstatus"),
        default=ApplicationStatus.APPLIED,
        nullable=False,
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # ---------- AI scoring columns (Phase 2) — all nullable ----------
    ai_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    semantic_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    skill_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    experience_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    education_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # -----------------------------------------------------------------

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="applications")
    job: Mapped["Job"] = relationship("Job", back_populates="applications")
    resume: Mapped[Optional["Resume"]] = relationship(
        "Resume", back_populates="applications"
    )
    status_history: Mapped[List["ApplicationStatusHistory"]] = relationship(
        "ApplicationStatusHistory", back_populates="application"
    )
    interviews: Mapped[List["Interview"]] = relationship(
        "Interview", back_populates="application"
    )

    __table_args__ = (
        # Enforce one application per student per job
        UniqueConstraint("student_id", "job_id", name="uq_application_student_job"),
        Index("ix_applications_student_id", "student_id"),
        Index("ix_applications_job_id", "job_id"),
        Index("ix_applications_status", "status"),
    )


# ---------------------------------------------------------------------------
# 8. ApplicationStatusHistory
# ---------------------------------------------------------------------------

class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    old_status: Mapped[Optional[ApplicationStatus]] = mapped_column(
        SAEnum(ApplicationStatus, name="applicationstatus"), nullable=True
    )
    new_status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus, name="applicationstatus"), nullable=False
    )
    changed_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    application: Mapped["Application"] = relationship(
        "Application", back_populates="status_history"
    )
    changed_by_user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="status_changes_made"
    )

    __table_args__ = (
        Index("ix_app_status_history_application_id", "application_id"),
    )


# ---------------------------------------------------------------------------
# 9. Interview
# ---------------------------------------------------------------------------

class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # Physical location (offline) or meeting link (online) — unified as location_or_link
    location_or_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # Legacy separate columns kept for DB back-compat; new code uses location_or_link
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mode: Mapped[InterviewMode] = mapped_column(
        SAEnum(InterviewMode, name="interviewmode"),
        default=InterviewMode.ONLINE,
        nullable=False,
    )
    round: Mapped[InterviewRound] = mapped_column(
        SAEnum(InterviewRound, name="interviewround"),
        default=InterviewRound.TECHNICAL,
        nullable=False,
    )
    interviewer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    result: Mapped[InterviewResult] = mapped_column(
        SAEnum(InterviewResult, name="interviewresult"),
        default=InterviewResult.PENDING,
        nullable=False,
    )
    meeting_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    application: Mapped["Application"] = relationship(
        "Application", back_populates="interviews"
    )

    __table_args__ = (
        Index("ix_interviews_application_id", "application_id"),
    )


# ---------------------------------------------------------------------------
# 10. Notification
# ---------------------------------------------------------------------------

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
    )
