from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.database.growth import GrowthLog
from app.models.schemas.growth import GrowthData
from typing import Optional, List
from datetime import datetime

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
        """Get latest growth log"""
        result = await self.db.execute(
            select(GrowthLog).order_by(desc(GrowthLog.timestamp)).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[GrowthLog]:
        """Get growth logs history with filters"""
        query = select(GrowthLog).order_by(desc(GrowthLog.timestamp))
        
        if start_date:
            query = query.where(GrowthLog.timestamp >= start_date)
        if end_date:
            query = query.where(GrowthLog.timestamp <= end_date)
        
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()
