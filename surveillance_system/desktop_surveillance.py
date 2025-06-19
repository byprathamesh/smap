#!/usr/bin/env python3
"""
WatchHer Desktop Surveillance Application
Better video display with desktop window support
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

# Import our surveillance modules
from camera_processor import CameraProcessor
from ai_analyzer import AIAnalyzer

class DesktopSurveillanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 WatchHer Surveillance System - Desktop")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')
        
        # Initialize components
        self.camera_processor = None
        self.ai_analyzer = None
        self.is_processing = False
        self.video_thread = None
        self.current_frame = None
        
        # Stats
        self.frame_count = 0
        self.risk_score = 0.0
        self.detection_count = 0
        self.fps = 0.0
        
        # Create UI
        self.create_interface()
        
        # Initialize AI components
        self.initialize_ai()
    
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
        
        # Right panel - Video and stats
        right_frame = tk.Frame(main_frame, bg='#2c3e50')
        right_frame.pack(side='right', fill='both', expand=True)
        
        self.create_video_panel(right_frame)
        
    def create_control_panel(self, parent):
        """Create control panel"""
        # Title
        control_title = tk.Label(parent, text="🎛️ Control Panel", 
                                font=('Arial', 14, 'bold'), fg='white', bg='#34495e')
        control_title.pack(pady=10)
        
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
                                  font=('Arial', 10, 'bold'), height=2)
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
        
        self.detection_label = tk.Label(stats_frame, text="👥 Detections: 0", 
                                       font=('Arial', 9), fg='white', bg='#34495e')
        self.detection_label.pack(anchor='w', padx=5, pady=2)
        
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
        
        log_scroll = tk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scroll.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=log_scroll.set)
        
    def create_video_panel(self, parent):
        """Create video display panel"""
        # Video display
        video_frame = tk.LabelFrame(parent, text="📺 Live Video Feed", 
                                   font=('Arial', 12, 'bold'), fg='white', bg='#2c3e50')
        video_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.video_label = tk.Label(video_frame, text="No Video Feed\nClick 'Start Analysis' to begin", 
                                   font=('Arial', 14), fg='#7f8c8d', bg='#2c3e50',
                                   width=50, height=20)
        self.video_label.pack(expand=True, padx=10, pady=10)
        
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
    
    def initialize_ai(self):
        """Initialize AI components"""
        def init_worker():
            try:
                self.add_log("🤖 Initializing AI components...")
                self.ai_analyzer = AIAnalyzer()
                self.add_log("✅ AI components ready!")
            except Exception as e:
                self.add_log(f"❌ AI initialization failed: {e}")
        
        # Initialize in background
        init_thread = threading.Thread(target=init_worker, daemon=True)
        init_thread.start()
    
    def start_analysis(self):
        """Start video analysis"""
        if self.is_processing:
            return
            
        source = self.source_var.get()
        
        try:
            if source == "webcam":
                # Initialize webcam
                self.camera_processor = CameraProcessor(source=None)
                self.add_log("✅ Webcam analysis started")
                
                # Start webcam capture
                self.start_webcam_capture()
                
            else:  # video file
                video_path = self.file_path.get()
                if not os.path.exists(video_path):
                    messagebox.showerror("Error", f"Video file not found: {video_path}")
                    return
                
                self.camera_processor = CameraProcessor(source=video_path)
                self.add_log(f"✅ Video file analysis started: {os.path.basename(video_path)}")
                
                # Start video processing
                self.start_video_processing()
            
            self.is_processing = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            
        except Exception as e:
            self.add_log(f"❌ Failed to start analysis: {e}")
            messagebox.showerror("Error", f"Failed to start analysis: {e}")
    
    def start_webcam_capture(self):
        """Start webcam capture"""
        def webcam_worker():
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            while self.is_processing:
                ret, frame = cap.read()
                if ret:
                    # Process frame
                    if self.camera_processor:
                        processed_frame, risk_score = self.camera_processor.process_frame_from_numpy(frame)
                        self.update_stats(risk_score)
                        self.display_frame(processed_frame)
                    
                time.sleep(0.033)  # ~30 FPS
            
            cap.release()
        
        self.video_thread = threading.Thread(target=webcam_worker, daemon=True)
        self.video_thread.start()
    
    def start_video_processing(self):
        """Start video file processing"""
        def video_worker():
            while self.is_processing:
                if self.camera_processor:
                    frame_bytes, risk_score = self.camera_processor.get_frame_for_video_file()
                    
                    if frame_bytes:
                        # Convert bytes back to frame for display
                        nparr = np.frombuffer(frame_bytes, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        self.update_stats(risk_score)
                        self.display_frame(frame)
                
                time.sleep(0.033)  # ~30 FPS
        
        self.video_thread = threading.Thread(target=video_worker, daemon=True)
        self.video_thread.start()
    
    def display_frame(self, frame):
        """Display frame in the GUI"""
        if frame is None:
            return
            
        try:
            # Resize frame for display
            display_frame = cv2.resize(frame, (640, 480))
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_frame)
            
            # Convert to Tkinter PhotoImage
            photo = ImageTk.PhotoImage(pil_image)
            
            # Update display (thread-safe)
            self.root.after(0, self._update_video_display, photo)
            
        except Exception as e:
            print(f"Display error: {e}")
    
    def _update_video_display(self, photo):
        """Update video display (main thread)"""
        self.video_label.config(image=photo, text="")
        self.video_label.image = photo  # Keep a reference
    
    def update_stats(self, risk_score):
        """Update statistics"""
        self.frame_count += 1
        self.risk_score = risk_score
        
        if self.camera_processor:
            self.fps = self.camera_processor.get_current_fps()
            self.detection_count = self.camera_processor.get_detections_count()
        
        # Update labels (thread-safe)
        self.root.after(0, self._update_stats_display)
    
    def _update_stats_display(self):
        """Update statistics display (main thread)"""
        # Color-code risk score
        if self.risk_score < 30:
            risk_color = '#27ae60'  # Green
        elif self.risk_score < 60:
            risk_color = '#f39c12'  # Orange
        else:
            risk_color = '#e74c3c'  # Red
        
        self.risk_label.config(text=f"🎯 Risk Score: {self.risk_score:.1f}%", fg=risk_color)
        self.fps_label.config(text=f"⚡ FPS: {self.fps:.1f}")
        self.detection_label.config(text=f"👥 Detections: {self.detection_count}")
        self.frame_label.config(text=f"📸 Frames: {self.frame_count}")
    
    def stop_analysis(self):
        """Stop video analysis"""
        self.is_processing = False
        
        if self.camera_processor:
            self.camera_processor.stop()
            self.camera_processor = None
        
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        
        self.video_label.config(image='', text="Analysis Stopped\nClick 'Start Analysis' to resume")
        self.video_label.image = None
        
        self.add_log("🛑 Analysis stopped")
    
    def add_log(self, message):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Thread-safe log update
        self.root.after(0, self._update_log, log_entry)
    
    def _update_log(self, message):
        """Update log display (main thread)"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_processing:
            self.stop_analysis()
        self.root.destroy()

def main():
    """Main function"""
    root = tk.Tk()
    app = DesktopSurveillanceApp(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main() 