#!/usr/bin/env python3
"""
Simple Desktop Test - Basic GUI First
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time

class SimpleDesktopTest:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 WatchHer Desktop Test")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        # Create simple interface
        self.create_simple_interface()
        
        print("[INFO] Desktop window created successfully!")
    
    def create_simple_interface(self):
        """Create a simple test interface"""
        # Title
        title_label = tk.Label(self.root, text="🔍 Desktop Surveillance Test", 
                              font=('Arial', 20, 'bold'), fg='white', bg='#2c3e50')
        title_label.pack(pady=20)
        
        # Status
        self.status_label = tk.Label(self.root, text="✅ Desktop window working!", 
                                    font=('Arial', 14), fg='#27ae60', bg='#2c3e50')
        self.status_label.pack(pady=10)
        
        # Test button
        test_btn = tk.Button(self.root, text="🧪 Test AI Components", 
                            command=self.test_ai, bg='#3498db', fg='white',
                            font=('Arial', 12, 'bold'), height=2)
        test_btn.pack(pady=20)
        
        # Status text
        self.status_text = tk.Text(self.root, height=15, width=80, 
                                  bg='#34495e', fg='white', font=('Consolas', 9))
        self.status_text.pack(pady=20, padx=20, fill='both', expand=True)
        
        self.add_status("🚀 Desktop app started successfully!")
        self.add_status("✅ GUI is working properly")
        self.add_status("Ready to test AI components...")
    
    def test_ai(self):
        """Test AI components in background"""
        def ai_test_worker():
            try:
                self.add_status("🤖 Testing AI imports...")
                
                # Test imports one by one
                self.add_status("📦 Importing camera processor...")
                from camera_processor import CameraProcessor
                self.add_status("✅ CameraProcessor imported")
                
                self.add_status("📦 Importing AI analyzer...")
                from ai_analyzer import AIAnalyzer
                self.add_status("✅ AIAnalyzer imported")
                
                self.add_status("🔧 Initializing AI components...")
                ai_analyzer = AIAnalyzer()
                self.add_status("✅ AI components initialized successfully!")
                
                self.add_status("🎯 AI test completed - everything working!")
                
            except Exception as e:
                self.add_status(f"❌ AI test failed: {e}")
                print(f"[ERROR] AI test failed: {e}")
        
        # Run in background thread
        test_thread = threading.Thread(target=ai_test_worker, daemon=True)
        test_thread.start()
        
        self.add_status("🔄 Running AI test in background...")
    
    def add_status(self, message):
        """Add status message"""
        def update_text():
            timestamp = time.strftime("%H:%M:%S")
            status_msg = f"[{timestamp}] {message}\n"
            self.status_text.insert(tk.END, status_msg)
            self.status_text.see(tk.END)
        
        # Thread-safe update
        self.root.after(0, update_text)

def main():
    """Main function"""
    print("[INFO] Starting simple desktop test...")
    
    root = tk.Tk()
    app = SimpleDesktopTest(root)
    
    print("[INFO] Starting GUI loop...")
    root.mainloop()
    print("[INFO] GUI closed")

if __name__ == "__main__":
    main() 