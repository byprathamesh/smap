import time
import threading
import signal
import sys
from camera_processor import CameraProcessor
import config
from alert_system import get_alert_statistics


def print_system_info():
    """
    Print system information and configuration details.
    """
    print("=" * 80)
    print("                    WatchHer Surveillance System")
    print("                      Public Safety Monitoring")
    print("=" * 80)
    print(f"Configured Cameras: {len(config.CAMERAS)}")
    
    for camera_id, camera_info in config.CAMERAS.items():
        status = "ENABLED" if camera_info.get('enabled', False) else "DISABLED"
        print(f"  - {camera_id}: {camera_info['name']} ({camera_info['location']}) - {status}")
    
    print(f"Detection Settings:")
    print(f"  - Person Detection Threshold: {config.DETECTION_SETTINGS['person_detection_threshold']}")
    print(f"  - Gender Classification Threshold: {config.DETECTION_SETTINGS['gender_classification_threshold']}")
    print(f"  - Group Proximity Threshold: {config.DETECTION_SETTINGS['group_proximity_threshold']} pixels")
    print(f"  - Lone Woman Duration: {config.DETECTION_SETTINGS['lone_woman_duration']} seconds")
    print(f"  - Alert Cooldown: {config.ALERT_SETTINGS['alert_cooldown']} seconds")
    print("=" * 80)


def signal_handler(signum, frame):
    """
    Handle system signals for graceful shutdown.
    """
    print(f"\n[INFO] Received signal {signum}. Initiating graceful shutdown...")
    sys.exit(0)


def main():
    """
    Main function to initialize and run the surveillance system.
    """
    # Print startup message and system information
    print("[INFO] WatchHer Surveillance System - Initializing...")
    print_system_info()
    
    # Initialize lists to track processors and threads
    processors = []
    threads = []
    
    try:
        # Launch loop - create processors for each enabled camera
        enabled_cameras = 0
        
        for camera_id, camera_info in config.CAMERAS.items():
            if camera_info.get('enabled', False):
                print(f"[INFO] Initializing processor for {camera_id} ({camera_info['name']})...")
                
                # Create camera processor instance
                processor = CameraProcessor(camera_id, camera_info)
                processors.append(processor)
                
                # Create and configure thread
                thread = threading.Thread(target=processor.run, daemon=True)
                thread.name = f"CameraProcessor-{camera_id}"
                threads.append(thread)
                
                # Start the thread
                thread.start()
                enabled_cameras += 1
                
                # Small delay between camera initializations
                time.sleep(1)
            else:
                print(f"[INFO] Skipping disabled camera: {camera_id}")
        
        if enabled_cameras == 0:
            print("[WARNING] No enabled cameras found in configuration!")
            print("[INFO] Please check your config.py file and enable at least one camera.")
            return
        
        # System is now live
        print(f"\n[INFO] System is now live. Monitoring {enabled_cameras} cameras.")
        print("[INFO] Press Ctrl+C to exit.")
        print("-" * 80)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Main monitoring loop
        last_status_time = time.time()
        status_interval = 300  # Print status every 5 minutes
        
        try:
            while True:
                time.sleep(1)
                
                # Periodically print system status
                current_time = time.time()
                if current_time - last_status_time >= status_interval:
                    print_status_update(processors)
                    last_status_time = current_time
        
        except Exception as e:
            print(f"[CRITICAL] An unexpected error occurred: {e}")
            print("[INFO] Initiating emergency shutdown due to critical error...")
            raise  # Re-raise to trigger the outer exception handler
    
    except KeyboardInterrupt:
        print(f"\n[INFO] Shutdown signal received. Stopping all camera processors...")
        
        # Stop all processors gracefully
        for i, processor in enumerate(processors):
            print(f"[INFO] Stopping processor {i+1}/{len(processors)}: {processor.camera_id}")
            processor.stop()
        
        # Wait for all threads to finish
        print("[INFO] Waiting for all threads to finish...")
        for i, thread in enumerate(threads):
            if thread.is_alive():
                print(f"[INFO] Waiting for thread {i+1}/{len(threads)}: {thread.name}")
                thread.join(timeout=10.0)  # Wait up to 10 seconds per thread
                
                if thread.is_alive():
                    print(f"[WARNING] Thread {thread.name} did not stop gracefully")
        
        print("[INFO] System has been shut down gracefully.")
    
    except Exception as e:
        print(f"[ERROR] Unexpected error in main loop: {e}")
        print("[INFO] Attempting emergency shutdown...")
        
        # Emergency stop all processors
        for processor in processors:
            try:
                processor.stop()
            except Exception as stop_error:
                print(f"[ERROR] Error stopping processor {processor.camera_id}: {stop_error}")
        
        print("[INFO] Emergency shutdown completed.")
        sys.exit(1)


def print_status_update(processors):
    """
    Print a status update for all camera processors.
    
    Args:
        processors: List of CameraProcessor instances
    """
    try:
        print("\n" + "=" * 60)
        print(f"[STATUS UPDATE] {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Print processor status
        for processor in processors:
            status = processor.get_status()
            status_indicators = []
            
            if status['running']:
                status_indicators.append("RUNNING")
            else:
                status_indicators.append("STOPPED")
                
            if status['analyzer_ready']:
                status_indicators.append("AI-READY")
            else:
                status_indicators.append("AI-NOT-READY")
                
            if status['camera_connected']:
                status_indicators.append("CONNECTED")
            else:
                status_indicators.append("DISCONNECTED")
                
            if status['lone_woman_tracking']:
                status_indicators.append("TRACKING-LONE-WOMAN")
            
            status_str = " | ".join(status_indicators)
            print(f"  {status['camera_id']}: {status['camera_name']} - {status_str}")
        
        # Print alert statistics
        alert_stats = get_alert_statistics()
        print(f"\nAlert Statistics:")
        print(f"  - Total Alerts: {alert_stats['total_alerts']}")
        print(f"  - Active Cooldowns: {alert_stats['active_cooldowns']}")
        print(f"  - Storage Used: {alert_stats['storage_used_mb']} MB")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] Error printing status update: {e}")


if __name__ == "__main__":
    main() 