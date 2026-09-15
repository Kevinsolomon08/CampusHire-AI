# app/api/notifications.py
# Notification endpoints for students and recruiters.

from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, AppError
from app.models.models import Notification, User, UserRole
from app.schemas.response import APIResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas (inline for notifications)
# ---------------------------------------------------------------------------

class NotificationSchema:
    """Notification response schema."""

    def __init__(
        self,
        id: int,
        title: str,
        message: str,
        is_read: bool,
        created_at: str,
    ):
        self.id = id
        self.title = title
        self.message = message
        self.is_read = is_read
        self.created_at = created_at

    @classmethod
    def from_orm(cls, notif: Notification) -> dict:
        """Convert ORM object to dict."""
        return {
            "id": notif.id,
            "title": notif.title,
            "message": notif.message,
            "is_read": notif.is_read,
            "created_at": notif.created_at.isoformat() if notif.created_at else None,
        }


class PaginatedNotificationsResponse:
    """Paginated notifications response."""

    def __init__(
        self,
        items: list[dict],
        total: int,
        page: int,
        page_size: int,
        total_pages: int,
    ):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = total_pages

    def to_dict(self) -> dict:
        """Convert to dict for JSON response."""
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
        }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=dict, tags=["Notifications"], summary="Get paginated notifications for current user")
async def get_notifications(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponse:
    """
    Get paginated notifications for the current user.

    **Access**: Student, Recruiter, Placement Officer

    Notifications are sorted by created_at descending (newest first).

    Query Parameters:
    - page: Page number (1-indexed), default 1
    - page_size: Items per page, default 10, max 100

    Returns:
        {
            "success": true,
            "data": {
                "items": [
                    {
                        "id": int,
                        "title": str,
                        "message": str,
                        "is_read": bool,
                        "created_at": ISO 8601 datetime
                    },
                    ...
                ],
                "total": int,
                "page": int,
                "page_size": int,
                "total_pages": int
            }
        }
    """
    # Query total count
    total = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .count()
    )

    # Calculate pagination
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size

    # Fetch notifications
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .offset(offset)
        .limit(page_size)
        .all()
    )

    # Format response
    items = [NotificationSchema.from_orm(n) for n in notifications]

    response_data = {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }

    return {"success": True, "data": response_data}


@router.patch("/{notification_id}/read", response_model=dict, tags=["Notifications"], summary="Mark a notification as read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponse:
    """
    Mark a notification as read.

    **Access**: Student, Recruiter, Placement Officer

    The notification must belong to the current user.

    Path Parameters:
    - notification_id: ID of the notification to mark as read

    Returns:
        {
            "success": true,
            "data": {
                "id": int,
                "title": str,
                "message": str,
                "is_read": true,
                "created_at": ISO 8601 datetime
            }
        }

    Errors:
    - 404 Not Found: Notification does not exist or does not belong to current user
    """
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )

    if not notification:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Notification not found.",
            error_code="NOT_FOUND",
        )

    # Mark as read
    notification.is_read = True
    db.add(notification)
    db.commit()

    # Return updated notification
    updated_data = NotificationSchema.from_orm(notification)

    return {
        "success": True,
        "data": updated_data,
    }


@router.get("/unread/count", response_model=dict, tags=["Notifications"], summary="Get total count of unread notifications")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponse:
    """
    Get count of unread notifications for the current user.

    **Access**: Student, Recruiter, Placement Officer

    Returns:
        {
            "success": true,
            "data": {
                "unread_count": int
            }
        }
    """
    unread_count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .count()
    )

    return {
        "success": True,
        "data": {"unread_count": unread_count},
    }
