from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal

class LedFanControl(BaseModel):
    state: Literal["ON", "OFF"]

class PumpControl(BaseModel):
    duration: int = 0

class RelayControlRequest(BaseModel):
    """Schema untuk request kontrol relay ke ESP32"""
    LED: Optional[LedFanControl] = None
    FAN: Optional[LedFanControl] = None
    PUMP: Optional[PumpControl] = None
    PH_UP: Optional[PumpControl] = None
    PH_DOWN: Optional[PumpControl] = None
    AB_MIX: Optional[PumpControl] = None

class ActuatorStatus(BaseModel):
    """Schema untuk status actuator dari MQTT (response dari ESP32)"""
    LED: str = "OFF"
    FAN: str = "OFF"
    PH_UP: str = "OFF"
    AB_MIX: str = "OFF"
    PH_DOWN: str = "OFF"
    PUMP: str = "OFF"

class ActuatorLogCreate(BaseModel):
    """Schema untuk menyimpan log actuator ke database"""
    led: str = "OFF"
    fan: str = "OFF"
    ph_up: bool = False
    ab_mix: bool = False
    ph_down: bool = False
    pump: bool = False

class ActuatorResponse(BaseModel):
    """Schema untuk response actuator data dari database"""
    id: int
    timestamp: datetime
    led: str
    fan: str
    ph_up: bool
    ab_mix: bool
    ph_down: bool
    pump: bool
    
    class Config:
        from_attributes = True