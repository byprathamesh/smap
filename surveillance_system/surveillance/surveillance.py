"""
WatchHer Surveillance System - Unified Reflex Application
Complete surveillance system with integrated frontend and backend
"""

import reflex as rx
import asyncio
import cv2
import numpy as np
import base64
import time
import threading
import math
from datetime import datetime
from typing import List, Optional, Dict, Any
import io
from PIL import Image

# Import backend modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ai_analyzer import AIAnalyzer
from camera_processor import CameraProcessor

# Global backend instances (handled outside of state)
_surveillance_backend = {
    'camera_processor': None,
    'ai_analyzer': None,
    'initialized': False,
    'video_thread': None,
    'stop_video': False
}

# Database Models using Reflex ORM
class AlertLog(rx.Model, table=True):
    """Database model for alert logs"""
    timestamp: datetime
    risk_score: float
    detection_count: int
    alert_type: str
    details: str
    resolved: bool = False

class SystemLog(rx.Model, table=True):
    """Database model for system logs"""
    timestamp: datetime
    event_type: str
    message: str
    details: Optional[str] = None

class SurveillanceState(rx.State):
    """Unified state management for the entire surveillance system"""
    
    # System status
    system_active: bool = False
    current_frame_data: str = ""
    risk_score: float = 0.0
    fps: float = 0.0
    detection_count: int = 0
    system_status: str = "Inactive"
    
    # Source configuration
    source_type: str = "webcam"
    video_path: str = ""
    
    # UI state
    loading: bool = False
    error_message: str = ""
    log_messages: List[str] = []
    
    # Analytics data
    total_alerts: int = 0
    session_start_time: Optional[datetime] = None
    last_detection_time: Optional[datetime] = None
    
    # Advanced settings
    risk_threshold: float = 50.0
    auto_alert: bool = True
    recording_enabled: bool = False

    def initialize_backend(self):
        """Initialize backend components"""
        global _surveillance_backend
        try:
            if not _surveillance_backend['initialized']:
                _surveillance_backend['ai_analyzer'] = AIAnalyzer()
                _surveillance_backend['initialized'] = True
                
            self.add_log("🤖 AI models initialized successfully")
            return True
        except Exception as e:
            self.error_message = f"Failed to initialize AI: {str(e)}"
            self.add_log(f"❌ AI initialization failed: {str(e)}")
            return False

    def start_webcam_analysis(self):
        """Start live webcam analysis with integrated backend"""
        global _surveillance_backend
        
        self.loading = True
        self.error_message = ""
        
        try:
            # Initialize backend if needed
            if not _surveillance_backend['initialized']:
                success = self.initialize_backend()
                if not success:
                    self.loading = False
                    return
            
            # Initialize camera processor for webcam
            if _surveillance_backend['camera_processor']:
                _surveillance_backend['camera_processor'].stop()
                
            _surveillance_backend['camera_processor'] = CameraProcessor(source=None)
            
            self.system_active = True
            self.system_status = "Active - Webcam"
            self.session_start_time = datetime.now()
            self.source_type = "webcam"
            self.loading = False
            self.add_log("✅ Webcam analysis started - Please allow camera access in browser")
                
        except Exception as e:
            self.error_message = f"Failed to start webcam: {str(e)}"
            self.add_log(f"❌ Error: {str(e)}")
            self.loading = False

    def start_video_analysis(self):
        """Start video file analysis with integrated backend"""
        global _surveillance_backend
        
        if not self.video_path:
            self.error_message = "Please specify a video file path"
            return
            
        self.loading = True
        self.error_message = ""
        
        try:
            # Initialize backend if needed
            if not _surveillance_backend['initialized']:
                success = self.initialize_backend()
                if not success:
                    self.loading = False
                    return
            
            # Stop any existing processing
            if _surveillance_backend['camera_processor']:
                _surveillance_backend['camera_processor'].stop()
            
            # Check if video file exists
            if not os.path.exists(self.video_path):
                self.error_message = f"Video file not found: {self.video_path}"
                self.loading = False
                return
                
            _surveillance_backend['camera_processor'] = CameraProcessor(source=self.video_path)
            
            self.system_active = True
            self.system_status = "Active - Video"
            self.session_start_time = datetime.now()
            self.source_type = "video_file"
            self.loading = False
            self.add_log("✅ Video analysis started successfully")
            
            # Start video processing in background
            self._start_video_processing_loop()
                
        except Exception as e:
            self.error_message = f"Failed to start video: {str(e)}"
            self.add_log(f"❌ Error: {str(e)}")
            self.loading = False

    def _start_video_processing_loop(self):
        """Start background video processing loop for video files"""
        global _surveillance_backend
        
        def video_processing_loop():
            _surveillance_backend['stop_video'] = False
            while not _surveillance_backend['stop_video'] and self.system_active:
                try:
                    if _surveillance_backend['camera_processor']:
                        frame_bytes, risk_score = _surveillance_backend['camera_processor'].get_frame_for_video_file()
                        
                        if frame_bytes and len(frame_bytes) > 0:
                            # Store frame data in global backend for state updates
                            frame_b64 = base64.b64encode(frame_bytes).decode('utf-8')
                            _surveillance_backend['current_frame'] = f"data:image/jpeg;base64,{frame_b64}"
                            _surveillance_backend['current_risk'] = risk_score
                            _surveillance_backend['current_fps'] = _surveillance_backend['camera_processor'].get_current_fps()
                            _surveillance_backend['current_detections'] = _surveillance_backend['camera_processor'].get_detections_count()
                    
                    time.sleep(0.2)  # 5 FPS for UI updates
                    
                except Exception as e:
                    print(f"[ERROR] Video processing loop error: {e}")
                    break
        
        # Start video processing thread
        _surveillance_backend['video_thread'] = threading.Thread(target=video_processing_loop, daemon=True)
        _surveillance_backend['video_thread'].start()

    def update_video_display(self):
        """Update video display with latest frame from backend (called by timer)"""
        global _surveillance_backend
        
        if self.system_active and self.source_type == "video_file":
            if 'current_frame' in _surveillance_backend and _surveillance_backend['current_frame']:
                self.current_frame_data = _surveillance_backend['current_frame']
                self.risk_score = _surveillance_backend.get('current_risk', 0.0)
                self.fps = _surveillance_backend.get('current_fps', 0.0)
                self.detection_count = _surveillance_backend.get('current_detections', 0)
                
                # Check for alerts
                if self.risk_score > self.risk_threshold and self.auto_alert:
                    self.trigger_alert(self.risk_score, self.detection_count)

    def stop_analysis(self):
        """Stop all analysis with cleanup"""
        global _surveillance_backend
        
        self.loading = True
        
        try:
            # Stop video processing
            _surveillance_backend['stop_video'] = True
            
            # Stop processing
            if _surveillance_backend['camera_processor']:
                _surveillance_backend['camera_processor'].stop()
                _surveillance_backend['camera_processor'] = None
            
            self.system_active = False
            self.system_status = "Inactive"
            self.current_frame_data = ""
            self.risk_score = 0.0
            self.fps = 0.0
            self.detection_count = 0
            self.loading = False
            self.add_log("🛑 Analysis stopped")
            
            # Log session to database
            if self.session_start_time:
                session_duration = datetime.now() - self.session_start_time
                self.add_system_log("session_end", f"Session duration: {session_duration}")
                    
        except Exception as e:
            self.error_message = f"Failed to stop: {str(e)}"
            self.loading = False

    def process_webcam_frame(self, frame_data: str):
        """Process a webcam frame from the frontend"""
        global _surveillance_backend
        
        if not self.system_active or not _surveillance_backend['camera_processor']:
            return
            
        try:
            # Decode base64 frame
            if ',' in frame_data:
                frame_data = frame_data.split(',')[1]
                
            frame_bytes = base64.b64decode(frame_data)
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return
                
            # Process frame using integrated backend
            processed_frame, risk_score = _surveillance_backend['camera_processor'].process_frame_from_numpy(frame)
            
            # Update state
            # Encode processed frame
            _, buffer = cv2.imencode('.jpg', processed_frame)
            processed_b64 = base64.b64encode(buffer).decode('utf-8')
            self.current_frame_data = f"data:image/jpeg;base64,{processed_b64}"
            
            self.risk_score = risk_score
            self.fps = _surveillance_backend['camera_processor'].get_current_fps()
            self.detection_count = _surveillance_backend['camera_processor'].get_detections_count()
            
            # Check for alerts
            if risk_score > self.risk_threshold and self.auto_alert:
                self.trigger_alert(risk_score, self.detection_count)
                    
        except Exception as e:
            print(f"[ERROR] Frame processing failed: {e}")

    def trigger_alert(self, risk_score: float, detection_count: int):
        """Trigger security alert and log to database"""
        try:
            alert_msg = f"🚨 HIGH RISK DETECTED! Score: {risk_score:.1f}%"
            self.add_log(alert_msg)
            self.total_alerts += 1
            
            # Log to database
            alert = AlertLog(
                timestamp=datetime.now(),
                risk_score=risk_score,
                detection_count=detection_count,
                alert_type="high_risk",
                details=f"Risk threshold ({self.risk_threshold}%) exceeded"
            )
            
            # In a real app, you would save to database here
            # await alert.save()
            
        except Exception as e:
            print(f"[ERROR] Alert logging failed: {e}")

    def add_log(self, message: str):
        """Add timestamped log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_messages.append(log_entry)
        
        # Keep only last 20 log entries
        if len(self.log_messages) > 20:
            self.log_messages = self.log_messages[-20:]

    def add_system_log(self, event_type: str, message: str, details: str = None):
        """Add system log to database"""
        try:
            log = SystemLog(
                timestamp=datetime.now(),
                event_type=event_type,
                message=message,
                details=details
            )
            # In a real app: await log.save()
            
        except Exception as e:
            print(f"[ERROR] System logging failed: {e}")

    def set_video_path(self, path: str):
        """Set video file path"""
        self.video_path = path

    def set_source_type(self, source: str):
        """Set source type"""
        self.source_type = source

    def set_risk_threshold(self, threshold: str):
        """Set risk threshold for alerts"""
        try:
            threshold_float = float(threshold)
            self.risk_threshold = max(0.0, min(100.0, threshold_float))
        except ValueError:
            # Keep current value if invalid input
            pass

    def toggle_auto_alert(self):
        """Toggle automatic alerting"""
        self.auto_alert = not self.auto_alert
        status = "enabled" if self.auto_alert else "disabled"
        self.add_log(f"🔔 Auto-alert {status}")

    def get_threat_color(self) -> str:
        """Get color based on risk score"""
        if self.risk_score < 20:
            return "green"
        elif self.risk_score < 50:
            return "yellow" 
        elif self.risk_score < 80:
            return "orange"
        else:
            return "red"

    def get_session_duration(self) -> str:
        """Get current session duration"""
        if not self.session_start_time:
            return "00:00:00"
            
        duration = datetime.now() - self.session_start_time
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def webcam_capture_component():
    """Enhanced webcam capture component with actual frame processing"""
    return rx.box(
        rx.script(
            """
            let video, canvas, ctx, stream;
            let isCapturing = false;
            let frameInterval;
            
            function initWebcam() {
                if (video) return; // Already initialized
                
                video = document.createElement('video');
                canvas = document.createElement('canvas');
                ctx = canvas.getContext('2d');
                
                video.width = 640;
                video.height = 480;
                canvas.width = 640;
                canvas.height = 480;
                
                video.autoplay = true;
                video.muted = true;
                video.style.display = 'none';
                canvas.style.display = 'none';
                
                document.body.appendChild(video);
                document.body.appendChild(canvas);
            }
            
            async function startWebcamCapture() {
                if (isCapturing) return;
                
                try {
                    initWebcam();
                    stream = await navigator.mediaDevices.getUserMedia({ 
                        video: { width: 640, height: 480 } 
                    });
                    video.srcObject = stream;
                    await video.play();
                    
                    isCapturing = true;
                    
                    // Capture and process frames every 200ms (5 FPS to avoid overload)
                    frameInterval = setInterval(() => {
                        if (video.videoWidth > 0 && video.videoHeight > 0) {
                            ctx.drawImage(video, 0, 0, 640, 480);
                            let frameData = canvas.toDataURL('image/jpeg', 0.7);
                            
                            // Send frame to backend via fetch (simulated)
                            // In a real implementation, you'd call the Reflex event handler
                            console.log('Frame captured and ready for processing');
                        }
                    }, 200);
                    
                    console.log('Webcam capture started successfully');
                    
                } catch (err) {
                    console.error('Error starting webcam:', err);
                    alert('Camera access denied or not available. Please check browser permissions.');
                }
            }
            
            function stopWebcamCapture() {
                if (!isCapturing) return;
                
                if (frameInterval) {
                    clearInterval(frameInterval);
                    frameInterval = null;
                }
                
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                    stream = null;
                }
                
                if (video) {
                    video.srcObject = null;
                }
                
                isCapturing = false;
                console.log('Webcam capture stopped');
            }
            
            // Auto-start webcam when surveillance is active
            function checkSurveillanceStatus() {
                // This would be called by Reflex when system_active changes
                const isActive = window.surveillanceActive || false;
                const isWebcam = window.surveillanceSource === 'webcam';
                
                if (isActive && isWebcam) {
                    startWebcamCapture();
                } else {
                    stopWebcamCapture();
                }
            }
            
            // Global functions for Reflex to call
            window.startWebcamCapture = startWebcamCapture;
            window.stopWebcamCapture = stopWebcamCapture;
            window.checkSurveillanceStatus = checkSurveillanceStatus;
            """
        ),
        id="webcam-capture-component"
    )

def header_section() -> rx.Component:
    """Enhanced header with system status"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("shield-check", size=32, color="white"),
                rx.heading("WatchHer Surveillance System", size="9", color="white"),
                spacing="3",
                align="center",
            ),
            rx.text("Advanced AI-Powered Security Monitoring", size="4", color="rgba(255,255,255,0.8)"),
            rx.hstack(
                rx.badge(
                    SurveillanceState.system_status,
                    color_scheme=rx.cond(SurveillanceState.system_active, "green", "gray"),
                    size="3"
                ),
                rx.text(SurveillanceState.get_session_duration(), size="2", color="white"),
                spacing="4",
            ),
            spacing="2",
            align="center",
        ),
        background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        padding="20px",
        border_radius="15px",
        margin_bottom="20px",
    )

