from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str | float]:
    return {
        "status": "ok",
        "service": "CareerOS API",
        "timestamp": datetime.now(timezone.utc).timestamp(),
    }


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - database health check guard
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ready", "service": "CareerOS API"}
