#!/usr/bin/env python3
"""
Test script for the upgraded WatchHer surveillance system.
Verifies that all components can be imported and initialized.
"""

import sys
import traceback

def test_imports():
    """Test all critical imports."""
    print("Testing imports...")
    
    try:
        import cv2
        print("✓ OpenCV imported")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False
        
    try:
        from ultralytics import YOLO
        print("✓ Ultralytics imported")
    except ImportError as e:
        print(f"✗ Ultralytics import failed: {e}")
        return False
        
    try:
        from deepface import DeepFace
        print("✓ DeepFace imported")
    except ImportError as e:
        print(f"✗ DeepFace import failed: {e}")
        return False
        
    try:
        from flask import Flask
        print("✓ Flask imported")
    except ImportError as e:
        print(f"✗ Flask import failed: {e}")
        return False
        
    return True

def test_ai_analyzer():
    """Test AI analyzer initialization."""
    print("\nTesting AI Analyzer...")
    
    try:
        from ai_analyzer import AIAnalyzer
        print("✓ AIAnalyzer imported")
        
        # Test initialization (this will download YOLO11 model if needed)
        print("Initializing AIAnalyzer (this may download the YOLO11 model)...")
        analyzer = AIAnalyzer()
        print("✓ AIAnalyzer initialized successfully")
        
        return True
    except Exception as e:
        print(f"✗ AIAnalyzer initialization failed: {e}")
        traceback.print_exc()
        return False

def test_camera_processor():
    """Test camera processor initialization."""
    print("\nTesting Camera Processor...")
    
    try:
        from camera_processor import CameraProcessor
        print("✓ CameraProcessor imported")
        
        # Test webcam-only initialization
        processor = CameraProcessor(source_index=0)
        print("✓ CameraProcessor initialized successfully")
        
        return True
    except Exception as e:
        print(f"✗ CameraProcessor initialization failed: {e}")
        traceback.print_exc()
        return False

def test_flask_app():
    """Test Flask app initialization."""
    print("\nTesting Flask App...")
    
    try:
        from app import app
        print("✓ Flask app imported")
        
        # Test if all routes are registered
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        expected_routes = ['/', '/start_analysis', '/video_feed', '/risk_score_stream', '/stop_analysis', '/api/status']
        
        for route in expected_routes:
            if route in routes:
                print(f"✓ Route {route} registered")
            else:
                print(f"✗ Route {route} missing")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Flask app initialization failed: {e}")
        traceback.print_exc()
        return False

def test_webcam_availability():
    """Test if webcam is available."""
    print("\nTesting Webcam Availability...")
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print("✓ Webcam is available and working")
                print(f"✓ Frame size: {frame.shape}")
                cap.release()
                return True
            else:
                print("✗ Webcam opened but cannot read frames")
                cap.release()
                return False
        else:
            print("✗ Cannot open webcam (may be in use by another application)")
            return False
            
    except Exception as e:
        print(f"✗ Webcam test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("WatchHer Surveillance System - Upgrade Test")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_flask_app,
        test_webcam_availability,
        test_camera_processor,
        # test_ai_analyzer,  # Comment out to avoid downloading model during test
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test_func.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed! The system is ready.")
        print("\nTo start the system:")
        print("  python app.py")
        print("\nThen open your browser to: http://127.0.0.1:5000/")
        return True
    else:
        print("❌ Some tests failed. Please fix the issues before running the system.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 