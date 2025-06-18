import sqlite3
import os
from datetime import datetime

def init_db():
    """
    Initialize the SQLite database for storing alerts.
    Creates the alerts table if it doesn't exist.
    """
    db_path = 'alerts.db'
    
    # Create database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            timestamp DATETIME NOT NULL,
            alert_type TEXT NOT NULL,
            threat_score INTEGER,
            details TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[INFO] Database initialized successfully")

def insert_alert(camera_id, alert_type, threat_score=0, details=""):
    """
    Insert a new alert into the database.
    
    Args:
        camera_id: ID of the camera that triggered the alert
        alert_type: Type of alert (e.g., 'high_threat_detected', 'distress_signal', 'surrounded')
        threat_score: Risk score calculated by the system
        details: Additional details about the alert
    """
    # Camera location mapping (replace with actual coordinates)
    camera_locations = {
        'camera_1': {'lat': 40.7128, 'lon': -74.0060},  # New York example
        'camera_2': {'lat': 40.7589, 'lon': -73.9851},  # Times Square example
        'camera_3': {'lat': 40.6892, 'lon': -74.0445},  # Statue of Liberty example
        'default': {'lat': 40.7128, 'lon': -74.0060}    # Default location
    }
    
    location = camera_locations.get(camera_id, camera_locations['default'])
    
    try:
        conn = sqlite3.connect('alerts.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (camera_id, latitude, longitude, timestamp, alert_type, threat_score, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (camera_id, location['lat'], location['lon'], datetime.now(), alert_type, threat_score, details))
        
        conn.commit()
        conn.close()
        print(f"[INFO] Alert stored in database: {camera_id} - {alert_type}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to insert alert: {e}")
        return False

def get_all_alerts():
    """
    Retrieve all alerts from the database.
    
    Returns:
        List of alert dictionaries
    """
    try:
        conn = sqlite3.connect('alerts.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM alerts ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        
        alerts = []
        for row in rows:
            alerts.append({
                'id': row[0],
                'camera_id': row[1],
                'latitude': row[2],
                'longitude': row[3],
                'timestamp': row[4],
                'alert_type': row[5],
                'threat_score': row[6],
                'details': row[7]
            })
        
        conn.close()
        return alerts
        
    except Exception as e:
        print(f"[ERROR] Failed to retrieve alerts: {e}")
        return []

def get_recent_alerts(hours=24):
    """
    Get alerts from the last N hours.
    
    Args:
        hours: Number of hours to look back
        
    Returns:
        List of recent alert dictionaries
    """
    try:
        conn = sqlite3.connect('alerts.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM alerts 
            WHERE timestamp >= datetime('now', '-{} hours')
            ORDER BY timestamp DESC
        '''.format(hours))
        
        rows = cursor.fetchall()
        
        alerts = []
        for row in rows:
            alerts.append({
                'id': row[0],
                'camera_id': row[1],
                'latitude': row[2],
                'longitude': row[3],
                'timestamp': row[4],
                'alert_type': row[5],
                'threat_score': row[6],
                'details': row[7]
            })
        
        conn.close()
        return alerts
        
    except Exception as e:
        print(f"[ERROR] Failed to retrieve recent alerts: {e}")
        return [] 