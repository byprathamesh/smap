from flask import Flask, render_template, jsonify, request
import folium
from folium.plugins import HeatMap
import threading
import time
from database import init_db, get_all_alerts, get_recent_alerts
from camera_processor import CameraProcessor
import config

app = Flask(__name__)

# Global storage for camera processors
camera_processors = []

@app.route('/')
def index():
    """
    Main dashboard showing system status and recent alerts.
    """
    try:
        recent_alerts = get_recent_alerts(24)  # Last 24 hours
        
        # Count alerts by type
        alert_counts = {}
        for alert in recent_alerts:
            alert_type = alert['alert_type']
            alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1
        
        # Get camera statuses
        camera_statuses = []
        for processor in camera_processors:
            status = processor.get_status()
            camera_statuses.append(status)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>WatchHer Surveillance Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .dashboard {{ display: flex; flex-wrap: wrap; gap: 20px; margin-top: 20px; }}
                .card {{ background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .alert-high {{ color: #e74c3c; font-weight: bold; }}
                .alert-medium {{ color: #f39c12; }}
                .alert-low {{ color: #27ae60; }}
                .button {{ background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
                .button:hover {{ background-color: #2980b9; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛡️ WatchHer Surveillance System</h1>
                <p>Real-time Safety Monitoring Dashboard</p>
            </div>
            
            <div class="dashboard">
                <div class="card">
                    <h3>📊 Alert Summary (24h)</h3>
                    <p>Total Alerts: <strong>{len(recent_alerts)}</strong></p>
                    {''.join([f'<p>{alert_type}: {count}</p>' for alert_type, count in alert_counts.items()])}
                    <a href="/heatmap" class="button">🗺️ View Risk Heatmap</a>
                </div>
                
                <div class="card">
                    <h3>📹 Camera Status</h3>
                    {
                        ''.join([
                            f'<p><strong>{status["camera_id"]}</strong>: '
                            f'{"🟢 Online" if status["running"] and status["camera_connected"] else "🔴 Offline"}'
                            f' {"(AI Ready)" if status["analyzer_ready"] else "(AI Loading)"}</p>'
                            for status in camera_statuses
                        ])
                    }
                </div>
                
                <div class="card">
                    <h3>⚡ Recent Alerts</h3>
                    {
                        ''.join([
                            f'<div style="margin-bottom: 10px; padding: 5px; border-left: 3px solid '
                            f'{"#e74c3c" if alert["threat_score"] > 25 else "#f39c12" if alert["threat_score"] > 15 else "#27ae60"}">'
                            f'<strong>{alert["camera_id"]}</strong> - {alert["alert_type"]}<br>'
                            f'<small>{alert["timestamp"]} | Score: {alert["threat_score"]}</small></div>'
                            for alert in recent_alerts[:10]
                        ]) if recent_alerts else '<p>No recent alerts</p>'
                    }
                </div>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        return f"Error loading dashboard: {e}"

@app.route('/heatmap')
def heatmap():
    """
    Generate and return an interactive heatmap showing alert locations.
    """
    try:
        # Get all alerts from database
        alerts = get_all_alerts()
        
        if not alerts:
            return """
            <html>
            <body>
                <h2>Risk Zone Heatmap</h2>
                <p>No alerts found in database yet.</p>
                <a href="/">← Back to Dashboard</a>
            </body>
            </html>
            """
        
        # Create base map centered on average location
        avg_lat = sum([alert['latitude'] for alert in alerts]) / len(alerts)
        avg_lon = sum([alert['longitude'] for alert in alerts]) / len(alerts)
        
        # Create map
        m = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=13,
            tiles='OpenStreetMap'
        )
        
        # Prepare heatmap data
        heat_data = []
        for alert in alerts:
            # Weight alerts by threat score and recency
            weight = max(1, alert['threat_score'] / 10)
            heat_data.append([alert['latitude'], alert['longitude'], weight])
        
        # Add heatmap layer
        HeatMap(heat_data, radius=15, blur=10, gradient={
            0.2: 'blue',
            0.4: 'lime', 
            0.6: 'orange',
            1.0: 'red'
        }).add_to(m)
        
        # Add markers for high-threat alerts
        for alert in alerts:
            if alert['threat_score'] > 20:
                folium.Marker(
                    location=[alert['latitude'], alert['longitude']],
                    popup=f"""
                        <strong>High Threat Alert</strong><br>
                        Camera: {alert['camera_id']}<br>
                        Type: {alert['alert_type']}<br>
                        Score: {alert['threat_score']}<br>
                        Time: {alert['timestamp']}<br>
                        Details: {alert['details']}
                    """,
                    icon=folium.Icon(color='red', icon='warning-sign')
                ).add_to(m)
        
        # Add title and navigation
        map_html = m._repr_html_()
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Risk Zone Heatmap - WatchHer</title>
            <style>
                body {{ margin: 0; font-family: Arial, sans-serif; }}
                .header {{ background-color: #2c3e50; color: white; padding: 15px; }}
                .nav {{ background-color: #34495e; padding: 10px; }}
                .nav a {{ color: white; text-decoration: none; margin-right: 20px; }}
                .nav a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🗺️ Risk Zone Heatmap</h1>
                <p>Showing {len(alerts)} alerts with threat-based intensity</p>
            </div>
            <div class="nav">
                <a href="/">← Dashboard</a>
                <a href="/api/alerts">📊 API Data</a>
                <span style="float: right;">🔴 High Risk | 🟠 Medium Risk | 🟢 Low Risk</span>
            </div>
            {map_html}
        </body>
        </html>
        """
        
    except Exception as e:
        return f"Error generating heatmap: {e}"

@app.route('/api/alerts')
def api_alerts():
    """
    API endpoint to get alerts as JSON.
    """
    try:
        hours = request.args.get('hours', 24, type=int)
        alerts = get_recent_alerts(hours)
        return jsonify(alerts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """
    API endpoint to get system status.
    """
    try:
        statuses = []
        for processor in camera_processors:
            statuses.append(processor.get_status())
        return jsonify(statuses)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_surveillance_system():
    """
    Start the surveillance system in background threads.
    """
    global camera_processors
    
    # Initialize database
    init_db()
    
    # Start camera processors
    for camera_id, camera_info in config.CAMERAS.items():
        if camera_info.get('enabled', False):
            processor = CameraProcessor(camera_id, camera_info)
            camera_processors.append(processor)
            
            # Start processor in background thread
            thread = threading.Thread(target=processor.run, daemon=True)
            thread.start()
            time.sleep(1)  # Delay between camera starts

if __name__ == '__main__':
    print("[INFO] Starting WatchHer Web Dashboard...")
    
    # Start surveillance system
    start_surveillance_system()
    
    # Start Flask web server
    app.run(host='0.0.0.0', port=5000, debug=True) 