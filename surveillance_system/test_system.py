#!/usr/bin/env python3
"""
WatchHer Surveillance System - Comprehensive Test Suite
Tests all components of the enhanced system with source selection
"""

import sys
import os
import warnings
import numpy as np

# Suppress warnings for cleaner test output
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

def print_header():
    print("=" * 60)
    print("WatchHer Surveillance System - Enhanced Test Suite")
    print("=" * 60)

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        # Core ML libraries
        import cv2
        print("✓ OpenCV imported")
        
        import torch
        from ultralytics import YOLO
        print("✓ Ultralytics imported")
        
        import deepface
        from deepface import DeepFace
        print("✓ DeepFace imported")
        
        # Web framework
        from flask import Flask
        print("✓ Flask imported")
        
        # Core utilities
        import numpy as np
        import threading
        import time
        import json
        import base64
        print("✓ Utility libraries imported")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_flask_app():
    """Test Flask application and routes"""
    print("\nTesting Flask App...")
    
    try:
        from app import app
        print("✓ Flask app imported")
        
        # Check required routes
        route_names = [rule.rule for rule in app.url_map.iter_rules()]
        
        required_routes = [
            '/',
            '/start_analysis',
            '/stop_analysis',
            '/process_live_frame',
            '/video_feed_stream',
            '/risk_score_stream',
            '/api/status',
            '/api/system_info',
            '/validate_video_path'
        ]
        
        missing_routes = []
        for route in required_routes:
            if route in route_names:
                print(f"✓ Route {route} registered")
            else:
                print(f"✗ Route {route} missing")
                missing_routes.append(route)
        
        if missing_routes:
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Flask app test failed: {e}")
        return False

def test_webcam_availability():
    """Test webcam access"""
    print("\nTesting Webcam Availability...")
    
    try:
        import cv2
        
        # Try to open webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("✗ Webcam not available")
            return False
        
        print("✓ Webcam is available and working")
        
        # Test frame capture
        ret, frame = cap.read()
        if ret and frame is not None:
            print(f"✓ Frame size: {frame.shape}")
        else:
            print("✗ Frame capture failed")
            cap.release()
            return False
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"✗ Webcam test failed: {e}")
        return False

def test_camera_processor():
    """Test CameraProcessor functionality"""
    print("\nTesting Camera Processor...")
    
    try:
        from camera_processor import CameraProcessor
        print("✓ CameraProcessor imported")
        
        # Test webcam initialization (source=None)
        processor_webcam = CameraProcessor(source=None)
        print("✓ CameraProcessor initialized for webcam")
        
        # Test video file initialization
        test_video_path = "test_video.mp4"  # Non-existent file for testing
        try:
            processor_video = CameraProcessor(source=test_video_path)
            print("✗ Should have failed with non-existent video file")
            return False
        except Exception:
            print("✓ Properly handles invalid video file paths")
        
        # Test frame processing with dummy frame
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        processed_frame, risk_score = processor_webcam.process_frame_from_numpy(dummy_frame)
        
        if processed_frame is not None and isinstance(risk_score, (int, float)):
            print("✓ Frame processing works")
            print(f"✓ Risk score: {risk_score}")
        else:
            print("✗ Frame processing failed")
            return False
        
        # Test AI analyzer
        if hasattr(processor_webcam, 'analyzer') and processor_webcam.analyzer:
            print("✓ AI analyzer initialized")
        else:
            print("✗ AI analyzer not initialized")
            return False
        
        processor_webcam.stop()
        print("✓ CameraProcessor cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"✗ CameraProcessor test failed: {e}")
        return False

def test_ai_analyzer():
    """Test AI Analyzer functionality"""
    print("\nTesting AI Analyzer...")
    
    try:
        from ai_analyzer import AIAnalyzer
        print("✓ AIAnalyzer imported")
        
        analyzer = AIAnalyzer()
        print("✓ AIAnalyzer initialized")
        
        # Test with dummy frame
        dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        detections = analyzer.analyze_frame(dummy_frame)
        
        if isinstance(detections, list):
            print(f"✓ Frame analysis works (detected {len(detections)} objects)")
        else:
            print("✗ Frame analysis failed")
            return False
        
        # Test drawing functionality
        annotated_frame = analyzer.draw_detections(dummy_frame.copy(), detections)
        if annotated_frame is not None:
            print("✓ Detection drawing works")
        else:
            print("✗ Detection drawing failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ AIAnalyzer test failed: {e}")
        return False

def test_system_integration():
    """Test system integration"""
    print("\nTesting System Integration...")
    
    try:
        # Test GPU availability
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name()
            print(f"✓ CUDA GPU available: {device_name}")
        else:
            print("ⓘ No CUDA GPU detected (will use CPU)")
        
        # Test system info
        try:
            import cv2
            print(f"✓ OpenCV version: {cv2.__version__}")
        except:
            pass
        
        # Test base64 encoding/decoding
        dummy_frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        import cv2
        _, buffer = cv2.imencode('.jpg', dummy_frame)
        import base64
        b64_data = base64.b64encode(buffer.tobytes()).decode('utf-8')
        
        # Test decoding
        decoded_bytes = base64.b64decode(b64_data)
        decoded_frame = cv2.imdecode(np.frombuffer(decoded_bytes, np.uint8), cv2.IMREAD_COLOR)
        
        if decoded_frame is not None:
            print("✓ Base64 frame encoding/decoding works")
        else:
            print("✗ Base64 frame encoding/decoding failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ System integration test failed: {e}")
        return False

def test_models():
    """Test AI models loading"""
    print("\nTesting AI Models...")
    
    try:
        from ultralytics import YOLO
        
        # Test YOLOv11 model loading
        print("Testing YOLOv11-Pose model...")
        model = YOLO('yolo11n-pose.pt')
        print("✓ YOLOv11-Pose model loaded successfully")
        
        # Test DeepFace initialization
        print("Testing DeepFace initialization...")
        from deepface import DeepFace
        print("✓ DeepFace imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Model loading failed: {e}")
        return False

def main():
    """Run all tests"""
    print_header()
    
    tests = [
        ("Import Tests", test_imports),
        ("Flask App Tests", test_flask_app),
        ("Webcam Tests", test_webcam_availability),
        ("Camera Processor Tests", test_camera_processor),
        ("AI Analyzer Tests", test_ai_analyzer),
        ("Model Loading Tests", test_models),
        ("System Integration Tests", test_system_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            failed += 1
        
        print()  # Add spacing between tests
    
    # Results
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed! System is ready for deployment.")
        return True
    else:
        print("❌ Some tests failed. Please fix the issues before running the system.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 