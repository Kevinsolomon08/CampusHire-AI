# app/main.py
# CampusHire FastAPI application entry point.

from __future__ import annotations

import logging
from sqlalchemy.exc import SQLAlchemyError

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.applications import router as applications_router
from app.api.auth import router as auth_router
from app.api.companies import router as companies_router
from app.api.deps import AppError
from app.api.jobs import router as jobs_router
from app.api.admin import router as admin_router
from app.api.notifications import router as notifications_router
from app.api.recruiters import router as recruiters_router
from app.api.students import router as students_router
from app.core.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="CampusHire API",
    description="Campus recruitment platform — backend API.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global Exception Handlers — enforces consistent response envelope:
# { "success": false, "message": "...", "error_code": "..." }
# ---------------------------------------------------------------------------
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Map common status codes to default error codes if none provided
    default_code = "HTTP_ERROR"
    if exc.status_code == 401:
        default_code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        default_code = "FORBIDDEN"
    elif exc.status_code == 404:
        default_code = "NOT_FOUND"

    error_code = getattr(exc, "error_code", default_code)
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": message,
            "error_code": error_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Extract friendly first error message
    first_error = exc.errors()[0] if exc.errors() else {}
    loc = " -> ".join(str(l) for l in first_error.get("loc", []))
    msg = first_error.get("msg", "Validation failed")
    detail_msg = f"{loc}: {msg}" if loc else msg

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": detail_msg,
            "error_code": "VALIDATION_ERROR",
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Catch database errors and return safe error response without stack traces."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Database operation failed. Please try again later.",
            "error_code": "DATABASE_ERROR",
        },
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """Simple liveness probe — returns 200 when the server is up."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Mount Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])

app.include_router(students_router, prefix="/students", tags=["Students"])
app.include_router(students_router, prefix="/api/v1/students", tags=["Students"])

app.include_router(applications_router, prefix="/applications", tags=["Applications"])
app.include_router(applications_router, prefix="/api/v1/applications", tags=["Applications"])

app.include_router(companies_router, prefix="/companies", tags=["Companies"])
app.include_router(companies_router, prefix="/api/v1/companies", tags=["Companies"])

app.include_router(recruiters_router, prefix="/recruiters", tags=["Recruiters"])
app.include_router(recruiters_router, prefix="/api/v1/recruiters", tags=["Recruiters"])

app.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])
app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["Jobs"])

app.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["Notifications"])

app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])


