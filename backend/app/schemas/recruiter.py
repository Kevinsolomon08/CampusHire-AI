# app/schemas/recruiter.py
# Pydantic schemas for Company, Recruiter, and Job Management.

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Company Schemas
# ---------------------------------------------------------------------------

class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)


class CompanyOut(BaseModel):
    id: int
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Recruiter Profile Schemas
# ---------------------------------------------------------------------------

class RecruiterProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str
    email: str
    designation: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[CompanyOut] = None
    total_jobs: int = 0
    active_jobs: int = 0


# ---------------------------------------------------------------------------
# Job CRUD Schemas
# ---------------------------------------------------------------------------

class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    min_cgpa: Optional[float] = None
    minimum_cgpa: Optional[float] = None
    allowed_branches: Optional[List[str]] = None
    maximum_backlogs: Optional[int] = None
    eligible_batch: Optional[int] = None
    experience_requirement: Optional[str] = None
    employment_type: str = "FULL_TIME"
    location: Optional[str] = None
    package_lpa: Optional[float] = None
    requirements: Optional[List[str]] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = "DRAFT"

    @field_validator("min_cgpa", "minimum_cgpa")
    @classmethod
    def validate_cgpa(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v < 0.0 or v > 10.0:
                raise ValueError("Minimum CGPA must be between 0.0 and 10.0.")
        return v

    @field_validator("maximum_backlogs")
    @classmethod
    def validate_backlogs(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v < 0:
                raise ValueError("Maximum backlogs must be greater than or equal to 0.")
        return v


class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    min_cgpa: Optional[float] = None
    minimum_cgpa: Optional[float] = None
    allowed_branches: Optional[List[str]] = None
    maximum_backlogs: Optional[int] = None
    eligible_batch: Optional[int] = None
    experience_requirement: Optional[str] = None
    employment_type: Optional[str] = None
    location: Optional[str] = None
    package_lpa: Optional[float] = None
    requirements: Optional[List[str]] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = None

    @field_validator("min_cgpa", "minimum_cgpa")
    @classmethod
    def validate_cgpa(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v < 0.0 or v > 10.0:
                raise ValueError("Minimum CGPA must be between 0.0 and 10.0.")
        return v

    @field_validator("maximum_backlogs")
    @classmethod
    def validate_backlogs(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v < 0:
                raise ValueError("Maximum backlogs must be greater than or equal to 0.")
        return v


class JobDetailResponse(BaseModel):
    id: int
    company_id: int
    company: Optional[CompanyOut] = None
    created_by: Optional[int] = None
    title: str
    description: Optional[str] = None
    requirements: Optional[Any] = None
    required_skills: Optional[Any] = None
    preferred_skills: Optional[Any] = None
    min_cgpa: Optional[float] = None
    allowed_branches: Optional[Any] = None
    maximum_backlogs: Optional[int] = None
    eligible_batch: Optional[int] = None
    experience_requirement: Optional[str] = None
    employment_type: str = "FULL_TIME"
    location: Optional[str] = None
    package_lpa: Optional[float] = None
    status: str
    deadline: Optional[datetime] = None
    total_applicants: int = 0
    eligible_applicants: int = 0
    created_at: datetime
    updated_at: datetime


class RecruiterJobListItem(BaseModel):
    id: int
    company_id: int
    company: Optional[CompanyOut] = None
    title: str
    location: Optional[str] = None
    package_lpa: Optional[float] = None
    status: str
    deadline: Optional[datetime] = None
    min_cgpa: Optional[float] = None
    allowed_branches: Optional[Any] = None
    maximum_backlogs: Optional[int] = None
    eligible_batch: Optional[int] = None
    required_skills: Optional[Any] = None
    employment_type: str = "FULL_TIME"
    total_applicants: int = 0
    eligible_applicants: int = 0
    created_at: datetime


class PaginatedRecruiterJobsResponse(BaseModel):
    items: List[RecruiterJobListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
