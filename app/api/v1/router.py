from fastapi import APIRouter
from app.api.v1.endpoints import sensors, actuators

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(sensors.router, prefix="/sensors", tags=["Sensors"])
api_router.include_router(actuators.router, prefix="/actuators", tags=["Actuators"])