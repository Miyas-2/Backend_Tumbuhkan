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

class SensorSummary(BaseModel):
    """Schema untuk data agregasi sensor (average) - untuk Dashboard charts"""
    timestamp: datetime
    ph: float = 0
    ph_voltage: float = 0
    tds: float = 0
    tds_voltage: float = 0
    temp_air: float = 0
    temp_udara: float = 0
    humidity: float = 0
    ldr: int = 0
    distance: float = 0
    flow: float = 0