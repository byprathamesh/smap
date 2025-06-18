#!/usr/bin/env python3
"""
Demo script for WatchHer Dynamic Risk Scoring System
This script demonstrates the new risk scoring features and video analysis capabilities.
"""

import cv2
import numpy as np
import time
from camera_processor import CameraProcessor

def create_demo_video():
    """
    Create a simple demo video with simulated scenarios for testing risk scoring.
    """
    print("🎬 Creating demo video with risk scenarios...")
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('demo_scenarios.mp4', fourcc, 10.0, (640, 480))
    
    # Create frames for different scenarios
    frames = []
    
    # Scenario 1: Low risk - Empty scene
    for i in range(30):
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 50
        cv2.putText(frame, "Scenario 1: Empty Scene (Low Risk)", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Frame {i+1}/30", (50, 400), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        frames.append(frame)
    
    # Scenario 2: Medium risk - Single person
    for i in range(30):
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 50
        cv2.putText(frame, "Scenario 2: Single Person (Medium Risk)", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        # Draw a person-like rectangle
        cv2.rectangle(frame, (250, 150), (350, 400), (100, 150, 200), -1)
        cv2.putText(frame, f"Frame {i+31}/60", (50, 400), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        frames.append(frame)
    
    # Scenario 3: High risk - Multiple people scenario
    for i in range(30):
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 50
        cv2.putText(frame, "Scenario 3: Group Scenario (High Risk)", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        # Draw multiple person-like rectangles
        cv2.rectangle(frame, (150, 150), (220, 350), (200, 100, 100), -1)  # Person 1
        cv2.rectangle(frame, (300, 120), (370, 320), (100, 200, 150), -1)  # Person 2
        cv2.rectangle(frame, (450, 160), (520, 360), (100, 150, 200), -1)  # Person 3
        cv2.putText(frame, f"Frame {i+61}/90", (50, 400), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        frames.append(frame)
    
    # Write frames to video
    for frame in frames:
        out.write(frame)
    
    out.release()
    print("✅ Demo video 'demo_scenarios.mp4' created successfully!")
    return 'demo_scenarios.mp4'

def test_risk_scoring_algorithm():
    """
    Test the risk scoring algorithm with various detection scenarios.
    """
    print("\n🧮 Testing Dynamic Risk Scoring Algorithm")
    print("=" * 50)
    
    # Create a processor for testing (without actual video)
    processor = CameraProcessor(source=0)  # Dummy source
    
    # Test scenarios
    test_cases = [
        {
            'name': 'Empty Scene',
            'detections': [],
            'expected_range': (0, 5)
        },
        {
            'name': 'Single Woman (Lone)',
            'detections': [
                {'gender': 'Woman', 'age_range': '25-30', 'distress': False, 'box': [100, 100, 80, 160]}
            ],
            'expected_range': (15, 25)
        },
        {
            'name': 'Distress Signal Detected',
            'detections': [
                {'gender': 'Woman', 'age_range': '25-30', 'distress': True, 'box': [100, 100, 80, 160]}
            ],
            'expected_range': (65, 75)
        },
        {
            'name': 'Woman Surrounded by Males',
            'detections': [
                {'gender': 'Woman', 'age_range': '25-30', 'distress': False, 'box': [300, 200, 60, 120]},
                {'gender': 'Man', 'age_range': '30-35', 'distress': False, 'box': [250, 180, 70, 140]},
                {'gender': 'Man', 'age_range': '28-32', 'distress': False, 'box': [370, 190, 65, 130]},
                {'gender': 'Man', 'age_range': '25-29', 'distress': False, 'box': [320, 150, 60, 125]}
            ],
            'expected_range': (40, 60)
        },
        {
            'name': 'High Risk: Distress + Surrounded',
            'detections': [
                {'gender': 'Woman', 'age_range': '25-30', 'distress': True, 'box': [300, 200, 60, 120]},
                {'gender': 'Man', 'age_range': '30-35', 'distress': False, 'box': [250, 180, 70, 140]},
                {'gender': 'Man', 'age_range': '28-32', 'distress': False, 'box': [370, 190, 65, 130]}
            ],
            'expected_range': (75, 95)
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        risk_score = processor._calculate_risk_score(test_case['detections'])
        min_expected, max_expected = test_case['expected_range']
        
        # Determine if within expected range
        status = "✅ PASS" if min_expected <= risk_score <= max_expected else "❌ FAIL"
        
        print(f"{i}. {test_case['name']}")
        print(f"   Risk Score: {risk_score:.1f}")
        print(f"   Expected: {min_expected}-{max_expected}")
        print(f"   Status: {status}")
        print()
    
    print("🎯 Risk Scoring Algorithm Test Complete!")

def demo_video_analysis():
    """
    Demonstrate video analysis with the dynamic risk scoring system.
    """
    print("\n🎥 Video Analysis Demo")
    print("=" * 50)
    
    # Create demo video
    demo_file = create_demo_video()
    
    print(f"\n📹 Now you can analyze the demo video with:")
    print(f"   python main.py --video {demo_file}")
    print("\n🎮 Interactive Controls:")
    print("   • Press 'q' to quit")
    print("   • Press 'space' to pause/resume")
    print("\n📊 Watch the risk scores change as different scenarios play!")

def main():
    """
    Main demo function
    """
    print("=" * 60)
    print("🛡️  WatchHer Dynamic Risk Scoring Demo")
    print("   Advanced AI-Powered Threat Assessment")
    print("=" * 60)
    
    # Test 1: Risk scoring algorithm
    test_risk_scoring_algorithm()
    
    # Test 2: Video analysis demo
    demo_video_analysis()
    
    print("\n" + "=" * 60)
    print("🚀 Demo Complete!")
    print("=" * 60)
    print("📝 Usage Examples:")
    print("   • Webcam analysis:     python main.py")
    print("   • Video file analysis: python main.py --video your_video.mp4")
    print("   • Multi-camera mode:   python main.py --multi-camera")
    print("   • Web dashboard:       python app.py")
    print("\n🔬 Advanced Features Available:")
    print("   ✅ YOLOv8-Pose for human pose detection")
    print("   ✅ DeepFace for demographic analysis")
    print("   ✅ Dynamic risk scoring algorithm")
    print("   ✅ Distress signal detection")
    print("   ✅ Woman surrounded detection")
    print("   ✅ Interactive web dashboard with heatmaps")
    print("   ✅ Database storage for historical analysis")

if __name__ == "__main__":
    main() 