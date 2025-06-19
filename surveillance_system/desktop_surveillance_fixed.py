#!/usr/bin/env python3
"""
Fixed Desktop Surveillance App
GUI first, AI components loaded after window is shown
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
from datetime import datetime
import os

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
        
        # Stats
        self.frame_count = 0
        self.risk_score = 0.0
        self.detection_count = 0
        self.fps = 0.0
        
        # Create UI FIRST
        self.create_interface()
        
        # Show window immediately
        self.root.update()
        
        # Start AI initialization in background AFTER window is shown
        self.root.after(100, self.start_ai_initialization)
        
        print("[INFO] Desktop window created and shown!")
    
    def create_interface(self):
        """Create the main interface"""
        # Title
        title_frame = tk.Frame(self.root, bg='#2c3e50')
        title_frame.pack(fill='x', padx=10, pady=5)
        
        title_label = tk.Label(title_frame, text="🔍 WatchHer Surveillance System", 
                              font=('Arial', 20, 'bold'), fg='white', bg='#2c3e50')
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame, text="Advanced AI-Powered Security Monitoring", 
                                 font=('Arial', 12), fg='#bdc3c7', bg='#2c3e50')
        subtitle_label.pack()
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left panel - Controls
        left_frame = tk.Frame(main_frame, bg='#34495e', relief='raised', bd=2)
        left_frame.pack(side='left', fill='y', padx=(0, 5))
        
        self.create_control_panel(left_frame)
        
        # Right panel - Video
        right_frame = tk.Frame(main_frame, bg='#2c3e50')
        right_frame.pack(side='right', fill='both', expand=True)
        
        self.create_video_panel(right_frame)
        
    def create_control_panel(self, parent):
        """Create control panel"""
        # Title
        control_title = tk.Label(parent, text="🎛️ Control Panel", 
                                font=('Arial', 14, 'bold'), fg='white', bg='#34495e')
        control_title.pack(pady=10)
        
        # AI Status
        self.ai_status_label = tk.Label(parent, text="🤖 AI: Loading...", 
                                       font=('Arial', 10, 'bold'), fg='#f39c12', bg='#34495e')
        self.ai_status_label.pack(pady=5)
        
        # Source selection
        source_frame = tk.LabelFrame(parent, text="📹 Video Source", 
                                    font=('Arial', 10, 'bold'), fg='white', bg='#34495e')
        source_frame.pack(fill='x', padx=10, pady=5)
        
        self.source_var = tk.StringVar(value="webcam")
        
        webcam_radio = tk.Radiobutton(source_frame, text="Webcam", variable=self.source_var, 
                                     value="webcam", fg='white', bg='#34495e', 
                                     selectcolor='#3498db', font=('Arial', 9))
        webcam_radio.pack(anchor='w', padx=5, pady=2)
        
        video_radio = tk.Radiobutton(source_frame, text="Video File", variable=self.source_var, 
                                    value="video", fg='white', bg='#34495e', 
                                    selectcolor='#3498db', font=('Arial', 9))
        video_radio.pack(anchor='w', padx=5, pady=2)
        
        # File selection
        file_frame = tk.Frame(source_frame, bg='#34495e')
        file_frame.pack(fill='x', padx=5, pady=5)
        
        self.file_path = tk.StringVar(value=r"C:\Users\prath\Downloads\delhigully.webm")
        file_entry = tk.Entry(file_frame, textvariable=self.file_path, font=('Arial', 8))
        file_entry.pack(side='left', fill='x', expand=True)
        
        browse_btn = tk.Button(file_frame, text="Browse", command=self.browse_file,
                              bg='#3498db', fg='white', font=('Arial', 8))
        browse_btn.pack(side='right', padx=(5, 0))
        
        # Control buttons
        button_frame = tk.Frame(parent, bg='#34495e')
        button_frame.pack(fill='x', padx=10, pady=10)
        
        self.start_btn = tk.Button(button_frame, text="▶️ Start Analysis", 
                                  command=self.start_analysis, bg='#27ae60', fg='white',
                                  font=('Arial', 10, 'bold'), height=2, state='disabled')
        self.start_btn.pack(fill='x', pady=2)
        
        self.stop_btn = tk.Button(button_frame, text="⏹️ Stop Analysis", 
                                 command=self.stop_analysis, bg='#e74c3c', fg='white',
                                 font=('Arial', 10, 'bold'), height=2, state='disabled')
        self.stop_btn.pack(fill='x', pady=2)
        
        # Statistics
        stats_frame = tk.LabelFrame(parent, text="📊 Live Statistics", 
                                   font=('Arial', 10, 'bold'), fg='white', bg='#34495e')
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        self.risk_label = tk.Label(stats_frame, text="🎯 Risk Score: 0.0%", 
                                  font=('Arial', 9, 'bold'), fg='#e74c3c', bg='#34495e')
        self.risk_label.pack(anchor='w', padx=5, pady=2)
        
        self.fps_label = tk.Label(stats_frame, text="⚡ FPS: 0.0", 
                                 font=('Arial', 9), fg='white', bg='#34495e')
        self.fps_label.pack(anchor='w', padx=5, pady=2)
        
        self.detection_label = tk.Label(stats_frame, text="👥 People: 0", 
                                       font=('Arial', 9), fg='white', bg='#34495e')
        self.detection_label.pack(anchor='w', padx=5, pady=2)
        
        self.gender_label = tk.Label(stats_frame, text="👨👩 Gender: 0M/0F", 
                                    font=('Arial', 9), fg='white', bg='#34495e')
        self.gender_label.pack(anchor='w', padx=5, pady=2)
        
        self.pose_label = tk.Label(stats_frame, text="🤸 Poses: 0", 
                                  font=('Arial', 9), fg='white', bg='#34495e')
        self.pose_label.pack(anchor='w', padx=5, pady=2)
        
        self.frame_label = tk.Label(stats_frame, text="📸 Frames: 0", 
                                   font=('Arial', 9), fg='white', bg='#34495e')
        self.frame_label.pack(anchor='w', padx=5, pady=2)
        
        # Activity log
        log_frame = tk.LabelFrame(parent, text="📋 Activity Log", 
                                 font=('Arial', 10, 'bold'), fg='white', bg='#34495e')
        log_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.log_text = tk.Text(log_frame, height=8, bg='#2c3e50', fg='#ecf0f1', 
                               font=('Consolas', 8), wrap='word')
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Add initial log
        self.add_log("✅ Desktop surveillance app started")
        self.add_log("🔄 Initializing AI components...")
        
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
                
                # Import and initialize AI
                from ai_analyzer import AIAnalyzer
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
            from camera_processor import CameraProcessor
            camera_proc = CameraProcessor(source=None)  # None = webcam mode
            
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            while self.is_processing:
                ret, frame = cap.read()
                if ret and camera_proc:
                    # Use full camera processor with complete AI analysis
                    processed_frame, risk_score = camera_proc.process_frame_from_numpy(frame)
                    
                    # Get detailed detection info
                    detections = camera_proc.last_detections if hasattr(camera_proc, 'last_detections') else []
                    
                    # Update display with full processed frame
                    self.display_frame(processed_frame)
                    self.update_stats(risk_score, detections)
                    
                    # Log detailed detection info
                    if detections:
                        self.log_detections(detections, risk_score)
                
                time.sleep(0.033)  # ~30 FPS
            
            cap.release()
        
        self.video_thread = threading.Thread(target=webcam_worker, daemon=True)
        self.video_thread.start()
    
    def start_video_processing(self, video_path):
        """Start video file processing with full AI analysis"""
        def video_worker():
            # Initialize camera processor for video file
            from camera_processor import CameraProcessor
            camera_proc = CameraProcessor(source=video_path)
            
            while self.is_processing:
                # Get processed frame from camera processor
                frame_bytes, risk_score = camera_proc.get_frame_for_video_file()
                
                if frame_bytes:
                    # Convert bytes back to frame for display
                    import numpy as np
                    nparr = np.frombuffer(frame_bytes, np.uint8)
                    processed_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    # Get detection details
                    detections = camera_proc.last_detections if hasattr(camera_proc, 'last_detections') else []
                    
                    # Update display
                    self.display_frame(processed_frame)
                    self.update_stats(risk_score, detections)
                    
                    # Log detailed detection info
                    if detections:
                        self.log_detections(detections, risk_score)
                
                time.sleep(0.033)  # ~30 FPS
        
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
        """Display frame in GUI"""
        try:
            # Make video much larger - resize to fit the available space better
            display_frame = cv2.resize(frame, (800, 600))  # Much bigger size
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Update display
            self.root.after(0, self._update_video_display, photo)
            
        except Exception as e:
            print(f"Display error: {e}")
    
    def _update_video_display(self, photo):
        """Update video display"""
        self.video_label.config(image=photo, text="")
        self.video_label.image = photo
    
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
            risk_color = '#27ae60'
        elif self.risk_score < 60:
            risk_color = '#f39c12'
        else:
            risk_color = '#e74c3c'
        
        self.risk_label.config(text=f"🎯 Risk Score: {self.risk_score:.1f}%", fg=risk_color)
        self.fps_label.config(text=f"⚡ FPS: {self.fps:.1f}")
        self.detection_label.config(text=f"👥 People: {self.detection_count}")
        
        # Show gender breakdown
        if hasattr(self, 'men_count') and hasattr(self, 'women_count'):
            self.gender_label.config(text=f"👨👩 Gender: {self.men_count}M/{self.women_count}F")
        
        # Show pose detection count
        if hasattr(self, 'pose_count'):
            self.pose_label.config(text=f"🤸 Poses: {self.pose_count}")
        
        self.frame_label.config(text=f"📸 Frames: {self.frame_count}")
    
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

def main():
    """Main function"""
    print("🚀 Starting Desktop Surveillance App...")
    
    root = tk.Tk()
    app = DesktopSurveillanceApp(root)
    
    print("✅ Window created, starting GUI...")
    root.mainloop()
    print("👋 Desktop app closed")

if __name__ == "__main__":
    main() 