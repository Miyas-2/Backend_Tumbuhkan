from sqlalchemy import Column, BigInteger, DateTime, Float, Integer, String
from datetime import datetime
from app.core.database import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    
    # pH sensor
    ph = Column(Float, nullable=True)
    ph_voltage = Column(Float, nullable=True)
    
    # TDS sensor
    tds = Column(Float, nullable=True)
    tds_voltage = Column(Float, nullable=True)
    
    # Temperature sensors
    temp_air = Column(Float, nullable=True)      # DS18B20 - water temperature
    temp_udara = Column(Float, nullable=True)    # DHT22 - air temperature
    
    # Humidity (DHT22)
    humidity = Column(Float, nullable=True)
    
    # LDR sensor
    ldr = Column(Integer, nullable=True)
    
    # Ultrasonic distance sensor
    distance = Column(Float, nullable=True)
    
    # Flow sensor
    flow = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<SensorReading(id={self.id}, timestamp={self.timestamp})>"