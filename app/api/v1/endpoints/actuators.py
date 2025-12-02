from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.repositories.actuator_repo import ActuatorRepository
from app.models.schemas.actuator import ActuatorResponse, ActuatorControl
from app.services.mqtt_service import mqtt_service
from typing import List

router = APIRouter()

@router.get("/latest", response_model=ActuatorResponse)
async def get_latest_actuator(db: AsyncSession = Depends(get_db)):
    """Get latest actuator status"""
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
    """Get actuator logs history"""
    repo = ActuatorRepository(db)
    actuators = await repo.get_history(limit, offset)
    return actuators

@router.post("/control")
async def control_actuator(
    actuator_control: ActuatorControl,
    db: AsyncSession = Depends(get_db)
):
    """Control actuator - publish to MQTT"""
    success = mqtt_service.publish_actuator_control(actuator_control)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to publish actuator control")
    
    # Save to database
    repo = ActuatorRepository(db)
    await repo.create(actuator_control)
    
    return {
        "status": "success",
        "message": "Actuator control sent",
        "data": actuator_control.model_dump()
    }