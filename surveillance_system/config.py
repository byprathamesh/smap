import os
from datetime import time

# Camera Configuration
CAMERAS = {
    'camera_1': {
        'url': 'C:\\Users\\prath\\Downloads\\delhigully.webm',
        'name': 'Main Entrance',
        'location': 'Building A',
        'enabled': True
    },
    'camera_2': {
        'url': 'rtsp://camera2.example.com:554/stream1',
        'name': 'Parking Lot',
        'location': 'Building A',
        'enabled': True
    }
}

# Detection Settings
DETECTION_SETTINGS = {
    # Minimum confidence threshold for person detection (0.0 to 1.0)
    'person_detection_threshold': 0.5,
    
    # Minimum confidence threshold for gender classification (0.0 to 1.0)
    'gender_classification_threshold': 0.7,
    
    # Minimum confidence threshold for age estimation (0.0 to 1.0)
    'age_estimation_threshold': 0.6,
    
    # Maximum distance (in pixels) to consider people as a group
    'group_proximity_threshold': 200,
    
    # Minimum number of people to consider as a surrounding group
    'min_surrounding_people': 3,
    
    # Duration (in seconds) to consider someone as "alone" before triggering alert
    'lone_woman_duration': 30,
    
    # Risk Scoring Algorithm Settings
    'risk_scoring': {
        # Base threat score for lone female
        'lone_female_score': 10,
        
        # Score modifiers for different demographics
        'adult_male_near_female_score': 10,
        'child_score_modifier': -15,  # Reduces threat (children present = safer)
        'elderly_score_modifier': -10,  # Reduces threat (elderly present = safer)
        'other_female_score_modifier': -5,  # Reduces threat (other women = safer)
        
        # Age thresholds for demographic classification
        'child_age_threshold': 15,
        'elderly_age_threshold': 60,
        
        # Final threat score threshold to trigger alert
        'threat_alert_threshold': 25,
        
        # Night time multiplier for threat scores
        'night_multiplier': 1.5
    }
}

# Time-based settings
TIME_SETTINGS = {
    # Night time definition (24-hour format)
    'night_start': time(22, 0),  # 10:00 PM
    'night_end': time(5, 0),     # 5:00 AM
    
    # Alert sensitivity multiplier during night hours
    'night_sensitivity_multiplier': 1.5
}

# Alert Settings
ALERT_SETTINGS = {
    # Directory to save alert snapshots
    'snapshot_dir': os.path.join(os.path.dirname(__file__), 'alerts'),
    
    # Maximum number of alerts to store
    'max_stored_alerts': 1000,
    
    # Alert cooldown period (in seconds) to prevent alert spam
    'alert_cooldown': 300,  # 5 minutes
}

# Model Paths
MODEL_PATHS = {
    # Advanced object detection using YOLOv3-tiny for person detection
    "object_detection": {
        "weights": os.path.join(os.path.dirname(__file__), "models", "yolov3-tiny.weights"),
        "config": os.path.join(os.path.dirname(__file__), "models", "yolov3-tiny.cfg"),
        "names": os.path.join(os.path.dirname(__file__), "models", "coco.names"),
    },
    "gender_classification": {
        "prototxt": os.path.join(os.path.dirname(__file__), "models", "gender_deploy.prototxt"),
        "model": os.path.join(os.path.dirname(__file__), "models", "gender_net.caffemodel"),
    },
    "age_estimation": {
        "prototxt": os.path.join(os.path.dirname(__file__), "models", "age_deploy.prototxt"),
        "model": os.path.join(os.path.dirname(__file__), "models", "age_net.caffemodel"),
    },
}

# Create necessary directories if they don't exist
os.makedirs(ALERT_SETTINGS['snapshot_dir'], exist_ok=True)
os.makedirs(os.path.dirname(MODEL_PATHS['person_detection']), exist_ok=True) 