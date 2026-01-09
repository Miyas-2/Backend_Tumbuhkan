from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, Union

class SensorData(BaseModel):
    """Schema untuk data sensor dari MQTT (sesuai format ESP32)"""
    ph: Optional[float] = None
    ph_voltage: Optional[float] = None
    tds: Optional[float] = None
    tds_voltage: Optional[float] = None
    temp_air: Optional[float] = None       # DS18B20 - water temperature
    temp_udara: Optional[float] = None     # DHT22 - air temperature
    humidity: Optional[float] = None
    ldr: Optional[int] = None
    distance: Optional[float] = None
    flow: Optional[float] = None
    image_path: Optional[str] = None       # Path to raw image
    annotated_image_path: Optional[str] = None # Path to annotated image
    growth_stage: Optional[Union[Dict[str, Any], str]] = None     # Growth stage from ML model

class SensorResponse(SensorData):
    """Schema untuk response sensor data"""
    id: int
    timestamp: datetime
    image_url: Optional[str] = None        # Full URL to annotated image
    
    class Config:
        from_attributes = True

class SensorHistoryQuery(BaseModel):
    """Query parameters untuk history"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)