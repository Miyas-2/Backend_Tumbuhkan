"""
Prediction API endpoints for ML model inference.
- Growth detection: ESP32-CAM → YOLO v8n → Save to DB
- Disease detection: Flutter app → YOLO v11n → Return result (no DB)
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.services.ml_service import growth_detection_service
from app.services.cv_service import disease_detection_service
from app.repositories.growth_repo import GrowthRepository
from app.models.schemas.growth import GrowthData
from app.models.schemas.prediction import (
    GrowthDetectionRequest,
    GrowthDetectionResponse,
    DiseaseDetectionResponse,
    ModelStatusResponse
)

router = APIRouter()


@router.get("/status", response_model=ModelStatusResponse)
async def get_model_status():
    """Check if ML models are loaded and ready"""
    return ModelStatusResponse(
        growth_model_loaded=growth_detection_service.is_model_loaded(),
        disease_model_loaded=disease_detection_service.is_model_loaded()
    )


@router.post("/growth/detect", response_model=GrowthDetectionResponse)
async def detect_growth_from_file(
    file: UploadFile = File(...),
    save_to_db: bool = Form(default=True),
    db: AsyncSession = Depends(get_db)
):
    """
    Detect plant growth stage from uploaded image.
    
    Supports both:
    - ESP32-CAM automatic upload
    - Flutter app manual upload
    
    - Accepts image file upload (multipart/form-data)
    - Processes with YOLO v8n model
    - Optionally saves result to database (growth_logs)
    
    Growth stages:
    - Stage 01: Early Growth
    - Stage 02: Leafy Growth  
    - Stage 03: Head Formation
    - Stage 04: Harvest Stage
    """
    print("\n" + "=" * 50)
    print("GROWTH DETECTION REQUEST RECEIVED")
    print(f"Filename: {file.filename}")
    print(f"Content-Type: {file.content_type}")
    print(f"Save to DB: {save_to_db}")
    print("=" * 50)
    
    # Check model is loaded
    if not growth_detection_service.is_model_loaded():
        print("ERROR: Model not loaded!")
        raise HTTPException(
            status_code=503,
            detail="Growth detection model not loaded"
        )
    
    print("Model is loaded, reading file...")
    
    # Read file bytes
    try:
        image_bytes = await file.read()
        print(f"File size: {len(image_bytes)} bytes")
    except Exception as e:
        print(f"ERROR reading file: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Error reading uploaded file: {str(e)}"
        )
    
    # Run prediction
    print("Running YOLO v8n prediction...")
    # Expects tuple: (growth_stage, confidence, raw_image_pil, annotated_image_pil)
    growth_stage, confidence, raw_image, annotated_image = growth_detection_service.predict_from_file(image_bytes)
    
    if growth_stage is None:
        print("No growth stage detected!")
        print("=" * 50 + "\n")
        return GrowthDetectionResponse(success=False)
    
    print(f"Prediction complete!")
    print(f"   Growth Stage: {growth_stage}")
    print(f"   Confidence: {confidence:.2%}")
    
    # Save to database and filesystem if requested
    if save_to_db and growth_stage:
        try:
            # Generate filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            raw_filename = f"{timestamp}.jpg"
            annotated_filename = f"{timestamp}_annotated.jpg"
            
            # Save Raw Image
            raw_path = f"app/static/images/growth/raw/{raw_filename}"
            if raw_image:
                 raw_image.save(raw_path, format="JPEG")

            # Save Annotated Image
            annotated_path = f"app/static/images/growth/annotated/{annotated_filename}"
            if annotated_image:
                 annotated_image.save(annotated_path, format="JPEG")
            
            # Save to DB
            repo = GrowthRepository(db)
            growth_data = GrowthData(
                growth_stage={
                    "growth_class": growth_stage,
                    "confidence": confidence
                },
                image_path=f"static/images/growth/raw/{raw_filename}",
                annotated_image_path=f"static/images/growth/annotated/{annotated_filename}"
            )
            await repo.create(growth_data)
            print(f"Saved to DB: {timestamp}")
            
        except Exception as e:
            print(f"ERROR saving to DB/File: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 50 + "\n")
    
    # Return simple success (no image payload)
    return GrowthDetectionResponse(
        success=True,
        growth_class=growth_stage,
        confidence=confidence
    )


@router.post("/growth/detect/base64", response_model=GrowthDetectionResponse)
async def detect_growth_from_base64(
    request: GrowthDetectionRequest,
    save_to_db: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Detect plant growth stage from Base64 encoded image.
    
    Alternative endpoint for ESP32-CAM if sending Base64 is preferred.
    """
    # Check model is loaded
    if not growth_detection_service.is_model_loaded():
        raise HTTPException(
            status_code=503,
            detail="Growth detection model not loaded"
        )
    
    # Run prediction
    growth_stage, confidence, raw_image, annotated_image = growth_detection_service.predict_from_base64(
        request.image_base64
    )
    
    if growth_stage is None:
        return GrowthDetectionResponse(success=False)
    
    # Save to database if requested
    if save_to_db and growth_stage:
        try:
            # Generate filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            raw_filename = f"{timestamp}.jpg"
            annotated_filename = f"{timestamp}_annotated.jpg"
            
            # Save Raw Image
            raw_path = f"app/static/images/growth/raw/{raw_filename}"
            if raw_image:
                 raw_image.save(raw_path, format="JPEG")

            # Save Annotated Image
            annotated_path = f"app/static/images/growth/annotated/{annotated_filename}"
            if annotated_image:
                 annotated_image.save(annotated_path, format="JPEG")
            
            repo = GrowthRepository(db)
            growth_data = GrowthData(
                growth_stage={
                    "growth_class": growth_stage,
                    "confidence": confidence
                },
                image_path=f"static/images/growth/raw/{raw_filename}",
                annotated_image_path=f"static/images/growth/annotated/{annotated_filename}"
            )
            await repo.create(growth_data)
        except Exception as e:
            print(f"❌ Error saving to DB: {e}")
    
    return GrowthDetectionResponse(
        success=True,
        growth_class=growth_stage,
        confidence=confidence
    )


