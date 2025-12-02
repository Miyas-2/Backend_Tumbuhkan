from sqlalchemy import Column, BigInteger, DateTime, Boolean
from datetime import datetime
from app.core.database import Base

class ActuatorLog(Base):
    __tablename__ = "actuator_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Pumps
    pump_nutrisi_A = Column(Boolean, nullable=False, default=False)
    pump_nutrisi_B = Column(Boolean, nullable=False, default=False)
    pump_Ph_Up = Column(Boolean, nullable=False, default=False)
    pump_Ph_Down = Column(Boolean, nullable=False, default=False)
    
    # Other actuators
    fan = Column(Boolean, nullable=False, default=False)
    led = Column(Boolean, nullable=False, default=False)
    
    def __repr__(self):
        return f"<ActuatorLog(id={self.id}, timestamp={self.timestamp})>"