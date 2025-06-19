# 🔍 WatchHer Surveillance System - Unified Reflex Application

## 🌟 Overview

The WatchHer Surveillance System is now a **unified Reflex application** that integrates all frontend and backend functionality into a single, maintainable Python codebase. This follows Reflex best practices and eliminates the need for separate backend servers.

## ✨ Key Features

### 🔧 **Unified Architecture**
- **Single Command Launch**: Run everything with `reflex run`
- **Integrated Backend**: AI processing, video analysis, and database operations built directly into Reflex
- **Real-time Analytics**: Live risk scoring, detection counts, and FPS monitoring
- **Database Integration**: SQLite database with Reflex ORM for alerts and system logs

### 🤖 **Advanced AI Capabilities**
- **YOLOv11-Pose Detection**: Real-time person detection and pose estimation
- **Face Analysis**: Age and gender estimation with YOLO-based face detection
- **Risk Assessment**: Sophisticated threat scoring algorithm
- **Harmful Object Detection**: Weapons and dangerous items detection

### 📊 **Real-time Monitoring**
- **Live Video Feed**: Processed frames with AI overlays
- **Risk Score Dashboard**: Dynamic threat level indicators
- **Activity Logging**: Timestamped system events and alerts
- **Session Tracking**: Duration monitoring and analytics

## 🚀 Quick Start

### **1. Launch the Unified System**
```bash
# Navigate to project directory
cd surveillance_system

# Start the unified application
reflex run
```

### **2. Access the Interface**
- **Web Interface**: http://localhost:3000
- **Backend**: Integrated (no separate server needed)

### **3. Using the System**
1. **Choose Source**: Select webcam or video file
2. **Configure Settings**: Set risk threshold and alerts
3. **Start Analysis**: Click "Start Webcam" or "Start Video"
4. **Monitor Results**: View live feed and analytics

## 📁 Project Structure

```
surveillance_system/
├── surveillance/
│   ├── __init__.py
│   └── surveillance.py          # 🎯 Unified Reflex app with integrated backend
├── ai_analyzer.py               # 🤖 YOLO-based AI analysis
├── camera_processor.py          # 📹 Video processing engine
├── yolo_face_detector.py        # 👤 Face detection module
├── rxconfig.py                  # ⚙️ Reflex configuration
├── surveillance.db              # 💾 SQLite database
├── alembic/                     # 🗃️ Database migrations
└── requirements.txt             # 📦 Dependencies
```

## 🔧 Configuration

### **Reflex Configuration** (`rxconfig.py`)
```python
import reflex as rx

config = rx.Config(
    app_name="surveillance",
    backend_port=8001,
    api_url="http://localhost:8001",
    frontend_port=3000,
    db_url="sqlite:///surveillance.db",
    tailwind=None,
)
```

### **Database Models**
The system uses Reflex ORM with two main models:

- **AlertLog**: Stores security alerts and risk events
- **SystemLog**: Tracks system events and operations

## 🎯 Core Components

### **1. SurveillanceState** (State Management)
```python
class SurveillanceState(rx.State):
    # System status
    system_active: bool = False
    risk_score: float = 0.0
    fps: float = 0.0
    detection_count: int = 0
    
    # Configuration
    source_type: str = "webcam"
    risk_threshold: float = 50.0
    auto_alert: bool = True
    
    # Methods for analysis control
    def start_webcam_analysis(self): ...
    def start_video_analysis(self): ...
    def stop_analysis(self): ...
```

### **2. Backend Integration**
The backend components (AI analyzer, camera processor) are handled via global instances outside of Reflex state to avoid serialization issues:

```python
_surveillance_backend = {
    'camera_processor': None,
    'ai_analyzer': None,
    'initialized': False
}
```

### **3. Real-time Processing**
- **Frame Processing**: Video frames processed through integrated AI pipeline
- **Risk Calculation**: Advanced algorithm considering multiple threat factors
- **Alert System**: Automatic alerts when risk threshold exceeded

## 📊 Features

### **🎯 Risk Assessment**
- **Base Risk Factors**: Person presence, gender analysis, object detection
- **Threat Multipliers**: Harmful objects, suspicious behavior patterns
- **Dynamic Scoring**: Real-time risk calculation (0-100%)

### **📹 Video Sources**
- **Live Webcam**: Real-time camera feed processing
- **Video Files**: Server-side video file analysis
- **Multi-format Support**: MP4, AVI, MOV, and more

### **🔔 Alert System**
- **Configurable Thresholds**: Set custom risk levels
- **Auto-alerts**: Automatic notification system
- **Alert Logging**: Database storage for all security events

### **📈 Analytics Dashboard**
- **Real-time Metrics**: Risk score, FPS, detection count
- **Session Tracking**: Duration and performance monitoring
- **Activity Log**: Timestamped event history

## 🛠️ Development

### **Database Operations**
```bash
# Initialize database
reflex db init

# Create migration
reflex db makemigrations --message "your_message"

# Apply migrations
reflex db migrate
```

### **Adding New Features**
1. **State Variables**: Add to `SurveillanceState` class
2. **Event Handlers**: Create methods in state class
3. **UI Components**: Build with Reflex components
4. **Backend Logic**: Extend AI analyzer or camera processor

### **Testing**
```bash
# Run the unified app in development mode
reflex run --env dev

# Access at http://localhost:3000
```

## 🔒 Security & Privacy

- **Local Processing**: All AI analysis runs locally
- **Data Privacy**: No external API calls for sensitive operations
- **SQLite Database**: Local storage for all system data
- **Configurable Settings**: User control over all privacy settings

## 📦 Dependencies

### **Core Requirements**
- **reflex**: Web framework and ORM
- **opencv-python**: Video processing
- **ultralytics**: YOLO models
- **numpy**: Numerical computing
- **pillow**: Image processing

### **AI Models**
- **YOLOv11-Pose**: Person detection and pose estimation
- **YOLO Face Detection**: Custom face analysis models

## 🚨 Troubleshooting

### **Common Issues**

1. **Database Errors**
   ```bash
   # Reset database
   rm surveillance.db
   reflex db init
   reflex db migrate
   ```

2. **Model Loading Issues**
   - Ensure YOLO model files are present
   - Check internet connection for initial model download

3. **Webcam Access**
   - Grant browser permissions for camera access
   - Check if other applications are using the camera

### **Performance Optimization**
- **GPU Acceleration**: Automatic CUDA detection for faster processing
- **Frame Skipping**: Optimized processing for better performance
- **Model Optimization**: Lightweight YOLO models for real-time processing

## 🎉 Benefits of Unified Architecture

### **✅ Advantages**
- **Single Command Launch**: No need for multiple servers
- **Simplified Deployment**: One application to manage
- **Better Integration**: Seamless frontend-backend communication
- **Easier Maintenance**: Single codebase for all functionality
- **Reflex Best Practices**: Following recommended patterns

### **🔄 Migration Complete**
- ❌ **Removed**: Separate FastAPI backend (`surveillance_api.py`)
- ❌ **Removed**: Old Flask app (`app.py`) 
- ❌ **Removed**: Separate launch scripts (`main.py`, `main_reflex.py`)
- ✅ **Added**: Unified Reflex application
- ✅ **Added**: Integrated database with ORM
- ✅ **Added**: Streamlined configuration

## 📞 Support

For issues or questions:
1. Check this documentation
2. Review the Reflex documentation: https://reflex.dev
3. Check the project's activity log for error messages
4. Ensure all dependencies are installed

---

**🎯 The WatchHer Surveillance System is now a modern, unified Python application built with Reflex best practices!** 