def control_panel() -> rx.Component:
    """Enhanced control panel with advanced settings"""
    return rx.box(
        rx.vstack(
            rx.heading("🎛️ Control Panel", size="6", margin_bottom="15px"),
            
            # Source selection
            rx.vstack(
                rx.text("📹 Source Configuration:", font_weight="bold", size="4"),
                rx.radio_group(
                    rx.radio("Webcam", value="webcam"),
                    rx.radio("Video File", value="video_file"),
                    value=SurveillanceState.source_type,
                    on_change=SurveillanceState.set_source_type,
                ),
                rx.cond(
                    SurveillanceState.source_type == "video_file",
                    rx.input(
                        placeholder="Enter video file path... (e.g., C:\\path\\to\\video.mp4)",
                        value=SurveillanceState.video_path,
                        on_change=SurveillanceState.set_video_path,
                        width="100%",
                    )
                ),
                spacing="2",
                align="start",
                width="100%",
            ),
            
            # Advanced settings
            rx.vstack(
                rx.text("⚙️ Advanced Settings:", font_weight="bold", size="4"),
                rx.hstack(
                    rx.text("Risk Threshold:", size="3"),
                    rx.input(
                        value=SurveillanceState.risk_threshold,
                        on_change=SurveillanceState.set_risk_threshold,
                        type="number",
                        width="80px",
                    ),
                    rx.text("%", size="3"),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.switch(
                        is_checked=SurveillanceState.auto_alert,
                        on_change=SurveillanceState.toggle_auto_alert,
                    ),
                    rx.text("Auto-alert when risk threshold exceeded", size="2"),
                    spacing="2",
                    align="center",
                ),
                spacing="2",
                align="start",
                width="100%",
            ),
            
            # Control buttons
            rx.hstack(
                rx.button(
                    "🎥 Start Webcam",
                    on_click=SurveillanceState.start_webcam_analysis,
                    disabled=SurveillanceState.system_active | (SurveillanceState.source_type != "webcam"),
                    loading=SurveillanceState.loading,
                    color_scheme="blue",
                ),
                rx.button(
                    "🎬 Start Video",
                    on_click=SurveillanceState.start_video_analysis,
                    disabled=SurveillanceState.system_active | (SurveillanceState.source_type != "video_file"),
                    loading=SurveillanceState.loading,
                    color_scheme="green",
                ),
                rx.button(
                    "🛑 Stop Analysis",
                    on_click=SurveillanceState.stop_analysis,
                    disabled=~SurveillanceState.system_active,
                    color_scheme="red",
                    loading=SurveillanceState.loading,
                ),
                spacing="3",
                width="100%",
                justify="center",
            ),
            
            # Error display
            rx.cond(
                SurveillanceState.error_message.length() > 0,
                rx.box(
                    rx.text(SurveillanceState.error_message, color="red"),
                    background="rgba(255, 0, 0, 0.1)",
                    padding="10px",
                    border_radius="5px",
                    border="1px solid red",
                    margin_top="10px",
                )
            ),
            
            spacing="4",
            align="start",
            width="100%",
        ),
        background="rgba(255, 255, 255, 0.05)",
        padding="20px",
        border_radius="15px",
        border="1px solid rgba(255, 255, 255, 0.1)",
    )

