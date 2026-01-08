from sqlalchemy import Column, BigInteger, DateTime, Boolean, Integer, String
from datetime import datetime
from app.core.database import Base

class ActuatorLog(Base):
    __tablename__ = "actuator_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # LED & FAN (ON/OFF only)
    led = Column(String(10), nullable=True, default="OFF")
    fan = Column(String(10), nullable=True, default="OFF")
    
    # Relay pumps with duration (in ms)
    ph_up = Column(Boolean, nullable=False, default=False)
    ph_up_duration = Column(Integer, nullable=True, default=0)
    
    ab_mix = Column(Boolean, nullable=False, default=False)
    ab_mix_duration = Column(Integer, nullable=True, default=0)
    
    ph_down = Column(Boolean, nullable=False, default=False)
    ph_down_duration = Column(Integer, nullable=True, default=0)
    
    pump = Column(Boolean, nullable=False, default=False)
    pump_duration = Column(Integer, nullable=True, default=0)
    
    def __repr__(self):
        return f"<ActuatorLog(id={self.id}, timestamp={self.timestamp})>"