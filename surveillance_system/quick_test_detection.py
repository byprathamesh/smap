#!/usr/bin/env python3
"""Quick test to verify weapon detection is working"""

import cv2
import numpy as np
from ai_analyzer import AIAnalyzer

def test_detection():
    """Test the AI analyzer with webcam feed"""
    print("🔥 Starting Quick Detection Test...")
    
    # Initialize AI analyzer
    analyzer = AIAnalyzer()
    
    if not analyzer.is_ready():
        print("❌ AI Analyzer not ready!")
        return
    
    print("✅ AI Analyzer ready!")
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open webcam!")
        return
    
    print("✅ Webcam opened, starting detection...")
    print("📝 Hold up objects to test detection...")
    print("🔧 Press 'q' to quit")
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Only process every 10th frame for performance
        if frame_count % 10 == 0:
            print(f"\n🎬 Frame {frame_count} - Processing...")
            
            # Analyze frame
            try:
                people, objects = analyzer.analyze_frame(frame)
                
                print(f"👥 People detected: {len(people)}")
                print(f"🔫 Objects detected: {len(objects)}")
                
                # Draw detections
                if people or objects:
                    annotated_frame = analyzer.draw_detections(frame, people, objects)
                    cv2.imshow('Detection Test', annotated_frame)
                else:
                    cv2.imshow('Detection Test', frame)
                    
            except Exception as e:
                print(f"❌ Error processing frame: {e}")
                cv2.imshow('Detection Test', frame)
        else:
            cv2.imshow('Detection Test', frame)
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_detection() 