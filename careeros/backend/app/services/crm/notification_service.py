"""Notification service for Phase 7 notification system.

Creates, retrieves, and manages in-app notifications for users.
Notifications are user-scoped and user-owned.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.crm import Notification, NotificationType


class NotificationService:
    """Service for managing user notifications."""

    @staticmethod
    def create_notification(
        db: Session,
        user_id: UUID,
        type: NotificationType,
        title: str,
        message: str,
        target_url: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> Notification:
        """Create a new notification for a user."""
        notification = Notification(
            user_id=user_id,
            type=type.value,
            title=title,
            message=message,
            target_url=target_url,
            expires_at=expires_at,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def create_interview_reminder(
        db: Session,
        user_id: UUID,
        interview_title: str,
        scheduled_at: datetime,
        target_url: Optional[str] = None,
    ) -> Notification:
        """Create an interview reminder notification."""
        return NotificationService.create_notification(
            db,
            user_id,
            NotificationType.INTERVIEW_REMINDER,
            f"Interview Reminder: {interview_title}",
            f"Your interview '{interview_title}' is scheduled for {scheduled_at.strftime('%B %d, %Y at %I:%M %p')}.",
            target_url=target_url,
            expires_at=scheduled_at,
        )

    @staticmethod
    def create_follow_up_reminder(
        db: Session,
        user_id: UUID,
        title: str,
        due_at: datetime,
        target_url: Optional[str] = None,
    ) -> Notification:
        """Create a follow-up reminder notification."""
        return NotificationService.create_notification(
            db,
            user_id,
            NotificationType.FOLLOW_UP_REMINDER,
            f"Follow-Up Reminder: {title}",
            f"Follow-up '{title}' is due on {due_at.strftime('%B %d, %Y')}.",
            target_url=target_url,
            expires_at=due_at,
        )

    @staticmethod
    def create_system_notification(
        db: Session,
        user_id: UUID,
        title: str,
        message: str,
        target_url: Optional[str] = None,
    ) -> Notification:
        """Create a system notification."""
        return NotificationService.create_notification(
            db, user_id, NotificationType.SYSTEM, title, message, target_url
        )

    @staticmethod
    def list_notifications(
        db: Session,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> dict:
        """List notifications for a user with pagination."""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.read == False)  # noqa: E712

        total = query.count()
        unread_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read == False,  # noqa: E712
        ).count()

        offset = (page - 1) * page_size
        items = (
            query.order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "unread_count": unread_count,
        }

    @staticmethod
    def mark_read(
        db: Session,
        user_id: UUID,
        notification_ids: Optional[list[UUID]] = None,
        mark_all: bool = False,
    ) -> int:
        """Mark notification(s) as read. Returns count of updated rows."""
        if mark_all:
            result = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.read == False,  # noqa: E712
            ).update({"read": True, "read_at": datetime.now(timezone.utc)})
            db.commit()
            return result

        if notification_ids:
            result = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.id.in_(notification_ids),
                Notification.read == False,  # noqa: E712
            ).update({"read": True, "read_at": datetime.now(timezone.utc)}, synchronize_session=False)
            db.commit()
            return result

        return 0

    @staticmethod
    def delete_notification(db: Session, user_id: UUID, notification_id: UUID) -> bool:
        """Delete a notification. Returns True if deleted."""
        result = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.id == notification_id,
        ).delete()
        db.commit()
        return result > 0
