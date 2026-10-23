# app/api/deps.py
# FastAPI dependencies for Authentication and Role Authorization.

from __future__ import annotations

from typing import Callable, List, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.connection import get_db
from app.models.models import User, UserRole

# HTTP Bearer authentication scheme
security_scheme = HTTPBearer(auto_error=False)


class AppError(HTTPException):
    """Custom HTTPException carrying an error_code for envelope responses."""

    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str = "ERROR",
        details: object | None = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.error_code = error_code
        self.details = details


def get_current_user(
    credentials: Union[HTTPAuthorizationCredentials, None] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT token and return the authenticated User object.

    Raises:
        AppError: 401 if token is missing, invalid, expired, or user not found.
    """
    if credentials is None:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Not authenticated.",
            error_code="NOT_AUTHENTICATED",
        )

    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise AppError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid or expired token.",
                error_code="INVALID_TOKEN",
            )
    except JWTError:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid or expired token.",
            error_code="INVALID_TOKEN",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="User not found.",
            error_code="USER_NOT_FOUND",
        )

    if not user.is_active:
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            message="User account is inactive.",
            error_code="USER_INACTIVE",
        )

    return user


def require_role(*allowed_roles: Union[str, UserRole]) -> Callable[[User], User]:
    """Dependency factory enforcing that current user has one of the allowed roles.

    Raises:
        AppError: 403 with exact message 'You are not authorized to perform this action.'
    """
    # Normalize roles to uppercase strings
    role_strings: List[str] = [
        r.value if isinstance(r, UserRole) else str(r).upper() for r in allowed_roles
    ]

    def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        if user_role_str not in role_strings:
            raise AppError(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You are not authorized to perform this action.",
                error_code="FORBIDDEN",
            )
        return current_user

    return _role_checker