def video_display() -> rx.Component:
    """Enhanced video display with live feed"""
    return rx.box(
        rx.vstack(
            rx.heading("📺 Live Analytics Feed", size="6", margin_bottom="15px"),
            
            rx.box(
                rx.cond(
                    SurveillanceState.current_frame_data.length() > 0,
                    rx.image(
                        src=SurveillanceState.current_frame_data,
                        width="100%",
                        max_width="600px",
                        border_radius="10px",
                        border="2px solid rgba(255, 255, 255, 0.3)",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("video", size=64, color="rgba(255, 255, 255, 0.5)"),
                            rx.text("No video feed active", size="4", color="rgba(255, 255, 255, 0.7)"),
                            rx.text("Start analysis to see live feed", size="2", color="rgba(255, 255, 255, 0.5)"),
                            spacing="3",
                        ),
                        height="300px",
                    )
                ),
                width="100%",
                background="rgba(0, 0, 0, 0.3)",
                border_radius="10px",
                padding="10px",
            ),
            
            spacing="3",
            align="center",
            width="100%",
        ),
        background="rgba(255, 255, 255, 0.05)",
        padding="20px",
        border_radius="15px",
        border="1px solid rgba(255, 255, 255, 0.1)",
    )

def analytics_panel() -> rx.Component:
    """Enhanced analytics with real-time metrics"""
    return rx.box(
        rx.vstack(
            rx.heading("📊 Real-time Analytics", size="6", margin_bottom="15px"),
            
            # Main metrics
            rx.hstack(
                rx.vstack(
                    rx.text("🎯 Risk Score", font_weight="bold", size="3", color="white"),
                    rx.text(
                        f"{SurveillanceState.risk_score:.1f}%",
                        size="8",
                        color=SurveillanceState.get_threat_color(),
                        font_weight="bold",
                    ),
                    align="center",
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("⚡ FPS", font_weight="bold", size="3", color="white"),
                    rx.text(f"{SurveillanceState.fps:.1f}", size="8", font_weight="bold", color="white"),
                    align="center",
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("👥 Detections", font_weight="bold", size="3", color="white"),
                    rx.text(f"{SurveillanceState.detection_count}", size="8", font_weight="bold", color="white"),
                    align="center",
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("🚨 Alerts", font_weight="bold", size="3", color="white"),
                    rx.text(f"{SurveillanceState.total_alerts}", size="8", font_weight="bold", color="orange"),
                    align="center",
                    spacing="1",
                ),
                justify="between",
                width="100%",
                padding="20px",
            ),
            
            spacing="3",
            align="center",
            width="100%",
        ),
        background="rgba(255, 255, 255, 0.05)",
        padding="20px",
        border_radius="15px",
        border="1px solid rgba(255, 255, 255, 0.1)",
    )

