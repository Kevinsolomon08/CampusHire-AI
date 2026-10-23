# app/api/auth.py
# Authentication and authorization routes for CampusHire.

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import AppError, get_current_user, require_role
from app.core.security import create_access_token, hash_password, verify_password
from app.database.connection import get_db
from app.models.models import Company, Recruiter, Student, User, UserRole
from app.schemas.auth import (
    LoginRequest,
    RecruiterProfile,
    RegisterRequest,
    StudentProfile,
    TokenResponse,
    UserOut,
)
from app.schemas.response import APIResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def _format_user_out(user: User) -> UserOut:
    """Helper to convert ORM User into Pydantic UserOut model."""
    student_profile = None
    if user.student:
        student_profile = StudentProfile(
            id=user.student.id,
            roll_number=user.student.roll_number,
            branch=user.student.branch,
            year=user.student.year,
        )

    recruiter_profile = None
    if user.recruiter:
        recruiter_profile = RecruiterProfile(
            id=user.recruiter.id,
            company_id=user.recruiter.company_id,
            designation=user.recruiter.designation,
        )

    return UserOut(
        id=user.id,
        email=user.email,
        name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        student_profile=student_profile,
        recruiter_profile=recruiter_profile,
    )


@router.post(
    "/register",
    response_model=APIResponse[UserOut],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (Student, Recruiter, or Placement Officer)",
)
def register(
    req: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new user in the system.

    - Hashes the password with passlib[bcrypt].
    - If role is STUDENT, also creates a linked Student row.
    - If role is RECRUITER, also creates/links Company and Recruiter row.
    """
    clean_email = req.email.strip().lower()

    # Check for existing email
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        logger.warning(f"Registration attempt with existing email: {clean_email}")
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Email already registered.",
            error_code="EMAIL_ALREADY_EXISTS",
        )

    # Hash password
    hashed_pwd = hash_password(req.password)

    # Create User record
    new_user = User(
        email=clean_email,
        hashed_password=hashed_pwd,
        role=req.role,
        full_name=req.name.strip(),
        is_active=True,
    )
    db.add(new_user)
    db.flush()  # Assigns new_user.id
    
    logger.info(f"User registered: {clean_email} (role: {req.role})")

    # Create linked profile records based on role
    if req.role == UserRole.STUDENT:
        if req.cgpa is not None:
            raise AppError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="CGPA can only be updated by uploading your marksheet.",
                error_code="CGPA_UPDATE_NOT_ALLOWED",
            )
        # Determine unique roll number
        roll_num = req.roll_number.strip() if req.roll_number else f"STU-{new_user.id:04d}"
        branch_name = req.branch.strip() if req.branch else "Computer Science"
        grad_year = req.year if req.year else datetime.now().year

        student_rec = Student(
            user_id=new_user.id,
            roll_number=roll_num,
            branch=branch_name,
            year=grad_year,
        )
        db.add(student_rec)

    elif req.role == UserRole.RECRUITER:
        company_name = (
            req.company_name.strip()
            if req.company_name
            else f"{req.name.strip()}'s Company"
        )
        # Find or create company
        company = db.query(Company).filter(Company.name == company_name).first()
        if not company:
            company = Company(name=company_name)
            db.add(company)
            db.flush()

        recruiter_rec = Recruiter(
            user_id=new_user.id,
            company_id=company.id,
            designation=req.designation.strip() if req.designation else "Recruiter",
        )
        db.add(recruiter_rec)

    db.commit()
    db.refresh(new_user)

    user_out = _format_user_out(new_user)
    return APIResponse[UserOut](
        success=True,
        data=user_out,
        message="User registered successfully.",
    )


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    summary="Authenticate user and issue JWT access token",
)
def login(
    req: LoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate user credentials and return a signed JWT token."""
    clean_email = req.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()

    if not user or not verify_password(req.password, user.hashed_password):
        logger.warning(f"Failed login attempt for: {clean_email}")
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid email or password.",
            error_code="INVALID_CREDENTIALS",
        )

    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {clean_email}")
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            message="User account is inactive.",
            error_code="USER_INACTIVE",
        )

    # Issue JWT access token
    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_access_token(
        subject=user.id,
        role=role_value,
        extra_claims={"email": user.email, "name": user.full_name},
    )
    
    logger.info(f"User logged in: {clean_email} (role: {user.role})")

    user_out = _format_user_out(user)
    return APIResponse[TokenResponse](
        success=True,
        data=TokenResponse(
            access_token=token,
            token_type="bearer",
            user=user_out,
        ),
        message="Login successful.",
    )


@router.get(
    "/me",
    response_model=APIResponse[UserOut],
    summary="Get current authenticated user profile",
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """Return profile details of the currently authenticated user."""
    user_out = _format_user_out(current_user)
    return APIResponse[UserOut](
        success=True,
        data=user_out,
        message="Current user profile retrieved.",
    )


# ---------------------------------------------------------------------------
# Role validation test routes
# ---------------------------------------------------------------------------
@router.get("/test-role/student", response_model=APIResponse[dict])
def test_student_role(current_user: User = Depends(require_role(UserRole.STUDENT))):
    return APIResponse(
        success=True,
        data={"user_id": current_user.id, "role": current_user.role.value},
        message="Welcome, Student!",
    )


@router.get("/test-role/recruiter", response_model=APIResponse[dict])
def test_recruiter_role(current_user: User = Depends(require_role(UserRole.RECRUITER))):
    return APIResponse(
        success=True,
        data={"user_id": current_user.id, "role": current_user.role.value},
        message="Welcome, Recruiter!",
    )


@router.get("/test-role/placement", response_model=APIResponse[dict])
def test_placement_role(
    current_user: User = Depends(require_role(UserRole.PLACEMENT_OFFICER)),
):
    return APIResponse(
        success=True,
        data={"user_id": current_user.id, "role": current_user.role.value},
        message="Welcome, Placement Officer!",
    )
