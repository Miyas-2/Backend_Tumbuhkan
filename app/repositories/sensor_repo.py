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

    async def get_aggregated_history(
        self,
        period: str = "day"  # day, week, month
    ) -> List[dict]:
        """Get aggregated sensor data for Dashboard charts
        
        Args:
            period: 'day' (10min buckets), 'week' (4hr buckets), 'month' (daily buckets)
        
        Returns:
            List of dicts with averaged sensor values grouped by time bucket
        """
        from sqlalchemy import func, text, literal_column
        
        # Define bucket width in seconds and total interval
        if period == "day":
            # Last 24 hours, grouped by 10 minutes (600 seconds)
            interval_seconds = 600
            pg_interval = "24 hours"
        elif period == "week":
            # Last 7 days, grouped by 4 hours (14400 seconds)
            interval_seconds = 14400
            pg_interval = "7 days"
        elif period == "month":
            # Last 30 days, grouped by 1 day (86400 seconds)
            interval_seconds = 86400
            pg_interval = "30 days"
        else:
            raise ValueError("Invalid period. Use: day, week, month")

        # Postgres Epoch-based grouping
        bucket_sql = f"to_timestamp(floor(extract('epoch' from timestamp) / {interval_seconds}) * {interval_seconds})"
        trunc_col = literal_column(bucket_sql).label("time_bucket")
        
        query = (
            select(
                trunc_col,
                func.avg(SensorReading.ph).label("avg_ph"),
                func.avg(SensorReading.ph_voltage).label("avg_ph_voltage"),
                func.avg(SensorReading.tds).label("avg_tds"),
                func.avg(SensorReading.tds_voltage).label("avg_tds_voltage"),
                func.avg(SensorReading.temp_air).label("avg_temp_air"),
                func.avg(SensorReading.temp_udara).label("avg_temp_udara"),
                func.avg(SensorReading.humidity).label("avg_humidity"),
                func.avg(SensorReading.ldr).label("avg_ldr"),
                func.avg(SensorReading.distance).label("avg_distance"),
                func.avg(SensorReading.flow).label("avg_flow")
            )
            .where(
                SensorReading.timestamp >= text(f"NOW() - INTERVAL '{pg_interval}'")
            )
            .group_by(trunc_col)
            .order_by(trunc_col)
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        # Convert to list of dicts
        data = []
        for row in rows:
            data.append({
                "timestamp": row.time_bucket,
                "ph": round(row.avg_ph, 2) if row.avg_ph else 0,
                "ph_voltage": round(row.avg_ph_voltage, 2) if row.avg_ph_voltage else 0,
                "tds": round(row.avg_tds, 2) if row.avg_tds else 0,
                "tds_voltage": round(row.avg_tds_voltage, 2) if row.avg_tds_voltage else 0,
                "temp_air": round(row.avg_temp_air, 2) if row.avg_temp_air else 0,
                "temp_udara": round(row.avg_temp_udara, 2) if row.avg_temp_udara else 0,
                "humidity": round(row.avg_humidity, 2) if row.avg_humidity else 0,
                "ldr": int(row.avg_ldr) if row.avg_ldr else 0,
                "distance": round(row.avg_distance, 2) if row.avg_distance else 0,
                "flow": round(row.avg_flow, 2) if row.avg_flow else 0
            })
            
        return data