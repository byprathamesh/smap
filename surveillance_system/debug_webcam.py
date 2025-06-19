#!/usr/bin/env python3
"""
Webcam Debug Script
Quick diagnostic to identify black screen issues
"""

import cv2
import numpy as np
import base64
from ai_analyzer import AIAnalyzer

def test_webcam_direct():
    """Test direct webcam access"""
    print("🔍 Testing direct webcam access...")
    
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot open webcam")
            return False
        
        # Read a few frames
        for i in range(5):
            ret, frame = cap.read()
            if ret:
                print(f"✅ Frame {i+1}: {frame.shape}, mean pixel value: {np.mean(frame):.1f}")
                
                # Save a test frame
                if i == 0:
                    cv2.imwrite('debug_webcam_frame.jpg', frame)
                    print(f"✅ Saved test frame: debug_webcam_frame.jpg")
            else:
                print(f"❌ Failed to read frame {i+1}")
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ Webcam test failed: {e}")
        return False

def test_ai_analyzer():
    """Test AI analyzer with a test frame"""
    print("\n🔍 Testing AI analyzer...")
    
    try:
        analyzer = AIAnalyzer()
        if not analyzer.is_ready():
            print("❌ AI analyzer not ready")
            return False
        
        # Create a test frame with some content
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        test_frame[100:380, 200:440] = [0, 255, 0]  # Green rectangle
        
        detections = analyzer.analyze_frame(test_frame)
        print(f"✅ AI analyzer working, found {len(detections)} detections")
        
        # Test drawing
        annotated = analyzer.draw_detections(test_frame, detections)
        cv2.imwrite('debug_ai_output.jpg', annotated)
        print("✅ Saved AI output: debug_ai_output.jpg")
        
        return True
        
    except Exception as e:
        print(f"❌ AI analyzer test failed: {e}")
        return False

def test_base64_encoding():
    """Test base64 frame encoding"""
    print("\n🔍 Testing base64 encoding...")
    
    try:
        # Create a test frame
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Encode to JPEG
        ret, buffer = cv2.imencode('.jpg', test_frame)
        if not ret:
            print("❌ Failed to encode frame to JPEG")
            return False
        
        # Encode to base64
        frame_b64 = base64.b64encode(buffer).decode('utf-8')
        print(f"✅ Base64 encoding successful, length: {len(frame_b64)}")
        
        # Test decoding
        decoded_buffer = base64.b64decode(frame_b64)
        decoded_frame = cv2.imdecode(np.frombuffer(decoded_buffer, np.uint8), cv2.IMREAD_COLOR)
        
        if decoded_frame is not None:
            print(f"✅ Base64 decoding successful: {decoded_frame.shape}")
            cv2.imwrite('debug_base64_test.jpg', decoded_frame)
            return True
        else:
            print("❌ Base64 decoding failed")
            return False
        
    except Exception as e:
        print(f"❌ Base64 test failed: {e}")
        return False

def test_frame_processing_pipeline():
    """Test the complete frame processing pipeline"""
    print("\n🔍 Testing complete frame processing pipeline...")
    
    try:
        from camera_processor import CameraProcessor
        
        # Initialize processor
        processor = CameraProcessor(source=None)
        if not processor.is_running:
            print("❌ Camera processor failed to initialize")
            return False
        
        # Test with webcam frame
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                print(f"✅ Got webcam frame: {frame.shape}")
                
                # Process frame
                processed_frame, risk_score = processor.process_frame_from_numpy(frame)
                print(f"✅ Processed frame: {processed_frame.shape}, risk: {risk_score}")
                
                # Save processed frame
                cv2.imwrite('debug_processed_frame.jpg', processed_frame)
                print("✅ Saved processed frame: debug_processed_frame.jpg")
                
                # Check if frame is black
                mean_pixel = np.mean(processed_frame)
                if mean_pixel < 10:
                    print(f"⚠️ WARNING: Processed frame appears very dark (mean: {mean_pixel:.1f})")
                else:
                    print(f"✅ Processed frame looks good (mean: {mean_pixel:.1f})")
                
                processor.stop()
                return True
            else:
                print("❌ Failed to get webcam frame")
                return False
        else:
            print("❌ Cannot open webcam for pipeline test")
            return False
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        return False

def main():
    """Run all diagnostic tests"""
    print("🔬 WatchHer Webcam Diagnostic Tool")
    print("=" * 50)
    
    tests = [
        ("Direct Webcam Access", test_webcam_direct),
        ("AI Analyzer", test_ai_analyzer), 
        ("Base64 Encoding", test_base64_encoding),
        ("Complete Pipeline", test_frame_processing_pipeline)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
        print("-" * 30)
    
    # Summary
    print(f"\n📊 Diagnostic Results:")
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed < len(results):
        print("\n💡 Troubleshooting Tips:")
        print("- Check if webcam is being used by another application")
        print("- Verify webcam permissions in browser")
        print("- Try refreshing the web page")
        print("- Check the saved debug images for visual confirmation")

if __name__ == "__main__":
    main() 