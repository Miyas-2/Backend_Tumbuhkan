"""
Growth API endpoints for accessing growth logs data and stage configurations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.database import get_db
from app.repositories.growth_repo import GrowthRepository
from app.models.schemas.growth import GrowthResponse
from app.models.database.plant import GrowthStageConfig
from datetime import datetime
from typing import List, Optional

router = APIRouter()


# ============================================================
# Pydantic Schemas for GrowthStageConfig
# ============================================================

class GrowthConfigResponse(BaseModel):
    """Response schema for growth stage configuration"""
    id: int
    stage_name: str
    tds_target: float
    tds_tolerance: float
    ph_target: float
    ph_tolerance: float
    temp_threshold_high: float
    ldr_threshold_dark: int
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class GrowthConfigUpdate(BaseModel):
    """Update schema for growth stage configuration"""
    tds_target: Optional[float] = None
    tds_tolerance: Optional[float] = None
    ph_target: Optional[float] = None
    ph_tolerance: Optional[float] = None
    temp_threshold_high: Optional[float] = None
    ldr_threshold_dark: Optional[int] = None


# ============================================================
# Growth Logs Endpoints
# ============================================================

@router.get("/latest", response_model=GrowthResponse)
async def get_latest_growth(request: Request, db: AsyncSession = Depends(get_db)):
    """Get latest growth log from database
    
    Returns the most recent growth stage detection result with image URLs.
    """
    repo = GrowthRepository(db)
    growth = await repo.get_latest()
    
    if not growth:
        raise HTTPException(status_code=404, detail="No growth data found")
    
    # Construct full URLs for images
    base_url = str(request.base_url).rstrip("/")
    response = GrowthResponse.model_validate(growth)
    
    if growth.image_path:
        response.image_url = f"{base_url}/{growth.image_path}"
    if growth.annotated_image_path:
        response.annotated_image_url = f"{base_url}/{growth.annotated_image_path}"
    
    return response

@router.get("/history", response_model=List[GrowthResponse])
async def get_growth_history(
    request: Request,
    start_date: Optional[datetime] = Query(None, description="Filter start date"),
    end_date: Optional[datetime] = Query(None, description="Filter end date"),
    limit: int = Query(100, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """Get growth logs history with optional date filters
    
    Returns list of growth stage detections with image URLs.
    """
    repo = GrowthRepository(db)
    growth_logs = await repo.get_history(start_date, end_date, limit, offset)
    
    # Construct full URLs for images
    base_url = str(request.base_url).rstrip("/")
    results = []
    
    for growth in growth_logs:
        response = GrowthResponse.model_validate(growth)
        if growth.image_path:
            response.image_url = f"{base_url}/{growth.image_path}"
        if growth.annotated_image_path:
            response.annotated_image_url = f"{base_url}/{growth.annotated_image_path}"
        results.append(response)
    
    return results


# ============================================================
# Growth Stage Config Endpoints
# ============================================================

@router.get("/configs", response_model=List[GrowthConfigResponse])
async def get_all_growth_configs(db: AsyncSession = Depends(get_db)):
    """Get all growth stage configurations
    
    Returns automation thresholds for each growth stage.
    """
    result = await db.execute(
        select(GrowthStageConfig).order_by(GrowthStageConfig.stage_name)
    )
    configs = result.scalars().all()
    return configs

@router.get("/configs/{stage_name}", response_model=GrowthConfigResponse)
async def get_growth_config_by_stage(
    stage_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Get growth configuration by stage name
    
    Stage names: 'Stage 01: Early Growth', 'Stage 02: Leafy Growth', etc.
    """
    result = await db.execute(
        select(GrowthStageConfig).where(GrowthStageConfig.stage_name == stage_name)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Config for '{stage_name}' not found")
    
    return config

@router.put("/configs/{stage_name}", response_model=GrowthConfigResponse)
async def update_growth_config(
    stage_name: str,
    update_data: GrowthConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update growth stage configuration
    
    Update automation thresholds (TDS, pH targets, etc.) for a specific growth stage.
    """
    result = await db.execute(
        select(GrowthStageConfig).where(GrowthStageConfig.stage_name == stage_name)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Config for '{stage_name}' not found")
    
    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(config, field, value)
    
    config.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(config)
    
    return config


# ============================================================
# Growth Log by ID (must be last due to path conflict)
# ============================================================

@router.get("/{growth_id}", response_model=GrowthResponse)
async def get_growth_by_id(
    growth_id: int, 
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get growth log by ID"""
    repo = GrowthRepository(db)
    growth = await repo.get_by_id(growth_id)
    
    if not growth:
        raise HTTPException(status_code=404, detail="Growth data not found")
    
    # Construct full URLs for images
    base_url = str(request.base_url).rstrip("/")
    response = GrowthResponse.model_validate(growth)
    
    if growth.image_path:
        response.image_url = f"{base_url}/{growth.image_path}"
    if growth.annotated_image_path:
        response.annotated_image_url = f"{base_url}/{growth.annotated_image_path}"
    
    return response
