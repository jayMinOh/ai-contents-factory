"""
SQLAlchemy ORM models for the AI Video Marketing Platform.

This module exports all model classes for easy imports throughout the application.

Usage:
    from app.models import Base, Brand, Product, ReferenceAnalysis, VideoProject, SceneImage, Storyboard
"""

from app.core.database import Base
from app.models.brand import Brand
from app.models.product import Product
from app.models.reference_analysis import ReferenceAnalysis
from app.models.video_project import VideoProject
from app.models.scene_image import SceneImage
from app.models.scene_video import SceneVideo
from app.models.storyboard import Storyboard
from app.models.image_project import ImageProject
from app.models.generated_image import GeneratedImage
from app.models.user import User, UserRole, UserStatus

__all__ = [
    "Base",
    "Brand",
    "Product",
    "ReferenceAnalysis",
    "VideoProject",
    "SceneImage",
    "SceneVideo",
    "Storyboard",
    "ImageProject",
    "GeneratedImage",
    "User",
    "UserRole",
    "UserStatus",
]
