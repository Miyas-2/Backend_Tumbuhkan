from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.repositories.sensor_repo import SensorRepository
from app.models.schemas.sensor import SensorResponse
from datetime import datetime
from typing import List, Optional

router = APIRouter()

@router.get("/latest", response_model=SensorResponse)
async def get_latest_sensor(db: AsyncSession = Depends(get_db)):
    """Get latest sensor reading"""
    repo = SensorRepository(db)
    sensor = await repo.get_latest()
    
    if not sensor:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    return sensor

@router.get("/history", response_model=List[SensorResponse])
async def get_sensor_history(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get sensor readings history with optional date filters"""
    repo = SensorRepository(db)
    sensors = await repo.get_history(start_date, end_date, limit, offset)
    return sensors

@router.get("/{sensor_id}", response_model=SensorResponse)
async def get_sensor_by_id(sensor_id: int, db: AsyncSession = Depends(get_db)):
    """Get sensor reading by ID"""
    repo = SensorRepository(db)
    sensor = await repo.get_by_id(sensor_id)
    
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor data not found")
    
    return sensor