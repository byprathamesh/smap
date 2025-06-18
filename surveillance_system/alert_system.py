import os
import datetime
import cv2
import config
from database import insert_alert


# Global dictionary to track last alert times for cooldown management
# Structure: {(camera_id, alert_type): datetime_object}
last_alert_times = {}


def trigger_alert(frame, camera_id, alert_type, details, threat_score=0):
    """
    Trigger an alert with cooldown management, console logging, and snapshot saving.
    
    Args:
        frame: The video frame (numpy array) to save as evidence
        camera_id: Identifier for the camera that triggered the alert
        alert_type: Type of alert (e.g., 'lone_woman', 'group_surrounding', 'distress_signal', 'surrounded')
        details: Additional details about the alert
        threat_score: Calculated threat score for this alert
    
    Returns:
        bool: True if alert was triggered, False if blocked by cooldown
    """
    global last_alert_times
    
    # Step 1: Check cooldown period
    alert_key = (camera_id, alert_type)
    current_time = datetime.datetime.now()
    cooldown_seconds = config.ALERT_SETTINGS['alert_cooldown']
    
    if alert_key in last_alert_times:
        time_since_last_alert = (current_time - last_alert_times[alert_key]).total_seconds()
        if time_since_last_alert < cooldown_seconds:
            # Alert is still in cooldown period, silently return
            return False
    
    # Step 2: Generate timestamp for logging and filename
    timestamp_str = current_time.strftime("%Y-%m-%d_%H-%M-%S")
    timestamp_display = current_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Step 3: Log alert to console
    camera_name = _get_camera_name(camera_id)
    alert_message = (
        f"[ALERT] [{timestamp_display}] Camera: {camera_id} ({camera_name}) - "
        f"Type: {alert_type} - Details: {details}"
    )
    print(alert_message)
    print("-" * 80)  # Separator line for better visibility
    
    # Step 4: Save snapshot
    snapshot_saved = _save_alert_snapshot(frame, camera_id, alert_type, timestamp_str)
    
    if snapshot_saved:
        print(f"Alert snapshot saved successfully")
    else:
        print(f"Warning: Failed to save alert snapshot")
    
    # Step 5: Store alert in database
    insert_alert(camera_id, alert_type, threat_score=threat_score, details=details)
    
    # Step 6: Update cooldown tracking
    last_alert_times[alert_key] = current_time
    
    # Optional: Clean up old alert files if we exceed the maximum
    _cleanup_old_alerts()
    
    return True


def _get_camera_name(camera_id):
    """
    Get the friendly name for a camera ID from the config.
    
    Args:
        camera_id: The camera identifier
        
    Returns:
        str: The camera name or 'Unknown' if not found
    """
    try:
        if camera_id in config.CAMERAS:
            return config.CAMERAS[camera_id]['name']
        else:
            return 'Unknown'
    except Exception:
        return 'Unknown'


def _save_alert_snapshot(frame, camera_id, alert_type, timestamp_str):
    """
    Save the alert frame as a JPEG snapshot.
    
    Args:
        frame: The video frame to save
        camera_id: Camera identifier
        alert_type: Type of alert
        timestamp_str: Formatted timestamp string
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Create filename: CAM01_group_surround_2025-06-14_17-30-00.jpg
        filename = f"{camera_id}_{alert_type}_{timestamp_str}.jpg"
        filepath = os.path.join(config.ALERT_SETTINGS['snapshot_dir'], filename)
        
        # Ensure the directory exists
        os.makedirs(config.ALERT_SETTINGS['snapshot_dir'], exist_ok=True)
        
        # Save the frame as JPEG
        success = cv2.imwrite(filepath, frame)
        
        if success:
            print(f"Snapshot saved: {filename}")
            return True
        else:
            print(f"Error: Failed to write image file {filename}")
            return False
            
    except Exception as e:
        print(f"Error saving alert snapshot: {e}")
        return False


def _cleanup_old_alerts():
    """
    Clean up old alert files if we exceed the maximum number of stored alerts.
    Removes the oldest files first.
    """
    try:
        alert_dir = config.ALERT_SETTINGS['snapshot_dir']
        max_alerts = config.ALERT_SETTINGS['max_stored_alerts']
        
        if not os.path.exists(alert_dir):
            return
        
        # Get all .jpg files in the alert directory
        alert_files = []
        for filename in os.listdir(alert_dir):
            if filename.lower().endswith('.jpg'):
                filepath = os.path.join(alert_dir, filename)
                if os.path.isfile(filepath):
                    # Get file modification time
                    mtime = os.path.getmtime(filepath)
                    alert_files.append((mtime, filepath, filename))
        
        # Sort by modification time (oldest first)
        alert_files.sort(key=lambda x: x[0])
        
        # Remove excess files
        if len(alert_files) > max_alerts:
            files_to_remove = len(alert_files) - max_alerts
            for i in range(files_to_remove):
                try:
                    os.remove(alert_files[i][1])
                    print(f"Cleaned up old alert file: {alert_files[i][2]}")
                except Exception as e:
                    print(f"Error removing old alert file {alert_files[i][2]}: {e}")
                    
    except Exception as e:
        print(f"Error during alert cleanup: {e}")


def get_alert_statistics():
    """
    Get statistics about the alert system.
    
    Returns:
        dict: Dictionary containing alert statistics
    """
    try:
        alert_dir = config.ALERT_SETTINGS['snapshot_dir']
        
        if not os.path.exists(alert_dir):
            return {
                'total_alerts': 0,
                'active_cooldowns': len(last_alert_times),
                'storage_used_mb': 0
            }
        
        # Count alert files
        alert_files = [f for f in os.listdir(alert_dir) if f.lower().endswith('.jpg')]
        total_alerts = len(alert_files)
        
        # Calculate storage used
        total_size = 0
        for filename in alert_files:
            filepath = os.path.join(alert_dir, filename)
            if os.path.isfile(filepath):
                total_size += os.path.getsize(filepath)
        
        storage_mb = total_size / (1024 * 1024)  # Convert to MB
        
        return {
            'total_alerts': total_alerts,
            'active_cooldowns': len(last_alert_times),
            'storage_used_mb': round(storage_mb, 2)
        }
        
    except Exception as e:
        print(f"Error getting alert statistics: {e}")
        return {
            'total_alerts': 0,
            'active_cooldowns': 0,
            'storage_used_mb': 0
        }


def clear_cooldowns():
    """
    Clear all active cooldowns. Useful for testing or manual reset.
    """
    global last_alert_times
    last_alert_times.clear()
    print("All alert cooldowns cleared")


def is_night_time():
    """
    Check if the current time is within the night hours defined in config.
    
    Returns:
        bool: True if it's currently night time
    """
    try:
        current_time = datetime.datetime.now().time()
        night_start = config.TIME_SETTINGS['night_start']
        night_end = config.TIME_SETTINGS['night_end']
        
        # Handle case where night spans midnight
        if night_start > night_end:
            # Night time spans midnight (e.g., 22:00 to 05:00)
            return current_time >= night_start or current_time <= night_end
        else:
            # Night time within same day
            return night_start <= current_time <= night_end
            
    except Exception as e:
        print(f"Error checking night time: {e}")
        return False 