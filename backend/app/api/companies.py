# app/api/companies.py
# API routes for Company creation, viewing, and management by recruiters.

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import AppError, get_current_user, require_role
from app.database.connection import get_db
from app.models.models import Company, Recruiter, User, UserRole
from app.schemas.recruiter import CompanyCreate, CompanyOut, CompanyUpdate
from app.schemas.response import APIResponse

router = APIRouter()


def _format_company_out(company: Company) -> CompanyOut:
    return CompanyOut(
        id=company.id,
        name=company.name,
        website=company.website,
        industry=company.industry,
        description=company.description,
        logo_url=company.logo_url,
        contact_email=company.contact_email,
        contact_phone=company.contact_phone,
        address=company.address,
        created_at=company.created_at,
    )


@router.post(
    "",
    response_model=APIResponse[CompanyOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create and link a new Company",
)
def create_company(
    payload: CompanyCreate,
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
    db: Session = Depends(get_db),
):
    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
    if not recruiter:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Recruiter profile not found.",
            error_code="RECRUITER_NOT_FOUND",
        )

    new_company = Company(
        name=payload.name.strip(),
        website=payload.website.strip() if payload.website else None,
        industry=payload.industry.strip() if payload.industry else None,
        description=payload.description.strip() if payload.description else None,
        logo_url=payload.logo_url.strip() if payload.logo_url else None,
        contact_email=payload.contact_email.strip() if payload.contact_email else None,
        contact_phone=payload.contact_phone.strip() if payload.contact_phone else None,
        address=payload.address.strip() if payload.address else None,
    )
    db.add(new_company)
    db.flush()

    # Link recruiter to the newly created company
    recruiter.company_id = new_company.id
    db.commit()
    db.refresh(new_company)

    return APIResponse(
        success=True,
        data=_format_company_out(new_company),
        message="Company created successfully.",
    )


@router.get(
    "/{company_id}",
    response_model=APIResponse[CompanyOut],
    summary="Get Company profile by ID",
)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Company not found.",
            error_code="COMPANY_NOT_FOUND",
        )

    return APIResponse(
        success=True,
        data=_format_company_out(company),
        message="Company retrieved successfully.",
    )


@router.put(
    "/{company_id}",
    response_model=APIResponse[CompanyOut],
    summary="Update Company profile (Scoped to owning recruiter)",
)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
    db: Session = Depends(get_db),
):
    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
    if not recruiter or recruiter.company_id != company_id:
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You are not authorized to perform this action.",
            error_code="FORBIDDEN",
        )

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Company not found.",
            error_code="COMPANY_NOT_FOUND",
        )

    if payload.name is not None and payload.name.strip():
        company.name = payload.name.strip()
    if payload.website is not None:
        company.website = payload.website.strip() if payload.website else None
    if payload.industry is not None:
        company.industry = payload.industry.strip() if payload.industry else None
    if payload.description is not None:
        company.description = payload.description.strip() if payload.description else None
    if payload.logo_url is not None:
        company.logo_url = payload.logo_url.strip() if payload.logo_url else None
    if payload.contact_email is not None:
        company.contact_email = payload.contact_email.strip() if payload.contact_email else None
    if payload.contact_phone is not None:
        company.contact_phone = payload.contact_phone.strip() if payload.contact_phone else None
    if payload.address is not None:
        company.address = payload.address.strip() if payload.address else None

    db.commit()
    db.refresh(company)

    return APIResponse(
        success=True,
        data=_format_company_out(company),
        message="Company profile updated successfully.",
    )
