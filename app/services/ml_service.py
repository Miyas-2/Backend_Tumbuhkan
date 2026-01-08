"""
ML Service for Growth Detection using YOLO v8n model.
Handles plant growth stage classification from ESP32-CAM images.
"""
import os
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import io
import base64

# Growth stage classes from the trained model
GROWTH_CLASSES = [
    "Stage 01: Early Growth",
    "Stage 02: Leafy Growth", 
    "Stage 03: Head Formation",
    "Stage 04: Harvest Stage"
]

# Model path
MODEL_PATH = Path(__file__).parent.parent / "ml_models" / "model_growth(yolo_v8n)" / "best.pt"


class GrowthDetectionService:
    """Service for detecting plant growth stages using YOLO v8n"""
    
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load YOLO v8n model"""
        try:
            from ultralytics import YOLO
            
            if MODEL_PATH.exists():
                self.model = YOLO(str(MODEL_PATH))
                print(f"✅ YOLO v8n model loaded from {MODEL_PATH}")
            else:
                print(f"❌ Model not found at {MODEL_PATH}")
                self.model = None
        except Exception as e:
            print(f"❌ Error loading YOLO model: {e}")
            self.model = None
    
    def predict_from_file(self, image_bytes: bytes) -> Tuple[Optional[str], float, Optional[Image.Image], Optional[Image.Image]]:
        """
        Predict growth stage from image bytes.
        
        Args:
            image_bytes: Raw image bytes from uploaded file
            
        Returns:
            Tuple of (growth_stage, confidence, raw_image, annotated_image)
        """
        if self.model is None:
            print("❌ Model not loaded")
            return None, 0.0, None, None
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Run inference
            results = self.model(image, verbose=False)
            
            if len(results) > 0 and len(results[0].boxes) > 0:
                # Get the prediction with highest confidence
                boxes = results[0].boxes
                confidences = boxes.conf.cpu().numpy()
                classes = boxes.cls.cpu().numpy()
                
                # Find highest confidence prediction
                max_idx = confidences.argmax()
                class_idx = int(classes[max_idx])
                confidence = float(confidences[max_idx])
                
                # Map class index to growth stage
                if 0 <= class_idx < len(GROWTH_CLASSES):
                    growth_stage = GROWTH_CLASSES[class_idx]
                else:
                    growth_stage = f"Unknown (class {class_idx})"
                
                # Get annotated image using native plot()
                # Returns numpy array
                plotted_img = results[0].plot()
                
                # Convert RGB -> BGR (Ultralytics plot uses BGR by default usually, but let's check results)
                # Note: plot() typically returns BGR numpy array
                # Convert to PIL Image (RGB)
                plotted_pil = Image.fromarray(plotted_img[..., ::-1])  # BGR to RGB
                
                print(f"🌱 Growth prediction: {growth_stage} ({confidence:.2%})")
                
                # Return raw image (PIL) and annotated image (PIL)
                return growth_stage, confidence, image, plotted_pil
            else:
                print("⚠️ No detection found in image")
                return None, 0.0, None, None

                
        except Exception as e:
            print(f"❌ Error predicting growth stage: {e}")
            import traceback
            traceback.print_exc()
            return None, 0.0, None
    
    def predict_from_base64(self, base64_image: str) -> Tuple[Optional[str], float, Optional[str]]:
        """
        Predict growth stage from Base64 encoded image.
        
        Args:
            base64_image: Base64 encoded image string
            
        Returns:
            Tuple of (growth_stage, confidence, image_base64) or (None, 0.0, None) if error
        """
        try:
            # Remove data URL prefix if present
            if "," in base64_image:
                base64_image = base64_image.split(",")[1]
            
            # Decode Base64
            image_bytes = base64.b64decode(base64_image)
            
            return self.predict_from_file(image_bytes)
            
        except Exception as e:
            print(f"❌ Error decoding Base64 image: {e}")
            return None, 0.0, None
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None


# Singleton instance
growth_detection_service = GrowthDetectionService()
