"""
Computer Vision Service for Disease Detection using YOLO v11n model.
Handles plant disease classification from Flutter app images.
Uses ONNX Runtime for inference.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont
import io
import numpy as np
import base64
import cv2

# Disease classes from the trained YOLO v11n model
DISEASE_CLASSES = [
    "Bacterial",
    "Downy_mildew_on_lettuce",
    "Powdery_mildew_on_lettuce", 
    "Septoria_Blight_on_lettuce",
    "Viral",
    "Wilt_and_leaf_blight_on_lettuce",
    "healthy"
]

# Colors for bounding boxes (BGR format for OpenCV)
CLASS_COLORS = {
    "Bacterial": (0, 0, 255),        # Red
    "Downy_mildew_on_lettuce": (0, 165, 255), # Orange
    "Powdery_mildew_on_lettuce": (255, 255, 0), # Cyan
    "Septoria_Blight_on_lettuce": (0, 255, 255), # Yellow
    "Viral": (255, 0, 0),            # Blue
    "Wilt_and_leaf_blight_on_lettuce": (128, 0, 128), # Purple
    "healthy": (0, 255, 0),          # Green
    "Unknown": (128, 128, 128)       # Gray
}

# Model path  
MODEL_PATH = Path(__file__).parent.parent / "ml_models" / "model_disease(yolov11n)" / "best.onnx"


class DiseaseDetectionService:
    """Service for detecting plant diseases using YOLO v11n ONNX model"""
    
    def __init__(self):
        self.session = None
        self.input_name = None
        self.input_shape = None
        self._load_model()
    
    def _load_model(self):
        """Load YOLO v11n ONNX model"""
        try:
            import onnxruntime as ort
            
            if MODEL_PATH.exists():
                # Create ONNX Runtime session
                self.session = ort.InferenceSession(
                    str(MODEL_PATH),
                    providers=['CPUExecutionProvider']
                )
                
                # Get input details
                input_info = self.session.get_inputs()[0]
                self.input_name = input_info.name
                self.input_shape = input_info.shape  # e.g., [1, 3, 640, 640]
                
                print(f"✅ YOLO v11n ONNX model loaded from {MODEL_PATH}")
                print(f"   Input name: {self.input_name}, shape: {self.input_shape}")
            else:
                print(f"❌ Model not found at {MODEL_PATH}")
                self.session = None
                
        except Exception as e:
            print(f"❌ Error loading disease detection model: {e}")
            import traceback
            traceback.print_exc()
            self.session = None
    
    def _preprocess_image(self, image: Image.Image) -> Tuple[np.ndarray, float, float]:
        """
        Preprocess image for YOLO v11n model input
        
        Returns:
            input_tensor: Preprocessed image tensor
            scale_x: Scale factor for width
            scale_y: Scale factor for height
        """
        # Get target size from model input shape (default 640x640)
        target_size = 640
        if self.input_shape and len(self.input_shape) >= 4:
            target_size = self.input_shape[2]  # Height dimension
        
        # Calculate scale factors to map back to original image size
        orig_w, orig_h = image.size
        scale_x = orig_w / target_size
        scale_y = orig_h / target_size
        
        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Resize image
        image = image.resize((target_size, target_size))
        
        # Convert to numpy array and normalize to [0, 1]
        img_array = np.array(image).astype(np.float32) / 255.0
        
        # Transpose from HWC to CHW format
        img_array = np.transpose(img_array, (2, 0, 1))
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array, scale_x, scale_y
    
    def _postprocess_output(self, output: np.ndarray, confidence_threshold=0.25) -> Tuple[int, float, list]:
        """
        Postprocess YOLO v11n output to get class, confidence, and bounding box.
        
        YOLO v11n output shape: [1, num_classes + 4, num_detections]
        - First 4 values per detection: x_center, y_center, w, h
        - Remaining values: class probabilities
        """
        predictions = output[0]  # [11, 8400]
        
        # Transpose to [num_detections, num_classes + 4]
        predictions = np.transpose(predictions)  # [8400, 11]
        
        # Get score and class with highest confidence for each detection
        scores = predictions[:, 4:]  # [8400, 7]
        max_scores = np.max(scores, axis=1)
        max_classes = np.argmax(scores, axis=1)
        
        # Filter by confidence threshold
        mask = max_scores > confidence_threshold
        filtered_indices = np.where(mask)[0]
        
        if len(filtered_indices) == 0:
            return None, 0.0, None
            
        # Get the detection with global maximum score
        best_idx = np.argmax(max_scores)
        best_confidence = float(max_scores[best_idx])
        best_class = int(max_classes[best_idx])
        best_box = predictions[best_idx, :4]  # x_center, y_center, w, h based on 640x640
        
        return best_class, best_confidence, best_box

    def _draw_bbox_on_image(self, image: Image.Image, box, class_idx, confidence, scale_x, scale_y) -> str:
        """Draw bounding box on image and return base64 string"""
        try:
            # Convert PIL image to OpenCV format (BGR)
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Map box coordinates (cx, cy, w, h) from 640x640 to original size
            cx, cy, w, h = box
            
            # Scale back to original image size
            cx *= scale_x
            cy *= scale_y
            w *= scale_x
            h *= scale_y
            
            # Convert center-wh to top-left-wh
            x1 = int(cx - w/2)
            y1 = int(cy - h/2)
            x2 = int(cx + w/2)
            y2 = int(cy + h/2)
            
            # Get class info
            if 0 <= class_idx < len(DISEASE_CLASSES):
                class_name = DISEASE_CLASSES[class_idx]
            else:
                class_name = "Unknown"
            
            color = CLASS_COLORS.get(class_name, (0, 255, 0))
            
            # Draw rectangle
            cv2.rectangle(opencv_image, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name} {confidence:.2f}"
            t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
            c2 = x1 + t_size[0] + 3, y1 - t_size[1] - 4
            cv2.rectangle(opencv_image, (x1, y1), c2, color, -1) # Filled label background
            cv2.putText(opencv_image, label, (x1, y1 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            
            # Convert back to Base64
            _, buffer = cv2.imencode('.jpg', opencv_image)
            img_str = base64.b64encode(buffer).decode('utf-8')
            
            return img_str
            
        except Exception as e:
            print(f"❌ Error drawing bounding box: {e}")
            import traceback
            traceback.print_exc()
            return None

    def predict_from_file(self, image_bytes: bytes) -> Dict:
        """
        Predict disease from image bytes.
        
        Args:
            image_bytes: Raw image bytes from uploaded file
            
        Returns:
            Dict with disease_class, confidence, and image_base64
        """
        if self.session is None:
            return {
                "success": False,
                "disease_class": None,
                "confidence": 0.0,
                "image_base64": None
            }
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Preprocess
            input_tensor, scale_x, scale_y = self._preprocess_image(image)
            
            # Run inference
            outputs = self.session.run(None, {self.input_name: input_tensor})
            
            # Postprocess
            class_idx, confidence, box = self._postprocess_output(outputs[0])
            
            image_base64 = None
            disease_class = None
            
            if class_idx is not None:
                # Map class index to disease name
                if 0 <= class_idx < len(DISEASE_CLASSES):
                    disease_class = DISEASE_CLASSES[class_idx]
                else:
                    disease_class = "Unknown"
                
                # Draw bounding box
                image_base64 = self._draw_bbox_on_image(image, box, class_idx, confidence, scale_x, scale_y)
                
                print(f"🔬 Disease prediction: {disease_class} ({confidence:.2%})")
            else:
                 # No detection above threshold -> Healthy or No Detection
                 # Logic can be adjusted based on requirements. For now return None but successful
                 disease_class = "Healthy" # Assuming low confidence means nothing detected = healthy? Or stick to strict logic?
                 # Let's keep it None if truly nothing detected, or return result if confidence exists
                 # In this logic if nothing detected above threshold, we return success=False or class=None
                 pass # Will return None class
            
            return {
                "success": True,
                "disease_class": disease_class,
                "confidence": confidence,
                "image_base64": image_base64
            }
                
        except Exception as e:
            print(f"❌ Error predicting disease: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "disease_class": None,
                "confidence": 0.0,
                "image_base64": None
            }
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.session is not None


# Singleton instance
disease_detection_service = DiseaseDetectionService()
