"""Audit logging service for recording security events."""

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    event_type: str,
    email: Optional[str] = None,
    user_id: Optional[UUID] = None,
    details: Optional[dict[str, Any]] = None,
) -> AuditLog:
    """
    Create an audit log entry.
    
    Args:
        db: Database session
        event_type: Type of event (USER_REGISTERED, LOGIN_SUCCESS, LOGIN_FAILURE, etc.)
        email: Email address associated with event (optional)
        user_id: User ID associated with event (optional)
        details: Additional event details as dict (optional)
    
    Returns:
        Created AuditLog instance
    """
    audit = AuditLog(
        event_type=event_type,
        email=email,
        user_id=user_id,
        details=json.dumps(details) if details else None,
    )
    db.add(audit)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    
    return audit


def get_audit_logs(
    db: Session,
    limit: int = 100,
    offset: int = 0,
    event_type: Optional[str] = None,
    user_id: Optional[UUID] = None,
) -> list[AuditLog]:
    """
    Retrieve audit logs with optional filtering.
    
    Args:
        db: Database session
        limit: Maximum number of results
        offset: Pagination offset
        event_type: Filter by event type (optional)
        user_id: Filter by user ID (optional)
    
    Returns:
        List of AuditLog entries
    """
    query = db.query(AuditLog)
    
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