@router.post("/disease/detect", response_model=DiseaseDetectionResponse)
async def detect_disease(
    file: UploadFile = File(...),
    save_to_db: bool = Form(default=True),
    db: AsyncSession = Depends(get_db)
):
    """
    Detect plant disease from uploaded image (Flutter app).
    
    - Accepts image file upload (multipart/form-data)
    - Processes with YOLO v11n model (.onnx)
    - Returns disease_class, confidence, and annotated image (Base64)
    - Optionally saves to database (disease_logs)
    
    Disease classes:
    - Bacterial
    - Downy_mildew_on_lettuce
    - Powdery_mildew_on_lettuce
    - Septoria_Blight_on_lettuce
    - Viral
    - Wilt_and_leaf_blight_on_lettuce
    - healthy
    """
    print("\n" + "=" * 50)
    print("DISEASE DETECTION REQUEST RECEIVED")
    print(f"Filename: {file.filename}")
    print(f"Content-Type: {file.content_type}")
    print(f"Save to DB: {save_to_db}")
    print("=" * 50)
    
    # Check model is loaded
    if not disease_detection_service.is_model_loaded():
        print("ERROR: Model not loaded!")
        raise HTTPException(
            status_code=503,
            detail="Disease detection model not loaded"
        )
    
    print("Model is loaded, reading file...")
    
    # Read file bytes
    try:
        image_bytes = await file.read()
        print(f"File size: {len(image_bytes)} bytes")
    except Exception as e:
        print(f"ERROR reading file: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Error reading uploaded file: {str(e)}"
        )
    
    # Run prediction
    print("Running YOLO v11n prediction...")
    result = disease_detection_service.predict_from_file(image_bytes)
    
    disease_class = result.get('disease_class', 'unknown')
    confidence = result.get('confidence', 0)
    is_healthy = disease_class.lower() == 'healthy'
    
    print(f"Prediction complete!")
    print(f"   Disease: {disease_class}")
    print(f"   Confidence: {confidence:.2%}")
    print(f"   Is Healthy: {is_healthy}")
    
    # Save to database if requested
    if save_to_db:
        try:
            from app.repositories.disease_repo import DiseaseRepository
            from app.models.schemas.disease import DiseaseData
            from PIL import Image
            import io
            import base64
            import os
            
            # Generate filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            raw_filename = f"{timestamp}.jpg"
            annotated_filename = f"{timestamp}_annotated.jpg"
            
            # Ensure directories exist
            os.makedirs("app/static/images/disease/raw", exist_ok=True)
            os.makedirs("app/static/images/disease/annotated", exist_ok=True)
            
            # Save Raw Image
            raw_path = f"app/static/images/disease/raw/{raw_filename}"
            raw_image = Image.open(io.BytesIO(image_bytes))
            raw_image.save(raw_path, format="JPEG")

            # Save Annotated Image (if available in result)
            annotated_path = f"app/static/images/disease/annotated/{annotated_filename}"
            if result.get('image_base64'):
                annotated_bytes = base64.b64decode(result['image_base64'])
                annotated_image = Image.open(io.BytesIO(annotated_bytes))
                annotated_image.save(annotated_path, format="JPEG")
            
            # Save to DB
            repo = DiseaseRepository(db)
            disease_data = DiseaseData(
                disease_result={
                    "disease_class": disease_class,
                    "confidence": confidence,
                    "is_healthy": is_healthy
                },
                image_path=f"static/images/disease/raw/{raw_filename}",
                annotated_image_path=f"static/images/disease/annotated/{annotated_filename}"
            )
            await repo.create(disease_data)
            print(f"Saved to DB: {timestamp}")
            
        except Exception as e:
            print(f"ERROR saving to DB/File: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 50 + "\n")
    
    return DiseaseDetectionResponse(**result)
