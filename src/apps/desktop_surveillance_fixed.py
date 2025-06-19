#!/usr/bin/env python3
"""
WatchHer Desktop Surveillance Application
Enhanced version with improved AI integration and safety focus
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import time
import threading
from datetime import datetime

# Import core components
from src.core.camera_processor import CameraProcessor

class DesktopSurveillanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 WatchHer Surveillance System - Desktop")
        self.root.geometry("1400x900")  # Larger window for bigger video
        self.root.configure(bg='#2c3e50')
        
        # Initialize basic variables
        self.camera_processor = None
        self.ai_analyzer = None
        self.is_processing = False
        self.video_thread = None
        self.ai_ready = False
        
        # Initialize statistics variables
        self.frame_count = 0
        self.risk_score = 0.0
        self.detection_count = 0
        self.men_count = 0
        self.women_count = 0
        self.pose_count = 0
        self.fps = 0.0
        
        # Create UI FIRST
        self.create_interface()
        
        # Show window immediately
        self.root.update()
        
        # Start AI initialization in background AFTER window is shown
        self.root.after(100, self.start_ai_initialization)
        
        print("[INFO] Desktop window created and shown!")
    
    def create_interface(self):
        """Create professional UI interface"""
        # Configure main window
        self.root.configure(bg='#1a1a1a')
        
        # Create header frame
        header_frame = tk.Frame(self.root, bg='#2d3748', height=70)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Title with icon
        title_label = tk.Label(header_frame, text="🛡️ WatchHer Surveillance System", 
                              font=('Segoe UI', 18, 'bold'), 
                              fg='#ffffff', bg='#2d3748')
        title_label.pack(side='left', padx=20, pady=20)
        
        # Status indicator
        self.status_label = tk.Label(header_frame, text="🔴 SYSTEM READY", 
                                    font=('Segoe UI', 12, 'bold'), 
                                    fg='#48bb78', bg='#2d3748')
        self.status_label.pack(side='right', padx=20, pady=20)
        
        # Main content area
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel for video
        video_frame = tk.LabelFrame(main_frame, text="📹 Live Video Feed", 
                                   font=('Segoe UI', 11, 'bold'),
                                   fg='#ffffff', bg='#2d3748', bd=2)
        video_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Video display with better placeholder
        self.video_label = tk.Label(video_frame, 
                                   text="🎥 WatchHer AI Surveillance System\n\nAdvanced AI-Powered Security Monitoring\n\nClick 'Start Analysis' to begin monitoring",
                                   font=('Segoe UI', 14), 
                                   fg='#a0aec0', bg='#1a1a1a',
                                   width=80, height=25, justify='center')
        self.video_label.pack(padx=10, pady=10, fill='both', expand=True)
        
        # Right panel for controls and stats
        right_panel = tk.Frame(main_frame, bg='#1a1a1a', width=350)
        right_panel.pack(side='right', fill='y', padx=(5, 0))
        right_panel.pack_propagate(False)
        
        self.create_control_panel(right_panel)
        self.create_stats_panel(right_panel)
        
    def create_control_panel(self, parent):
        """Create modern control panel"""
        # Control Panel Frame
        control_frame = tk.LabelFrame(parent, text="🎮 Control Panel", 
                                     font=('Segoe UI', 11, 'bold'),
                                     fg='#ffffff', bg='#2d3748', bd=2)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # AI Status
        ai_frame = tk.Frame(control_frame, bg='#2d3748')
        ai_frame.pack(fill='x', padx=10, pady=5)
        
        self.ai_status_label = tk.Label(ai_frame, text="🤖 AI: Loading...", 
                                       font=('Segoe UI', 10, 'bold'), 
                                       fg='#ffd700', bg='#2d3748')
        self.ai_status_label.pack(anchor='w')
        
        # Video Source Selection
        source_frame = tk.LabelFrame(control_frame, text="Video Source", 
                                    font=('Segoe UI', 9, 'bold'),
                                    fg='#e2e8f0', bg='#4a5568')
        source_frame.pack(fill='x', padx=10, pady=10)
        
        # Webcam option
        webcam_frame = tk.Frame(source_frame, bg='#4a5568')
        webcam_frame.pack(fill='x', padx=5, pady=2)
        
        self.source_var = tk.StringVar(value="webcam")
        webcam_radio = tk.Radiobutton(webcam_frame, text="📷 Live Webcam", 
                                     variable=self.source_var, value="webcam",
                                     font=('Segoe UI', 9), fg='#ffffff', bg='#4a5568', 
                                     selectcolor='#2d3748', activebackground='#4a5568')
        webcam_radio.pack(anchor='w')
        
        # Video file option
        file_frame = tk.Frame(source_frame, bg='#4a5568')
        file_frame.pack(fill='x', padx=5, pady=2)
        
        file_radio = tk.Radiobutton(file_frame, text="📁 Video File", 
                                   variable=self.source_var, value="file",
                                   font=('Segoe UI', 9), fg='#ffffff', bg='#4a5568',
                                   selectcolor='#2d3748', activebackground='#4a5568')
        file_radio.pack(anchor='w')
        
        # File selection
        file_select_frame = tk.Frame(source_frame, bg='#4a5568')
        file_select_frame.pack(fill='x', padx=5, pady=5)
        
        self.file_path = tk.StringVar()
        file_entry = tk.Entry(file_select_frame, textvariable=self.file_path, 
                             font=('Segoe UI', 9), width=25, bg='#1a1a1a', fg='#ffffff')
        file_entry.pack(side='left', padx=(0, 5))
        
        browse_btn = tk.Button(file_select_frame, text="Browse", command=self.browse_file,
                              font=('Segoe UI', 8), bg='#4299e1', fg='#ffffff', 
                              bd=0, padx=10, relief='flat')
        browse_btn.pack(side='right')
        
        # Control buttons
        button_frame = tk.Frame(control_frame, bg='#2d3748')
        button_frame.pack(fill='x', padx=10, pady=15)
        
        # Start button
        self.start_btn = tk.Button(button_frame, text="▶️ Start Analysis", 
                                  command=self.start_analysis,
                                  font=('Segoe UI', 11, 'bold'), bg='#48bb78', fg='#ffffff',
                                  bd=0, padx=20, pady=8, relief='flat')
        self.start_btn.pack(fill='x', pady=(0, 5))
        
        # Stop button
        self.stop_btn = tk.Button(button_frame, text="⏹️ Stop Analysis", 
                                 command=self.stop_analysis,
                                 font=('Segoe UI', 11, 'bold'), bg='#f56565', fg='#ffffff',
                                 bd=0, padx=20, pady=8, relief='flat', state='disabled')
        self.stop_btn.pack(fill='x')
        
    def create_video_panel(self, parent):
        """Create video display panel"""
        video_frame = tk.LabelFrame(parent, text="📺 Live Video Feed", 
                                   font=('Arial', 12, 'bold'), fg='white', bg='#2c3e50')
        video_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create larger video display area
        self.video_label = tk.Label(video_frame, text="No Video Feed\nWaiting for AI initialization...", 
                                   font=('Arial', 16), fg='#7f8c8d', bg='#2c3e50',
                                   width=80, height=30)
        self.video_label.pack(fill='both', expand=True, padx=10, pady=10)
    
    def start_ai_initialization(self):
        """Start AI initialization in background"""
        def ai_init_worker():
            try:
                self.add_log("🤖 Loading AI analyzer...")
                
                # AI initialization with proper imports
                from src.core.ai_analyzer import AIAnalyzer
                self.ai_analyzer = AIAnalyzer()
                
                self.add_log("✅ AI analyzer loaded successfully!")
                
                # Update UI on main thread
                self.root.after(0, self.ai_initialization_complete)
                
            except Exception as e:
                self.add_log(f"❌ AI initialization failed: {e}")
                print(f"[ERROR] AI init failed: {e}")
        
        # Start in background thread
        ai_thread = threading.Thread(target=ai_init_worker, daemon=True)
        ai_thread.start()
    
    def ai_initialization_complete(self):
        """Called when AI initialization is complete"""
        self.ai_ready = True
        self.ai_status_label.config(text="🤖 AI: Ready ✅", fg='#27ae60')
        self.start_btn.config(state='normal')
        self.video_label.config(text="AI Ready!\nClick 'Start Analysis' to begin")
        self.add_log("🎯 System ready for surveillance!")
    
    def start_analysis(self):
        """Start video analysis"""
        if not self.ai_ready:
            messagebox.showwarning("Not Ready", "AI components are still loading. Please wait.")
            return
            
        if self.is_processing:
            return
        
        source = self.source_var.get()
        
        try:
            if source == "webcam":
                self.add_log("📹 Starting webcam analysis...")
                self.start_webcam_capture()
            else:
                video_path = self.file_path.get()
                if not os.path.exists(video_path):
                    messagebox.showerror("Error", f"Video file not found: {video_path}")
                    return
                self.add_log(f"🎬 Starting video file analysis: {os.path.basename(video_path)}")
                self.start_video_processing(video_path)
            
            self.is_processing = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            
        except Exception as e:
            self.add_log(f"❌ Failed to start analysis: {e}")
            messagebox.showerror("Error", f"Failed to start analysis: {e}")
    
    def start_webcam_capture(self):
        """Start webcam capture with full AI analysis"""
        def webcam_worker():
            # Initialize camera processor for full AI capabilities
            processor = CameraProcessor()
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            if not cap.isOpened():
                self.add_log("❌ Failed to open webcam")
                return
            
            self.add_log("📹 Webcam analysis started")
            frame_skip_counter = 0
            
            while self.is_processing:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process every 2nd frame to reduce CPU load and flickering
                frame_skip_counter += 1
                if frame_skip_counter % 2 != 0:
                    continue
                
                # Process frame with AI
                analyzed_frame, detections, risk_score = processor.process_frame(frame)
                
                # Update display and stats
                self.display_frame(analyzed_frame)
                self.update_stats(risk_score, detections)
                self.log_detections(detections, risk_score)
                
                # Add small delay to prevent excessive CPU usage and reduce flicker
                time.sleep(0.03)  # ~30 FPS maximum
            
            cap.release()
            self.add_log("📹 Webcam capture stopped")
        
        self.video_thread = threading.Thread(target=webcam_worker, daemon=True)
        self.video_thread.start()
    
    def start_video_processing(self, video_path):
        """Start video file processing with full AI analysis"""
        def video_worker():
            # Initialize camera processor for video file
            processor = CameraProcessor()
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                self.add_log(f"❌ Failed to open video: {video_path}")
                return
            
            self.add_log(f"🎬 Video processing started: {video_path}")
            frame_skip_counter = 0
            
            while self.is_processing:
                ret, frame = cap.read()
                if not ret:
                    self.add_log("🎬 Video finished")
                    break
                
                # Process every 3rd frame for video files to reduce processing load
                frame_skip_counter += 1
                if frame_skip_counter % 3 != 0:
                    continue
                
                # Process frame with AI
                analyzed_frame, detections, risk_score = processor.process_frame(frame)
                
                # Update display and stats
                self.display_frame(analyzed_frame)
                self.update_stats(risk_score, detections)
                self.log_detections(detections, risk_score)
                
                # Add delay to control playback speed and reduce flicker
                time.sleep(0.05)  # ~20 FPS for video files
            
            cap.release()
            self.add_log("🎬 Video processing stopped")
        
        self.video_thread = threading.Thread(target=video_worker, daemon=True)
        self.video_thread.start()
    
    def log_detections(self, detections, risk_score):
        """Log detailed detection information"""
        try:
            # Count people by gender
            men_count = sum(1 for d in detections if d.get('gender') == 'man')
            women_count = sum(1 for d in detections if d.get('gender') == 'woman')
            unknown_count = sum(1 for d in detections if d.get('gender') == 'unknown')
            
            # Log gender breakdown every 30 frames to avoid spam
            if self.frame_count % 30 == 0:
                gender_info = f"👥 People detected: {len(detections)} (👨 Men: {men_count}, 👩 Women: {women_count}, ❓ Unknown: {unknown_count})"
                self.add_log(gender_info)
                
                # Log risk level
                if risk_score > 70:
                    self.add_log(f"🚨 HIGH RISK detected: {risk_score:.1f}%")
                elif risk_score > 40:
                    self.add_log(f"⚠️ Medium risk: {risk_score:.1f}%")
                else:
                    self.add_log(f"✅ Low risk: {risk_score:.1f}%")
                
                # Log pose/gesture detection
                pose_detections = [d for d in detections if d.get('pose_keypoints')]
                if pose_detections:
                    self.add_log(f"🤸 Pose analysis: {len(pose_detections)} people with pose data")
                    
                    # Check for specific gestures
                    for detection in pose_detections:
                        if 'gesture' in detection:
                            gesture = detection['gesture']
                            self.add_log(f"✋ Gesture detected: {gesture}")
                        
                        if 'pose_analysis' in detection:
                            pose_info = detection['pose_analysis']
                            if 'hands_up' in pose_info and pose_info['hands_up']:
                                self.add_log("🙋 Hands raised detected!")
                            if 'unusual_posture' in pose_info and pose_info['unusual_posture']:
                                self.add_log("⚠️ Unusual posture detected!")
                                
        except Exception as e:
            print(f"[ERROR] Detection logging failed: {e}")
    
    def display_frame(self, frame):
        """Display frame in GUI with anti-flicker optimization"""
        try:
            # Make video much larger - resize to fit the available space better
            display_frame = cv2.resize(frame, (800, 600))  # Much bigger size
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Store photo reference to prevent garbage collection
            if hasattr(self, '_current_photo'):
                del self._current_photo
            self._current_photo = photo
            
            # Update display with minimal delay to prevent flickering
            self.root.after_idle(self._update_video_display, photo)
            
        except Exception as e:
            print(f"Display error: {e}")
    
    def _update_video_display(self, photo):
        """Update video display with flicker prevention"""
        try:
            self.video_label.config(image=photo, text="")
            self.video_label.image = photo
        except Exception as e:
            print(f"Video display update error: {e}")
    
    def update_stats(self, risk_score, detections):
        """Update statistics with detailed detection info"""
        self.frame_count += 1
        self.risk_score = risk_score
        
        # Count different types of detections
        if isinstance(detections, list):
            self.detection_count = len(detections)
            # Count by gender
            self.men_count = sum(1 for d in detections if d.get('gender') == 'man')
            self.women_count = sum(1 for d in detections if d.get('gender') == 'woman')
            # Count poses
            self.pose_count = sum(1 for d in detections if d.get('pose_keypoints'))
        else:
            self.detection_count = detections if isinstance(detections, int) else 0
            self.men_count = 0
            self.women_count = 0
            self.pose_count = 0
        
        # Calculate FPS
        current_time = time.time()
        if not hasattr(self, 'fps_start_time'):
            self.fps_start_time = current_time
            self.fps_frame_count = 0
        
        self.fps_frame_count += 1
        elapsed = current_time - self.fps_start_time
        if elapsed > 1.0:
            self.fps = self.fps_frame_count / elapsed
            self.fps_start_time = current_time
            self.fps_frame_count = 0
        
        # Update display
        self.root.after(0, self._update_stats_display)
    
    def _update_stats_display(self):
        """Update stats display with detailed info"""
        # Color-code risk
        if self.risk_score < 30:
            risk_color = '#48bb78'  # Green
        elif self.risk_score < 60:
            risk_color = '#ffd700'  # Yellow
        else:
            risk_color = '#f56565'  # Red
        
        self.risk_label.config(text=f"{self.risk_score:.1f}%", fg=risk_color)
        self.fps_label.config(text=f"{self.fps:.1f}")
        self.people_label.config(text=f"{self.detection_count}")
        
        # Show gender breakdown
        if hasattr(self, 'men_count') and hasattr(self, 'women_count'):
            self.gender_label.config(text=f"{self.men_count}M|{self.women_count}F")
        
        # Show pose detection count
        if hasattr(self, 'pose_count'):
            self.poses_label.config(text=f"{self.pose_count}")
        
        self.frames_label.config(text=f"{self.frame_count}")
    
    def stop_analysis(self):
        """Stop analysis"""
        self.is_processing = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.video_label.config(image='', text="Analysis Stopped\nClick 'Start Analysis' to resume")
        self.video_label.image = None
        self.add_log("🛑 Analysis stopped")
    
    def browse_file(self):
        """Browse for video file"""
        filename = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.file_path.set(filename)
    
    def add_log(self, message):
        """Add log message"""
        def update_log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
        
        self.root.after(0, update_log)

    def create_stats_panel(self, parent):
        """Create modern statistics panel"""
        # Statistics Panel
        stats_frame = tk.LabelFrame(parent, text="📊 Live Statistics", 
                                   font=('Segoe UI', 11, 'bold'),
                                   fg='#ffffff', bg='#2d3748', bd=2)
        stats_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Risk Level Display
        risk_frame = tk.Frame(stats_frame, bg='#2d3748')
        risk_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(risk_frame, text="🚨 Risk Score:", 
                font=('Segoe UI', 10, 'bold'), fg='#ffffff', bg='#2d3748').pack(anchor='w')
        self.risk_label = tk.Label(risk_frame, text="0.0%", 
                                  font=('Segoe UI', 14, 'bold'), fg='#48bb78', bg='#2d3748')
        self.risk_label.pack(anchor='w')
        
        # Performance Stats
        perf_frame = tk.Frame(stats_frame, bg='#2d3748')
        perf_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(perf_frame, text="⚡ FPS:", 
                font=('Segoe UI', 10), fg='#e2e8f0', bg='#2d3748').pack(anchor='w')
        self.fps_label = tk.Label(perf_frame, text="0.0", 
                                 font=('Segoe UI', 11, 'bold'), fg='#4299e1', bg='#2d3748')
        self.fps_label.pack(anchor='w')
        
        # Detection Stats
        detection_frame = tk.Frame(stats_frame, bg='#2d3748')
        detection_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(detection_frame, text="👥 People:", 
                font=('Segoe UI', 10), fg='#e2e8f0', bg='#2d3748').pack(anchor='w')
        self.people_label = tk.Label(detection_frame, text="0", 
                                    font=('Segoe UI', 11, 'bold'), fg='#ed8936', bg='#2d3748')
        self.people_label.pack(anchor='w')
        
        # Gender breakdown
        gender_frame = tk.Frame(stats_frame, bg='#2d3748')
        gender_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(gender_frame, text="🚺 Gender:", 
                font=('Segoe UI', 10), fg='#e2e8f0', bg='#2d3748').pack(anchor='w')
        self.gender_label = tk.Label(gender_frame, text="0M|0F", 
                                    font=('Segoe UI', 11, 'bold'), fg='#9f7aea', bg='#2d3748')
        self.gender_label.pack(anchor='w')
        
        # Threat level
        threat_frame = tk.Frame(stats_frame, bg='#2d3748')
        threat_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(threat_frame, text="⚠️ Poses:", 
                font=('Segoe UI', 10), fg='#e2e8f0', bg='#2d3748').pack(anchor='w')
        self.poses_label = tk.Label(threat_frame, text="0", 
                                   font=('Segoe UI', 11, 'bold'), fg='#38b2ac', bg='#2d3748')
        self.poses_label.pack(anchor='w')
        
        # Frame count
        frame_frame = tk.Frame(stats_frame, bg='#2d3748')
        frame_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(frame_frame, text="🎬 Frames:", 
                font=('Segoe UI', 10), fg='#e2e8f0', bg='#2d3748').pack(anchor='w')
        self.frames_label = tk.Label(frame_frame, text="0", 
                                    font=('Segoe UI', 11, 'bold'), fg='#68d391', bg='#2d3748')
        self.frames_label.pack(anchor='w')
        
        # Activity Log
        log_frame = tk.LabelFrame(stats_frame, text="📝 Activity Log", 
                                 font=('Segoe UI', 9, 'bold'),
                                 fg='#e2e8f0', bg='#4a5568')
        log_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create scrollable text widget
        log_scroll_frame = tk.Frame(log_frame, bg='#4a5568')
        log_scroll_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(log_scroll_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.log_text = tk.Text(log_scroll_frame, height=8, width=25,
                               font=('Consolas', 8), bg='#1a1a1a', fg='#e2e8f0',
                               yscrollcommand=scrollbar.set, wrap='word')
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # Add initial log entries
        self.add_log("✅ WatchHer System Initialized")
        self.add_log("🔄 Loading AI components...")

    def cleanup(self):
        """Cleanup resources before closing"""
        try:
            self.is_processing = False
            
            # Wait for video thread to finish
            if self.video_thread and self.video_thread.is_alive():
                self.video_thread.join(timeout=2.0)
            
            # Clear photo references
            if hasattr(self, '_current_photo'):
                del self._current_photo
            
            self.add_log("🧹 Cleanup completed")
        except Exception as e:
            print(f"Cleanup error: {e}")

    def on_closing(self):
        """Handle window closing"""
        self.cleanup()
        self.root.destroy()

def main():
    """Main function with proper error handling"""
    print("🚀 Starting WatchHer Desktop Surveillance...")
    
    try:
        root = tk.Tk()
        app = DesktopSurveillanceApp(root)
        
        # Handle window closing properly
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        print("[INFO] Desktop window created and shown!")
        print("✅ Window created, starting GUI...")
        
        # Start the application
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Application error: {e}")
        messagebox.showerror("Application Error", f"Failed to start application: {e}")
    finally:
        print("👋 Desktop app closed")

if __name__ == "__main__":
    main()