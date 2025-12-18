"""
Brand and Product Pydantic Schemas

This module defines all Pydantic schemas for Brand and Product entities.
Schemas are designed to match the frontend TypeScript interfaces exactly.
Enhanced for cosmetics products with ingredient and skin compatibility data.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ========== Cosmetics Enums ==========


class ProductCategory(str, Enum):
    """Product category types for cosmetics."""

    SERUM = "serum"
    CREAM = "cream"
    TONER = "toner"
    ESSENCE = "essence"
    OIL = "oil"
    MASK = "mask"
    CLEANSER = "cleanser"
    SUNSCREEN = "sunscreen"
    MOISTURIZER = "moisturizer"
    EYE_CARE = "eye_care"
    LIP_CARE = "lip_care"
    MIST = "mist"
    AMPOULE = "ampoule"
    LOTION = "lotion"
    EMULSION = "emulsion"
    BALM = "balm"
    GEL = "gel"
    FOAM = "foam"
    SHAMPOO = "shampoo"
    CONDITIONER = "conditioner"
    TREATMENT = "treatment"
    OTHER = "other"


class SkinType(str, Enum):
    """Skin types for product compatibility."""

    DRY = "dry"
    OILY = "oily"
    COMBINATION = "combination"
    NORMAL = "normal"
    SENSITIVE = "sensitive"
    ALL = "all"


class SkinConcern(str, Enum):
    """Skin concerns that products can address."""

    ACNE = "acne"
    PORES = "pores"
    WRINKLES = "wrinkles"
    FINE_LINES = "fine_lines"
    DARK_SPOTS = "dark_spots"
    PIGMENTATION = "pigmentation"
    DULLNESS = "dullness"
    REDNESS = "redness"
    DRYNESS = "dryness"
    OILINESS = "oiliness"
    SAGGING = "sagging"
    ELASTICITY = "elasticity"
    UNEVEN_TONE = "uneven_tone"
    DARK_CIRCLES = "dark_circles"
    SENSITIVITY = "sensitivity"
    DEHYDRATION = "dehydration"
    BLACKHEADS = "blackheads"
    WHITEHEADS = "whiteheads"
    AGING = "aging"
    SUN_DAMAGE = "sun_damage"
    TEXTURE = "texture"
    BARRIER_DAMAGE = "barrier_damage"
    HAIR_LOSS = "hair_loss"
    DANDRUFF = "dandruff"
    SCALP_TROUBLE = "scalp_trouble"
    OTHER = "other"


class IngredientCategory(str, Enum):
    """Categories for cosmetic ingredients."""

    ACTIVE = "active"
    MOISTURIZING = "moisturizing"
    SOOTHING = "soothing"
    ANTIOXIDANT = "antioxidant"
    EXFOLIANT = "exfoliant"
    BRIGHTENING = "brightening"
    FIRMING = "firming"
    BARRIER = "barrier"
    ANTI_AGING = "anti_aging"
    HYDRATING = "hydrating"
    CLEANSING = "cleansing"
    OTHER = "other"


class TextureType(str, Enum):
    """Texture types for cosmetic products."""

    CREAM = "cream"
    GEL = "gel"
    SERUM = "serum"
    OIL = "oil"
    WATER = "water"
    MILK = "milk"
    BALM = "balm"
    FOAM = "foam"
    MOUSSE = "mousse"
    MIST = "mist"
    POWDER = "powder"
    STICK = "stick"
    SHEET = "sheet"
    PATCH = "patch"
    OTHER = "other"


class FinishType(str, Enum):
    """Finish types after product application."""

    MATTE = "matte"
    DEWY = "dewy"
    SATIN = "satin"
    NATURAL = "natural"
    LUMINOUS = "luminous"
    VELVET = "velvet"
    GLOSSY = "glossy"
    INVISIBLE = "invisible"


class CertificationType(str, Enum):
    """Certification types for cosmetic products."""

    VEGAN = "vegan"
    CRUELTY_FREE = "cruelty_free"
    ORGANIC = "organic"
    EWG_VERIFIED = "ewg_verified"
    DERMATOLOGIST_TESTED = "dermatologist_tested"
    HYPOALLERGENIC = "hypoallergenic"
    NON_COMEDOGENIC = "non_comedogenic"
    FRAGRANCE_FREE = "fragrance_free"
    PARABEN_FREE = "paraben_free"
    SULFATE_FREE = "sulfate_free"
    ALCOHOL_FREE = "alcohol_free"
    SILICONE_FREE = "silicone_free"
    CLINICAL_TESTED = "clinical_tested"
    KFDA_APPROVED = "kfda_approved"
    OTHER = "other"


# ========== Nested Schemas for Cosmetics ==========


class Ingredient(BaseModel):
    """Schema for a single cosmetic ingredient."""

    name: str = Field(..., min_length=1, max_length=100, description="Ingredient name (English)")
    name_ko: Optional[str] = Field(None, max_length=100, description="Korean ingredient name")
    effect: str = Field(..., min_length=1, max_length=500, description="Effect or benefit of this ingredient")
    category: Optional[IngredientCategory] = Field(IngredientCategory.OTHER, description="Ingredient category")
    concentration: Optional[str] = Field(None, max_length=50, description="Concentration (e.g., '5%', 'high')")
    is_hero: bool = Field(False, description="Is this a hero/featured ingredient?")


class Certification(BaseModel):
    """Schema for product certification."""

    name: CertificationType = Field(..., description="Certification type")
    grade: Optional[str] = Field(None, max_length=50, description="Grade or level (e.g., 'EWG Grade 1')")
    details: Optional[str] = Field(None, max_length=500, description="Additional certification details")
    badge_icon: Optional[str] = Field(None, max_length=100, description="Icon identifier for UI display")


class ClinicalResult(BaseModel):
    """Schema for clinical test results."""

    metric: str = Field(..., min_length=1, max_length=200, description="What was measured")
    result: str = Field(..., min_length=1, max_length=200, description="Quantified result (e.g., '89% improvement')")
    test_period: Optional[str] = Field(None, max_length=100, description="Duration of test (e.g., '4 weeks')")
    sample_size: Optional[int] = Field(None, ge=1, description="Number of participants")
    source: Optional[str] = Field(None, max_length=200, description="Testing organization or study reference")


# ========== Product Schemas ==========


class ProductBase(BaseModel):
    """Common product fields shared across create/update/response schemas."""

    name: str
    description: Optional[str] = None

    # Product Image
    image_url: Optional[str] = None
    image_description: Optional[str] = None

    # Cosmetics Category
    product_category: Optional[ProductCategory] = None

    # Key Ingredients (MVP)
    key_ingredients: list[Ingredient] = []

    # Skin Compatibility (MVP)
    suitable_skin_types: list[SkinType] = []
    skin_concerns: list[SkinConcern] = []

    # Texture & Sensory (MVP)
    texture_type: Optional[TextureType] = None
    finish_type: Optional[FinishType] = None

    # Certifications & Clinical (Phase 2)
    certifications: list[Certification] = []
    clinical_results: list[ClinicalResult] = []

    # Additional Info
    volume_ml: Optional[int] = None

    # Legacy fields (backward compatibility)
    features: list[str] = []
    benefits: list[str] = []
    price_range: Optional[str] = None
    target_segment: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema for creating a new product."""

    pass


