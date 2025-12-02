from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.database.actuator import ActuatorLog
from app.models.schemas.actuator import ActuatorStatus
from typing import Optional, List

class ActuatorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, actuator_data: ActuatorStatus) -> ActuatorLog:
        """Create new actuator log"""
        db_actuator = ActuatorLog(**actuator_data.model_dump())
        self.db.add(db_actuator)
        await self.db.commit()
        await self.db.refresh(db_actuator)
        return db_actuator
    
    async def get_latest(self) -> Optional[ActuatorLog]:
        """Get latest actuator status"""
        result = await self.db.execute(
            select(ActuatorLog).order_by(desc(ActuatorLog.timestamp)).limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_history(self, limit: int = 100, offset: int = 0) -> List[ActuatorLog]:
        """Get actuator logs history"""
        result = await self.db.execute(
            select(ActuatorLog)
            .order_by(desc(ActuatorLog.timestamp))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()