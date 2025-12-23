from fastapi import APIRouter

from app.api.v1.references import router as references_router
from app.api.v1.health import router as health_router
from app.api.v1.brands import router as brands_router
from app.api.v1.studio import router as studio_router
from app.api.v1.storyboard import router as storyboard_router
from app.api.v1.image_project import router as image_project_router

router = APIRouter()

router.include_router(health_router, prefix="/health", tags=["health"])
router.include_router(references_router, prefix="/references", tags=["references"])
router.include_router(brands_router, prefix="/brands", tags=["brands"])
router.include_router(studio_router, prefix="/studio", tags=["studio"])
router.include_router(storyboard_router, prefix="/storyboard", tags=["storyboard"])
router.include_router(image_project_router, tags=["image-projects"])
