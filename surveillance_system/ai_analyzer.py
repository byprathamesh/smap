import cv2
from ultralytics import YOLO
from deepface import DeepFace
import tensorflow as tf

class AIAnalyzer:
    def __init__(self):
        print("[INFO] Loading YOLOv8 pose estimation model...")
        self.person_detector = YOLO('yolov8n-pose.pt')
        
        # **PART 3 FIX**: Ensure Explicit Device Placement for YOLO
        try:
            import torch
            if torch.cuda.is_available():
                self.person_detector.to('cuda')
                print("[INFO] ✅ YOLO model moved to GPU (CUDA)")
                print(f"[INFO] YOLO Device: {self.person_detector.device}")
            else:
                print("[INFO] ⚠️ CUDA not available, YOLO using CPU")
        except Exception as e:
            print(f"[WARNING] Could not move YOLO to GPU: {e}")
        
        # **PART 3 FIX**: Deep-check TensorFlow/DeepFace GPU Usage
        print("[INFO] Checking TensorFlow GPU availability...")
        tf_gpus = tf.config.list_physical_devices('GPU')
        if tf_gpus:
            print(f"[INFO] ✅ TensorFlow detected GPU devices: {[gpu.name for gpu in tf_gpus]}")
            try:
                # Ensure GPU memory growth is enabled
                for gpu in tf_gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                print("[INFO] ✅ TensorFlow GPU memory growth enabled")
            except Exception as e:
                print(f"[WARNING] Could not set TensorFlow GPU memory growth: {e}")
        else:
            print("[INFO] ⚠️ TensorFlow will run on CPU - no GPU devices found")
        
        print("[INFO] YOLOv8 pose model loaded successfully!")
        self.ready = True
    
    def is_ready(self):
        """
        Check if the analyzer is ready for processing.
        
        Returns:
            bool: True if analyzer is ready
        """
        return self.ready
    
    def analyze_frame(self, frame):
        """
        Three-stage AI analysis pipeline:
        1. Detect people and poses using YOLOv8-pose
        2. Check for distress signals from pose keypoints
        3. Analyze detected people for age and gender using DeepFace
        
        Returns:
            List of dictionaries containing bounding box, gender, age, and distress status for each detected person
        """
        detections = []
        
        # **PART 3 FIX**: Add TensorFlow device logging before DeepFace calls
        tf_gpus = tf.config.list_physical_devices('GPU')
        if tf_gpus:
            print(f"DEBUG_AN: TensorFlow is using GPU: {tf_gpus[0].name}")
        else:
            print("DEBUG_AN: TensorFlow is running on CPU.")
        
        # Stage 1: Detect people and poses using YOLO
        print(f"DEBUG_AI: Starting YOLO detection on frame of shape {frame.shape}")
        results = self.person_detector.predict(frame, verbose=False)
        
        # NEW DEBUG: Check YOLO device and raw detection count
        print(f"DEBUG_AN: YOLO predict device: {self.person_detector.device}")
        print(f"DEBUG_AN: YOLO detected raw boxes: {len(results[0].boxes) if results and results[0].boxes is not None else 0}")
        
        print(f"DEBUG_AI: YOLO returned {len(results)} result objects")
        
        # Count total raw detections across all results
        total_raw_detections = 0
        for result in results:
            if result.boxes is not None:
                total_raw_detections += len(result.boxes)
        print(f"DEBUG_AI: Number of raw YOLO detections: {total_raw_detections}")
        
        # Stage 2 & 3: Analyze each detected person
        for result in results:
            boxes = result.boxes
            keypoints = result.keypoints if hasattr(result, 'keypoints') else None
            
            if boxes is not None:
                print(f"DEBUG_AI: Processing {len(boxes)} detections from this result")
                
                for i, box in enumerate(boxes):
                    # Get confidence and class
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    
                    # NEW DEBUG: Detailed box processing info
                    print(f"DEBUG_AN: Processing box: {box.xyxy[0]} class: {self.person_detector.names[class_id]} conf: {confidence:.3f}")
                    
                    print(f"DEBUG_AI: Detection {i}: class_id={class_id}, confidence={confidence:.3f}")
                    
                    # Filter for 'person' class (class_id = 0 in COCO dataset) with confidence > 0.5
                    if class_id == 0 and confidence > 0.5:
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        print(f"DEBUG_AI: Person detected at bbox: ({x1}, {y1}, {x2}, {y2})")
                        
                        # Stage 2: Check for distress pose if keypoints are available
                        distress_detected = False
                        if keypoints is not None and len(keypoints.xy) > i:
                            person_keypoints = keypoints.xy[i].cpu().numpy()
                            distress_detected = self._check_distress_pose(person_keypoints, x1, y1, x2, y2)
                            print(f"DEBUG_AI: Distress detection result: {distress_detected}")
                        else:
                            print(f"DEBUG_AI: No keypoints available for distress detection")
                        
                        # Crop the person from the frame
                        cropped_person = frame[y1:y2, x1:x2]
                        
                        # Check crop size
                        if cropped_person.shape[0] < 30 or cropped_person.shape[1] < 30:
                            print(f"DEBUG_AI: Skipping detection - crop too small: {cropped_person.shape}")
                            continue
                        
                        print(f"DEBUG_AI: Cropped person image shape: {cropped_person.shape}")
                        
                        # Initialize default values in case DeepFace fails
                        gender = "Unknown"
                        age_range = "Unknown"
                        
                        try:
                            # Stage 3: Analyze the cropped person image with DeepFace
                            print(f"DEBUG_AN: Calling DeepFace on cropped image size: {cropped_person.shape}")
                            print(f"DEBUG_AI: Starting DeepFace analysis...")
                            analysis = DeepFace.analyze(
                                img_path=cropped_person,
                                actions=['age', 'gender'],
                                enforce_detection=False,
                                detector_backend='opencv'  # Using opencv instead of retinaface for better reliability
                            )
                            
                            # Extract gender and age (handle both list and dict responses)
                            if isinstance(analysis, list):
                                analysis = analysis[0]
                            
                            gender = analysis.get('dominant_gender', 'Unknown')
                            age = analysis.get('age', 25)  # Default age if not detected
                            
                            # Convert age to age range for compatibility
                            if age < 18:
                                age_range = f"{max(0, age-2)}-{age+2}"
                            elif age < 65:
                                age_range = f"{age-3}-{age+3}"
                            else:
                                age_range = f"{age-5}-{age+5}"
                            
                            # NEW DEBUG: DeepFace success result
                            print(f"DEBUG_AN: DeepFace result: {gender} {age_range}")
                            print(f"DEBUG_AI: DeepFace results - Gender: {gender}, Age: {age}, Age Range: {age_range}")
                            
                        except Exception as e:
                            # Keep the detection even if DeepFace fails
                            print(f"DEBUG_AN: DeepFace failed for this person: {e}")
                            print(f"DEBUG_AI: DeepFace analysis failed, using defaults: {e}")
                            gender = "Unknown"
                            age_range = "Unknown"
                        
                        # Append detection dictionary with expected keys
                        detection_dict = {
                            'box': [x1, y1, x2-x1, y2-y1],  # Convert to x,y,w,h format
                            'gender': gender,
                            'age_range': age_range,
                            'confidence': confidence,
                            'distress': distress_detected
                        }
                        detections.append(detection_dict)
                        
                        print(f"DEBUG_AI: Processed detection (box, gender, age, distress): {detection_dict}")
                    else:
                        print(f"DEBUG_AI: Skipping detection - not person or low confidence")
            else:
                print(f"DEBUG_AI: No boxes in this result")
        
        # NEW DEBUG: Final count before return
        print(f"DEBUG_AN: Final detections count from AIAnalyzer: {len(detections)}")
        print(f"DEBUG_AI: Final detections count: {len(detections)}")
        return detections
    
    def _check_distress_pose(self, keypoints, x1, y1, x2, y2):
        """
        Check if the detected person is showing distress signals based on pose keypoints.
        
        Args:
            keypoints: YOLO pose keypoints array [17, 2] for COCO format
            x1, y1, x2, y2: Bounding box coordinates
            
        Returns:
            bool: True if distress signal detected, False otherwise
        """
        try:
            # COCO pose keypoints indices:
            # 0: nose, 1: left_eye, 2: right_eye, 3: left_ear, 4: right_ear
            # 5: left_shoulder, 6: right_shoulder, 7: left_elbow, 8: right_elbow
            # 9: left_wrist, 10: right_wrist, 11: left_hip, 12: right_hip
            # 13: left_knee, 14: right_knee, 15: left_ankle, 16: right_ankle
            
            if len(keypoints) < 17:
                return False
            
            nose = keypoints[0]
            left_wrist = keypoints[9]
            right_wrist = keypoints[10]
            left_shoulder = keypoints[5]
            right_shoulder = keypoints[6]
            
            # Check 1: Hands Up (both wrists above nose level)
            hands_up = False
            if (nose[1] > 0 and left_wrist[1] > 0 and right_wrist[1] > 0):
                if left_wrist[1] < nose[1] and right_wrist[1] < nose[1]:
                    hands_up = True
                    print(f"[DISTRESS] Hands up detected!")
            
            # Check 2: Falling detection (person is horizontal)
            bbox_width = x2 - x1
            bbox_height = y2 - y1
            falling = False
            if bbox_height > 0 and bbox_width / bbox_height > 1.5:
                falling = True
                print(f"[DISTRESS] Falling position detected!")
            
            # Check 3: Arms spread wide (distress signal)
            arms_spread = False
            if (left_shoulder[0] > 0 and right_shoulder[0] > 0 and 
                left_wrist[0] > 0 and right_wrist[0] > 0):
                shoulder_width = abs(right_shoulder[0] - left_shoulder[0])
                arm_span = abs(right_wrist[0] - left_wrist[0])
                if shoulder_width > 0 and arm_span / shoulder_width > 1.8:
                    arms_spread = True
                    print(f"[DISTRESS] Arms spread wide detected!")
            
            return hands_up or falling or arms_spread
            
        except Exception as e:
            print(f"[WARNING] Error in distress pose detection: {e}")
            return False 