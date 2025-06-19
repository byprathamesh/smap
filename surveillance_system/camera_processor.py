#!/usr/bin/env python3
"""
WatchHer Camera Processor - Advanced Version
Webcam-only processing with comprehensive floating-point risk scoring
Optimized for real-time performance
"""

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
    """Advanced camera processor with sophisticated risk assessment"""
    
    def __init__(self, source_index=0):
        """Initialize for webcam-only input"""
        self.source_index = source_index
        self.cap = None
        self.analyzer = AIAnalyzer()
        self.is_running = False
        self.current_risk_score = 0.0
        self.frame_count = 0
        self.last_detections = []
        
        # Performance tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
        
        # Risk scoring parameters (floating-point precision)
        self.risk_weights = {
            'base_person_presence_risk': 0.05,
            'female_vulnerability_factor': 0.2,
            'harmful_object_proximity_impact': 2.0,
            'male_to_female_ratio_impact': 0.3,
            'lone_woman_multiplier': 1.5,
            'distress_signal_impact': 1.0,
            'unidentified_person_impact': 0.1,
            'night_time_multiplier': 1.2,
            'location_risk_multiplier': 1.0
        }
        
        self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize webcam with optimal settings"""
        try:
            print(f"[INFO] Initializing webcam (index {self.source_index})...")
            self.cap = cv2.VideoCapture(self.source_index)
            
            if not self.cap.isOpened():
                raise Exception(f"Cannot open webcam with index {self.source_index}")
            
            # Optimize camera settings for performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for lower latency
            
            # Verify settings
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            print(f"[INFO] Webcam initialized: {width}x{height} @ {fps} FPS")
            print(f"CameraProcessor initialized for Webcam {self.source_index} (webcam_{self.source_index})")
            
            self.is_running = True
            
        except Exception as e:
            print(f"[ERROR] Camera initialization failed: {e}")
            self.is_running = False
            raise
    
    def get_frame(self):
        """
        Get processed frame with AI analysis and risk scoring
        
        Returns:
            tuple: (frame_bytes, risk_score)
        """
        if not self.is_running or not self.cap.isOpened():
            # Return black frame if camera not available
            black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(black_frame, "Camera Not Available", (200, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            _, buffer = cv2.imencode('.jpg', black_frame)
            return buffer.tobytes(), 0.0
        
        try:
            ret, frame = self.cap.read()
            if not ret:
                print("[WARNING] Failed to read frame from webcam")
                return self._get_error_frame(), 0.0
            
            self.frame_count += 1
            
            # AI Analysis (every frame for real-time detection)
            detections = self.analyzer.analyze_frame(frame)
            self.last_detections = detections
            
            # Calculate comprehensive risk score
            self.current_risk_score = self._calculate_risk_score(detections)
            
            # Draw enhanced overlay
            annotated_frame = self._draw_enhanced_overlay(frame, detections)
            
            # Update FPS counter
            self._update_fps()
            
            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return buffer.tobytes(), self.current_risk_score
            
        except Exception as e:
            print(f"[ERROR] Frame processing failed: {e}")
            return self._get_error_frame(), 0.0
    
    def _calculate_risk_score(self, detections):
        """
        Advanced floating-point risk scoring algorithm
        
        Args:
            detections: List of detection dictionaries from AI analyzer
            
        Returns:
            float: Risk score from 0.0 to 100.0
        """
        if not detections:
            return 0.0
        
        # Initialize base risk components
        total_risk = 0.0
        
        # Count people by gender
        total_people = len(detections)
        women_count = sum(1 for d in detections if d.get('gender') == 'woman')
        men_count = sum(1 for d in detections if d.get('gender') == 'man')
        unidentified_count = sum(1 for d in detections if d.get('gender') == 'unknown')
        
        # Base person presence risk
        total_risk += total_people * self.risk_weights['base_person_presence_risk']
        
        # Individual person risk assessment
        for detection in detections:
            person_risk = 0.0
            
            # Gender-based vulnerability
            if detection.get('gender') == 'woman':
                person_risk += self.risk_weights['female_vulnerability_factor']
            
            # Harmful object proximity (critical factor)
            if detection.get('has_harmful_object'):
                harmful_impact = self.risk_weights['harmful_object_proximity_impact']
                # Scale by number and confidence of harmful objects
                for obj in detection.get('harmful_objects_nearby', []):
                    weapon_multiplier = {
                        'gun': 3.0, 'firearm': 3.0, 'pistol': 3.0, 'rifle': 3.5,
                        'knife': 2.0, 'sword': 2.5,
                        'club': 1.5, 'baseball bat': 1.5
                    }.get(obj['type'], 2.0)
                    
                    person_risk += harmful_impact * weapon_multiplier * obj['confidence']
            
            # Age-based risk (young women at higher risk)
            age = detection.get('age', 25)
            if detection.get('gender') == 'woman' and 18 <= age <= 30:
                person_risk += 0.15  # Higher vulnerability for young women
            elif detection.get('gender') == 'woman' and age > 60:
                person_risk += 0.1   # Elderly women also vulnerable
            
            # Confidence-based risk (low confidence = unidentified = higher risk)
            if detection.get('confidence', 1.0) < 0.5:
                person_risk += self.risk_weights['unidentified_person_impact']
            
            total_risk += person_risk
        
        # Group dynamics risk factors
        if total_people > 1:
            # Male-to-female ratio analysis
            if women_count > 0 and men_count > 0:
                male_female_ratio = men_count / women_count
                if male_female_ratio > 2.0:  # Significantly more men than women
                    total_risk += self.risk_weights['male_to_female_ratio_impact'] * (male_female_ratio - 1.0)
            
            # Lone woman in group scenario
            if women_count == 1 and men_count >= 2:
                total_risk += self.risk_weights['lone_woman_multiplier']
        
        # Environmental risk factors
        current_hour = datetime.now().hour
        
        # Night time risk multiplier (10 PM to 6 AM)
        if current_hour >= 22 or current_hour <= 6:
            total_risk *= self.risk_weights['night_time_multiplier']
        
        # Unidentified persons risk
        if unidentified_count > 0:
            total_risk += unidentified_count * self.risk_weights['unidentified_person_impact']
        
        # Crowding factor (many people = higher risk of incidents)
        if total_people > 5:
            crowding_factor = 1.0 + (total_people - 5) * 0.05
            total_risk *= crowding_factor
        
        # Apply sigmoid normalization to ensure 0-100 scale with smooth transitions
        normalized_risk = 100.0 / (1.0 + math.exp(-0.1 * (total_risk - 10.0)))
        
        # Ensure bounds
        return max(0.0, min(100.0, normalized_risk))
    
    def _draw_enhanced_overlay(self, frame, detections):
        """Draw comprehensive overlay with AI detection results"""
        overlay_frame = frame.copy()
        
        # Use AI analyzer's drawing method for consistent visualization
        if detections:
            overlay_frame = self.analyzer.draw_detections(overlay_frame, detections)
        
        # Add system status overlay
        self._draw_system_status(overlay_frame, detections)
        
        return overlay_frame
    
    def _draw_system_status(self, frame, detections):
        """Draw system status information"""
        h, w = frame.shape[:2]
        
        # Semi-transparent overlay for status
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 120), (0, 0, 0), -1)
        frame[:] = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)[:]
        
        # Status text
        status_lines = [
            f"WatchHer AI Surveillance System",
            f"People Detected: {len(detections)}",
            f"Risk Score: {self.current_risk_score:.1f}/100.0",
            f"FPS: {self.current_fps:.1f} | Frame: {self.frame_count}"
        ]
        
        # Color code risk score
        risk_color = (0, 255, 0)  # Green
        if self.current_risk_score > 30:
            risk_color = (0, 255, 255)  # Yellow
        if self.current_risk_score > 60:
            risk_color = (0, 165, 255)  # Orange
        if self.current_risk_score > 80:
            risk_color = (0, 0, 255)  # Red
        
        for i, line in enumerate(status_lines):
            color = risk_color if "Risk Score" in line else (255, 255, 255)
            cv2.putText(frame, line, (15, 30 + i * 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Draw threat level indicator
        threat_level = "SAFE"
        if self.current_risk_score > 70:
            threat_level = "HIGH RISK"
        elif self.current_risk_score > 40:
            threat_level = "MODERATE"
        elif self.current_risk_score > 15:
            threat_level = "LOW RISK"
        
        cv2.putText(frame, f"Status: {threat_level}", (w - 200, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, risk_color, 2)
    
    def _update_fps(self):
        """Update FPS counter"""
        self.fps_counter += 1
        if self.fps_counter >= 30:  # Update every 30 frames
            current_time = time.time()
            elapsed = current_time - self.fps_start_time
            self.current_fps = 30.0 / elapsed if elapsed > 0 else 0.0
            self.fps_counter = 0
            self.fps_start_time = current_time
    
    def _get_error_frame(self):
        """Generate error frame"""
        error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(error_frame, "Camera Error", (250, 240),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        _, buffer = cv2.imencode('.jpg', error_frame)
        return buffer.tobytes()
    
    def get_current_risk_score(self):
        """Get current risk score"""
        return self.current_risk_score
    
    def get_current_fps(self):
        """Get current FPS"""
        return self.current_fps
    
    def get_detections_count(self):
        """Get current number of people detected"""
        return len(self.last_detections)
    
    def stop(self):
        """Stop camera processing"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        print("[INFO] Camera processor stopped")
    
    def __del__(self):
        """Cleanup on destruction"""
        self.stop() 