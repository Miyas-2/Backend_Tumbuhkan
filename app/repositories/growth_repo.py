from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, cast, Float
from app.models.database.growth import GrowthLog
from app.models.schemas.growth import GrowthData
from typing import Optional, List
from datetime import datetime

# Minimum confidence threshold to filter out 0.0 results
MIN_CONFIDENCE = 0.01

class GrowthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, growth_data: GrowthData) -> GrowthLog:
        """Create new growth log"""
        db_growth = GrowthLog(**growth_data.model_dump())
        self.db.add(db_growth)
        await self.db.commit()
        await self.db.refresh(db_growth)
        return db_growth
    
    async def get_latest(self) -> Optional[GrowthLog]:
        """Get latest growth log with confidence > 0"""
        result = await self.db.execute(
            select(GrowthLog)
            .where(
                cast(GrowthLog.growth_stage['confidence'].astext, Float) > MIN_CONFIDENCE
            )
            .order_by(desc(GrowthLog.timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, growth_id: int) -> Optional[GrowthLog]:
        """Get growth log by ID"""
        result = await self.db.execute(
            select(GrowthLog).where(GrowthLog.id == growth_id)
        )
        return result.scalar_one_or_none()

    async def get_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[GrowthLog]:
        """Get growth logs history with filters (excludes confidence 0.0)"""
        query = select(GrowthLog).where(
            cast(GrowthLog.growth_stage['confidence'].astext, Float) > MIN_CONFIDENCE
        ).order_by(desc(GrowthLog.timestamp))
        
        if start_date:
            query = query.where(GrowthLog.timestamp >= start_date)
        if end_date:
            query = query.where(GrowthLog.timestamp <= end_date)
        
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()
