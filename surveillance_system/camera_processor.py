import cv2
import threading
import time
import math
import os
from datetime import datetime
from ai_analyzer import AIAnalyzer
from alert_system import trigger_alert, is_night_time
import config


class CameraProcessor:
    """
    Camera processor class that handles video stream processing for a single camera.
    Runs in a separate thread and performs person detection, threat analysis, and real-time visualization.
    """
    
    def __init__(self, camera_id, camera_config):
        """
        Initialize the camera processor.
        
        Args:
            camera_id: Identifier for the camera (e.g., 'camera_1')
            camera_config: Dictionary containing camera configuration
        """
        self.camera_id = camera_id
        self.camera_url = camera_config['url']
        self.camera_name = camera_config['name']
        self.camera_location = camera_config.get('location', 'Unknown')
        
        # Initialize AI analyzer
        try:
            self.analyzer = AIAnalyzer()
        except SystemExit:
            # Re-raise SystemExit from AI analyzer
            print(f"[FATAL] Cannot initialize AI analyzer for camera {self.camera_id}")
            raise
        except Exception as e:
            print(f"[ERROR] Failed to initialize AI analyzer for camera {self.camera_id}: {e}")
            self.analyzer = None
        
        # Thread control
        self.running = False
        self.thread = None
        
        # Video capture object
        self.cap = None
        
        # Processing settings
        self.frame_rate = 2.0  # Process 2 frames per second (configurable)
        self.frame_interval = 1.0 / self.frame_rate
        
        # Tracking for lone woman detection
        self.lone_woman_start_time = None
        self.lone_woman_detected = False
        
        print(f"CameraProcessor initialized for {self.camera_name} ({self.camera_id})")
    
    def start(self):
        """
        Start the camera processing thread.
        """
        if not self.running:
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            print(f"Started processing thread for camera {self.camera_id}")
    
    def run(self):
        """
        Main processing loop that runs continuously in a thread.
        Handles video capture, frame analysis, threat assessment, and real-time visualization.
        """
        self.running = True
        reconnect_delay = 5  # seconds to wait before reconnecting
        
        print(f"Starting video processing for {self.camera_name}")
        
        # Pre-check for video file existence if it's a file path
        if isinstance(self.camera_url, str) and not self.camera_url.startswith(('http://', 'https://', 'rtsp://')):
            if not os.path.exists(self.camera_url):
                print(f"[ERROR] Video file not found at path: {self.camera_url}")
                print(f"[INFO] Please check the file path in config.py for camera {self.camera_id}")
                print(f"[INFO] Current working directory: {os.getcwd()}")
                self.running = False
                return
        
        while self.running:
            try:
                # Initialize video capture
                if not self._initialize_camera():
                    print(f"Failed to initialize camera {self.camera_id}, retrying in {reconnect_delay} seconds...")
                    time.sleep(reconnect_delay)
                    continue
                
                # Main processing loop
                last_frame_time = time.time()
                
                while self.running and self.cap and self.cap.isOpened():
                    # Control frame rate
                    current_time = time.time()
                    if current_time - last_frame_time < self.frame_interval:
                        time.sleep(0.1)  # Small sleep to prevent busy waiting
                        continue
                    
                    # Read frame from camera
                    try:
                        ret, frame = self.cap.read()
                        
                        if not ret or frame is None:
                            print(f"[WARNING] Failed to read frame from camera {self.camera_id}")
                            print(f"[INFO] This may be due to end of video file or camera disconnection")
                            break
                    except Exception as e:
                        print(f"[ERROR] Exception while reading frame from camera {self.camera_id}: {e}")
                        break
                    
                    # Check if analyzer is available and ready
                    if self.analyzer is None:
                        print(f"[ERROR] AI analyzer not available for camera {self.camera_id}")
                        break
                    
                    if not self.analyzer.is_ready():
                        continue
                    
                    # Step 1: Analyze frame for person detection and classification
                    detections = self.analyzer.analyze_frame(frame)
                    
                    # Step 2: Calculate threat score using Risk Scoring Algorithm
                    if detections:
                        threat_score = self._analyze_threat_level(frame, detections)
                    else:
                        # Reset lone woman tracking if no people detected
                        self._reset_lone_woman_tracking()
                        threat_score = 0
                    
                    # Step 3: Display frame with all visualizations
                    self._display_frame_with_overlay(frame, threat_score, detections)
                    
                    # Check for exit key
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print(f"[INFO] Exit key pressed for camera {self.camera_id}")
                        break
                    
                    last_frame_time = current_time
                
            except Exception as e:
                print(f"Error in camera processing loop for {self.camera_id}: {e}")
            
            finally:
                # Clean up camera connection
                self._cleanup_camera()
            
            # Wait before attempting to reconnect
            if self.running:
                print(f"Camera {self.camera_id} disconnected, attempting reconnect in {reconnect_delay} seconds...")
                time.sleep(reconnect_delay)
        
        print(f"Camera processor stopped for {self.camera_id}")
    
    def _initialize_camera(self):
        """
        Initialize the video capture for the camera.
        
        Returns:
            bool: True if camera was successfully initialized
        """
        try:
            # Check if it's a file path and verify it exists
            if isinstance(self.camera_url, str) and (self.camera_url.endswith('.mp4') or 
                                                   self.camera_url.endswith('.avi') or
                                                   self.camera_url.endswith('.webm') or
                                                   self.camera_url.endswith('.mov')):
                if not os.path.exists(self.camera_url):
                    print(f"[ERROR] Video file not found at path: {self.camera_url}")
                    print("[INFO] Please check the file path in config.py")
                    return False
            
            self.cap = cv2.VideoCapture(self.camera_url)
            
            if not self.cap.isOpened():
                print(f"[ERROR] Could not open camera/video stream: {self.camera_url}")
                if isinstance(self.camera_url, str) and self.camera_url.startswith('http'):
                    print("[INFO] If this is an IP camera, check network connectivity and camera settings")
                return False
            
            # Set buffer size to reduce latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Test read a frame
            ret, frame = self.cap.read()
            if not ret or frame is None:
                print(f"[ERROR] Could not read initial frame from camera {self.camera_id}")
                return False
            
            print(f"Camera {self.camera_id} initialized successfully")
            return True
            
        except cv2.error as e:
            print(f"[ERROR] OpenCV error initializing camera {self.camera_id}: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Unexpected error initializing camera {self.camera_id}: {e}")
            return False
    
    def _cleanup_camera(self):
        """
        Clean up camera resources.
        """
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def _analyze_threat_level(self, frame, detections):
        """
        Analyze threat level using the Risk Scoring Algorithm (RSA).
        
        Args:
            frame: Current video frame
            detections: List of person detections with gender and age information
            
        Returns:
            int: Calculated threat score
        """
        try:
            # Initialize threat score
            threat_score = 0
            
            if not detections:
                # Reset lone woman tracking if no people detected
                self._reset_lone_woman_tracking()
                return 0
            
            # Get risk scoring settings
            risk_settings = config.DETECTION_SETTINGS['risk_scoring']
            
            # Check for lone female (single person detected and female)
            if len(detections) == 1 and detections[0]['gender'] == 'Female':
                threat_score += risk_settings['lone_female_score']
                print(f"[RSA] Lone female detected (+{risk_settings['lone_female_score']} points)")
            
            # Analyze each person and apply demographic modifiers
            females = []
            males = []
            children = []
            elderly = []
            
            for person in detections:
                age_category = self._get_age_from_range(person['age_range'])
                gender = person['gender']
                
                # Categorize person
                if age_category < risk_settings['child_age_threshold']:
                    children.append(person)
                elif age_category > risk_settings['elderly_age_threshold']:
                    elderly.append(person)
                elif gender == 'Female':
                    females.append(person)
                elif gender == 'Male':
                    males.append(person)
            
            # Apply demographic score modifiers
            if len(females) > 0:
                # For each adult male near females
                for male in males:
                    if self._is_near_females(male, females):
                        threat_score += risk_settings['adult_male_near_female_score']
                        print(f"[RSA] Adult male near female (+{risk_settings['adult_male_near_female_score']} points)")
                
                # Reduce threat for other adult females (safety in numbers)
                if len(females) > 1:
                    other_females_modifier = (len(females) - 1) * risk_settings['other_female_score_modifier']
                    threat_score += other_females_modifier
                    print(f"[RSA] {len(females)-1} other females ({other_females_modifier} points)")
            
            # Reduce threat for children present
            if len(children) > 0:
                children_modifier = len(children) * risk_settings['child_score_modifier']
                threat_score += children_modifier
                print(f"[RSA] {len(children)} children present ({children_modifier} points)")
            
            # Reduce threat for elderly present
            if len(elderly) > 0:
                elderly_modifier = len(elderly) * risk_settings['elderly_score_modifier']
                threat_score += elderly_modifier
                print(f"[RSA] {len(elderly)} elderly present ({elderly_modifier} points)")
            
            # Apply night time multiplier
            if is_night_time():
                original_score = threat_score
                threat_score = int(threat_score * risk_settings['night_multiplier'])
                print(f"[RSA] Night time multiplier applied: {original_score} -> {threat_score}")
            
            # Check if threat score exceeds threshold
            if threat_score >= risk_settings['threat_alert_threshold']:
                # Create detailed threat analysis
                details = self._create_threat_details(detections, threat_score, females, males, children, elderly)
                
                success = trigger_alert(frame, self.camera_id, 'high_threat_detected', details)
                if success:
                    print(f"[RSA] High threat alert triggered for camera {self.camera_id} (Score: {threat_score})")
            else:
                print(f"[RSA] Threat score: {threat_score} (Below threshold: {risk_settings['threat_alert_threshold']})")
            
            return threat_score
                
        except Exception as e:
            print(f"Error in threat level analysis for camera {self.camera_id}: {e}")
            return 0
    
    def _get_age_from_range(self, age_range):
        """
        Convert age range to approximate age for categorization.
        
        Args:
            age_range: Age range string (e.g., "25-32")
            
        Returns:
            int: Approximate age
        """
        if age_range == "unknown":
            return 25  # Default to adult
        
        try:
            # Extract the lower bound of the age range
            age_lower = int(age_range.split('-')[0])
            return age_lower
        except:
            return 25  # Default to adult if parsing fails
    
    def _is_near_females(self, male_person, females):
        """
        Check if a male person is near any female persons.
        
        Args:
            male_person: Male person detection data
            females: List of female person detections
            
        Returns:
            bool: True if male is near any female
        """
        try:
            proximity_threshold = config.DETECTION_SETTINGS['group_proximity_threshold']
            
            # Calculate center point of male's bounding box
            mx, my, mw, mh = male_person['box']
            male_center = (mx + mw // 2, my + mh // 2)
            
            # Check distance to each female
            for female in females:
                fx, fy, fw, fh = female['box']
                female_center = (fx + fw // 2, fy + fh // 2)
                
                # Calculate distance between centers
                distance = math.sqrt(
                    (male_center[0] - female_center[0]) ** 2 + 
                    (male_center[1] - female_center[1]) ** 2
                )
                
                if distance <= proximity_threshold:
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error calculating proximity for camera {self.camera_id}: {e}")
            return False
    
    def _create_threat_details(self, detections, threat_score, females, males, children, elderly):
        """
        Create detailed threat analysis for alert.
        
        Args:
            detections: All person detections
            threat_score: Final calculated threat score
            females, males, children, elderly: Categorized person lists
            
        Returns:
            str: Detailed threat analysis
        """
        try:
            details = f"Threat Score: {threat_score} | "
            details += f"Total People: {len(detections)} | "
            details += f"Females: {len(females)}, Males: {len(males)}, "
            details += f"Children: {len(children)}, Elderly: {len(elderly)}"
            
            if is_night_time():
                details += " | Night Time"
            
            return details
            
        except Exception as e:
            print(f"Error creating threat details: {e}")
            return f"Threat Score: {threat_score}"
    
    def _display_frame_with_overlay(self, frame, threat_score, detections=None):
        """
        Display frame with complete visual overlay including threat score and person bounding boxes.
        
        Args:
            frame: Video frame to display
            threat_score: Current threat score to overlay
            detections: List of detected persons with their information
        """
        try:
            # Create a copy of the frame for overlay
            display_frame = frame.copy()
            
            # Step 1: Draw individual person bounding boxes and labels
            if detections:
                for person in detections:
                    try:
                        # Extract bounding box coordinates
                        x, y, w, h = person['box']
                        
                        # Draw bright green bounding box around the person
                        cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        
                        # Create label text with gender and age
                        gender = person.get('gender', 'Unknown')
                        age_range = person.get('age_range', 'Unknown')
                        label_text = f"{gender}, {age_range}"
                        
                        # Add confidence information if available
                        if 'gender_confidence' in person and 'age_confidence' in person:
                            gender_conf = person['gender_confidence']
                            age_conf = person['age_confidence']
                            label_text += f" ({gender_conf:.1f}, {age_conf:.1f})"
                        
                        # Calculate label position (above the bounding box)
                        label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                        label_x = x
                        label_y = y - 10 if y - 10 > 10 else y + h + 25
                        
                        # Draw background rectangle for label readability
                        cv2.rectangle(display_frame, 
                                    (label_x, label_y - label_size[1] - 5), 
                                    (label_x + label_size[0] + 5, label_y + 5), 
                                    (0, 0, 0), -1)
                        
                        # Draw the label text
                        cv2.putText(display_frame, label_text, (label_x + 2, label_y), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        
                    except Exception as e:
                        print(f"Error drawing person detection: {e}")
                        continue
            
            # Step 2: Draw overall threat score overlay at top
            # Determine status and color based on threat score
            if threat_score < 15:
                status_text = f"Risk Score: {threat_score} (Low)"
                color = (0, 255, 0)  # Green
            elif threat_score < 25:
                status_text = f"Risk Score: {threat_score} (Medium)"
                color = (0, 255, 255)  # Yellow
            else:
                status_text = f"Risk Score: {threat_score} (High Threat!)"
                color = (0, 0, 255)  # Red
            
            # Get frame dimensions
            height, width = display_frame.shape[:2]
            
            # Draw black background bar for text readability
            bar_height = 60
            cv2.rectangle(display_frame, (0, 0), (width, bar_height), (0, 0, 0), -1)
            
            # Add camera name and timestamp
            camera_text = f"Camera: {self.camera_name} ({self.camera_id})"
            timestamp_text = f"Time: {time.strftime('%H:%M:%S')}"
            
            # Draw text on the overlay
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            thickness = 2
            
            # Camera name (top left)
            cv2.putText(display_frame, camera_text, (10, 25), font, font_scale, (255, 255, 255), thickness)
            
            # Timestamp (top right)
            text_size = cv2.getTextSize(timestamp_text, font, font_scale, thickness)[0]
            cv2.putText(display_frame, timestamp_text, (width - text_size[0] - 10, 25), font, font_scale, (255, 255, 255), thickness)
            
            # Threat score (center, larger)
            threat_font_scale = 0.8
            threat_thickness = 2
            threat_text_size = cv2.getTextSize(status_text, font, threat_font_scale, threat_thickness)[0]
            threat_x = (width - threat_text_size[0]) // 2
            cv2.putText(display_frame, status_text, (threat_x, 50), font, threat_font_scale, color, threat_thickness)
            
            # Step 3: Display the final frame
            try:
                window_name = f"WatchHer - {self.camera_name}"
                cv2.imshow(window_name, display_frame)
            except cv2.error as e:
                print(f"[ERROR] Display error for camera {self.camera_id}: {e}")
                print("[INFO] This may be due to display/GUI issues. Check if display is available.")
                print("[INFO] On remote servers, you may need X11 forwarding or run in headless mode.")
            except Exception as e:
                print(f"[ERROR] Unexpected display error for camera {self.camera_id}: {e}")
                print("[INFO] OpenCV may not be compiled with GUI support.")
            
        except Exception as e:
            print(f"Error displaying frame for camera {self.camera_id}: {e}")
    
    def _reset_lone_woman_tracking(self):
        """
        Reset the lone woman detection tracking variables.
        """
        self.lone_woman_start_time = None
        self.lone_woman_detected = False
    
    def stop(self):
        """
        Stop the camera processing thread gracefully.
        """
        print(f"Stopping camera processor for {self.camera_id}")
        self.running = False
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        
        # Clean up camera resources
        self._cleanup_camera()
        
        # Close OpenCV windows
        cv2.destroyAllWindows()
        
        print(f"Camera processor stopped for {self.camera_id}")
    
    def get_status(self):
        """
        Get the current status of the camera processor.
        
        Returns:
            dict: Status information
        """
        return {
            'camera_id': self.camera_id,
            'camera_name': self.camera_name,
            'running': self.running,
            'analyzer_ready': self.analyzer.is_ready() if self.analyzer else False,
            'camera_connected': self.cap is not None and self.cap.isOpened() if self.cap else False,
            'lone_woman_tracking': self.lone_woman_detected
        } 