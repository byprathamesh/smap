#!/usr/bin/env python3
"""
Test script to demonstrate all advanced features of WatchHer surveillance system.
"""

import cv2
import numpy as np
from database import init_db, insert_alert, get_all_alerts
from ai_analyzer import AIAnalyzer
import time

def create_test_frame():
    """Create a simple test frame for demonstration."""
    # Create a 640x480 test image
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 50  # Dark gray background
    
    # Add some text
    cv2.putText(frame, "WatchHer Test Frame", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, "Testing AI Analysis Pipeline", (50, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Add some shapes to simulate people
    cv2.rectangle(frame, (200, 200), (280, 350), (100, 150, 200), -1)  # Person 1
    cv2.rectangle(frame, (350, 180), (430, 330), (150, 100, 200), -1)  # Person 2
    
    return frame

def test_database():
    """Test database functionality."""
    print("🗄️  Testing Database Functionality...")
    
    # Initialize database
    init_db()
    
    # Insert test alerts
    test_alerts = [
        ('camera_1', 'high_threat_detected', 28, 'Test high threat scenario'),
        ('camera_2', 'distress_signal', 35, 'Test distress signal detected'),
        ('camera_1', 'surrounded', 25, 'Test woman surrounded scenario'),
        ('camera_3', 'lone_woman', 15, 'Test lone woman detection'),
    ]
    
    for camera_id, alert_type, score, details in test_alerts:
        success = insert_alert(camera_id, alert_type, score, details)
        if success:
            print(f"  ✅ Inserted alert: {camera_id} - {alert_type} (Score: {score})")
        else:
            print(f"  ❌ Failed to insert alert: {camera_id} - {alert_type}")
    
    # Retrieve and display alerts
    all_alerts = get_all_alerts()
    print(f"  📊 Total alerts in database: {len(all_alerts)}")
    
    return len(all_alerts) > 0

def test_ai_analyzer():
    """Test AI analyzer with pose detection."""
    print("\n🤖 Testing AI Analyzer (YOLOv8-Pose + DeepFace)...")
    
    try:
        # Initialize AI analyzer
        analyzer = AIAnalyzer()
        
        if not analyzer.is_ready():
            print("  ❌ AI Analyzer not ready")
            return False
        
        print("  ✅ AI Analyzer initialized successfully")
        
        # Create test frame
        test_frame = create_test_frame()
        
        # Analyze frame
        print("  🔍 Analyzing test frame...")
        detections = analyzer.analyze_frame(test_frame)
        
        print(f"  📈 Analysis Results:")
        print(f"    - Detections found: {len(detections)}")
        
        for i, detection in enumerate(detections):
            print(f"    - Person {i+1}:")
            print(f"      • Bounding box: {detection['box']}")
            print(f"      • Gender: {detection['gender']}")
            print(f"      • Age range: {detection['age_range']}")
            print(f"      • Confidence: {detection['confidence']:.2f}")
            print(f"      • Distress detected: {detection['distress']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ AI Analyzer test failed: {e}")
        return False

def test_web_dashboard():
    """Test web dashboard functionality."""
    print("\n🌐 Testing Web Dashboard...")
    
    try:
        from app import app
        print("  ✅ Flask app imported successfully")
        print("  🚀 You can start the web dashboard with: python app.py")
        print("  📍 Access at: http://localhost:5000")
        print("  🗺️  Heatmap at: http://localhost:5000/heatmap")
        return True
        
    except Exception as e:
        print(f"  ❌ Web dashboard test failed: {e}")
        return False

def main():
    """Run all feature tests."""
    print("=" * 60)
    print("🛡️  WatchHer Advanced Features Test Suite")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Database functionality
    results['database'] = test_database()
    
    # Test 2: AI analyzer with pose detection
    results['ai_analyzer'] = test_ai_analyzer()
    
    # Test 3: Web dashboard
    results['web_dashboard'] = test_web_dashboard()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)
    
    for feature, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {feature.replace('_', ' ').title()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All advanced features are working correctly!")
        print("\n🚀 Ready to start the complete surveillance system:")
        print("   • For command-line mode: python main.py")
        print("   • For web dashboard: python app.py")
    else:
        print("\n⚠️  Some features need attention. Check the errors above.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 