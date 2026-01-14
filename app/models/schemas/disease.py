from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class DiseaseData(BaseModel):
    """Schema for disease detection data from ML model"""
    disease_result: Dict[str, Any]
    image_path: Optional[str] = None
    annotated_image_path: Optional[str] = None

class DiseaseResponse(DiseaseData):
    """Schema for disease log response"""
    id: int
    timestamp: datetime
    # Full URLs for frontend (constructed in endpoint)
    image_url: Optional[str] = None
    annotated_image_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class DiseaseDetectionResult(BaseModel):
    """Schema for ML prediction result (used by cv_service)"""
    disease_class: str
    confidence: float
    is_healthy: bool = False
    annotated_image_base64: Optional[str] = None
