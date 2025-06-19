#!/usr/bin/env python3
"""
WatchHer Web Application - Advanced Version
Supports both client-side webcam and server-side video file processing
Real-time AI analysis with dynamic map visualization
"""

from flask import Flask, render_template, jsonify, request, Response
import threading
import time
import json
import base64
import cv2
import numpy as np
import os
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
source_type = None  # 'webcam' or 'video_file'

# Thread lock for shared resources
processor_lock = threading.Lock()

@app.route('/')
def index():
    """
    Main web interface with source selection and dynamic map
    """
    return render_template('index.html')

@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    """Initialize and start analysis based on source type"""
    global camera_processor, processing_active, system_status, source_type
    
    try:
        data = request.get_json()
        source_type = data.get('source_type', 'webcam')
        video_path = data.get('video_path', '')
        
        with processor_lock:
            if camera_processor is not None:
                camera_processor.stop()
            
            if source_type == 'webcam':
                # Initialize for client-side webcam frames
                camera_processor = CameraProcessor(source=None)
                print("[INFO] WatchHer analysis started for live webcam")
                
            elif source_type == 'video_file':
                # Validate video file path
                if not video_path or not os.path.exists(video_path):
                    raise Exception(f"Video file not found: {video_path}")
                
                # Initialize for server-side video file processing
                camera_processor = CameraProcessor(source=video_path)
                camera_processor.start_video_processing_thread()
                print(f"[INFO] WatchHer analysis started for video file: {video_path}")
                
            else:
                raise Exception(f"Invalid source type: {source_type}")
            
            processing_active = True
            system_status = "active"
        
        return jsonify({
            "status": "success", 
            "message": f"Analysis started for {source_type}",
            "source_type": source_type,
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
    """Stop analysis and cleanup resources"""
    global camera_processor, processing_active, system_status, source_type
    
    try:
        with processor_lock:
            processing_active = False
            system_status = "inactive"
            if camera_processor:
                camera_processor.stop()
                camera_processor = None
            source_type = None
        
        return jsonify({
            "status": "success", 
            "message": "Analysis stopped successfully"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Failed to stop analysis: {str(e)}"
        }), 500

@app.route('/process_live_frame', methods=['POST'])
def process_live_frame():
    """
    Process frame from client-side webcam
    Receives base64 encoded frame, processes with AI, returns processed frame
    """
    global current_risk_score, current_fps, detection_count
    
    try:
        # Get frame data from request
        data = request.get_json()
        if not data or 'frame' not in data:
            return jsonify({"status": "error", "message": "No frame data provided"}), 400
        
        # Decode base64 frame
        frame_data = data['frame']
        if ',' in frame_data:
            frame_data = frame_data.split(',')[1]  # Remove data:image/jpeg;base64,
        
        frame_bytes = base64.b64decode(frame_data)
        
        # Convert to OpenCV format
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({"status": "error", "message": "Invalid frame data"}), 400
        
        # Process frame with camera processor if active
        if processing_active and camera_processor and source_type == 'webcam':
            with processor_lock:
                # Process the frame
                processed_frame, risk_score = camera_processor.process_frame_from_numpy(frame)
                current_risk_score = risk_score
                current_fps = camera_processor.get_current_fps()
                detection_count = camera_processor.get_detections_count()
                
                # Encode processed frame back to base64
                _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                processed_b64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
                
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

@app.route('/video_feed_stream')
def video_feed_stream():
    """
    MJPEG video stream for server-side video file processing
    """
    def generate():
        global camera_processor, current_risk_score, current_fps
        
        while processing_active and camera_processor and source_type == 'video_file':
            try:
                with processor_lock:
                    # Get frame and risk score from camera processor
                    frame_bytes, risk_score = camera_processor.get_frame_for_video_file()
                    current_risk_score = risk_score
                    current_fps = camera_processor.get_current_fps()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"[ERROR] Error in video feed stream: {e}")
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
                    'source_type': source_type,
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
        'source_type': source_type,
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
        'supported_sources': ['webcam', 'video_file']
    })

@app.route('/validate_video_path', methods=['POST'])
def validate_video_path():
    """Validate if video file path exists and is accessible"""
    try:
        data = request.get_json()
        video_path = data.get('video_path', '')
        
        if not video_path:
            return jsonify({'valid': False, 'message': 'No path provided'})
        
        if not os.path.exists(video_path):
            return jsonify({'valid': False, 'message': 'File does not exist'})
        
        # Try to open with OpenCV
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return jsonify({'valid': False, 'message': 'Cannot open video file'})
        
        # Get video info
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return jsonify({
            'valid': True, 
            'message': f'Valid video file: {fps:.1f} FPS, {duration:.1f}s duration',
            'fps': fps,
            'frame_count': frame_count,
            'duration': duration
        })
        
    except Exception as e:
        return jsonify({'valid': False, 'message': str(e)})

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
    """Get map color based on risk score"""
    if risk_score >= 70:
        return "#FF0000"  # Red
    elif risk_score >= 40:
        return "#FFA500"  # Orange
    elif risk_score >= 15:
        return "#FFFF00"  # Yellow
    else:
        return "#00FF00"  # Green

if __name__ == '__main__':
    print("[INFO] Starting WatchHer Web Interface...")
    print("[INFO] Navigate to http://127.0.0.1:5000/ to access the interface")
    print("[INFO] Features: Webcam + Video File support, AI Analysis, Dynamic Map")
    
    # Start Flask web server
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True) 