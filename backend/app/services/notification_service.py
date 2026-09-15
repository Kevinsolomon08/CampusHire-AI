# app/services/notification_service.py
"""
CampusHire Notification Service.

Provides notification creation and retrieval helpers for the notification system.
Notifications are sent to users on application status changes, interview scheduling,
and other recruitment workflow events.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.models import Notification


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
) -> Notification:
    """
    Create a notification for a user.

    Args:
        db: Database session
        user_id: ID of the user to notify
        title: Notification title (short, human-readable)
        message: Notification message (detailed description)

    Returns:
        The created Notification object

    Example:
        create_notification(
            db,
            user_id=student_user_id,
            title="Application Shortlisted",
            message=f"You have been shortlisted for {job.title} at {company.name}",
        )
    """
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        is_read=False,
        created_at=datetime.now(tz=timezone.utc),
    )
    db.add(notification)
    db.flush()  # Flush to get ID without committing
    return notification
