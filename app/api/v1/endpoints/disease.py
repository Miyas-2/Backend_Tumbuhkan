"""
Disease API endpoints for accessing disease detection logs.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.repositories.disease_repo import DiseaseRepository
from app.models.schemas.disease import DiseaseResponse
from datetime import datetime
from typing import List, Optional

router = APIRouter()


@router.get("/latest", response_model=DiseaseResponse)
async def get_latest_disease(request: Request, db: AsyncSession = Depends(get_db)):
    """Get latest disease detection log from database
    
    Returns the most recent disease detection result with image URLs.
    """
    repo = DiseaseRepository(db)
    disease = await repo.get_latest()
    
    if not disease:
        raise HTTPException(status_code=404, detail="No disease data found")
    
    # Construct full URLs for images
    base_url = str(request.base_url).rstrip("/")
    response = DiseaseResponse.model_validate(disease)
    
    if disease.image_path:
        response.image_url = f"{base_url}/{disease.image_path}"
    if disease.annotated_image_path:
        response.annotated_image_url = f"{base_url}/{disease.annotated_image_path}"
    
    return response


@router.get("/history", response_model=List[DiseaseResponse])
async def get_disease_history(
    request: Request,
    start_date: Optional[datetime] = Query(None, description="Filter start date"),
    end_date: Optional[datetime] = Query(None, description="Filter end date"),
    limit: int = Query(100, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """Get disease detection logs history with optional date filters
    
    Returns list of disease detections with image URLs.
    """
    repo = DiseaseRepository(db)
    disease_logs = await repo.get_history(start_date, end_date, limit, offset)
    
    # Construct full URLs for images
    base_url = str(request.base_url).rstrip("/")
    results = []
    
    for disease in disease_logs:
        response = DiseaseResponse.model_validate(disease)
        if disease.image_path:
            response.image_url = f"{base_url}/{disease.image_path}"
        if disease.annotated_image_path:
            response.annotated_image_url = f"{base_url}/{disease.annotated_image_path}"
        results.append(response)
    
    return results


@router.get("/by-class/{disease_class}", response_model=List[DiseaseResponse])
async def get_disease_by_class(
    disease_class: str,
    request: Request,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get disease logs filtered by disease class
    
    Available classes: Bacterial, Downy_mildew_on_lettuce, Powdery_mildew_on_lettuce,
    Septoria_Blight_on_lettuce, Viral, Wilt_and_leaf_blight_on_lettuce, healthy
    """
    repo = DiseaseRepository(db)
    disease_logs = await repo.get_by_disease_class(disease_class, limit)
    
    # Construct full URLs for images
    base_url = str(request.base_url).rstrip("/")
    results = []
    
    for disease in disease_logs:
        response = DiseaseResponse.model_validate(disease)
        if disease.image_path:
            response.image_url = f"{base_url}/{disease.image_path}"
        if disease.annotated_image_path:
            response.annotated_image_url = f"{base_url}/{disease.annotated_image_path}"
        results.append(response)
    
    return results


@router.get("/{disease_id}", response_model=DiseaseResponse)
async def get_disease_by_id(
    disease_id: int, 
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get disease log by ID"""
    repo = DiseaseRepository(db)
    disease = await repo.get_by_id(disease_id)
    
    if not disease:
        raise HTTPException(status_code=404, detail="Disease data not found")
    
    # Construct full URLs for images
    base_url = str(request.base_url).rstrip("/")
    response = DiseaseResponse.model_validate(disease)
    
    if disease.image_path:
        response.image_url = f"{base_url}/{disease.image_path}"
    if disease.annotated_image_path:
        response.annotated_image_url = f"{base_url}/{disease.annotated_image_path}"
    
    return response
