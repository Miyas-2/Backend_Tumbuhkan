from sqlalchemy import Column, BigInteger, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.core.database import Base

class GrowthLog(Base):
    __tablename__ = "growth_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Growth stage from ML model (YOLO v8n) - Stores {growth_class, confidence}
    growth_stage = Column(JSONB, nullable=True)
    
    # Image paths
    image_path = Column(String(255), nullable=True)
    annotated_image_path = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<GrowthLog(id={self.id}, timestamp={self.timestamp})>"
