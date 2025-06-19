"""
Simplified WatchHer Surveillance System - Working Video Processing
"""

import reflex as rx
import cv2
import numpy as np
import base64
import time
import os
from datetime import datetime
from typing import List, Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from camera_processor import CameraProcessor
from ai_analyzer import AIAnalyzer

# Global instances
_processor = None
_analyzer = None

class SimpleSurveillanceState(rx.State):
    """Simplified surveillance state"""
    
    # System status
    system_active: bool = False
    current_frame_data: str = ""
    risk_score: float = 0.0
    detection_count: int = 0
    system_status: str = "Inactive"
    
    # Configuration
    video_path: str = r"C:\Users\prath\Downloads\delhigully.webm"
    
    # UI state
    loading: bool = False
    error_message: str = ""
    log_messages: List[str] = []

    def start_video_analysis(self):
        """Start video analysis"""
        global _processor, _analyzer
        
        self.loading = True
        self.error_message = ""
        
        try:
            # Check file exists
            if not os.path.exists(self.video_path):
                self.error_message = f"File not found: {self.video_path}"
                self.loading = False
                return
            
            # Initialize components
            if _analyzer is None:
                _analyzer = AIAnalyzer()
                self.add_log("✅ AI Analyzer initialized")
            
            if _processor is not None:
                _processor.stop()
            
            _processor = CameraProcessor(source=self.video_path)
            
            self.system_active = True
            self.system_status = "Active - Video Processing"
            self.loading = False
            self.add_log("✅ Video analysis started")
            
            # Process first frame immediately
            self.process_next_frame()
            
        except Exception as e:
            self.error_message = f"Error: {str(e)}"
            self.add_log(f"❌ Error: {str(e)}")
            self.loading = False

    def process_next_frame(self):
        """Process the next video frame"""
        global _processor
        
        if not self.system_active or _processor is None:
            return
            
        try:
            frame_bytes, risk_score = _processor.get_frame_for_video_file()
            
            if frame_bytes and len(frame_bytes) > 0:
                # Convert to base64 for display
                frame_b64 = base64.b64encode(frame_bytes).decode('utf-8')
                self.current_frame_data = f"data:image/jpeg;base64,{frame_b64}"
                self.risk_score = risk_score
                self.detection_count = _processor.get_detections_count()
                
                self.add_log(f"Frame processed - Risk: {risk_score:.1f}%")
            else:
                self.add_log("No frame data received")
                
        except Exception as e:
            self.add_log(f"❌ Frame processing error: {str(e)}")

    def stop_analysis(self):
        """Stop analysis"""
        global _processor
        
        try:
            if _processor:
                _processor.stop()
                _processor = None
            
            self.system_active = False
            self.system_status = "Inactive"
            self.current_frame_data = ""
            self.risk_score = 0.0
            self.detection_count = 0
            self.add_log("🛑 Analysis stopped")
            
        except Exception as e:
            self.error_message = f"Stop error: {str(e)}"

    def add_log(self, message: str):
        """Add log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_messages.append(log_entry)
        
        # Keep last 15 entries
        if len(self.log_messages) > 15:
            self.log_messages = self.log_messages[-15:]

def simple_index() -> rx.Component:
    """Simple surveillance interface"""
    return rx.container(
        rx.vstack(
            # Header
            rx.heading("🔍 WatchHer Surveillance - Simple Test", size="8", color="white"),
            rx.text("Video Processing Test", size="4", color="rgba(255,255,255,0.8)"),
            
            rx.badge(
                SimpleSurveillanceState.system_status,
                color_scheme=rx.cond(SimpleSurveillanceState.system_active, "green", "gray"),
                size="3"
            ),
            
            # Controls
            rx.hstack(
                rx.button(
                    "▶️ Start Video",
                    on_click=SimpleSurveillanceState.start_video_analysis,
                    disabled=SimpleSurveillanceState.system_active,
                    loading=SimpleSurveillanceState.loading,
                    color_scheme="green",
                    size="3"
                ),
                rx.button(
                    "⏸️ Next Frame",
                    on_click=SimpleSurveillanceState.process_next_frame,
                    disabled=~SimpleSurveillanceState.system_active,
                    color_scheme="blue",
                    size="3"
                ),
                rx.button(
                    "⏹️ Stop",
                    on_click=SimpleSurveillanceState.stop_analysis,
                    disabled=~SimpleSurveillanceState.system_active,
                    color_scheme="red",
                    size="3"
                ),
                spacing="3"
            ),
            
            # Error display
            rx.cond(
                SimpleSurveillanceState.error_message.length() > 0,
                rx.box(
                    rx.text(SimpleSurveillanceState.error_message, color="red"),
                    background="rgba(255, 0, 0, 0.1)",
                    padding="10px",
                    border_radius="5px",
                    border="1px solid red",
                )
            ),
            
            # Video display
            rx.box(
                rx.cond(
                    SimpleSurveillanceState.current_frame_data.length() > 0,
                    rx.image(
                        src=SimpleSurveillanceState.current_frame_data,
                        width="600px",
                        height="400px",
                        border_radius="10px",
                        border="2px solid white",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("video", size=64, color="rgba(255, 255, 255, 0.5)"),
                            rx.text("No video feed", size="4", color="white"),
                            spacing="3",
                        ),
                        height="400px",
                        width="600px",
                        border="2px dashed white",
                        border_radius="10px",
                    )
                ),
                margin="20px",
            ),
            
            # Analytics
            rx.hstack(
                rx.text(f"Risk Score: {SimpleSurveillanceState.risk_score:.1f}%", 
                       size="4", color="white", font_weight="bold"),
                rx.text(f"Detections: {SimpleSurveillanceState.detection_count}", 
                       size="4", color="white", font_weight="bold"),
                spacing="4"
            ),
            
            # Activity log
            rx.box(
                rx.vstack(
                    rx.text("Activity Log:", font_weight="bold", size="4", color="white"),
                    rx.box(
                        rx.vstack(
                            rx.foreach(
                                SimpleSurveillanceState.log_messages,
                                lambda log: rx.text(log, size="2", font_family="monospace", color="white")
                            ),
                            align="start",
                            spacing="1",
                        ),
                        height="150px",
                        overflow_y="auto",
                        background="rgba(0, 0, 0, 0.3)",
                        padding="10px",
                        border_radius="5px",
                        width="100%"
                    ),
                    spacing="2",
                    align="start",
                    width="100%"
                ),
                width="100%",
                margin_top="20px"
            ),
            
            spacing="4",
            align="center",
            width="100%",
        ),
        max_width="800px",
        padding="20px",
        min_height="100vh",
        background="linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
        color="white",
    )

# Create simple app
simple_app = rx.App()
simple_app.add_page(simple_index, route="/simple") 