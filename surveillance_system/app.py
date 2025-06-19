#!/usr/bin/env python3
"""
WatchHer Web Application - Advanced Version
Webcam-only surveillance system with real-time AI analysis and dynamic map visualization
"""

from flask import Flask, render_template, jsonify, request, Response
import threading
import time
import json
import base64
import cv2
import numpy as np
from camera_processor import CameraProcessor
from datetime import datetime

app = Flask(__name__)

# Global system state
camera_processor = None
current_risk_score = 0.0
current_fps = 0.0
processing_active = False
system_status = "inactive"
detection_count = 0

# Thread lock for shared resources
processor_lock = threading.Lock()

@app.route('/')
def index():
    """
    Main web interface with webcam stream and dynamic map
    Strict color scheme: black, white, grey, red, green only
    """
    return render_template('index.html')

@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    """Initialize and start the camera processor for webcam analysis"""
    global camera_processor, processing_active, system_status
    
    try:
        with processor_lock:
            if camera_processor is not None:
                camera_processor.stop()
            
            # Initialize webcam-only camera processor
            camera_processor = CameraProcessor(source_index=0)
            processing_active = True
            system_status = "active"
        
        print("[INFO] WatchHer analysis started successfully")
        return jsonify({
            "status": "success", 
            "message": "WatchHer analysis started successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"[ERROR] Failed to start analysis: {e}")
        processing_active = False
        system_status = "error"
        return jsonify({
            "status": "error", 
            "message": f"Failed to start analysis: {str(e)}"
        }), 500

@app.route('/stop_analysis', methods=['POST'])
def stop_analysis():
    """Stop the camera processor and analysis"""
    global camera_processor, processing_active, system_status
    
    try:
        with processor_lock:
            processing_active = False
            system_status = "inactive"
            if camera_processor:
                camera_processor.stop()
                camera_processor = None
        
        return jsonify({
            "status": "success", 
            "message": "Analysis stopped successfully"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Failed to stop analysis: {str(e)}"
        }), 500

@app.route('/process_frame', methods=['POST'])
def process_frame():
    """
    Process frame from client-side webcam
    Receives base64 encoded frame, processes with AI, returns analysis
    """
    global current_risk_score, current_fps, detection_count
    
    try:
        # Get frame data from request
        data = request.get_json()
        if not data or 'frame' not in data:
            return jsonify({"status": "error", "message": "No frame data provided"}), 400
        
        # Decode base64 frame
        frame_data = data['frame'].split(',')[1]  # Remove data:image/jpeg;base64,
        frame_bytes = base64.b64decode(frame_data)
        
        # Convert to OpenCV format
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({"status": "error", "message": "Invalid frame data"}), 400
        
        # Process frame with camera processor if active
        if processing_active and camera_processor:
            with processor_lock:
                # Temporarily set frame for processing
                processed_frame_bytes, risk_score = camera_processor.get_frame()
                current_risk_score = risk_score
                current_fps = camera_processor.get_current_fps()
                detection_count = camera_processor.get_detections_count()
                
                # Encode processed frame back to base64
                processed_b64 = base64.b64encode(processed_frame_bytes).decode('utf-8')
                
                return jsonify({
                    "status": "success",
                    "processed_frame": f"data:image/jpeg;base64,{processed_b64}",
                    "risk_score": round(current_risk_score, 2),
                    "fps": round(current_fps, 1),
                    "detection_count": detection_count,
                    "timestamp": datetime.now().isoformat()
                })
        
        # If processing not active, return original frame
        _, buffer = cv2.imencode('.jpg', frame)
        original_b64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
        
        return jsonify({
            "status": "inactive",
            "processed_frame": f"data:image/jpeg;base64,{original_b64}",
            "risk_score": 0.0,
            "fps": 0.0,
            "detection_count": 0
        })
        
    except Exception as e:
        print(f"[ERROR] Frame processing failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/video_feed')
def video_feed():
    """
    MJPEG video stream for processed frames
    Alternative to client-side processing
    """
    def generate():
        global camera_processor, current_risk_score, current_fps
        
        frame_count = 0
        start_time = time.time()
        
        while processing_active and camera_processor:
            try:
                with processor_lock:
                    # Get frame and risk score from camera processor
                    frame_bytes, risk_score = camera_processor.get_frame()
                    current_risk_score = risk_score
                    current_fps = camera_processor.get_current_fps()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                time.sleep(0.1)  # Limit to ~10 FPS for web streaming
                
            except Exception as e:
                print(f"[ERROR] Error in video feed: {e}")
                break
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/risk_score_stream')
def risk_score_stream():
    """
    Server-Sent Events (SSE) endpoint for real-time risk score and system data
    """
    def generate():
        global current_risk_score, current_fps, processing_active, detection_count, system_status
        
        while True:
            try:
                # Prepare comprehensive data for frontend
                data = {
                    'risk_score': round(current_risk_score, 2),
                    'fps': round(current_fps, 1),
                    'detection_count': detection_count,
                    'timestamp': datetime.now().isoformat(),
                    'status': system_status,
                    'processing_active': processing_active,
                    'threat_level': get_threat_level(current_risk_score),
                    'map_color': get_map_color(current_risk_score)
                }
                
                yield f"data: {json.dumps(data)}\n\n"
                time.sleep(0.5)  # Update every 500ms
                
            except Exception as e:
                print(f"[ERROR] Error in risk score stream: {e}")
                break
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/status')
def api_status():
    """
    API endpoint to get comprehensive system status
    """
    global camera_processor, current_risk_score, current_fps, detection_count
    
    status = {
        'processing_active': processing_active,
        'camera_connected': camera_processor is not None,
        'system_status': system_status,
        'current_risk_score': round(current_risk_score, 2),
        'current_fps': round(current_fps, 1),
        'detection_count': detection_count,
        'threat_level': get_threat_level(current_risk_score),
        'analyzer_ready': camera_processor.analyzer.is_ready() if camera_processor and camera_processor.analyzer else False,
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(status)

@app.route('/api/system_info')
def system_info():
    """Get system capabilities and information"""
    import torch
    import cv2 as cv_version
    
    try:
        cuda_available = torch.cuda.is_available()
        cuda_device = torch.cuda.get_device_name() if cuda_available else "N/A"
    except:
        cuda_available = False
        cuda_device = "N/A"
    
    return jsonify({
        'opencv_version': cv_version.__version__,
        'cuda_available': cuda_available,
        'cuda_device': cuda_device,
        'webcam_resolution': "640x480",
        'ai_models': ['YOLOv11-Pose', 'DeepFace'],
        'max_fps': 30,
        'color_scheme': ['black', 'white', 'grey', 'red', 'green']
    })

def get_threat_level(risk_score):
    """Convert risk score to threat level"""
    if risk_score >= 80:
        return "CRITICAL"
    elif risk_score >= 60:
        return "HIGH"
    elif risk_score >= 30:
        return "MODERATE"
    elif risk_score >= 10:
        return "LOW"
    else:
        return "SAFE"

def get_map_color(risk_score):
    """Get map color based on risk score (strict color scheme)"""
    if risk_score >= 70:
        return "#FF0000"  # Red
    elif risk_score >= 40:
        return "#808080"  # Grey (representing orange in our limited palette)
    elif risk_score >= 15:
        return "#FFFFFF"  # White (representing yellow in our limited palette)
    else:
        return "#00FF00"  # Green

if __name__ == '__main__':
    print("[INFO] Starting WatchHer Web Interface...")
    print("[INFO] Navigate to http://127.0.0.1:5000/ to access the interface")
    print("[INFO] Strict color scheme: BLACK, WHITE, GREY, RED, GREEN")
    
    # Start Flask web server
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True) 