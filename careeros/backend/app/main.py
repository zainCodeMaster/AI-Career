from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, log_api_event
from app.db.database import SessionLocal, init_db
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    configure_logging()
    init_db()
    # Start automatic job discovery scheduler
    try:
        start_scheduler()
    except Exception as exc:
        # Log but don't crash — scheduler is best-effort
        import logging
        logging.getLogger("app.main").warning(
            "Failed to start discovery scheduler: %s", exc
        )
    yield
    # Shut down scheduler on exit
    try:
        stop_scheduler()
    except Exception:
        pass


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="CareerOS API",
        description="Production-oriented foundation for CareerOS AI.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=app_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
        max_age=86400,  # Cache preflight for 24 hours
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logging.getLogger("app.api").info(
            "HTTP %s %s -> %s",
            request.method,
            request.url.path,
            response.status_code,
            extra={"request_id": request_id, "method": request.method, "path": request.url.path, "status_code": response.status_code},
        )
        return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        log_api_event(
            "HTTP_EXCEPTION",
            endpoint=request.url.path,
            status_code=exc.status_code,
            details={"request_id": getattr(request.state, "request_id", None), "detail": exc.detail},
        )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        log_api_event(
            "VALIDATION_ERROR",
            endpoint=request.url.path,
            status_code=422,
            details={"error_count": len(exc.errors()), "request_id": getattr(request.state, "request_id", None)},
        )
        return JSONResponse(status_code=422, content={"detail": "Invalid request data"})

    @app.exception_handler(Exception)
    async def internal_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        log_api_event(
            "INTERNAL_SERVER_ERROR",
            endpoint=request.url.path,
            status_code=500,
            details={"request_id": getattr(request.state, "request_id", None), "error": str(exc)},
        )
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.get("/health")
    async def health_check() -> dict[str, str | float]:
        return {"status": "ok", "service": "CareerOS API", "timestamp": datetime.now(timezone.utc).timestamp()}

    @app.get("/ready")
    async def readiness_check():
        try:
            with SessionLocal() as session:
                session.execute(text("SELECT 1"))
        except Exception as exc:  # pragma: no cover - readiness guard
            raise HTTPException(status_code=503, detail="Database unavailable") from exc
        return {"status": "ready", "service": "CareerOS API"}

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "CareerOS API", "version": "0.1.0"}

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