class ProductUpdate(BaseModel):
    """Schema for updating an existing product. All fields are optional."""

    name: Optional[str] = None
    description: Optional[str] = None

    # Product Image
    image_url: Optional[str] = None
    image_description: Optional[str] = None

    # Cosmetics fields
    product_category: Optional[ProductCategory] = None
    key_ingredients: Optional[list[Ingredient]] = None
    suitable_skin_types: Optional[list[SkinType]] = None
    skin_concerns: Optional[list[SkinConcern]] = None
    texture_type: Optional[TextureType] = None
    finish_type: Optional[FinishType] = None
    certifications: Optional[list[Certification]] = None
    clinical_results: Optional[list[ClinicalResult]] = None
    volume_ml: Optional[int] = None

    # Legacy fields
    features: Optional[list[str]] = None
    benefits: Optional[list[str]] = None
    price_range: Optional[str] = None
    target_segment: Optional[str] = None


class ProductResponse(ProductBase):
    """Schema for product API responses. Includes all fields plus metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    brand_id: str
    created_at: str
    updated_at: str


# ========== Brand Schemas ==========


class BrandBase(BaseModel):
    """Common brand fields shared across create/update/response schemas."""

    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    target_audience: Optional[str] = None
    tone_and_manner: Optional[str] = None
    usp: Optional[str] = None
    keywords: list[str] = []
    industry: Optional[str] = None


class BrandCreate(BrandBase):
    """Schema for creating a new brand."""

    pass


class BrandUpdate(BaseModel):
    """Schema for updating an existing brand. All fields are optional."""

    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    target_audience: Optional[str] = None
    tone_and_manner: Optional[str] = None
    usp: Optional[str] = None
    keywords: Optional[list[str]] = None
    industry: Optional[str] = None


class BrandResponse(BrandBase):
    """Schema for brand API responses. Includes all fields plus metadata and products."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: str
    updated_at: str
    products: list[ProductResponse] = []


class BrandSummary(BaseModel):
    """Schema for brand list view. Includes product count instead of full products."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    target_audience: Optional[str] = None
    tone_and_manner: Optional[str] = None
    usp: Optional[str] = None
    keywords: list[str] = []
    industry: Optional[str] = None
    created_at: str
    updated_at: str
    product_count: int = 0
