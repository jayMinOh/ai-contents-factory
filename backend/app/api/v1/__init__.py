from fastapi import APIRouter

from app.api.v1.references import router as references_router
from app.api.v1.health import router as health_router
from app.api.v1.brands import router as brands_router
from app.api.v1.studio import router as studio_router
from app.api.v1.storyboard import router as storyboard_router
from app.api.v1.image_project import router as image_project_router
from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router

router = APIRouter()

# Public routes (no auth required)
router.include_router(health_router, prefix="/health", tags=["health"])
router.include_router(auth_router, tags=["auth"])

# Admin routes (admin only)
router.include_router(admin_router, tags=["admin"])

# Protected routes (approved users only)
router.include_router(references_router, prefix="/references", tags=["references"])
router.include_router(brands_router, prefix="/brands", tags=["brands"])
router.include_router(studio_router, prefix="/studio", tags=["studio"])
router.include_router(storyboard_router, prefix="/storyboard", tags=["storyboard"])
router.include_router(image_project_router, tags=["image-projects"])
