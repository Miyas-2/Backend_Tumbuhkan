from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
from app.core.config import get_settings
from app.core.database import create_tables
from app.api.v1.router import api_router
from app.services.mqtt_service import mqtt_service

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Creating database tables...")
    await create_tables()
    print("✅ Database tables created!")
    
    # Set event loop untuk MQTT service
    loop = asyncio.get_event_loop()
    mqtt_service.set_event_loop(loop)
    
    print("📡 Connecting to MQTT broker...")
    mqtt_service.connect()
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")
    mqtt_service.disconnect()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Include API router
app.include_router(api_router, prefix=settings.API_PREFIX)

# Mount static files
from fastapi.staticfiles import StaticFiles
import os

# Create static directory if not exists
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def root():
    return {
        "message": "Tumbuhkan Backend API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "mqtt_connected": mqtt_service.connected
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mqtt_connected": mqtt_service.connected
    }