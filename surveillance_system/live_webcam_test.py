#!/usr/bin/env python3
"""
Live Webcam Test for YOLO-Based Face Detection
Real-time testing to verify the system is working properly
"""

import cv2
import numpy as np
import time
from datetime import datetime
from ai_analyzer import AIAnalyzer
from camera_processor import CameraProcessor
import os

class LiveWebcamTest:
    def __init__(self):
        self.analyzer = None
        self.processor = None
        self.cap = None
        self.frame_count = 0
        self.start_time = time.time()
        
    def initialize(self):
        """Initialize all components"""
        print("🚀 Initializing YOLO-based surveillance system...")
        
        # Initialize webcam
        print("📹 Opening webcam...")
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("❌ Cannot open webcam")
            return False
        
        # Set webcam properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        print("✅ Webcam opened successfully")
        
        # Initialize AI analyzer
        print("🤖 Loading AI models...")
        self.analyzer = AIAnalyzer()
        if not self.analyzer.is_ready():
            print("❌ AI analyzer failed to initialize")
            return False
        print("✅ AI analyzer ready")
        
        # Initialize camera processor
        print("⚙️ Initializing camera processor...")
        self.processor = CameraProcessor(source=None)
        if not self.processor.is_running:
            print("❌ Camera processor failed to initialize")
            return False
        print("✅ Camera processor ready")
        
        print("🎯 System initialization complete!")
        return True
    
    def run_test(self, duration_seconds=30):
        """Run live webcam test"""
        print(f"\n🔴 Starting {duration_seconds}-second live test...")
        print("👀 Look at your webcam - the system will detect and analyze you!")
        print("📊 Real-time stats will be displayed below:")
        print("-" * 80)
        
        test_start = time.time()
        last_save_time = 0
        detection_history = []
        
        while time.time() - test_start < duration_seconds:
            ret, frame = self.cap.read()
            if not ret:
                print("❌ Failed to read frame")
                break
            
            self.frame_count += 1
            current_time = time.time()
            
            # Process frame with AI
            detections = self.analyzer.analyze_frame(frame)
            processed_frame, risk_score = self.processor.process_frame_from_numpy(frame)
            
            # Calculate FPS
            elapsed = current_time - self.start_time
            fps = self.frame_count / elapsed if elapsed > 0 else 0
            
            # Update detection history
            detection_history.append({
                'timestamp': current_time,
                'detections': len(detections),
                'risk_score': risk_score,
                'people': [d for d in detections if d['class'] == 'person']
            })
            
            # Keep only last 30 detections
            if len(detection_history) > 30:
                detection_history.pop(0)
            
            # Print real-time stats every second
            if current_time - last_save_time >= 1.0:
                self.print_stats(detections, risk_score, fps, current_time - test_start)
                
                # Save sample frames
                if len(detections) > 0:
                    timestamp = datetime.now().strftime("%H%M%S")
                    cv2.imwrite(f'live_test_frame_{timestamp}.jpg', processed_frame)
                    print(f"  💾 Saved frame with {len(detections)} detection(s)")
                
                last_save_time = current_time
            
            # Allow some processing time
            time.sleep(0.033)  # ~30 FPS
        
        print("-" * 80)
        self.print_final_summary(detection_history, duration_seconds)
    
    def print_stats(self, detections, risk_score, fps, elapsed_time):
        """Print real-time statistics"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"[{timestamp}] Frame {self.frame_count:4d} | "
              f"FPS: {fps:5.1f} | "
              f"People: {len(detections):2d} | "
              f"Risk: {risk_score:6.2f} | "
              f"Time: {elapsed_time:5.1f}s")
        
        # Show detailed detection info
        for i, detection in enumerate(detections):
            age = detection.get('age', 'unknown')
            gender = detection.get('gender', 'unknown')
            confidence = detection.get('confidence', 0)
            has_weapon = detection.get('has_harmful_object', False)
            
            weapon_status = "⚠️ ARMED" if has_weapon else "✅ Safe"
            print(f"    Person {i+1}: {gender}, age {age}, conf {confidence:.2f} - {weapon_status}")
    
    def print_final_summary(self, history, duration):
        """Print final test summary"""
        print("\n📈 TEST SUMMARY")
        print("=" * 50)
        
        if not history:
            print("❌ No data collected")
            return
        
        # Calculate averages
        total_detections = sum(len(h['people']) for h in history)
        avg_people = total_detections / len(history)
        avg_risk = sum(h['risk_score'] for h in history) / len(history)
        avg_fps = self.frame_count / duration
        
        # Count frames with people
        frames_with_people = sum(1 for h in history if len(h['people']) > 0)
        detection_rate = (frames_with_people / len(history)) * 100
        
        print(f"📊 Frames processed: {self.frame_count}")
        print(f"📊 Average FPS: {avg_fps:.1f}")
        print(f"📊 Detection rate: {detection_rate:.1f}% (frames with people)")
        print(f"📊 Average people detected: {avg_people:.1f}")
        print(f"📊 Average risk score: {avg_risk:.2f}")
        
        # Show detected attributes
        all_people = []
        for h in history:
            all_people.extend(h['people'])
        
        if all_people:
            print(f"\n👥 DETECTED PEOPLE ANALYSIS:")
            genders = [p.get('gender', 'unknown') for p in all_people]
            ages = [p.get('age', 0) for p in all_people if p.get('age', 0) > 0]
            
            gender_counts = {}
            for g in genders:
                gender_counts[g] = gender_counts.get(g, 0) + 1
            
            print(f"   Gender distribution: {gender_counts}")
            if ages:
                print(f"   Age range: {min(ages)}-{max(ages)} (avg: {sum(ages)/len(ages):.1f})")
            
            # Check face detection
            faces_detected = sum(1 for p in all_people if p.get('face_bbox'))
            face_rate = (faces_detected / len(all_people)) * 100 if all_people else 0
            print(f"   Face detection rate: {face_rate:.1f}%")
        
        print(f"\n🎯 SYSTEM PERFORMANCE:")
        if avg_fps > 20:
            print("   ✅ Excellent performance (>20 FPS)")
        elif avg_fps > 10:
            print("   ✅ Good performance (>10 FPS)")
        else:
            print("   ⚠️ Moderate performance (<10 FPS)")
        
        if detection_rate > 80:
            print("   ✅ Excellent detection reliability")
        elif detection_rate > 50:
            print("   ✅ Good detection reliability")
        else:
            print("   ⚠️ Consider improving lighting or camera position")
        
        print(f"\n💾 Saved sample frames in current directory")
        print("🎉 Test completed successfully!")
    
    def cleanup(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
        if self.processor:
            self.processor.stop()
        print("🧹 Cleanup completed")

def main():
    """Main test function"""
    print("🎯 WatchHer Live Webcam Test")
    print("Testing YOLO-based face detection with your webcam")
    print("=" * 60)
    
    test = LiveWebcamTest()
    
    try:
        if not test.initialize():
            print("❌ Initialization failed")
            return
        
        # Ask user for test duration
        print("\n⏱️ How long would you like to test? (default: 30 seconds)")
        try:
            duration = int(input("Enter duration in seconds (or press Enter for 30): ") or "30")
        except:
            duration = 30
        
        test.run_test(duration)
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    finally:
        test.cleanup()

if __name__ == "__main__":
    main() 