from fastapi import FastAPI
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import asyncio
import socket
from app.core.config import get_settings
from app.core.database import create_tables, init_growth_configs
from app.api.v1.router import api_router
from app.services.mqtt_service import mqtt_service
from app.services.automation_service import automation_service

settings = get_settings()

def get_local_ip():
    """Get local IP address for network access"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    local_ip = get_local_ip()
    print("\n" + "=" * 60)
    print("TUMBUHKAN BACKEND SERVER")
    print("=" * 60)
    print(f"Local IP Address: {local_ip}")
    print(f"Server URL: http://{local_ip}:8000")
    print(f"API Docs: http://{local_ip}:8000/docs")
    print(f"Dashboard: http://{local_ip}:8000/dashboard")
    print("=" * 60 + "\n")
    
    print("Creating database tables...")
    await create_tables()
    await init_growth_configs()
    print("Database tables created!")
    
    # Set event loop untuk MQTT service
    loop = asyncio.get_event_loop()
    mqtt_service.set_event_loop(loop)
    
    print("Connecting to MQTT broker...")
    mqtt_service.connect()
    
    # Start Automation Service
    # automation_service.start()
    
    yield
    
    # Shutdown
    print("Shutting down...")
    await automation_service.stop()
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
os.makedirs("app/static/images/growth/raw", exist_ok=True)
os.makedirs("app/static/images/growth/annotated", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/dashboard")
async def dashboard():
    """Web Dashboard for monitoring sensors and charts"""
    return FileResponse("app/static/dashboard.html")

@app.get("/")
async def root():
    return {
        "message": "Tumbuhkan Backend API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "dashboard": "/dashboard",
        "mqtt_connected": mqtt_service.connected
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mqtt_connected": mqtt_service.connected
    }