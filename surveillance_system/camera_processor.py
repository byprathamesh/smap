import cv2
import threading
import time
import math
import os
import numpy as np
from datetime import datetime
from ai_analyzer import AIAnalyzer
from alert_system import trigger_alert, is_night_time
import config

"""
PERFORMANCE NOTE:
The YOLOv8-Pose and DeepFace models are computationally intensive. When running on CPU-only systems:
- FPS will typically be very low (0.1-2 FPS)
- Display windows may show "Not Responding" during processing
- This is EXPECTED behavior for CPU-only execution

For real-time performance (>10 FPS), a CUDA-enabled NVIDIA GPU is REQUIRED.
The models will automatically use GPU if available, otherwise fall back to CPU.
"""

class CameraProcessor:
    """
    Camera processor class that handles video stream processing for a single camera.
    Runs in a separate thread and performs person detection, threat analysis, and real-time visualization.
    """

    def __init__(self, camera_id=None, camera_config=None, source=None):
        """
        Initialize the camera processor.

        Args:
            camera_id: Identifier for the camera (e.g., 'camera_1')
            camera_config: Dictionary containing camera configuration
            source: Direct source for video (file path or camera index) - used for simplified interface
        """
        if source is not None:
            # Simplified interface for direct video file or camera access
            self.camera_id = f"source_{source}" if isinstance(source, int) else f"file_{os.path.basename(str(source))}"
            self.camera_url = source
            self.camera_name = f"Source {source}" if isinstance(source, int) else f"Video File: {os.path.basename(str(source))}"
            self.camera_location = "Direct Source"
        else:
            # Traditional config-based interface
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
            if len(detections) == 1 and detections[0]['gender'] == 'Woman':
                threat_score += risk_settings['lone_female_score']
                print(f"[RSA] Lone female detected (+{risk_settings['lone_female_score']} points)")

            # Analyze each person and apply demographic modifiers
            females = []
            males = []
            children = []
            elderly = []
            distressed_people = []

            for person in detections:
                # Initialize flags that might be missing
                if 'surrounded' not in person:
                    person['surrounded'] = False
                if 'distress' not in person:
                    person['distress'] = False

                age_category = self._get_age_from_range(person['age_range'])
                gender = person['gender']

                # Check for distress signals
                if person.get('distress', False):
                    distressed_people.append(person)
                    print(f"[DISTRESS] Distress signal detected for {gender}")

                # Categorize person
                if age_category < risk_settings['child_age_threshold']:
                    children.append(person)
                elif age_category > risk_settings['elderly_age_threshold']:
                    elderly.append(person)
                elif gender == 'Woman':
                    females.append(person)
                elif gender == 'Man':
                    males.append(person)

            # Apply distress signal modifiers (highest priority)
            if len(distressed_people) > 0:
                distress_bonus = len(distressed_people) * 30  # High penalty for distress
                threat_score += distress_bonus
                print(f"[RSA] {len(distressed_people)} distress signals detected (+{distress_bonus} points)")

                # Trigger immediate distress alert
                for person in distressed_people:
                    from alert_system import trigger_alert
                    success = trigger_alert(frame, self.camera_id, 'distress_signal', 
                                          f"Distress signal detected: {person['gender']}", threat_score)
                    if success:
                        print(f"[ALERT] Distress signal alert triggered")

            # Apply demographic score modifiers and surrounding logic
            if len(females) > 0:
                # Check for "woman surrounded" scenarios
                for female in females:
                    surrounding_males = self._count_surrounding_males(female, males)
                    if surrounding_males >= 2:  # 2 or more males surrounding a woman
                        # IMPORTANT: Add 'surrounded' flag to the female detection
                        female['surrounded'] = True

                        surrounded_bonus = surrounding_males * 15
                        threat_score += surrounded_bonus
                        print(f"[RSA] Woman potentially surrounded by {surrounding_males} males (+{surrounded_bonus} points)")

                        # Trigger specific "surrounded" alert
                        from alert_system import trigger_alert
                        details = f"Woman potentially surrounded by {surrounding_males} males"
                        success = trigger_alert(frame, self.camera_id, 'surrounded', details, threat_score)
                        if success:
                            print(f"[ALERT] Woman surrounded alert triggered")
                    else:
                        # Ensure flag is set to False if not surrounded
                        female['surrounded'] = False

                # For each adult male near females (general proximity)
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

                success = trigger_alert(frame, self.camera_id, 'high_threat_detected', details, threat_score)
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

    def _count_surrounding_males(self, female_person, males):
        """
        Count how many males are surrounding a specific female person.

        Args:
            female_person: Female person detection data
            males: List of male person detections

        Returns:
            int: Number of males within proximity threshold
        """
        try:
            proximity_threshold = 150  # Closer threshold for "surrounding" detection

            # Calculate center point of female's bounding box
            fx, fy, fw, fh = female_person['box']
            female_center = (fx + fw // 2, fy + fh // 2)

            surrounding_count = 0

            # Check distance to each male
            for male in males:
                mx, my, mw, mh = male['box']
                male_center = (mx + mw // 2, my + mh // 2)

                # Calculate distance between centers
                distance = math.sqrt(
                    (female_center[0] - male_center[0]) ** 2 + 
                    (female_center[1] - male_center[1]) ** 2
                )

                if distance <= proximity_threshold:
                    surrounding_count += 1

            return surrounding_count

        except Exception as e:
            print(f"Error counting surrounding males for camera {self.camera_id}: {e}")
            return 0

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
            # **PART 1 FIX**: Critical debugging for multi-person display
            if detections and len(detections) > 0:
                # Print only first few detections to avoid spamming console
                for i, det in enumerate(detections[:3]): # Print up to 3 detections

            # Create a copy of the frame for overlay
            display_frame = frame.copy()

            # Step 1: Draw individual person bounding boxes and labels
            if detections:
                for i, person in enumerate(detections):
                    # NEW DEBUG: Log each detection being drawn
                    try:
                        # Extract bounding box coordinates
                        x, y, w, h = person['box']

                        # Determine box color based on status
                        box_color = (0, 255, 0)  # Default green
                        if person.get('distress', False):
                            box_color = (0, 0, 255)  # Red for distress
                        elif person.get('surrounded', False):
                            box_color = (0, 165, 255)  # Orange for surrounded

                        # Draw bounding box around the person
                        cv2.rectangle(display_frame, (x, y), (x + w, y + h), box_color, 3)

                        # Create label text with gender and age
                        gender = person.get('gender', 'Unknown')
                        age_range = person.get('age_range', 'Unknown')
                        confidence = person.get('confidence', 0.0)

                        # Base label
                        label_text = f"{gender}, {age_range}"
                        if confidence > 0:
                            label_text += f" ({confidence:.2f})"

                        # Add special status indicators
                        status_indicators = []
                        if person.get('distress', False):
                            status_indicators.append("DISTRESS!")
                        if person.get('surrounded', False):
                            status_indicators.append("SURROUNDED!")

                        # Calculate label position (above the bounding box)
                        label_y = y - 10 if y - 10 > 20 else y + h + 25

                        # Draw background rectangle for main label
                        label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                        cv2.rectangle(display_frame, 
                                    (x, label_y - label_size[1] - 5), 
                                    (x + label_size[0] + 10, label_y + 5), 
                                    (0, 0, 0), -1)

                        # Draw the main label text
                        cv2.putText(display_frame, label_text, (x + 5, label_y), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                        # Draw status indicators below main label
                        status_y = label_y + 25
                        for status in status_indicators:
                            status_size = cv2.getTextSize(status, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                            # Draw background for status
                            cv2.rectangle(display_frame, 
                                        (x, status_y - status_size[1] - 3), 
                                        (x + status_size[0] + 10, status_y + 3), 
                                        (0, 0, 255), -1)  # Red background for alerts
                            # Draw status text
                            cv2.putText(display_frame, status, (x + 5, status_y), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                            status_y += 25

                    except Exception as e:
                        continue
            else:

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

            # **PART 2 FIX**: Add Frame Saving to verify overlays are being drawn
            # DEBUG: Save a frame after drawing to verify overlays
            import os
            import time as time_module # Import time for unique filenames

            debug_output_dir = "debug_frames"
            os.makedirs(debug_output_dir, exist_ok=True)

            # Initialize counter in a safer way if not already there
            if not hasattr(self, '_frame_save_counter'):
                self._frame_save_counter = 0

            self._frame_save_counter += 1

            if self._frame_save_counter % 50 == 0:
                timestamp = int(time_module.time())
                cv2.imwrite(os.path.join(debug_output_dir, f"frame_with_overlay_{self._frame_save_counter:05d}_{timestamp}.jpg"), display_frame)

            # Step 3: Display the final frame
            try:
                # **PART 2 FIX**: Use consistent window naming to prevent multiple windows
                # No longer call cv2.imshow here since main.py will handle display
                # window_name = f"WatchHer - {self.camera_name}"
                # cv2.imshow(window_name, display_frame)

                # Return the display_frame so main.py can show it
                frame[:] = display_frame
            except cv2.error as e:
                print(f"[ERROR] Display error for camera {self.camera_id}: {e}")
                print("[INFO] This may be due to display/GUI issues. Check if display is available.")
                print("[INFO] On remote servers, you may need X11 forwarding or run in headless mode.")
            except Exception as e:
                print(f"[ERROR] Unexpected display error for camera {self.camera_id}: {e}")
                print("[INFO] OpenCV may not be compiled with GUI support.")

        except Exception as e:
            print(f"Error displaying frame for camera {self.camera_id}: {e}")

    def _calculate_risk_score(self, detections, context=None):
        """
        **PART 2: SOPHISTICATED RISK CALCULATION - "BEST POSSIBLE" VERSION**
        Calculates a comprehensive, nuanced risk score using multiple weighted factors.

        Args:
            detections: List of person detection dictionaries
            context: Optional context dictionary for additional factors

        Returns:
            float: Calculated risk score (0-200 range, higher = more risk)
        """
        if context is None:
            context = {}

        if not detections:
            return 0.0

        total_risk = 0.0

        # === INDIVIDUAL PERSON RISK FACTORS ===

        # Base risk for each detected person + gender vulnerability + confidence weighting
        individual_scores = []
        females = []
        males = []
        unknown_gender = []
        distressed_people = 0
        surrounded_females = 0

        for i, det in enumerate(detections):
            person_risk = 5.0  # Base risk for any detected person

            # Gender-based vulnerability scoring
            gender = det.get('gender', 'Unknown').lower()
            confidence = det.get('confidence', 0.5)

            if 'woman' in gender or 'female' in gender:
                person_risk += 10.0  # Higher vulnerability for females
                females.append(det)
            elif 'man' in gender or 'male' in gender:
                person_risk += 2.0   # Lower base risk for males
                males.append(det)
            else:
                person_risk += 5.0   # Unknown gender is moderate risk
                unknown_gender.append(det)

            # Confidence weighting - lower confidence = slightly higher risk
            confidence_multiplier = 1.0 + (0.5 - confidence) * 0.5  # Range: 0.75 to 1.25
            person_risk *= confidence_multiplier

            # Distress signal detection
            if det.get('distress', False):
                person_risk += 50.0  # Major risk increase for distress
                distressed_people += 1

            # Check if this female is surrounded
            if 'woman' in gender or 'female' in gender:
                surrounding_males = self._count_surrounding_males(det, males)
                if surrounding_males >= 2:
                    person_risk += 40.0  # Surrounded female is high risk
                    surrounded_females += 1
                    det['surrounded'] = True  # Mark for visual display
                else:
                    det['surrounded'] = False

            individual_scores.append(person_risk)

        # Sum individual risk scores
        total_risk += sum(individual_scores)

        # === GROUP DYNAMICS RISK FACTORS ===
        female_count = len(females)
        male_count = len(males)
        unknown_count = len(unknown_gender)
        total_people = len(detections)

        # Male-to-Female ratio analysis
        if female_count > 0:
            male_to_female_ratio = male_count / female_count
            if male_to_female_ratio > 4:
                ratio_risk = 25.0
            elif male_to_female_ratio > 2:
                ratio_risk = 15.0
            else:
                ratio_risk = 0.0
            total_risk += ratio_risk

        # Lone woman scenario
        if female_count == 1 and male_count > 0:
            lone_woman_risk = 20.0
            total_risk += lone_woman_risk

        # Large group dynamics
        if total_people >= 5:
            crowd_risk = 10.0
            total_risk += crowd_risk

        # Unknown faces (potential concealment)
        if unknown_count > 0:
            unknown_risk = unknown_count * 5.0
            total_risk += unknown_risk

        # === CONTEXTUAL MULTIPLIERS ===
        context_multiplier = 1.0

        # Time-based risk multiplier
        if is_night_time():
            context_multiplier *= 1.5

        # Historical location risk (placeholder)
        location_risk = context.get('location_risk', 1.0)
        context_multiplier *= location_risk

        # Apply contextual multipliers
        total_risk *= context_multiplier

        # === NORMALIZATION AND SCALING ===
        # Scale to 0-200 range for human readability
        final_risk = min(total_risk, 200.0)

        print(f"  - Individual scores sum: {sum(individual_scores):.1f}")
        print(f"  - Group dynamics: {total_risk - sum(individual_scores):.1f}")
        print(f"  - Context multiplier: {context_multiplier:.2f}")
        print(f"  - Final risk score: {final_risk:.1f}/200")

        return final_risk

    def get_frame(self):
        """
        Process and return a single frame with analysis overlays and risk score.

        Returns:
            tuple: (frame_bytes, risk_score) where frame_bytes is JPEG encoded frame
        """
        if self.cap is None or not self.cap.isOpened():
            # Return a black frame with error message if camera not available
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "Camera Not Available", (50, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            ret, jpeg = cv2.imencode('.jpg', frame)
            return (jpeg.tobytes(), 0)

        # Read frame
        ret, frame = self.cap.read()
        if not ret or frame is None:
            # Return a black frame if no frame available
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "No Frame Available", (50, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            ret, jpeg = cv2.imencode('.jpg', frame)
            return (jpeg.tobytes(), 0)

        # Analyze frame if analyzer is available
        detections = []
        if self.analyzer and self.analyzer.is_ready():
            detections = self.analyzer.analyze_frame(frame)
            # NEW DEBUG: Check what AIAnalyzer returned

        # Calculate risk score (includes threat analysis)
        risk_score = self._calculate_risk_score(detections)

        # NEW DEBUG: Check detections before overlay drawing

        # **PART 2 FIX**: Apply overlays to the frame BEFORE encoding
        # Apply overlays using _display_frame_with_overlay (it modifies frame in-place)
        self._display_frame_with_overlay(frame, risk_score, detections)

        # Encode frame as JPEG after overlays have been applied
        ret, jpeg = cv2.imencode('.jpg', frame)
        return (jpeg.tobytes(), risk_score)

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