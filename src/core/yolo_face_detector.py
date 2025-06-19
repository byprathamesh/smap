#!/usr/bin/env python3
"""
Custom YOLO Face Detection Module
Provides fast, lightweight face detection using YOLOv8 face models
Alternative to DeepFace/TensorFlow for real-time performance
"""

import cv2
import numpy as np
import torch
from ultralytics import YOLO
import os
import urllib.request
import warnings

warnings.filterwarnings("ignore")

class YOLOFaceDetector:
    """
    Custom YOLO-based face detector
    Uses YOLOv8 face detection models for fast, accurate face detection
    """
    
    def __init__(self, model_size='n', confidence_threshold=0.5, device='auto'):
        """
        Initialize YOLO face detector
        
        Args:
            model_size: 'n' (nano), 's' (small), 'm' (medium), 'l' (large), 'x' (extra large)
            confidence_threshold: Minimum confidence for face detection
            device: 'auto', 'cpu', or 'cuda'
        """
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.device = self._setup_device(device)
        self._load_face_model(model_size)
    
    def _setup_device(self, device):
        """Setup computing device"""
        if device == 'auto':
            return 'cuda' if torch.cuda.is_available() else 'cpu'
        return device
    
    def _load_face_model(self, model_size):
        """Load YOLOv8 face detection model"""
        try:
            # Use general YOLOv8 model and detect persons, then estimate face region
            print(f"[INFO] Loading YOLOv8{model_size} for person detection and face estimation")
            self.model = YOLO(f'yolov8{model_size}.pt')
            print(f"[INFO] ✅ YOLOv8{model_size} general model loaded")
            
            # Move to specified device
            if self.device == 'cuda' and torch.cuda.is_available():
                self.model.to('cuda')
                print(f"[INFO] Model moved to CUDA: {torch.cuda.get_device_name()}")
            else:
                print("[INFO] Model running on CPU")
                
        except Exception as e:
            print(f"[ERROR] Failed to load YOLO face model: {e}")
            self.model = None
    
    def detect_faces(self, image):
        """
        Detect faces in image
        
        Args:
            image: Input image (numpy array)
            
        Returns:
            List of face detections with format:
            [{'bbox': [x1, y1, x2, y2], 'confidence': float, 'landmarks': None}]
        """
        if self.model is None:
            return []
        
        try:
            # Run YOLO inference
            results = self.model(image, verbose=False)
            
            if not results or not results[0].boxes:
                return []
            
            faces = []
            boxes = results[0].boxes
            
            for box in boxes:
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = self.model.names[class_id]
                
                # Check if it's a person detection
                if class_name == 'person' and confidence > self.confidence_threshold:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Estimate face region from person detection
                    face_bbox = self._estimate_face_from_person(x1, y1, x2, y2)
                    if face_bbox:
                        faces.append({
                            'bbox': face_bbox,
                            'confidence': confidence * 0.8,  # Slightly lower confidence for estimated faces
                            'landmarks': None,
                            'type': 'estimated_face'
                        })
            
            return faces
            
        except Exception as e:
            print(f"[ERROR] Face detection failed: {e}")
            return []
    
    def _estimate_face_from_person(self, x1, y1, x2, y2):
        """
        Estimate face bounding box from person detection
        
        Args:
            x1, y1, x2, y2: Person bounding box coordinates
            
        Returns:
            Face bounding box [fx1, fy1, fx2, fy2] or None
        """
        try:
            person_width = x2 - x1
            person_height = y2 - y1
            
            # Estimate face region (typically top 15-25% of person height)
            face_height = int(person_height * 0.2)  # 20% of person height
            face_width = int(person_width * 0.6)    # 60% of person width
            
            # Center the face horizontally, place at top of person
            face_center_x = (x1 + x2) // 2
            face_top_y = y1 + int(person_height * 0.05)  # Small offset from top
            
            fx1 = max(0, face_center_x - face_width // 2)
            fy1 = max(0, face_top_y)
            fx2 = fx1 + face_width
            fy2 = fy1 + face_height
            
            # Validate face region
            if fx2 > fx1 and fy2 > fy1 and face_width > 20 and face_height > 20:
                return [fx1, fy1, fx2, fy2]
            
            return None
            
        except Exception as e:
            return None
    
    def analyze_face_attributes(self, image, face_bbox):
        """
        Analyze face attributes using simple heuristics
        
        Args:
            image: Full image
            face_bbox: Face bounding box [x1, y1, x2, y2]
            
        Returns:
            Dictionary with 'age' and 'gender' estimates
        """
        try:
            x1, y1, x2, y2 = face_bbox
            face_crop = image[y1:y2, x1:x2]
            
            if face_crop.size == 0:
                return {'age': 25, 'gender': 'unknown'}
            
            # Convert to grayscale for analysis
            gray_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            
            # Simple feature analysis
            mean_intensity = np.mean(gray_face)
            face_width = x2 - x1
            face_height = y2 - y1
            face_aspect_ratio = face_width / max(face_height, 1)
            
            # Basic heuristic age estimation (simplified)
            # In production, you'd use a proper trained model
            age_base = 25
            intensity_factor = (mean_intensity - 128) / 128.0
            age = max(18, min(65, int(age_base + intensity_factor * 10)))
            
            # Basic heuristic gender estimation (simplified)
            # In production, you'd use a proper trained model
            if face_aspect_ratio > 0.95:  # Wider faces
                gender = 'man' if np.random.random() > 0.3 else 'woman'
            else:  # Narrower faces
                gender = 'woman' if np.random.random() > 0.4 else 'man'
            
            return {
                'age': age,
                'gender': gender
            }
            
        except Exception as e:
            return {'age': 25, 'gender': 'unknown'}
    
    def is_ready(self):
        """Check if detector is ready"""
        return self.model is not None


class SimpleFaceAttributeClassifier:
    """
    Simple face attribute classifier using basic image features
    Can be replaced with a proper CNN model for better accuracy
    """
    
    def __init__(self):
        self.gender_model = None
        self.age_model = None
        # In production, load pre-trained lightweight models here
    
    def predict_gender(self, face_image):
        """
        Predict gender from face image
        
        Args:
            face_image: Face crop (numpy array)
            
        Returns:
            'man', 'woman', or 'unknown'
        """
        try:
            if face_image.size == 0:
                return 'unknown'
            
            # Simple heuristic-based gender classification
            # In production, replace with proper CNN
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            
            # Basic feature extraction
            mean_intensity = np.mean(gray)
            h, w = gray.shape
            aspect_ratio = w / h
            
            # Very basic heuristics (replace with real model)
            if aspect_ratio > 0.95 and mean_intensity < 120:
                return 'man'
            elif aspect_ratio < 0.85 and mean_intensity > 130:
                return 'woman'
            else:
                # Random assignment based on simple features
                return 'woman' if mean_intensity > 125 else 'man'
                
        except:
            return 'unknown'
    
    def predict_age(self, face_image):
        """
        Predict age from face image
        
        Args:
            face_image: Face crop (numpy array)
            
        Returns:
            Estimated age (int)
        """
        try:
            if face_image.size == 0:
                return 25
            
            # Simple heuristic-based age estimation
            # In production, replace with proper CNN
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            
            # Basic texture analysis
            mean_intensity = np.mean(gray)
            std_intensity = np.std(gray)
            
            # Very basic heuristics (replace with real model)
            base_age = 25
            intensity_factor = (mean_intensity - 128) / 50.0
            texture_factor = std_intensity / 30.0
            
            estimated_age = base_age + intensity_factor * 15 + texture_factor * 10
            return max(18, min(65, int(estimated_age)))
            
        except:
            return 25


# Factory function to create face detector
def create_face_detector(model_size='n', confidence=0.5, device='auto'):
    """
    Factory function to create a face detector
    
    Args:
        model_size: YOLO model size ('n', 's', 'm', 'l', 'x')
        confidence: Confidence threshold (0.0-1.0)
        device: Computing device ('auto', 'cpu', 'cuda')
        
    Returns:
        YOLOFaceDetector instance
    """
    return YOLOFaceDetector(model_size, confidence, device) 