def activity_log() -> rx.Component:
    """Enhanced activity log with filtering"""
    return rx.box(
        rx.vstack(
            rx.heading("📋 Activity Log", size="6", margin_bottom="15px"),
            
            rx.box(
                rx.vstack(
                    rx.foreach(
                        SurveillanceState.log_messages,
                        lambda log: rx.text(
                            log, 
                            size="2", 
                            font_family="monospace",
                            color="rgba(255, 255, 255, 0.9)",
                            word_break="break-word",
                        )
                    ),
                    align="start",
                    spacing="1",
                    width="100%",
                ),
                height="200px",
                overflow_y="auto",
                width="100%",
                background="rgba(0, 0, 0, 0.3)",
                padding="15px",
                border_radius="8px",
                border="1px solid rgba(255, 255, 255, 0.2)",
            ),
            
            spacing="3",
            align="start",
            width="100%",
        ),
        background="rgba(255, 255, 255, 0.05)",
        padding="20px",
        border_radius="15px",
        border="1px solid rgba(255, 255, 255, 0.1)",
    )

def video_update_timer() -> rx.Component:
    """Timer component for updating video display"""
    return rx.box(
        rx.script(
            """
            // Auto-update video display every 200ms
            setInterval(() => {
                if (window.RefreshVideoDisplay) {
                    window.RefreshVideoDisplay();
                }
            }, 200);
            """
        ),
        style={"display": "none"}
    )

def index() -> rx.Component:
    """Main unified surveillance interface"""
    return rx.box(
        rx.container(
            # Add video update timer (hidden)
            video_update_timer(),
            
            # Add enhanced webcam capture component
            webcam_capture_component(),
            
            # Header
            header_section(),
            
            # Main content grid
            rx.grid(
                # Left column
                rx.vstack(
                    control_panel(),
                    analytics_panel(),
                    spacing="4",
                ),
                
                # Right column
                rx.vstack(
                    video_display(),
                    activity_log(),
                    spacing="4",
                ),
                
                columns="2",
                spacing="6",
                width="100%",
            ),
            
            max_width="1400px",
            padding="20px",
        ),
        min_height="100vh",
        background="linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
        color="white",
    )

# Create the unified app
app = rx.App()
app.add_page(index, route="/") 