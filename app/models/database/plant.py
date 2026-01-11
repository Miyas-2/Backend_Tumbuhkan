from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.core.database import Base

class GrowthStageConfig(Base):
    __tablename__ = "growth_stage_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Must match the string from ML classification
    stage_name = Column(String(100), unique=True, nullable=False)
    
    # Target values
    tds_target = Column(Float, nullable=False)
    tds_tolerance = Column(Float, default=50.0)
    
    ph_target = Column(Float, nullable=False)
    ph_tolerance = Column(Float, default=0.2)
    
    temp_threshold_high = Column(Float, default=30.0)
    ldr_threshold_dark = Column(Integer, default=500)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GrowthConfig(stage={self.stage_name}, tds={self.tds_target})>"
