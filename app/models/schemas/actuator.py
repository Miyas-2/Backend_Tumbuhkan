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
    ph_up_duration: int = 0
    ab_mix: bool = False
    ab_mix_duration: int = 0
    ph_down: bool = False
    ph_down_duration: int = 0
    pump: bool = False
    pump_duration: int = 0

class ActuatorResponse(BaseModel):
    """Schema untuk response actuator data dari database"""
    id: int
    timestamp: datetime
    led: str
    fan: str
    ph_up: bool
    ph_up_duration: int
    ab_mix: bool
    ab_mix_duration: int
    ph_down: bool
    ph_down_duration: int
    pump: bool
    pump_duration: int
    
    class Config:
        from_attributes = True