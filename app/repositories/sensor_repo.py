from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.database.sensor import SensorReading
from app.models.schemas.sensor import SensorData
from datetime import datetime
from typing import Optional, List

class SensorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, sensor_data: SensorData) -> SensorReading:
        """Create new sensor reading"""
        db_sensor = SensorReading(**sensor_data.model_dump())
        self.db.add(db_sensor)
        await self.db.commit()
        await self.db.refresh(db_sensor)
        return db_sensor
    
    async def get_latest(self) -> Optional[SensorReading]:
        """Get latest sensor reading"""
        result = await self.db.execute(
            select(SensorReading).order_by(desc(SensorReading.timestamp)).limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, sensor_id: int) -> Optional[SensorReading]:
        """Get sensor reading by ID"""
        result = await self.db.execute(
            select(SensorReading).where(SensorReading.id == sensor_id)
        )
        return result.scalar_one_or_none()
    
    async def get_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SensorReading]:
        """Get sensor readings history with filters"""
        query = select(SensorReading).order_by(desc(SensorReading.timestamp))
        
        if start_date:
            query = query.where(SensorReading.timestamp >= start_date)
        if end_date:
            query = query.where(SensorReading.timestamp <= end_date)
        
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_latest_growth(self) -> Optional[dict]:
        """Get latest growth stage info (where growth_stage is not null)"""
        result = await self.db.execute(
            select(SensorReading.growth_stage)
            .where(SensorReading.growth_stage.is_not(None))
            .order_by(desc(SensorReading.timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()