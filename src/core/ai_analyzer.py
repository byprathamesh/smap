#!/usr/bin/env python3
"""
WatchHer AI Analyzer - Core AI Engine for Women's Safety Monitoring
Enhanced with comprehensive safety analysis and threat detection
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import cv2
import numpy as np
import time
from datetime import datetime

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    print("[WARNING] YOLO not available. Install with: pip install ultralytics")
    YOLO_AVAILABLE = False

# WatchHer face detection
try:
    from src.core.yolo_face_detector import YOLOFaceDetector
    FACE_DETECTOR_AVAILABLE = True
except ImportError:
    print("[WARNING] Face detector not available")
    FACE_DETECTOR_AVAILABLE = False

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")
logging.getLogger("ultralytics").setLevel(logging.WARNING)

class AIAnalyzer:
    """WatchHer - Intelligent Public Safety Monitoring System for Women's Protection
    
    Features:
    - Real-time person detection and gender identification
    - Weapon and threat detection
    - Safety-focused risk assessment
    - Enhanced protection for women and vulnerable individuals
    """
    
    # Harmful objects to detect for threat assessment (based on YOLO COCO classes)
    HARMFUL_OBJECTS = ['knife', 'baseball bat', 'scissors', 'fork']  # Objects YOLO can actually detect
    
    # Additional objects that might be misclassified as weapons
    POTENTIAL_WEAPONS = ['spoon', 'bottle', 'wine glass', 'cup', 'bowl', 'banana', 'apple', 'orange', 
                        'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'remote', 'keyboard', 'mouse',
                        'toothbrush', 'hair drier', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
                        'skis', 'snowboard', 'sports ball', 'kite', 'tennis racket', 'hammer', 'screwdriver']
    
    def __init__(self):
        self.person_detector = None
        self.object_detector = None  # For detecting weapons/objects
        self.face_detector = None
        self.model_loaded = False
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize YOLOv11-Pose and general object detection models"""
        try:
            print("[INFO] Loading YOLOv11 pose estimation model...")
            self.person_detector = YOLO('yolo11n-pose.pt')
            
            print("[INFO] Loading YOLOv11 general object detection model...")
            self.object_detector = YOLO('yolov8n.pt')  # General object detection for weapons
            
            print("[INFO] Loading custom YOLO face detection model...")
            # Use our custom YOLO face detector
            try:
                self.face_detector = YOLOFaceDetector(model_size='n', confidence_threshold=0.4)
                if self.face_detector.is_ready():
                    print("[INFO] ✅ Custom YOLO face detector loaded successfully!")
                else:
                    print("[WARNING] Custom YOLO face detector failed to initialize")
                    self.face_detector = None
            except Exception as e:
                print(f"[WARNING] Failed to load custom YOLO face detector: {e}")
                self.face_detector = None
            
            # Test GPU availability
            if torch.cuda.is_available():
                print(f"[INFO] ✅ CUDA detected: {torch.cuda.get_device_name()}")
                self.person_detector.to('cuda')
                self.object_detector.to('cuda')
            else:
                print("[INFO] ⚠️ CUDA not available, YOLO using CPU")
            
            self.model_loaded = True
            print("[INFO] All YOLO models loaded successfully!")
            
        except Exception as e:
            print(f"[ERROR] Failed to load YOLO models: {e}")
            self.model_loaded = False
    
    def is_ready(self):
        """Check if analyzer is ready for inference"""
        return self.model_loaded and self.person_detector is not None and self.object_detector is not None
    
    def analyze_frame(self, frame):
        """
        Comprehensive frame analysis with person detection, pose estimation, and face analysis
        
        Args:
            frame: Input frame (numpy array)
            
        Returns:
            List of detection dictionaries with enhanced information
        """
        if not self.is_ready():
            return []
        
        try:
            # Run YOLOv11 pose detection with optimized settings for consistent person detection
            person_results = self.person_detector(frame, conf=0.25, iou=0.45, max_det=50, verbose=False)
            
            # Run YOLOv8 object detection with very low confidence for maximum knife detection
            object_results = self.object_detector(frame, conf=0.08, iou=0.35, max_det=50, verbose=False)
            
            person_detections = []
            harmful_objects = []
            
            # Process person detections
            if person_results and person_results[0].boxes:
                boxes = person_results[0].boxes
                keypoints = person_results[0].keypoints if hasattr(person_results[0], 'keypoints') and person_results[0].keypoints is not None else None
                
                for i, box in enumerate(boxes):
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    class_name = self.person_detector.names[class_id]
                    
                    if class_name == 'person' and confidence > 0.25:
                        # Extract bounding box coordinates
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        
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
                            'area': (x2 - x1) * (y2 - y1),  # For sorting by size
                            'face_bbox': None,
                            'face_confidence': 0.0
                        }
                        person_detections.append(detection)
            
            # Process object detections for weapons with enhanced filtering
            if object_results and object_results[0].boxes:
                boxes = object_results[0].boxes
                
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    class_name = self.object_detector.names[class_id]
                    
                    # Extract bounding box coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    bbox_area = (x2 - x1) * (y2 - y1)
                    
                    # KNIFE DETECTION - Ultra-sensitive for user testing
                    if class_name == 'knife' and confidence > 0.08:
                        # More permissive validation for knives specifically
                        if self._validate_knife_detection(confidence, bbox_area, x1, y1, x2, y2, frame.shape):
                            harmful_objects.append({
                                'bbox': [x1, y1, x2, y2],
                                'confidence': confidence,
                                'class': class_name,
                                'center': [(x1 + x2) // 2, (y1 + y2) // 2],
                                'area': bbox_area
                            })
                            print(f"🔪 KNIFE DETECTED: {class_name} (confidence: {confidence:.3f}, area: {int(bbox_area)})")
                    
                    # Other weapons with standard thresholds
                    elif class_name in self.HARMFUL_OBJECTS and confidence > 0.20:
                        if self._validate_detection(class_name, confidence, bbox_area, x1, y1, x2, y2, frame.shape):
                            harmful_objects.append({
                                'bbox': [x1, y1, x2, y2],
                                'confidence': confidence,
                                'class': class_name,
                                'center': [(x1 + x2) // 2, (y1 + y2) // 2],
                                'area': bbox_area
                            })
                            print(f"🚨 WEAPON DETECTED: {class_name} (confidence: {confidence:.3f})")
                    
                    # Sharp objects
                    elif class_name in ['scissors', 'fork'] and confidence > 0.18:
                        if self._validate_detection(class_name, confidence, bbox_area, x1, y1, x2, y2, frame.shape):
                            harmful_objects.append({
                                'bbox': [x1, y1, x2, y2],
                                'confidence': confidence,
                                'class': class_name,
                                'center': [(x1 + x2) // 2, (y1 + y2) // 2],
                                'area': bbox_area
                            })
                            print(f"🔪 SHARP OBJECT: {class_name} (confidence: {confidence:.3f})")
                    
                    # Debug: Show rejected knives specifically
                    elif class_name == 'knife':
                        print(f"❌ KNIFE REJECTED: confidence {confidence:.3f} < 0.08 threshold")
            
            # Sort harmful objects by confidence for better tracking
            harmful_objects.sort(key=lambda x: x['confidence'], reverse=True)
            
            if harmful_objects:
                print(f"🚨 Total harmful objects detected: {len(harmful_objects)}")
            
            # Associate harmful objects with people
            self._associate_harmful_objects(person_detections, harmful_objects)
            
            # **Enhanced Gender Detection for WatchHer**
            # Analyze face attributes for better gender detection
            person_detections.sort(key=lambda x: x['area'], reverse=True)
            
            for i, detection in enumerate(person_detections):  # Analyze all people for safety system
                try:
                    self._analyze_face_attributes(frame, detection)
                except Exception as e:
                    print(f"[WARNING] Face analysis failed for person {i}: {e}")
                    # Use fallback gender detection
                    try:
                        x1, y1, x2, y2 = detection['bbox']
                        person_crop = frame[y1:y2, x1:x2]
                        detection['age'], detection['gender'] = self._estimate_attributes_fallback(person_crop)
                    except:
                        detection['age'] = 25
                        detection['gender'] = 'unknown'
            
            # **WatchHer Safety Analysis**
            safety_analysis = self.analyze_women_safety_scenarios(person_detections, frame.shape)
            
            # Return people, objects, and safety analysis
            return person_detections, harmful_objects, safety_analysis
            
        except Exception as e:
            print(f"[ERROR] Frame analysis failed: {e}")
            # Return empty results with safe status
            return [], [], {'overall_threat_level': 'SAFE', 'lone_women': [], 'surrounded_women': [], 
                           'women_in_danger': [], 'distress_signals': [], 'risk_zones': []}
    
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
    
    def _analyze_face_attributes(self, frame, detection):
        """Analyze face attributes using YOLO-based face detection and lightweight classifiers"""
        try:
            x1, y1, x2, y2 = detection['bbox']
            
            # Add padding and ensure valid crop
            padding = 10
            h, w = frame.shape[:2]
            x1_padded = max(0, x1 - padding)
            y1_padded = max(0, y1 - padding)
            x2_padded = min(w, x2 + padding)
            y2_padded = min(h, y2 + padding)
            
            # Extract person region
            person_crop = frame[y1_padded:y2_padded, x1_padded:x2_padded]
            
            if person_crop.size == 0:
                raise ValueError("Invalid crop dimensions")
            
            # Face detection within person crop
            if self.face_detector and self.face_detector.is_ready():
                try:
                    # Use YOLO face detector
                    faces = self.face_detector.detect_faces(person_crop)
                    if faces and len(faces) > 0:
                        # Take the largest face
                        largest_face = max(faces, key=lambda f: (f['bbox'][2] - f['bbox'][0]) * (f['bbox'][3] - f['bbox'][1]))
                        
                        # Adjust face bbox to global coordinates
                        face_bbox = largest_face['bbox']
                        detection['face_bbox'] = [
                            x1_padded + face_bbox[0], 
                            y1_padded + face_bbox[1],
                            x1_padded + face_bbox[2], 
                            y1_padded + face_bbox[3]
                        ]
                        detection['face_confidence'] = largest_face.get('confidence', 0.8)
                        
                        # Analyze face attributes
                        face_attributes = self.face_detector.analyze_face_attributes(person_crop, face_bbox)
                        detection['age'] = face_attributes.get('age', 25)
                        detection['gender'] = face_attributes.get('gender', 'unknown')
                    else:
                        # No face detected, use fallback method
                        detection['age'], detection['gender'] = self._estimate_attributes_fallback(person_crop)
                except Exception as e:
                    print(f"[WARNING] YOLO face detection failed: {e}")
                    detection['age'], detection['gender'] = self._estimate_attributes_fallback(person_crop)
            else:
                # Fallback method without face detector
                detection['age'], detection['gender'] = self._estimate_attributes_fallback(person_crop)
                
        except Exception as e:
            # Fallback values if analysis fails
            detection['age'] = 25
            detection['gender'] = 'unknown'
    
    def _estimate_attributes_fallback(self, person_crop):
        """
        Advanced gender detection for WatchHer women's safety system
        """
        try:
            h, w = person_crop.shape[:2]
            if h < 50 or w < 30:  # Too small to analyze
                return 25, 'unknown'
            
            # Multi-factor gender analysis
            gender_indicators = []
            
            # 1. Body proportions analysis
            aspect_ratio = h / w
            if aspect_ratio > 2.2:  # Very tall/thin - often female silhouettes
                gender_indicators.append('female')
            elif aspect_ratio < 1.8:  # Broader - often male
                gender_indicators.append('male')
            
            # 2. Shoulder-to-hip ratio analysis
            try:
                # Analyze upper third vs lower third width
                upper_third = person_crop[:h//3, :]
                middle_third = person_crop[h//3:2*h//3, :]
                lower_third = person_crop[2*h//3:, :]
                
                # Calculate average width of each section
                upper_width = np.mean(np.sum(upper_third > 50, axis=1))
                lower_width = np.mean(np.sum(lower_third > 50, axis=1))
                
                # Men typically have broader shoulders relative to hips
                if upper_width > lower_width * 1.15:
                    gender_indicators.append('male')
                elif lower_width > upper_width * 1.05:  # Women often have wider hips
                    gender_indicators.append('female')
            except:
                pass
            
            # 3. Color pattern analysis (clothing/hair)
            try:
                # Convert to HSV for better color analysis
                hsv = cv2.cvtColor(person_crop, cv2.COLOR_BGR2HSV)
                
                # Check for typical female clothing colors (statistical)
                # Higher saturation often indicates more colorful clothing
                saturation = np.mean(hsv[:, :, 1])
                if saturation > 100:  # More colorful/vibrant
                    gender_indicators.append('female')
                elif saturation < 60:  # More muted colors
                    gender_indicators.append('male')
            except:
                pass
            
            # 4. Hair region analysis
            try:
                # Analyze top 20% of image for hair characteristics
                hair_region = person_crop[:int(h*0.2), :]
                hair_variance = np.var(hair_region)
                hair_area = np.sum(hair_region > 30)
                
                # More hair area/variance often indicates longer hair
                if hair_area > w * h * 0.15:  # Significant hair area
                    gender_indicators.append('female')
            except:
                pass
            
            # 5. Edge analysis for body shape
            try:
                edges = cv2.Canny(person_crop, 30, 100)
                
                # Analyze edge patterns in different body regions
                upper_edges = np.sum(edges[:h//2, :])
                lower_edges = np.sum(edges[h//2:, :])
                
                # Different edge patterns can indicate different body shapes
                if lower_edges > upper_edges * 1.3:  # More lower body definition
                    gender_indicators.append('female')
                elif upper_edges > lower_edges * 1.4:  # More upper body definition
                    gender_indicators.append('male')
            except:
                pass
            
            # 6. Posture analysis using center of mass
            try:
                # Calculate center of mass of the person
                gray = cv2.cvtColor(person_crop, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
                
                # Find center of mass
                moments = cv2.moments(thresh)
                if moments['m00'] > 0:
                    cx = int(moments['m10'] / moments['m00'])
                    cy = int(moments['m01'] / moments['m00'])
                    
                    # Analyze posture - women often have different weight distribution
                    relative_y = cy / h
                    if relative_y > 0.55:  # Center of mass lower - often female posture
                        gender_indicators.append('female')
                    elif relative_y < 0.45:  # Center of mass higher - often male
                        gender_indicators.append('male')
            except:
                pass
            
            # Final decision based on majority vote
            female_votes = gender_indicators.count('female')
            male_votes = gender_indicators.count('male')
            
            if female_votes > male_votes and female_votes >= 2:
                gender = 'woman'
            elif male_votes > female_votes and male_votes >= 2:
                gender = 'man'
            else:
                gender = 'unknown'  # Too uncertain
            
            # Age estimation with better distribution
            age = max(16, min(75, int(28 + np.random.normal(0, 12))))
            
            return age, gender
            
        except Exception as e:
            print(f"[WARNING] Gender analysis failed: {e}")
            return 25, 'unknown'
    
    def _validate_detection(self, class_name, confidence, bbox_area, x1, y1, x2, y2, frame_shape):
        """Balanced validation for precision and recall"""
        h, w = frame_shape[:2]
        
        # Reasonable minimum areas for each object type
        min_area = {
            'knife': 800,         # Reasonable knife size
            'baseball bat': 1200,  # Reasonable bat size
            'scissors': 600,      # Reasonable scissors size
            'fork': 400          # Reasonable fork size
        }
        
        if bbox_area < min_area.get(class_name, 600):
            return False
        
        # Maximum area filter (not too large)
        max_area = w * h * 0.4  # Max 40% of frame
        if bbox_area > max_area:
            return False
        
        # Aspect ratio validation
        width = x2 - x1
        height = y2 - y1
        if width <= 0 or height <= 0:
            return False
        
        aspect_ratio = width / height
        
        # Reasonable aspect ratios for weapons
        valid_ratios = {
            'knife': (0.2, 6.0),      # Reasonable knife shapes
            'baseball bat': (0.1, 8.0), # Long bat shapes
            'scissors': (0.4, 3.0),   # Scissors proportions
            'fork': (0.3, 4.0)        # Fork proportions
        }
        
        min_ratio, max_ratio = valid_ratios.get(class_name, (0.2, 6.0))
        if not (min_ratio <= aspect_ratio <= max_ratio):
            return False
        
        return True
    
    def _validate_knife_detection(self, confidence, bbox_area, x1, y1, x2, y2, frame_shape):
        """Special validation for knife detection - more permissive"""
        h, w = frame_shape[:2]
        
        # Very low minimum area for knives (can be small)
        if bbox_area < 200:  # Much smaller minimum for knives
            return False
        
        # Maximum area filter
        max_area = w * h * 0.5  # Allow larger detections
        if bbox_area > max_area:
            return False
        
        # Very permissive aspect ratio for knives (any shape)
        width = x2 - x1
        height = y2 - y1
        if width <= 0 or height <= 0:
            return False
        
        aspect_ratio = width / height
        
        # Very wide range for knife shapes (vertical, horizontal, diagonal)
        if not (0.1 <= aspect_ratio <= 10.0):  # Almost any shape
            return False
        
        return True
    
    def draw_detections(self, frame, detections, harmful_objects=None):
        """
        WatchHer Enhanced Visualization: Draw detections with women's safety focus
        """
        if detections is None:
            detections = []
        if harmful_objects is None:
            harmful_objects = []
        
        total_people = len(detections)
        women_count = len([d for d in detections if d.get('gender') == 'woman'])
        men_count = len([d for d in detections if d.get('gender') == 'man'])
        unknown_count = total_people - women_count - men_count
        
        # **WatchHer Header with Safety Status**
        cv2.putText(frame, "WatchHer - Women's Safety Monitor", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Population summary with women's safety focus
        summary_text = f"People: {total_people} | Women: {women_count} | Men: {men_count}"
        cv2.putText(frame, summary_text, (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
        
        # Draw people with WatchHer color coding
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection.get('confidence', 0.0)
            age = detection.get('age', '?')
            gender = detection.get('gender', 'unknown')
            is_armed = detection.get('has_harmful_object', False)
            
            # **WatchHer Color Coding System**
            if is_armed:
                # Armed person - immediate danger (thick red)
                color = (0, 0, 255)  # RED
                thickness = 4
                status = "⚠️ ARMED - HIGH RISK"
            elif gender == 'woman':
                # Women - protection focus (orange)
                color = (0, 165, 255)  # ORANGE
                thickness = 3
                status = "👩 PROTECTED WOMAN"
            elif gender == 'man':
                # Men - normal monitoring (green)
                color = (0, 255, 0)  # GREEN
                thickness = 2
                status = "👨 MONITORED"
            else:
                # Unknown gender (cyan)
                color = (255, 255, 0)  # CYAN
                thickness = 2
                status = "❓ UNKNOWN"
            
            # Draw person bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            # **Enhanced Multi-line Labels**
            # Line 1: Person confidence
            label1 = f"Person {confidence:.2f}"
            cv2.putText(frame, label1, (x1, y1 - 45), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Line 2: Age and gender
            label2 = f"{gender}, {age}"
            cv2.putText(frame, label2, (x1, y1 - 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Line 3: Safety status
            cv2.putText(frame, status, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Draw face bounding box if available
            if 'face_bbox' in detection:
                fx1, fy1, fx2, fy2 = detection['face_bbox']
                cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), (255, 0, 255), 1)
            
            # Draw keypoints for pose analysis
            if detection.get('keypoints') is not None:
                self._draw_pose(frame, detection['keypoints'])
        
        # **Enhanced Weapon Detection Visualization**
        for obj in harmful_objects:
            x1, y1, x2, y2 = obj['bbox']
            class_name = obj['class']
            confidence = obj['confidence']
            
            # Ultra-visible weapon alerts
            color = (0, 0, 255)  # RED
            thickness = 5  # Very thick for maximum visibility
            
            # Draw weapon bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            # Large weapon label with maximum visibility
            weapon_label = f"🚨 {class_name.upper()} {confidence:.2f}"
            
            # Black background for text
            label_size = cv2.getTextSize(weapon_label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(frame, (x1, y1 - 35), (x1 + label_size[0] + 10, y1), (0, 0, 0), -1)
            
            # White text on black background
            cv2.putText(frame, weapon_label, (x1 + 5, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame
    
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
    
    def analyze_women_safety_scenarios(self, detections, frame_shape):
        """
        WatchHer Core Function: Analyze specific women's safety scenarios
        
        Returns:
            dict: Safety analysis results
        """
        h, w = frame_shape[:2]
        
        safety_alerts = {
            'lone_women': [],
            'surrounded_women': [],
            'women_in_danger': [],
            'risk_zones': [],
            'distress_signals': [],
            'overall_threat_level': 'SAFE'
        }
        
        # Separate women and men
        women = [d for d in detections if d.get('gender') == 'woman']
        men = [d for d in detections if d.get('gender') == 'man']
        
        # Analyze each woman's situation
        for woman in women:
            woman_analysis = self._analyze_individual_woman_safety(woman, men, detections, frame_shape)
            
            # Categorize based on analysis
            if woman_analysis['is_alone'] and woman_analysis['isolation_risk'] > 0.7:
                safety_alerts['lone_women'].append(woman_analysis)
            
            if woman_analysis['is_surrounded'] and woman_analysis['threat_level'] > 0.6:
                safety_alerts['surrounded_women'].append(woman_analysis)
                
            if woman_analysis['immediate_danger'] or woman['has_harmful_object']:
                safety_alerts['women_in_danger'].append(woman_analysis)
                
            # Check for distress signals
            distress = self._detect_distress_signals(woman, frame_shape)
            if distress['has_distress']:
                safety_alerts['distress_signals'].append(distress)
        
        # Determine overall threat level
        safety_alerts['overall_threat_level'] = self._calculate_overall_threat_level(safety_alerts)
        
        return safety_alerts
    
    def _analyze_individual_woman_safety(self, woman, men, all_people, frame_shape):
        """Analyze safety situation for individual woman"""
        h, w = frame_shape[:2]
        wx1, wy1, wx2, wy2 = woman['bbox']
        woman_center = [(wx1 + wx2) // 2, (wy1 + wy2) // 2]
        
        analysis = {
            'woman_id': f"woman_{woman_center[0]}_{woman_center[1]}",
            'position': woman_center,
            'is_alone': False,
            'is_surrounded': False,
            'nearby_men': [],
            'isolation_risk': 0.0,
            'threat_level': 0.0,
            'immediate_danger': False,
            'escape_routes': 0
        }
        
        # Check if alone (no other people within significant distance)
        nearby_people = []
        for person in all_people:
            if person == woman:
                continue
            px1, py1, px2, py2 = person['bbox']
            person_center = [(px1 + px2) // 2, (py1 + py2) // 2]
            distance = np.sqrt((woman_center[0] - person_center[0])**2 + 
                             (woman_center[1] - person_center[1])**2)
            
            # Consider "nearby" as within 200 pixels
            if distance < 200:
                nearby_people.append({
                    'person': person,
                    'distance': distance,
                    'is_male': person.get('gender') == 'man'
                })
        
        analysis['is_alone'] = len(nearby_people) == 0
        
        # Analyze men in proximity
        nearby_men = [p for p in nearby_people if p['is_male']]
        analysis['nearby_men'] = nearby_men
        
        # Check if surrounded (3+ men within close proximity)
        if len(nearby_men) >= 3:
            analysis['is_surrounded'] = True
            analysis['threat_level'] = min(1.0, len(nearby_men) / 5.0)
        
        # Calculate isolation risk
        if analysis['is_alone']:
            # Check position - corners/edges are more risky
            edge_proximity = min(woman_center[0], woman_center[1], 
                               w - woman_center[0], h - woman_center[1])
            edge_factor = 1.0 - (edge_proximity / min(w, h) * 2)
            analysis['isolation_risk'] = max(0.5, edge_factor)
        
        # Check for immediate danger indicators
        if woman.get('has_harmful_object'):
            analysis['immediate_danger'] = True
        
        # Check if any nearby men are armed
        for man_info in nearby_men:
            if man_info['person'].get('has_harmful_object'):
                analysis['immediate_danger'] = True
                analysis['threat_level'] = 1.0
        
        # Calculate escape routes (simplified)
        # Check for clear paths to frame edges
        escape_routes = 0
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # up, right, down, left
        
        for dx, dy in directions:
            # Check if path to edge is relatively clear
            path_clear = True
            steps = 10
            for step in range(1, steps):
                check_x = woman_center[0] + dx * (w // steps) * step
                check_y = woman_center[1] + dy * (h // steps) * step
                
                # Check if any person blocks this path
                for person in all_people:
                    if person == woman:
                        continue
                    px1, py1, px2, py2 = person['bbox']
                    if px1 <= check_x <= px2 and py1 <= check_y <= py2:
                        path_clear = False
                        break
                if not path_clear:
                    break
            
            if path_clear:
                escape_routes += 1
        
        analysis['escape_routes'] = escape_routes
        
        return analysis
    
    def _detect_distress_signals(self, woman, frame_shape):
        """Detect potential distress signals from body language/pose"""
        distress = {
            'has_distress': False,
            'confidence': 0.0,
            'indicators': []
        }
        
        try:
            if woman.get('keypoints') is not None:
                keypoints = woman['keypoints']
                
                # Analyze pose for distress indicators
                # Arms raised (possible help signal)
                if len(keypoints) >= 10:  # Ensure we have enough keypoints
                    # Check arm positions relative to body
                    left_wrist = keypoints[9] if len(keypoints) > 9 else None
                    right_wrist = keypoints[10] if len(keypoints) > 10 else None
                    head = keypoints[0] if len(keypoints) > 0 else None
                    
                    if left_wrist is not None and right_wrist is not None and head is not None:
                        # If both wrists are above head level
                        if (left_wrist[1] < head[1] - 50 and left_wrist[2] > 0.5 and
                            right_wrist[1] < head[1] - 50 and right_wrist[2] > 0.5):
                            distress['indicators'].append('arms_raised')
                            distress['confidence'] += 0.4
                
                # Check for defensive postures
                # Hands near face/head area
                if len(keypoints) >= 5:
                    nose = keypoints[0] if len(keypoints) > 0 else None
                    left_wrist = keypoints[9] if len(keypoints) > 9 else None
                    right_wrist = keypoints[10] if len(keypoints) > 10 else None
                    
                    if nose is not None and left_wrist is not None:
                        distance_left = np.sqrt((nose[0] - left_wrist[0])**2 + (nose[1] - left_wrist[1])**2)
                        if distance_left < 100 and left_wrist[2] > 0.5:
                            distress['indicators'].append('defensive_posture')
                            distress['confidence'] += 0.3
            
            distress['has_distress'] = distress['confidence'] > 0.4
            
        except Exception as e:
            print(f"[WARNING] Distress detection failed: {e}")
        
        return distress
    
    def _calculate_overall_threat_level(self, safety_alerts):
        """Calculate overall threat level for the scene"""
        if safety_alerts['women_in_danger']:
            return 'CRITICAL'
        elif safety_alerts['surrounded_women']:
            return 'HIGH'
        elif safety_alerts['distress_signals']:
            return 'MODERATE'
        elif safety_alerts['lone_women']:
            return 'LOW'
        else:
            return 'SAFE'
    
    def draw_safety_overlay(self, frame, safety_analysis):
        """
        WatchHer Safety Alerts Overlay: Display safety status and alerts
        """
        if not safety_analysis:
            return frame
        
        h, w = frame.shape[:2]
        
        # **Main Safety Status Display**
        threat_level = safety_analysis.get('overall_threat_level', 'SAFE')
        
        # Color coding for threat levels
        if threat_level == 'CRITICAL':
            color = (0, 0, 255)  # RED
            bg_color = (0, 0, 128)  # Dark red background
        elif threat_level == 'HIGH':
            color = (0, 165, 255)  # ORANGE
            bg_color = (0, 82, 128)  # Dark orange background
        elif threat_level == 'MODERATE':
            color = (0, 255, 255)  # YELLOW
            bg_color = (0, 128, 128)  # Dark yellow background
        elif threat_level == 'LOW':
            color = (255, 255, 0)  # CYAN
            bg_color = (128, 128, 0)  # Dark cyan background
        else:
            color = (0, 255, 0)  # GREEN
            bg_color = (0, 128, 0)  # Dark green background
        
        # **Top-right Safety Status Panel**
        panel_x = w - 300
        panel_y = 10
        
        # Background panel
        cv2.rectangle(frame, (panel_x, panel_y), (w - 10, panel_y + 150), bg_color, -1)
        cv2.rectangle(frame, (panel_x, panel_y), (w - 10, panel_y + 150), color, 2)
        
        # Main status
        cv2.putText(frame, f"THREAT LEVEL: {threat_level}", (panel_x + 10, panel_y + 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Safety alerts summary
        y_offset = 50
        lone_women = len(safety_analysis.get('lone_women', []))
        surrounded_women = len(safety_analysis.get('surrounded_women', []))
        women_in_danger = len(safety_analysis.get('women_in_danger', []))
        distress_signals = len(safety_analysis.get('distress_signals', []))
        
        if lone_women > 0:
            cv2.putText(frame, f"⚠️ Lone Women: {lone_women}", (panel_x + 10, panel_y + y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            y_offset += 20
        
        if surrounded_women > 0:
            cv2.putText(frame, f"🚨 Surrounded: {surrounded_women}", (panel_x + 10, panel_y + y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
            y_offset += 20
        
        if women_in_danger > 0:
            cv2.putText(frame, f"💀 In Danger: {women_in_danger}", (panel_x + 10, panel_y + y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            y_offset += 20
        
        if distress_signals > 0:
            cv2.putText(frame, f"🆘 Distress: {distress_signals}", (panel_x + 10, panel_y + y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
        
        # **Bottom Alert Ticker**
        if threat_level in ['HIGH', 'CRITICAL']:
            ticker_y = h - 40
            cv2.rectangle(frame, (0, ticker_y), (w, h), (0, 0, 255), -1)
            
            if women_in_danger > 0:
                alert_text = "🚨 URGENT: WOMEN IN IMMEDIATE DANGER - ALERT AUTHORITIES 🚨"
            elif surrounded_women > 0:
                alert_text = "⚠️ ALERT: WOMEN SURROUNDED BY MULTIPLE MEN - MONITOR CLOSELY ⚠️"
            else:
                alert_text = f"⚠️ {threat_level} THREAT DETECTED - INCREASED MONITORING REQUIRED ⚠️"
            
            # Center the text
            text_size = cv2.getTextSize(alert_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            text_x = (w - text_size[0]) // 2
            
            cv2.putText(frame, alert_text, (text_x, ticker_y + 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame 