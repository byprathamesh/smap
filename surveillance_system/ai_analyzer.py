import cv2
from ultralytics import YOLO
from deepface import DeepFace

class AIAnalyzer:
    def __init__(self):
        print("[INFO] Loading YOLOv11 model for person detection...")
        self.person_detector = YOLO('yolo11n.pt')
        print("[INFO] YOLOv11 model loaded successfully!")
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
        Two-stage AI analysis pipeline:
        1. Detect people using YOLOv11
        2. Analyze detected people for age and gender using DeepFace
        
        Returns:
            List of dictionaries containing bounding box, gender, and age for each detected person
        """
        detections = []
        
        # Stage 1: Detect people using YOLO
        results = self.person_detector.predict(frame, verbose=False)
        
        # Stage 2: Analyze each detected person
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get confidence and class
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    
                    # Filter for 'person' class (class_id = 0 in COCO dataset) with confidence > 0.5
                    if class_id == 0 and confidence > 0.5:
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        # Crop the person from the frame
                        cropped_person = frame[y1:y2, x1:x2]
                        
                        # Skip if cropped image is too small
                        if cropped_person.shape[0] < 30 or cropped_person.shape[1] < 30:
                            continue
                        
                        try:
                            # Analyze the cropped person image with DeepFace
                            analysis = DeepFace.analyze(
                                img_path=cropped_person,
                                actions=['age', 'gender'],
                                enforce_detection=False,
                                detector_backend='retinaface'
                            )
                            
                            # Extract gender and age (handle both list and dict responses)
                            if isinstance(analysis, list):
                                analysis = analysis[0]
                            
                            gender = analysis.get('dominant_gender', 'Unknown')
                            age = analysis.get('age', 0)
                            
                            # Convert age to age range for compatibility
                            if age < 18:
                                age_range = f"{max(0, age-2)}-{age+2}"
                            elif age < 65:
                                age_range = f"{age-3}-{age+3}"
                            else:
                                age_range = f"{age-5}-{age+5}"
                            
                            # Append detection dictionary with expected keys
                            detection_dict = {
                                'box': [x1, y1, x2-x1, y2-y1],  # Convert to x,y,w,h format
                                'gender': gender,
                                'age_range': age_range,
                                'confidence': confidence
                            }
                            detections.append(detection_dict)
                            
                        except Exception as e:
                            # Skip this detection if DeepFace analysis fails
                            print(f"[WARNING] DeepFace analysis failed for detection: {e}")
                            continue
        
        return detections 