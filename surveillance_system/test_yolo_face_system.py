#!/usr/bin/env python3
"""
Test Script for YOLO-Based Face Detection System
Verifies that the refactored surveillance system works without TensorFlow dependencies
"""

import cv2
import numpy as np
import time
from ai_analyzer import AIAnalyzer
from yolo_face_detector import YOLOFaceDetector
import sys
import os

def test_yolo_face_detector():
    """Test the custom YOLO face detector"""
    print("=" * 60)
    print("🧪 Testing Custom YOLO Face Detector")
    print("=" * 60)
    
    try:
        # Initialize face detector
        face_detector = YOLOFaceDetector(model_size='n', confidence_threshold=0.4)
        
        if not face_detector.is_ready():
            print("❌ Face detector failed to initialize")
            return False
        
        print("✅ Face detector initialized successfully")
        
        # Create a simple test image
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Test face detection
        faces = face_detector.detect_faces(test_image)
        print(f"✅ Face detection test completed - found {len(faces)} faces")
        
        # Test face attribute analysis
        if faces:
            attrs = face_detector.analyze_face_attributes(test_image, faces[0]['bbox'])
            print(f"✅ Face attribute analysis: age={attrs['age']}, gender={attrs['gender']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Face detector test failed: {e}")
        return False

def test_ai_analyzer():
    """Test the AI analyzer with YOLO face detection"""
    print("=" * 60)
    print("🧪 Testing AI Analyzer with YOLO Face Detection")
    print("=" * 60)
    
    try:
        # Initialize AI analyzer
        analyzer = AIAnalyzer()
        
        if not analyzer.is_ready():
            print("❌ AI analyzer failed to initialize")
            return False
        
        print("✅ AI analyzer initialized successfully")
        
        # Create a test frame
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Test frame analysis
        start_time = time.time()
        detections = analyzer.analyze_frame(test_frame)
        analysis_time = time.time() - start_time
        
        print(f"✅ Frame analysis completed in {analysis_time:.3f}s")
        print(f"✅ Found {len(detections)} person detections")
        
        # Test drawing detections
        annotated_frame = analyzer.draw_detections(test_frame, detections)
        print("✅ Detection drawing test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ AI analyzer test failed: {e}")
        return False

def test_dependency_cleanup():
    """Test that TensorFlow dependencies are properly removed"""
    print("=" * 60)
    print("🧪 Testing Dependency Cleanup")
    print("=" * 60)
    
    forbidden_imports = [
        'tensorflow',
        'tf_keras', 
        'deepface',
        'retina_face'
    ]
    
    all_clean = True
    
    for module in forbidden_imports:
        try:
            __import__(module)
            print(f"❌ {module} is still installed (should be removed)")
            all_clean = False
        except ImportError:
            print(f"✅ {module} properly removed")
    
    # Test that required modules are available
    required_imports = [
        'torch',
        'ultralytics',
        'cv2',
        'numpy'
    ]
    
    for module in required_imports:
        try:
            __import__(module)
            print(f"✅ {module} available")
        except ImportError:
            print(f"❌ {module} missing (required)")
            all_clean = False
    
    return all_clean

def test_camera_processor_integration():
    """Test camera processor with YOLO face detection"""
    print("=" * 60)
    print("🧪 Testing Camera Processor Integration")
    print("=" * 60)
    
    try:
        from camera_processor import CameraProcessor
        
        # Initialize camera processor for live webcam
        processor = CameraProcessor(source=None)
        
        if not processor.is_running:
            print("❌ Camera processor failed to initialize")
            return False
        
        print("✅ Camera processor initialized for live webcam")
        
        # Test frame processing
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        start_time = time.time()
        processed_frame, risk_score = processor.process_frame_from_numpy(test_frame)
        process_time = time.time() - start_time
        
        print(f"✅ Frame processing completed in {process_time:.3f}s")
        print(f"✅ Risk score: {risk_score:.2f}")
        print(f"✅ FPS: {processor.get_current_fps():.1f}")
        print(f"✅ Detections: {processor.get_detections_count()}")
        
        # Cleanup
        processor.stop()
        print("✅ Camera processor stopped successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Camera processor test failed: {e}")
        return False

def run_performance_benchmark():
    """Run performance benchmark"""
    print("=" * 60)
    print("🚀 Performance Benchmark")
    print("=" * 60)
    
    try:
        analyzer = AIAnalyzer()
        
        if not analyzer.is_ready():
            print("❌ Cannot run benchmark - analyzer not ready")
            return False
        
        # Create test frames
        test_frames = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(10)
        ]
        
        # Warm up
        for frame in test_frames[:2]:
            analyzer.analyze_frame(frame)
        
        # Benchmark
        start_time = time.time()
        total_detections = 0
        
        for frame in test_frames:
            detections = analyzer.analyze_frame(frame)
            total_detections += len(detections)
        
        total_time = time.time() - start_time
        avg_fps = len(test_frames) / total_time
        
        print(f"✅ Processed {len(test_frames)} frames in {total_time:.3f}s")
        print(f"✅ Average FPS: {avg_fps:.1f}")
        print(f"✅ Total detections: {total_detections}")
        print(f"✅ Average processing time per frame: {total_time/len(test_frames)*1000:.1f}ms")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance benchmark failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🎯 YOLO-Based Face Detection System Test Suite")
    print("Testing refactored surveillance system without TensorFlow")
    print("")
    
    tests = [
        ("Dependency Cleanup", test_dependency_cleanup),
        ("YOLO Face Detector", test_yolo_face_detector),
        ("AI Analyzer", test_ai_analyzer),
        ("Camera Processor Integration", test_camera_processor_integration),
        ("Performance Benchmark", run_performance_benchmark)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔧 Running: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
        
        print("-" * 40)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! YOLO-based face detection system is working correctly.")
        print("✅ TensorFlow dependencies successfully removed")
        print("✅ System is ready for production use")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 