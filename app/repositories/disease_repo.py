from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, cast, Float
from app.models.database.disease import DiseaseLog
from app.models.schemas.disease import DiseaseData
from typing import Optional, List
from datetime import datetime

# Minimum confidence threshold to filter out 0.0 results
MIN_CONFIDENCE = 0.01

class DiseaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, disease_data: DiseaseData) -> DiseaseLog:
        """Create new disease log"""
        db_disease = DiseaseLog(**disease_data.model_dump())
        self.db.add(db_disease)
        await self.db.commit()
        await self.db.refresh(db_disease)
        return db_disease
    
    async def get_latest(self) -> Optional[DiseaseLog]:
        """Get latest disease log with confidence > 0"""
        result = await self.db.execute(
            select(DiseaseLog)
            .where(
                cast(DiseaseLog.disease_result['confidence'].astext, Float) > MIN_CONFIDENCE
            )
            .order_by(desc(DiseaseLog.timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, disease_id: int) -> Optional[DiseaseLog]:
        """Get disease log by ID"""
        result = await self.db.execute(
            select(DiseaseLog).where(DiseaseLog.id == disease_id)
        )
        return result.scalar_one_or_none()

    async def get_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DiseaseLog]:
        """Get disease logs history with filters (excludes confidence 0.0)"""
        query = select(DiseaseLog).where(
            cast(DiseaseLog.disease_result['confidence'].astext, Float) > MIN_CONFIDENCE
        ).order_by(desc(DiseaseLog.timestamp))
        
        if start_date:
            query = query.where(DiseaseLog.timestamp >= start_date)
        if end_date:
            query = query.where(DiseaseLog.timestamp <= end_date)
        
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_disease_class(
        self,
        disease_class: str,
        limit: int = 50
    ) -> List[DiseaseLog]:
        """Get disease logs filtered by disease class (excludes confidence 0.0)"""
        query = (
            select(DiseaseLog)
            .where(
                and_(
                    DiseaseLog.disease_result['disease_class'].astext == disease_class,
                    cast(DiseaseLog.disease_result['confidence'].astext, Float) > MIN_CONFIDENCE
                )
            )
            .order_by(desc(DiseaseLog.timestamp))
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
