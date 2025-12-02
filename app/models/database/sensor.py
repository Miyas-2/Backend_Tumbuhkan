from sqlalchemy import Column, BigInteger, DateTime, Float, Integer
from datetime import datetime
from app.core.database import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # water quality sensors
    ph = Column(Float, nullable=True)
    tds = Column(Integer, nullable=True)
    water_flow = Column(Float, nullable=True)
    
    # Air sensors
    air_humidity = Column(Float, nullable=True)
    air_temperature = Column(Float, nullable=True)
    
    ldr_value = Column(Integer, nullable=True)
    water_temperature = Column(Float, nullable=True)
    water_level = Column(Float, nullable=True)
    
def __repr__(self):
        return f"<SensorReading(id={self.id}, timestamp={self.timestamp})>"
    