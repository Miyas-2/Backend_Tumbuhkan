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
    
    # Relay pumps (ON/OFF)
    ph_up = Column(Boolean, nullable=False, default=False)
    ab_mix = Column(Boolean, nullable=False, default=False)
    ph_down = Column(Boolean, nullable=False, default=False)
    pump = Column(Boolean, nullable=False, default=False)
    
    def __repr__(self):
        return f"<ActuatorLog(id={self.id}, timestamp={self.timestamp})>"