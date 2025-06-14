import cv2
import numpy as np
import config
import os


class AIAnalyzer:
    """
    Advanced AI Analyzer class for context-aware threat analysis.
    Uses YOLOv3-tiny for object detection, gender classification, and age estimation.
    """
    
    def __init__(self):
        """
        Initialize the AI Analyzer by loading the required models.
        """
        self.yolo_net = None
        self.gender_net = None
        self.age_net = None
        self.class_names = []
        
        # Load YOLOv3-tiny object detection model
        self._load_yolo_model()
        
        # Load gender classification model
        self._load_gender_classification_model()
        
        # Load age estimation model
        self._load_age_estimation_model()
        
        print("Advanced AIAnalyzer initialized successfully")
    
    def _load_yolo_model(self):
        """
        Load the YOLOv3-tiny object detection model.
        """
        try:
            weights_path = config.MODEL_PATHS['object_detection']['weights']
            config_path = config.MODEL_PATHS['object_detection']['config']
            names_path = config.MODEL_PATHS['object_detection']['names']
            
            # Check if model files exist
            if not os.path.exists(weights_path):
                print(f"Warning: YOLO weights not found at {weights_path}")
                print("Please run 'python download_advanced_models.py' to download the required models.")
                return
            
            if not os.path.exists(config_path):
                print(f"Warning: YOLO config not found at {config_path}")
                print("Please run 'python download_advanced_models.py' to download the required models.")
                return
            
            if not os.path.exists(names_path):
                print(f"Warning: COCO names not found at {names_path}")
                print("Please run 'python download_advanced_models.py' to download the required models.")
                return
            
            # Load YOLO model
            self.yolo_net = cv2.dnn.readNet(weights_path, config_path)
            
            # Load class names
            with open(names_path, 'r') as f:
                self.class_names = [line.strip() for line in f.readlines()]
            
            print("YOLOv3-tiny object detection model loaded successfully")
            print(f"Loaded {len(self.class_names)} object classes")
            
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            self.yolo_net = None
    
    def _load_gender_classification_model(self):
        """
        Load the gender classification model using OpenCV DNN with Caffe format.
        """
        try:
            prototxt_path = config.MODEL_PATHS['gender_classification']['prototxt']
            model_path = config.MODEL_PATHS['gender_classification']['model']
            
            # Check if model files exist
            if not os.path.exists(prototxt_path):
                print(f"Warning: Gender classification prototxt not found at {prototxt_path}")
                print("Please run 'python download_models.py' to download the basic models.")
                return
            
            if not os.path.exists(model_path):
                print(f"Warning: Gender classification model not found at {model_path}")
                print("Please run 'python download_models.py' to download the basic models.")
                return
            
            # Load Caffe model
            self.gender_net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
            print("Gender classification model loaded successfully")
            
        except Exception as e:
            print(f"Error loading gender classification model: {e}")
            self.gender_net = None
    
    def _load_age_estimation_model(self):
        """
        Load the age estimation model using OpenCV DNN with Caffe format.
        """
        try:
            prototxt_path = config.MODEL_PATHS['age_estimation']['prototxt']
            model_path = config.MODEL_PATHS['age_estimation']['model']
            
            # Check if model files exist
            if not os.path.exists(prototxt_path):
                print(f"Warning: Age estimation prototxt not found at {prototxt_path}")
                print("Please run 'python download_advanced_models.py' to download the advanced models.")
                return
            
            if not os.path.exists(model_path):
                print(f"Warning: Age estimation model not found at {model_path}")
                print("Please run 'python download_advanced_models.py' to download the advanced models.")
                return
            
            # Load Caffe model
            self.age_net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
            print("Age estimation model loaded successfully")
            
        except Exception as e:
            print(f"Error loading age estimation model: {e}")
            self.age_net = None
    
    def _detect_objects(self, frame):
        """
        Detect objects in the given frame using YOLOv3-tiny.
        
        Args:
            frame: Input video frame (numpy array)
            
        Returns:
            List of detection results with bounding boxes, confidence scores, and class IDs
        """
        if self.yolo_net is None:
            return []
        
        try:
            # Get frame dimensions
            height, width = frame.shape[:2]
            
            # Create blob from frame for YOLO
            # YOLOv3-tiny typically uses 416x416 input
            blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
            
            # Set input to the network
            self.yolo_net.setInput(blob)
            
            # Get output layer names
            layer_names = self.yolo_net.getLayerNames()
            output_layers = [layer_names[i - 1] for i in self.yolo_net.getUnconnectedOutLayers()]
            
            # Run forward pass
            outputs = self.yolo_net.forward(output_layers)
            
            # Parse detections
            boxes = []
            confidences = []
            class_ids = []
            
            confidence_threshold = config.DETECTION_SETTINGS['person_detection_threshold']
            
            for output in outputs:
                for detection in output:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    
                    if confidence > confidence_threshold:
                        # Get bounding box coordinates
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        box_width = int(detection[2] * width)
                        box_height = int(detection[3] * height)
                        
                        # Calculate top-left corner
                        x = int(center_x - box_width / 2)
                        y = int(center_y - box_height / 2)
                        
                        # Ensure coordinates are within frame bounds
                        x = max(0, x)
                        y = max(0, y)
                        box_width = min(box_width, width - x)
                        box_height = min(box_height, height - y)
                        
                        boxes.append([x, y, box_width, box_height])
                        confidences.append(float(confidence))
                        class_ids.append(class_id)
            
            # Apply Non-Maximum Suppression
            indices = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, 0.4)
            
            detections = []
            if len(indices) > 0:
                for i in indices.flatten():
                    x, y, w, h = boxes[i]
                    detections.append({
                        'box': [x, y, w, h],
                        'confidence': confidences[i],
                        'class_id': class_ids[i],
                        'class_name': self.class_names[class_ids[i]] if class_ids[i] < len(self.class_names) else 'unknown'
                    })
            
            return detections
            
        except Exception as e:
            print(f"Error in object detection: {e}")
            return []
    
    def _classify_gender(self, person_roi):
        """
        Classify gender of a person from their region of interest.
        
        Args:
            person_roi: Person region of interest (numpy array)
            
        Returns:
            Tuple of (gender_label, confidence_score)
        """
        if self.gender_net is None:
            return "unknown", 0.0
        
        try:
            # Create blob from person ROI for gender classification
            # Gender model expects 227x227 input with specific mean subtraction
            blob = cv2.dnn.blobFromImage(person_roi, 1.0, (227, 227), 
                                       (78.4263377603, 87.7689143744, 114.895847746))
            
            # Set input to the network
            self.gender_net.setInput(blob)
            
            # Run forward pass
            gender_preds = self.gender_net.forward()
            
            # Get the prediction with highest confidence
            # Gender model outputs: [Male, Female]
            gender_labels = ['Male', 'Female']
            gender_idx = np.argmax(gender_preds)
            confidence = gender_preds[0][gender_idx]
            
            # Check if confidence meets threshold
            if confidence < config.DETECTION_SETTINGS['gender_classification_threshold']:
                return "unknown", float(confidence)
            
            return gender_labels[gender_idx], float(confidence)
            
        except Exception as e:
            print(f"Error in gender classification: {e}")
            return "unknown", 0.0
    
    def _estimate_age(self, person_roi):
        """
        Estimate age of a person from their region of interest.
        
        Args:
            person_roi: Person region of interest (numpy array)
            
        Returns:
            Tuple of (age_range, confidence_score)
        """
        if self.age_net is None:
            return "unknown", 0.0
        
        try:
            # Create blob from person ROI for age estimation
            # Age model expects 227x227 input with specific mean subtraction
            blob = cv2.dnn.blobFromImage(person_roi, 1.0, (227, 227), 
                                       (78.4263377603, 87.7689143744, 114.895847746))
            
            # Set input to the network
            self.age_net.setInput(blob)
            
            # Run forward pass
            age_preds = self.age_net.forward()
            
            # Age model outputs 8 age ranges: (0-2), (4-6), (8-12), (15-20), (25-32), (38-43), (48-53), (60-100)
            age_ranges = ['0-2', '4-6', '8-12', '15-20', '25-32', '38-43', '48-53', '60-100']
            
            # Get the prediction with highest confidence
            age_idx = np.argmax(age_preds)
            confidence = age_preds[0][age_idx]
            
            # Check if confidence meets threshold
            if confidence < config.DETECTION_SETTINGS['age_estimation_threshold']:
                return "unknown", float(confidence)
            
            age_range = age_ranges[age_idx] if age_idx < len(age_ranges) else 'unknown'
            
            return age_range, float(confidence)
            
        except Exception as e:
            print(f"Error in age estimation: {e}")
            return "unknown", 0.0
    
    def _get_age_category(self, age_range):
        """
        Convert age range to age category for risk scoring.
        
        Args:
            age_range: Age range string (e.g., "25-32")
            
        Returns:
            int: Approximate age for categorization
        """
        if age_range == "unknown":
            return 25  # Default to adult
        
        try:
            # Extract the lower bound of the age range
            age_lower = int(age_range.split('-')[0])
            return age_lower
        except:
            return 25  # Default to adult if parsing fails
    
    def analyze_frame(self, frame):
        """
        Main method to analyze a video frame for context-aware threat analysis.
        
        Args:
            frame: Input video frame (numpy array)
            
        Returns:
            List of dictionaries containing detection results:
            [
                {
                    "box": [x, y, w, h],
                    "gender": "Female",
                    "age_range": "25-32"
                },
                ...
            ]
        """
        if frame is None:
            return []
        
        # Step 1: Detect all objects in the frame using YOLO
        object_detections = self._detect_objects(frame)
        
        # Step 2: Filter for only 'person' objects
        person_detections = [det for det in object_detections if det['class_name'] == 'person']
        
        # Step 3: Process each detected person
        results = []
        
        for detection in person_detections:
            try:
                # Extract bounding box coordinates
                x, y, w, h = detection['box']
                
                # Extract region of interest (ROI) for the person
                person_roi = frame[y:y+h, x:x+w]
                
                # Skip if ROI is too small or invalid
                if person_roi.size == 0 or w < 30 or h < 30:
                    continue
                
                # Step 4: Classify gender for this person
                gender, gender_confidence = self._classify_gender(person_roi)
                
                # Step 5: Estimate age for this person
                age_range, age_confidence = self._estimate_age(person_roi)
                
                # Add to results with the new structure
                result = {
                    "box": [x, y, w, h],
                    "gender": gender,
                    "age_range": age_range,
                    "detection_confidence": detection['confidence'],
                    "gender_confidence": gender_confidence,
                    "age_confidence": age_confidence
                }
                
                results.append(result)
                
            except Exception as e:
                print(f"Error processing person detection: {e}")
                continue
        
        return results
    
    def is_ready(self):
        """
        Check if the analyzer is ready to process frames.
        
        Returns:
            bool: True if all models are loaded successfully
        """
        return (self.yolo_net is not None and 
                self.gender_net is not None and 
                self.age_net is not None and 
                len(self.class_names) > 0)
    
    def get_model_info(self):
        """
        Get information about the loaded models.
        
        Returns:
            dict: Model information
        """
        return {
            'yolo_loaded': self.yolo_net is not None,
            'gender_classification_loaded': self.gender_net is not None,
            'age_estimation_loaded': self.age_net is not None,
            'class_names_loaded': len(self.class_names),
            'object_detection_path': config.MODEL_PATHS['object_detection'],
            'gender_classification_path': config.MODEL_PATHS['gender_classification'],
            'age_estimation_path': config.MODEL_PATHS['age_estimation']
        } 