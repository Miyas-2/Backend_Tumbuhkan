from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.repositories.actuator_repo import ActuatorRepository
from app.models.schemas.actuator import (
    ActuatorResponse, 
    RelayControlRequest, 
    RelayControl,
    ActuatorLogCreate,
    ActuatorStatus
)
from app.services.mqtt_service import mqtt_service
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()

# ============================================================
#                    RESPONSE SCHEMAS
# ============================================================

class RelayControlResponse(BaseModel):
    status: str
    message: str
    data: dict

class LatestStatusResponse(BaseModel):
    status: str
    from_mqtt: bool
    data: Optional[ActuatorStatus] = None
    from_database: Optional[ActuatorResponse] = None

# ============================================================
#                    RELAY CONTROL ENDPOINTS
# ============================================================

@router.post("/control", response_model=RelayControlResponse)
async def control_relay(
    relay_control: RelayControlRequest,
    db: AsyncSession = Depends(get_db)
):
    """Control relay via MQTT
    
    Flow: Frontend -> API -> MQTT -> ESP32
    
    Contoh request:
    ```json
    {
        "LED": {"state": "ON"},
        "FAN": {"state": "OFF"},
        "PH_UP": {"duration": 5000},
        "PUMP": {"duration": 10000}
    }
    ```
    
    Catatan:
    - LED dan FAN menggunakan state "ON"/"OFF"
    - PH_UP, AB_MIX, PH_DOWN, PUMP menggunakan duration dalam milliseconds
    """
    # Publish to MQTT
    success = mqtt_service.publish_relay_control(relay_control)
    
    if not success:
        raise HTTPException(
            status_code=500, 
            detail="Failed to publish relay control to MQTT"
        )
    
    # Save to database for logging
    try:
        repo = ActuatorRepository(db)
        log_data = ActuatorLogCreate(
            led=relay_control.LED.state if relay_control.LED else "OFF",
            fan=relay_control.FAN.state if relay_control.FAN else "OFF",
            ph_up=relay_control.PH_UP is not None and relay_control.PH_UP.duration > 0,
            ph_up_duration=relay_control.PH_UP.duration if relay_control.PH_UP else 0,
            ab_mix=relay_control.AB_MIX is not None and relay_control.AB_MIX.duration > 0,
            ab_mix_duration=relay_control.AB_MIX.duration if relay_control.AB_MIX else 0,
            ph_down=relay_control.PH_DOWN is not None and relay_control.PH_DOWN.duration > 0,
            ph_down_duration=relay_control.PH_DOWN.duration if relay_control.PH_DOWN else 0,
            pump=relay_control.PUMP is not None and relay_control.PUMP.duration > 0,
            pump_duration=relay_control.PUMP.duration if relay_control.PUMP else 0
        )
        await repo.create(log_data)
    except Exception as e:
        print(f"⚠️ Failed to log actuator control: {e}")
    
    return RelayControlResponse(
        status="success",
        message="Relay control command sent to ESP32",
        data=relay_control.model_dump(exclude_none=True)
    )

@router.post("/led/{state}")
async def control_led(
    state: str,
    db: AsyncSession = Depends(get_db)
):
    """Quick control for LED (ON/OFF)"""
    if state.upper() not in ["ON", "OFF"]:
        raise HTTPException(status_code=400, detail="State must be 'ON' or 'OFF'")
    
    relay_control = RelayControlRequest(
        LED=RelayControl(state=state.upper())
    )
    
    success = mqtt_service.publish_relay_control(relay_control)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to control LED")
    
    return {"status": "success", "led": state.upper()}

@router.post("/fan/{state}")
async def control_fan(
    state: str,
    db: AsyncSession = Depends(get_db)
):
    """Quick control for FAN (ON/OFF)"""
    if state.upper() not in ["ON", "OFF"]:
        raise HTTPException(status_code=400, detail="State must be 'ON' or 'OFF'")
    
    relay_control = RelayControlRequest(
        FAN=RelayControl(state=state.upper())
    )
    
    success = mqtt_service.publish_relay_control(relay_control)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to control FAN")
    
    return {"status": "success", "fan": state.upper()}

@router.post("/pump/{pump_name}/{duration}")
async def control_pump(
    pump_name: str,
    duration: int,
    db: AsyncSession = Depends(get_db)
):
    """Control pump relays with duration
    
    Args:
        pump_name: PH_UP, AB_MIX, PH_DOWN, or PUMP
        duration: Duration in milliseconds
    """
    pump_name = pump_name.upper()
    valid_pumps = ["PH_UP", "AB_MIX", "PH_DOWN", "PUMP"]
    
    if pump_name not in valid_pumps:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid pump name. Must be one of: {valid_pumps}"
        )
    
    if duration <= 0:
        raise HTTPException(
            status_code=400, 
            detail="Duration must be greater than 0"
        )
    
    # Build relay control request dynamically
    relay_control_data = {pump_name: RelayControl(duration=duration)}
    relay_control = RelayControlRequest(**relay_control_data)
    
    success = mqtt_service.publish_relay_control(relay_control)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to control {pump_name}")
    
    return {
        "status": "success", 
        "pump": pump_name, 
        "duration_ms": duration
    }

# ============================================================
#                    STATUS ENDPOINTS
# ============================================================

@router.get("/status/live")
async def get_live_status():
    """Get real-time actuator status from MQTT memory (not database)"""
    status = mqtt_service.get_latest_actuator_status()
    
    if not status:
        return {
            "status": "no_data",
            "message": "No actuator status received yet from ESP32",
            "data": None
        }
    
    return {
        "status": "success",
        "message": "Live status from MQTT",
        "data": status.model_dump()
    }

@router.get("/latest", response_model=ActuatorResponse)
async def get_latest_actuator(db: AsyncSession = Depends(get_db)):
    """Get latest actuator status from database"""
    repo = ActuatorRepository(db)
    actuator = await repo.get_latest()
    
    if not actuator:
        raise HTTPException(status_code=404, detail="No actuator data found")
    
    return actuator

@router.get("/history", response_model=List[ActuatorResponse])
async def get_actuator_history(
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get actuator logs history from database"""
    repo = ActuatorRepository(db)
    actuators = await repo.get_history(limit, offset)
    return actuators