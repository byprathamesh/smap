#!/usr/bin/env python3
"""
WatchHer AI Analyzer - Advanced Version
Integrates YOLOv11-Pose for person detection, pose estimation, and harmful object detection
Optimized for real-time performance with selective DeepFace analysis
"""

import cv2
import numpy as np
from ultralytics import YOLO
from deepface import DeepFace
import logging
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")
logging.getLogger("ultralytics").setLevel(logging.WARNING)

class AIAnalyzer:
    """Advanced AI analyzer with YOLOv11-Pose and harmful object detection"""
    
    # Harmful objects to detect for threat assessment
    HARMFUL_OBJECTS = ['knife', 'gun', 'sword', 'baseball bat', 'firearm', 'club', 'pistol', 'rifle', 'weapon']
    
    def __init__(self):
        self.person_detector = None
        self.model_loaded = False
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize YOLOv11-Pose model for detection and pose estimation"""
        try:
            print("[INFO] Loading YOLOv11 pose estimation model...")
            self.person_detector = YOLO('yolo11n-pose.pt')
            
            # Test GPU availability
            import torch
            if torch.cuda.is_available():
                print(f"[INFO] ✅ CUDA detected: {torch.cuda.get_device_name()}")
                self.person_detector.to('cuda')
            else:
                print("[INFO] ⚠️ CUDA not available, YOLO using CPU")
            
            # Test TensorFlow for DeepFace
            try:
                import tensorflow as tf
                gpus = tf.config.list_physical_devices('GPU')
                if gpus:
                    print(f"[INFO] ✅ TensorFlow GPU detected: {len(gpus)} device(s)")
                else:
                    print("[INFO] ⚠️ TensorFlow will run on CPU - no GPU devices found")
            except:
                print("[INFO] ⚠️ TensorFlow GPU check failed")
            
            self.model_loaded = True
            print("[INFO] YOLOv11 pose model loaded successfully!")
            
        except Exception as e:
            print(f"[ERROR] Failed to load YOLO model: {e}")
            self.model_loaded = False
    
    def is_ready(self):
        """Check if analyzer is ready for inference"""
        return self.model_loaded and self.person_detector is not None
    
    def analyze_frame(self, frame):
        """
        Comprehensive frame analysis with person detection, pose estimation, and harmful object detection
        
        Args:
            frame: Input frame (numpy array)
            
        Returns:
            List of detection dictionaries with enhanced information
        """
        if not self.is_ready():
            return []
        
        try:
            # Run YOLOv11 inference for all objects
            results = self.person_detector(frame, verbose=False)
            
            if not results or not results[0].boxes:
                return []
            
            # Extract all detections
            boxes = results[0].boxes
            keypoints = results[0].keypoints if hasattr(results[0], 'keypoints') and results[0].keypoints is not None else None
            
            person_detections = []
            harmful_objects = []
            
            # Process all detections
            for i, box in enumerate(boxes):
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = self.person_detector.names[class_id]
                
                # Extract bounding box coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # Separate people and harmful objects
                if class_name == 'person' and confidence > 0.3:
                    # Get pose keypoints for this person
                    person_keypoints = None
                    if keypoints is not None and i < len(keypoints.data):
                        person_keypoints = keypoints.data[i].cpu().numpy() if hasattr(keypoints.data[i], 'cpu') else keypoints.data[i]
                    
                    detection = {
                        'bbox': [x1, y1, x2, y2],
                        'confidence': confidence,
                        'class': 'person',
                        'keypoints': person_keypoints,
                        'age': None,
                        'gender': None,
                        'has_harmful_object': False,
                        'harmful_objects_nearby': [],
                        'area': (x2 - x1) * (y2 - y1)  # For sorting by size
                    }
                    person_detections.append(detection)
                    
                elif class_name in self.HARMFUL_OBJECTS and confidence > 0.2:
                    harmful_objects.append({
                        'bbox': [x1, y1, x2, y2],
                        'confidence': confidence,
                        'class': class_name,
                        'center': [(x1 + x2) // 2, (y1 + y2) // 2]
                    })
            
            # Associate harmful objects with people
            self._associate_harmful_objects(person_detections, harmful_objects)
            
            # Performance optimization: Analyze only top 2 largest people with DeepFace
            person_detections.sort(key=lambda x: x['area'], reverse=True)
            
            for i, detection in enumerate(person_detections[:2]):  # Only top 2 largest
                try:
                    self._analyze_person_attributes(frame, detection)
                except Exception as e:
                    print(f"[WARNING] DeepFace analysis failed for person {i}: {e}")
                    # Set defaults if DeepFace fails
                    detection['age'] = 25
                    detection['gender'] = 'unknown'
            
            return person_detections
            
        except Exception as e:
            print(f"[ERROR] Frame analysis failed: {e}")
            return []
    
    def _associate_harmful_objects(self, person_detections, harmful_objects):
        """Associate harmful objects with nearby people"""
        for person in person_detections:
            px1, py1, px2, py2 = person['bbox']
            person_center = [(px1 + px2) // 2, (py1 + py2) // 2]
            
            for obj in harmful_objects:
                obj_center = obj['center']
                
                # Check if object is within person's bounding box or nearby (100 pixels)
                distance = np.sqrt((person_center[0] - obj_center[0])**2 + 
                                 (person_center[1] - obj_center[1])**2)
                
                # Object is associated if within person's bbox or within 100 pixels
                within_bbox = (px1 <= obj_center[0] <= px2 and py1 <= obj_center[1] <= py2)
                nearby = distance <= 100
                
                if within_bbox or nearby:
                    person['has_harmful_object'] = True
                    person['harmful_objects_nearby'].append({
                        'type': obj['class'],
                        'confidence': obj['confidence'],
                        'distance': distance
                    })
    
    def _analyze_person_attributes(self, frame, detection):
        """Analyze person attributes using DeepFace (optimized for performance)"""
        try:
            x1, y1, x2, y2 = detection['bbox']
            
            # Add padding and ensure valid crop
            padding = 10
            h, w = frame.shape[:2]
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(w, x2 + padding)
            y2 = min(h, y2 + padding)
            
            # Extract face region
            person_crop = frame[y1:y2, x1:x2]
            
            if person_crop.size == 0:
                raise ValueError("Invalid crop dimensions")
            
            # DeepFace analysis with enforce_detection=False for robustness
            analysis = DeepFace.analyze(
                person_crop,
                actions=['age', 'gender'],
                enforce_detection=False,
                silent=True
            )
            
            # Handle both single and multiple face results
            if isinstance(analysis, list):
                analysis = analysis[0]
            
            detection['age'] = analysis.get('age', 25)
            detection['gender'] = analysis.get('dominant_gender', 'unknown').lower()
            
        except Exception as e:
            # Fallback values if analysis fails
            detection['age'] = 25
            detection['gender'] = 'unknown'
    
    def draw_detections(self, frame, detections):
        """Draw all detections with enhanced visualization"""
        annotated_frame = frame.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            
            # Color coding based on threat level
            color = (0, 255, 0)  # Green for normal
            if detection['has_harmful_object']:
                color = (0, 0, 255)  # Red for armed person
            elif detection['gender'] == 'Woman':
                color = (0, 255, 255)  # Yellow for women (higher vulnerability)
            
            # Draw bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw pose keypoints if available
            if detection['keypoints'] is not None:
                self._draw_pose(annotated_frame, detection['keypoints'])
            
            # Draw labels
            label = f"Person {detection['confidence']:.2f}"
            if detection['age'] and detection['gender']:
                label += f" | {detection['gender']}, {detection['age']}"
            
            if detection['has_harmful_object']:
                label += " | ⚠️ ARMED"
            
            # Draw label background
            (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated_frame, (x1, y1 - label_height - 10), 
                         (x1 + label_width, y1), color, -1)
            
            # Draw label text
            cv2.putText(annotated_frame, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return annotated_frame
    
    def _draw_pose(self, frame, keypoints):
        """Draw pose keypoints and connections"""
        if keypoints is None or len(keypoints) == 0:
            return
        
        # COCO pose connections (YOLOv11 uses COCO format)
        connections = [
            (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # Arms
            (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),  # Legs
            (5, 11), (6, 12)  # Torso
        ]
        
        # Draw keypoints
        for i, (x, y, conf) in enumerate(keypoints):
            if conf > 0.5:  # Only draw visible keypoints
                cv2.circle(frame, (int(x), int(y)), 3, (0, 255, 0), -1)
        
        # Draw connections
        for connection in connections:
            pt1, pt2 = connection
            if pt1 < len(keypoints) and pt2 < len(keypoints):
                x1, y1, conf1 = keypoints[pt1]
                x2, y2, conf2 = keypoints[pt2]
                
                if conf1 > 0.5 and conf2 > 0.5:
                    cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2) 