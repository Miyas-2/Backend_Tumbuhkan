from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class SensorData(BaseModel):
    """Schema untuk data sensor dari MQTT"""
    ph: Optional[float] = None
    tds: Optional[float] = None
    water_flow: Optional[float] = None
    air_temperature: Optional[float] = None
    air_humidity: Optional[float] = None
    ldr_value: Optional[int] = None
    water_temperature: Optional[float] = None
    water_level: Optional[float] = None

class SensorResponse(SensorData):
    """Schema untuk response sensor data"""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class SensorHistoryQuery(BaseModel):
    """Query parameters untuk history"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)