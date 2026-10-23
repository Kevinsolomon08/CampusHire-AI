# app/schemas/auth.py
# Pydantic schemas for Authentication in CampusHire.

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.models import UserRole


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Full name of the user")
    email: EmailStr = Field(..., description="Unique email address")
    password: str = Field(..., min_length=6, max_length=128, description="Plain text password")
    role: UserRole = Field(..., description="User role: STUDENT, RECRUITER, or PLACEMENT_OFFICER")
    cgpa: Optional[float] = Field(None, description="Not allowed; CGPA must come from a marksheet upload")

    # Optional fields for STUDENT role
    roll_number: Optional[str] = Field(None, max_length=50)
    branch: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1, le=2100)

    # Optional fields for RECRUITER role
    company_name: Optional[str] = Field(None, max_length=255)
    designation: Optional[str] = Field(None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class StudentProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    roll_number: str
    branch: str
    year: int


class RecruiterProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    designation: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    student_profile: Optional[StudentProfile] = None
    recruiter_profile: Optional[RecruiterProfile] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
