from pydantic import BaseModel
from datetime import datetime

class ActuatorStatus(BaseModel):
    """Schema untuk status actuator dari MQTT"""
    pump_nutrisi_A: bool = False
    pump_nutrisi_B: bool = False
    pump_Ph_Up: bool = False
    pump_Ph_Down: bool = False
    fan: bool = False
    led: bool = False

class ActuatorControl(ActuatorStatus):
    """Schema untuk kontrol actuator"""
    pass

class ActuatorResponse(ActuatorStatus):
    """Schema untuk response actuator data"""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True