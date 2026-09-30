from fastapi import APIRouter

from app.api.routes import (
    auth_router,
    career_brain_router,
    certifications_router,
    crm_router,
    education_router,
    experience_router,
    health_router,
    jobs_router,
    matching_router,
    profile_router,
    resumes_router,
    skills_router,
)

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(profile_router)
api_router.include_router(education_router)
api_router.include_router(experience_router)
api_router.include_router(skills_router)
api_router.include_router(certifications_router)
api_router.include_router(career_brain_router)
api_router.include_router(jobs_router)
api_router.include_router(matching_router)
api_router.include_router(resumes_router)
api_router.include_router(crm_router)
