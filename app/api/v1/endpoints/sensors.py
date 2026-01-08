from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.repositories.sensor_repo import SensorRepository
from app.models.schemas.sensor import SensorResponse, SensorData
from app.services.mqtt_service import mqtt_service
from datetime import datetime
from typing import List, Optional

router = APIRouter()

@router.get("/live")
async def get_live_sensor():
    """Get real-time sensor data from MQTT memory (not database)
    
    Data ini langsung dari ESP32 via MQTT, belum disimpan ke database.
    Untuk data yang sudah tersimpan, gunakan /latest atau /history.
    """
    sensor = mqtt_service.get_latest_sensor()
    
    if not sensor:
        return {
            "status": "no_data",
            "message": "No sensor data received yet from ESP32",
            "data": None
        }
    
    return {
        "status": "success",
        "message": "Live sensor data from MQTT",
        "data": sensor.model_dump()
    }

@router.get("/latest", response_model=SensorResponse)
async def get_latest_sensor(request: Request, db: AsyncSession = Depends(get_db)):
    """Get latest sensor reading from database"""
    repo = SensorRepository(db)
    sensor = await repo.get_latest()
    
    if not sensor:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    # Construct full URL for image if exists
    if sensor.annotated_image_path:
        base_url = str(request.base_url).rstrip("/")
        sensor.image_url = f"{base_url}/{sensor.annotated_image_path}"
    
    return sensor

@router.get("/history", response_model=List[SensorResponse])
async def get_sensor_history(
    request: Request,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get sensor readings history with optional date filters"""
    repo = SensorRepository(db)
    sensors = await repo.get_history(start_date, end_date, limit, offset)
    
    # Construct full URL for images
    base_url = str(request.base_url).rstrip("/")
    for sensor in sensors:
        if sensor.annotated_image_path:
            sensor.image_url = f"{base_url}/{sensor.annotated_image_path}"
            
    return sensors

@router.get("/{sensor_id}", response_model=SensorResponse)
async def get_sensor_by_id(sensor_id: int, db: AsyncSession = Depends(get_db)):
    """Get sensor reading by ID"""
    repo = SensorRepository(db)
    sensor = await repo.get_by_id(sensor_id)
    
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor data not found")
    
    return sensor