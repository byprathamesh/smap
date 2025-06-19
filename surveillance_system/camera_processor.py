#!/usr/bin/env python3
"""
WatchHer Camera Processor - Advanced Version
Supports both client-side webcam frames and server-side video file processing
Optimized for real-time performance with comprehensive risk scoring
"""

import cv2
import numpy as np
import time
import math
import threading
from datetime import datetime
from ai_analyzer import AIAnalyzer

class CameraProcessor:
    """Advanced camera processor with sophisticated risk assessment"""
    
    def __init__(self, source=None):
        """
        Initialize camera processor
        
        Args:
            source: None for live webcam (frames from client), str for video file path
        """
        self.source = source
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
        
        # Threading for video file processing
        self.processing_thread = None
        self.stop_processing = False
        
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
        
        if self.source is not None:
            # Initialize for video file processing
            self._initialize_video_file()
        else:
            # For live webcam, frames will be provided via process_frame_from_numpy
            print(f"[INFO] CameraProcessor initialized for live webcam (client-side frames)")
            self.is_running = True
    
    def _initialize_video_file(self):
        """Initialize video file capture for server-side processing"""
        try:
            print(f"[INFO] Initializing video file: {self.source}")
            self.cap = cv2.VideoCapture(self.source)
            
            if not self.cap.isOpened():
                raise Exception(f"Cannot open video file: {self.source}")
            
            # Get video properties
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            print(f"[INFO] Video file loaded: {fps:.1f} FPS, {frame_count} frames, {duration:.1f}s duration")
            self.is_running = True
            
        except Exception as e:
            print(f"[ERROR] Video file initialization failed: {e}")
            self.is_running = False
            raise
    
    def process_frame_from_numpy(self, frame_np):
        """
        Process a single numpy frame (from client-side webcam)
        
        Args:
            frame_np: numpy array representing the frame
            
        Returns:
            tuple: (processed_frame_np, risk_score)
        """
        if not self.is_running or frame_np is None:
            return frame_np, 0.0
        
        try:
            self.frame_count += 1
            
            # AI Analysis
            detections = self.analyzer.analyze_frame(frame_np)
            self.last_detections = detections
            
            # Calculate comprehensive risk score
            self.current_risk_score = self._calculate_risk_score(detections)
            
            # Draw enhanced overlay
            processed_frame = self._draw_enhanced_overlay(frame_np.copy(), detections)
            
            # Update FPS counter
            self._update_fps()
            
            return processed_frame, self.current_risk_score
            
        except Exception as e:
            print(f"[ERROR] Frame processing failed: {e}")
            return frame_np, 0.0
    
    def get_frame_for_video_file(self):
        """
        Get processed frame for video file (server-side processing)
        
        Returns:
            tuple: (frame_bytes, risk_score)
        """
        if not self.is_running or not self.cap or not self.cap.isOpened():
            return self._get_error_frame(), 0.0
        
        try:
            ret, frame = self.cap.read()
            if not ret:
                # End of video, loop back to beginning
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    return self._get_error_frame(), 0.0
            
            # Process frame
            processed_frame, risk_score = self.process_frame_from_numpy(frame)
            
            # Encode to JPEG bytes
            _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return buffer.tobytes(), risk_score
            
        except Exception as e:
            print(f"[ERROR] Video file frame processing failed: {e}")
            return self._get_error_frame(), 0.0
    
    def start_video_processing_thread(self):
        """Start background thread for video file processing"""
        if self.source is None:
            print("[WARNING] Cannot start video processing thread for live webcam")
            return
        
        if self.processing_thread and self.processing_thread.is_alive():
            print("[INFO] Video processing thread already running")
            return
        
        self.stop_processing = False
        self.processing_thread = threading.Thread(target=self._video_processing_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        print("[INFO] Video processing thread started")
    
    def _video_processing_loop(self):
        """Background loop for video file processing"""
        while not self.stop_processing and self.is_running:
            try:
                frame_bytes, risk_score = self.get_frame_for_video_file()
                time.sleep(0.033)  # ~30 FPS
            except Exception as e:
                print(f"[ERROR] Video processing loop error: {e}")
                break
    
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
        cv2.putText(error_frame, "Video Processing Error", (200, 240),
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
        self.stop_processing = True
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
        
        if self.cap:
            self.cap.release()
        
        print("[INFO] Camera processor stopped")
    
    def __del__(self):
        """Cleanup on destruction"""
        self.stop() 