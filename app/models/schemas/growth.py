from pydantic import BaseModel
from typing import Optional, Dict, Any, Union
from datetime import datetime

class GrowthData(BaseModel):
    """Schema for growth stage data from ML model"""
    growth_stage: Union[Dict[str, Any], str]
    image_path: Optional[str] = None
    annotated_image_path: Optional[str] = None

class GrowthResponse(GrowthData):
    """Schema for growth data response"""
    id: int
    timestamp: datetime
    # Full URLs for frontend (constructed in endpoint)
    image_url: Optional[str] = None
    annotated_image_url: Optional[str] = None
    
    class Config:
        from_attributes = True
