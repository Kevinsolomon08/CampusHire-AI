# app/schemas/application.py
# Pydantic schemas for Application workflow and Interview management.

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Application Schemas
# ---------------------------------------------------------------------------

class ApplicationStatusHistoryItem(BaseModel):
    """Single status history entry for timeline display."""
    id: int
    old_status: Optional[str] = None
    new_status: str
    changed_by_name: Optional[str] = None
    changed_by_role: Optional[str] = None
    remarks: Optional[str] = None
    changed_at: datetime

    model_config = {"from_attributes": True}


class JobBriefForApplication(BaseModel):
    """Minimal job info embedded in application responses."""
    id: int
    title: str
    company_name: str
    package_lpa: Optional[float] = None
    location: Optional[str] = None
    deadline: Optional[datetime] = None


class ApplicationListItem(BaseModel):
    """Application list item for student's /applications endpoint."""
    id: int
    job: JobBriefForApplication
    status: str
    applied_at: datetime
    updated_at: datetime
    # AI scoring placeholders
    ai_score: Optional[float] = None
    rank: Optional[int] = None


class ApplicationDetailResponse(BaseModel):
    """Full application detail with complete status history timeline."""
    id: int
    student_id: int
    job_id: int
    resume_id: Optional[int] = None
    status: str
    applied_at: datetime
    updated_at: datetime
    # AI scoring
    ai_score: Optional[float] = None
    semantic_score: Optional[float] = None
    skill_score: Optional[float] = None
    experience_score: Optional[float] = None
    education_score: Optional[float] = None
    rank: Optional[int] = None
    # Nested details
    job: JobBriefForApplication
    status_history: List[ApplicationStatusHistoryItem]


class ApplicationCreate(BaseModel):
    """Request payload for student applying to a job (resume_id optional if primary exists)."""
    job_id: int
    resume_id: Optional[int] = None


class ApplicationStatusUpdateRequest(BaseModel):
    """Request payload for recruiter/placement officer updating application status."""
    new_status: str = Field(..., min_length=1)
    remarks: Optional[str] = None


# ---------------------------------------------------------------------------
# Interview Schemas
# ---------------------------------------------------------------------------

class InterviewCreate(BaseModel):
    """Request payload for scheduling an interview."""
    application_id: int
    scheduled_at: datetime
    mode: str = Field(..., pattern="^(ONLINE|OFFLINE)$")
    round: str = Field(default="TECHNICAL", pattern="^(TECHNICAL|HR|MANAGERIAL|ASSESSMENT|OTHER)$")
    interviewer: Optional[str] = None
    location_or_link: Optional[str] = None
    notes: Optional[str] = None


class InterviewUpdate(BaseModel):
    """Request payload for updating interview details or result."""
    scheduled_at: Optional[datetime] = None
    mode: Optional[str] = Field(None, pattern="^(ONLINE|OFFLINE)$")
    round: Optional[str] = Field(None, pattern="^(TECHNICAL|HR|MANAGERIAL|ASSESSMENT|OTHER)$")
    interviewer: Optional[str] = None
    location_or_link: Optional[str] = None
    result: Optional[str] = Field(None, pattern="^(PENDING|PASSED|FAILED|NO_SHOW)$")
    notes: Optional[str] = None


class InterviewDetail(BaseModel):
    """Full interview details."""
    id: int
    application_id: int
    scheduled_at: datetime
    mode: str
    round: str
    interviewer: Optional[str] = None
    location_or_link: Optional[str] = None
    result: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # Nested application info for context
    student_name: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None

    model_config = {"from_attributes": True}


class PaginatedInterviewsResponse(BaseModel):
    """Paginated interview list."""
    items: List[InterviewDetail]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Recruiter Applicant Management
# ---------------------------------------------------------------------------

class ApplicantListItem(BaseModel):
    """Single applicant row for recruiter's job applicant table."""
    application_id: int
    student_id: int
    student_name: str
    student_email: str
    roll_number: str
    branch: str
    cgpa: Optional[float] = None
    backlog_count: int
    status: str
    applied_at: datetime
    # AI scoring placeholders
    ai_score: Optional[float] = None
    rank: Optional[int] = None


class PaginatedApplicantsResponse(BaseModel):
    """Paginated applicant list for a job."""
    items: List[ApplicantListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
