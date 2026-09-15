# app/schemas/student.py
# Pydantic schemas for the Student Module.

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Profile Update & View Schemas
# ---------------------------------------------------------------------------

class StudentProfileUpdate(BaseModel):
    department: Optional[str] = Field(None, max_length=100)
    batch: Optional[int] = None
    cgpa: Optional[float] = None
    backlog_count: Optional[int] = None
    phone: Optional[str] = Field(None, max_length=20)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    roll_number: Optional[str] = Field(None, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)
    skills: Optional[List[str]] = None
    education: Optional[Union[List[Any], Dict[str, Any]]] = None
    experience: Optional[Union[List[Any], Dict[str, Any]]] = None
    projects: Optional[Union[List[Any], Dict[str, Any]]] = None
    certifications: Optional[Union[List[Any], Dict[str, Any]]] = None

    @field_validator("cgpa")
    @classmethod
    def validate_cgpa(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v < 0.0 or v > 10.0:
                raise ValueError("CGPA must be between 0.0 and 10.0.")
        return v

    @field_validator("backlog_count")
    @classmethod
    def validate_backlogs(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v < 0:
                raise ValueError("Backlog count must be greater than or equal to 0.")
        return v


class ResumeInfo(BaseModel):
    id: int
    filename: Optional[str] = None
    file_path: str
    is_primary: bool = False
    uploaded_at: datetime


class StudentProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str
    email: str
    roll_number: str
    department: str
    batch: int
    cgpa: Optional[float] = None
    backlog_count: int = 0
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    skills: Optional[List[str]] = None
    education: Optional[Any] = None
    experience: Optional[Any] = None
    projects: Optional[Any] = None
    certifications: Optional[Any] = None
    primary_resume: Optional[ResumeInfo] = None
    profile_completion_pct: int = 0


# ---------------------------------------------------------------------------
# Job Eligibility & Listing Schemas
# ---------------------------------------------------------------------------

class JobEligibilityInfo(BaseModel):
    eligible: bool
    reasons: List[str] = []


class CompanyBrief(BaseModel):
    id: int
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None


class StudentJobListItem(BaseModel):
    id: int
    title: str
    company: Optional[CompanyBrief] = None
    location: Optional[str] = None
    package_lpa: Optional[float] = None
    status: str
    deadline: Optional[datetime] = None
    min_cgpa: Optional[float] = None
    allowed_branches: Optional[Any] = None
    maximum_backlogs: Optional[int] = None
    eligible_batch: Optional[int] = None
    required_skills: Optional[Any] = None
    eligibility: JobEligibilityInfo
    created_at: datetime


class StudentJobDetailResponse(BaseModel):
    id: int
    title: str
    company: Optional[CompanyBrief] = None
    description: Optional[str] = None
    location: Optional[str] = None
    package_lpa: Optional[float] = None
    status: str
    deadline: Optional[datetime] = None
    min_cgpa: Optional[float] = None
    allowed_branches: Optional[Any] = None
    maximum_backlogs: Optional[int] = None
    eligible_batch: Optional[int] = None
    requirements: Optional[Any] = None
    required_skills: Optional[Any] = None
    eligibility: JobEligibilityInfo
    created_at: datetime


class PaginatedJobsResponse(BaseModel):
    items: List[StudentJobListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
