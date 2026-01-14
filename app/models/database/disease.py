from sqlalchemy import Column, BigInteger, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.core.database import Base

class DiseaseLog(Base):
    __tablename__ = "disease_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    
    # Disease detection result from ML model (YOLO v11n)
    # Stores {disease_class, confidence, is_healthy}
    disease_result = Column(JSONB, nullable=True)
    
    # Image paths
    image_path = Column(String(255), nullable=True)
    annotated_image_path = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<DiseaseLog(id={self.id}, timestamp={self.timestamp})>"
