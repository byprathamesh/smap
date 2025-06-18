import cv2
import argparse
import numpy as np
import time
from camera_processor import CameraProcessor


def main(video_path):
    """
    Main function to run WatchHer surveillance analysis on video files or webcam.
    
    Args:
        video_path: Path to video file or None for webcam
    """
    # Initialize processor with video file or webcam
    source = video_path if video_path else 0
    
    try:
        processor = CameraProcessor(source=source)
        
        print("=" * 60)
        print("🛡️  WatchHer Surveillance System")
        print("   Intelligent Public Safety Monitoring")
        print("=" * 60)
        print(f"📹 Source: {'Webcam 0' if source == 0 else video_path}")
        print("🎯 Features: YOLOv8-Pose + DeepFace + Dynamic Risk Scoring")
        print("⚠️  Press 'q' to quit")
        print("=" * 60)
        
        # Initialize camera
        if not processor._initialize_camera():
            print(f"❌ Failed to initialize source: {source}")
            return
        
        # **PART 1 FIX**: Create window ONCE outside the main loop to prevent multiple windows
        window_name = 'WatchHer Surveillance'
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
        print(f"DEBUG_MAIN: Created single window: {window_name}")
            
        frame_count = 0
        start_time = time.time()
        
        while True:
            try:
                # Get processed frame and risk score
                frame_bytes, risk_score = processor.get_frame()
                
                # Decode frame for display
                frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
                
                if frame is None:
                    print("⚠️  End of video or no frame available")
                    break
                
                # Display real-time risk score
                frame_count += 1
                elapsed_time = time.time() - start_time
                fps = frame_count / elapsed_time if elapsed_time > 0 else 0
                
                # Risk level classification
                if risk_score > 100:
                    risk_level = "🔴 HIGH RISK"
                    risk_color = "RED"
                elif risk_score > 40:
                    risk_level = "🟡 MEDIUM RISK"
                    risk_color = "YELLOW"
                else:
                    risk_level = "🟢 LOW RISK"
                    risk_color = "GREEN"
                
                # Print risk score to console with timestamp
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] Risk Score: {risk_score:.1f} | {risk_level} | FPS: {fps:.1f}")
                
                # **PART 1 FIX**: Display frame using consistent window name
                cv2.imshow(window_name, frame)
                print(f"DEBUG_MAIN: Displayed frame in window: {window_name}")
                
                # **PART 1 FIX**: Use cv2.waitKey(1) for faster response instead of 25ms
                key = cv2.waitKey(1) & 0xFF  
                if key == ord('q'):
                    print("\n🛑 Stopping analysis...")
                    break
                elif key == ord(' '):
                    print(f"\n⏸️  Paused - Current Risk Score: {risk_score:.1f}")
                    cv2.waitKey(0)  # Wait for any key to continue
                    print("▶️  Resuming...")
                    
            except KeyboardInterrupt:
                print("\n🛑 Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error processing frame: {e}")
                break
        
        # Cleanup
        processor._cleanup_camera()
        # **PART 1 FIX**: Destroy windows ONCE after loop terminates
        cv2.destroyAllWindows()
        print(f"DEBUG_MAIN: Destroyed all windows after loop termination")
        
        # Final statistics
        total_time = time.time() - start_time
        avg_fps = frame_count / total_time if total_time > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 Analysis Complete")
        print("=" * 60)
        print(f"⏱️  Total Time: {total_time:.1f} seconds")
        print(f"🎞️  Frames Processed: {frame_count}")
        print(f"📈 Average FPS: {avg_fps:.1f}")
        print("✅ Analysis stopped successfully")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        print("💡 Please check your video file path or camera connection")


def run_multi_camera_mode():
    """
    Run the traditional multi-camera surveillance mode using config.py
    """
    import threading
    import signal
    import sys
    import config
    from alert_system import get_alert_statistics
    
    def signal_handler(signum, frame):
        print(f"\n[INFO] Received signal {signum}. Initiating graceful shutdown...")
        sys.exit(0)
    
    def print_system_info():
        print("=" * 80)
        print("                    WatchHer Surveillance System")
        print("                      Multi-Camera Monitoring")
        print("=" * 80)
        print(f"Configured Cameras: {len(config.CAMERAS)}")
        
        for camera_id, camera_info in config.CAMERAS.items():
            status = "ENABLED" if camera_info.get('enabled', False) else "DISABLED"
            print(f"  - {camera_id}: {camera_info['name']} ({camera_info['location']}) - {status}")
        print("=" * 80)
    
    print_system_info()
    
    processors = []
    threads = []
    
    try:
        enabled_cameras = 0
        
        for camera_id, camera_info in config.CAMERAS.items():
            if camera_info.get('enabled', False):
                print(f"[INFO] Initializing processor for {camera_id} ({camera_info['name']})...")
                
                processor = CameraProcessor(camera_id, camera_info)
                processors.append(processor)
                
                thread = threading.Thread(target=processor.run, daemon=True)
                thread.name = f"CameraProcessor-{camera_id}"
                threads.append(thread)
                
                thread.start()
                enabled_cameras += 1
                time.sleep(1)
            else:
                print(f"[INFO] Skipping disabled camera: {camera_id}")
        
        if enabled_cameras == 0:
            print("[WARNING] No enabled cameras found in configuration!")
            return
        
        print(f"\n[INFO] System is now live. Monitoring {enabled_cameras} cameras.")
        print("[INFO] Press Ctrl+C to exit.")
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        while True:
            time.sleep(60)  # Status update every minute
            
    except KeyboardInterrupt:
        print(f"\n[INFO] Shutdown signal received. Stopping all camera processors...")
        
        for processor in processors:
            processor.stop()
            
        for thread in threads:
            if thread.is_alive():
                thread.join(timeout=10.0)
        
        print("[INFO] System has been shut down gracefully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="WatchHer: Intelligent Public Safety Monitoring with Dynamic Risk Scoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Use webcam
  python main.py --video sample_video.mp4           # Analyze video file
  python main.py --video /path/to/surveillance.mp4  # Analyze video with full path
  python main.py --multi-camera                     # Run multi-camera mode with config.py
  
Features:
  • YOLOv8-Pose for human pose detection
  • DeepFace for gender and age analysis
  • Dynamic risk scoring algorithm
  • Distress signal detection (hands up, falling)
  • Woman surrounded detection
  • Real-time threat assessment
        """
    )
    
    parser.add_argument('--video', type=str, 
                       help='Path to the video file to analyze')
    parser.add_argument('--multi-camera', action='store_true',
                       help='Run traditional multi-camera mode using config.py')
    
    args = parser.parse_args()
    
    if args.multi_camera:
        run_multi_camera_mode()
    else:
        main(args.video) 