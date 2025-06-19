#!/usr/bin/env python3
"""
Test Harmful Object Detection
Specifically tests weapon/knife detection capabilities
"""

import cv2
import numpy as np
from ai_analyzer import AIAnalyzer
from camera_processor import CameraProcessor
import time

def test_weapon_detection():
    """Test harmful object detection"""
    print("🔫 Testing Harmful Object Detection System")
    print("=" * 50)
    
    # Initialize AI components
    print("🤖 Initializing AI analyzer...")
    analyzer = AIAnalyzer()
    
    if not analyzer.is_ready():
        print("❌ AI analyzer not ready!")
        return
    
    print("✅ AI analyzer ready!")
    print(f"🎯 Harmful objects to detect: {analyzer.HARMFUL_OBJECTS}")
    print()
    
    # Test with webcam
    print("📹 Starting webcam test...")
    print("🔍 Point camera at any of these objects to test:")
    print("   - 🔪 Knife, kitchen knife, utility knife")
    print("   - 🔫 Toy gun, water gun, any gun-like object")
    print("   - ⚾ Baseball bat, stick, club")
    print("   - ⚔️ Sword, long knife")
    print()
    print("📊 Watch for:")
    print("   - 🚨 Risk score should JUMP to 60-90%+")
    print("   - 📝 Activity log should show weapon detection")
    print("   - 🟥 Red bounding boxes around weapons")
    print()
    print("Press 'q' to quit, 's' to take screenshot")
    print("=" * 50)
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    camera_proc = CameraProcessor(source=None)
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Process frame with full AI analysis
        processed_frame, risk_score = camera_proc.process_frame_from_numpy(frame)
        detections = camera_proc.last_detections if hasattr(camera_proc, 'last_detections') else []
        
        # Analyze detection details
        weapon_detected = False
        for detection in detections:
            if detection.get('has_harmful_object'):
                weapon_detected = True
                weapons = detection.get('harmful_objects_nearby', [])
                
                # Print weapon detection info
                for weapon in weapons:
                    print(f"🚨 WEAPON DETECTED: {weapon['type']} (confidence: {weapon['confidence']:.2f}, distance: {weapon['distance']:.1f}px)")
                
                # Print risk impact
                print(f"🎯 Risk Score: {risk_score:.1f}% (HIGH!)")
                print(f"👥 Person with weapon at: {detection['bbox']}")
                print("-" * 30)
        
        # Add text overlay with current status
        status_color = (0, 255, 0) if not weapon_detected else (0, 0, 255)
        status_text = f"Risk: {risk_score:.1f}% | Weapons: {'YES' if weapon_detected else 'NO'}"
        
        cv2.putText(processed_frame, status_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        
        cv2.putText(processed_frame, f"Frame: {frame_count} | Press 'q' to quit", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Show detection instructions
        if frame_count < 100:  # Show for first few seconds
            cv2.putText(processed_frame, "Point camera at knife, gun, bat, or weapon", (10, 450), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Display frame
        cv2.imshow('Weapon Detection Test', processed_frame)
        
        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            # Save screenshot
            filename = f"weapon_test_frame_{int(time.time())}.jpg"
            cv2.imwrite(filename, processed_frame)
            print(f"📸 Screenshot saved: {filename}")
    
    cap.release()
    cv2.destroyAllWindows()
    print("👋 Weapon detection test completed!")

def test_specific_objects():
    """Test detection of specific objects"""
    print("\n🎯 Testing Specific Object Recognition:")
    print("Objects that should trigger HIGH RISK:")
    
    harmful_objects = [
        '🔪 knife', '🔫 gun', '⚔️ sword', '⚾ baseball bat', 
        '🔫 firearm', '🏒 club', '🔫 pistol', '🔫 rifle', '⚠️ weapon'
    ]
    
    for obj in harmful_objects:
        print(f"   - {obj}")
    
    print("\n📊 Expected Risk Score Multipliers:")
    print("   - Gun/Firearm/Pistol: 3.0x (HIGHEST)")
    print("   - Rifle: 3.5x (MAXIMUM)")
    print("   - Knife: 2.0x")
    print("   - Sword: 2.5x")
    print("   - Club/Bat: 1.5x")
    print()
    print("💡 Final risk = (base_risk + person_factors) × weapon_multiplier")

if __name__ == "__main__":
    test_specific_objects()
    test_weapon_detection() 