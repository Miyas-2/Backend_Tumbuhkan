"""
Prediction schemas for ML model responses.
"""
from pydantic import BaseModel
from typing import Optional


class GrowthDetectionRequest(BaseModel):
    """Request schema for growth detection with Base64 image"""
    image_base64: str


class GrowthDetectionResponse(BaseModel):
    """Response schema for growth detection"""
    success: bool
    growth_class: Optional[str] = None
    confidence: float = 0.0
    image_base64: Optional[str] = None


class DiseaseDetectionResponse(BaseModel):
    """Response schema for disease detection"""
    success: bool
    disease_class: Optional[str] = None
    confidence: float = 0.0
    image_base64: Optional[str] = None


class ModelStatusResponse(BaseModel):
    """Response schema for model status check"""
    growth_model_loaded: bool
    disease_model_loaded: bool
