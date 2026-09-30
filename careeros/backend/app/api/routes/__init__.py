from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.profile import router as profile_router
from app.api.routes.education import router as education_router
from app.api.routes.experience import router as experience_router
from app.api.routes.skills import router as skills_router
from app.api.routes.certifications import router as certifications_router
from app.api.routes.career_brain import router as career_brain_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.matching import router as matching_router
from app.api.routes.resumes import router as resumes_router
from app.api.routes.crm import router as crm_router

__all__ = [
    "auth_router",
    "health_router",
    "profile_router",
    "education_router",
    "experience_router",
    "skills_router",
    "certifications_router",
    "career_brain_router",
    "jobs_router",
    "matching_router",
    "resumes_router",
    "crm_router",
]
