"""Audit logging model for security and compliance."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class AuditLog(Base):
    """
    Audit log for tracking important security and account events.
    
    Stores:
    - USER_REGISTERED: New user created
    - LOGIN_SUCCESS: Successful authentication
    - LOGIN_FAILURE: Failed login attempt
    - REGISTRATION_RATE_LIMITED: Registration rate limit exceeded
    - LOGIN_RATE_LIMITED: Login rate limit exceeded
    """

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(String(50), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, user_id={self.user_id}, created_at={self.created_at})>"
