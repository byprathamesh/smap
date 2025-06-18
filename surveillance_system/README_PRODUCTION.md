# 🛡️ WatchHer - Advanced AI Surveillance System (Production v2.0)

## 🎯 Overview

WatchHer is an intelligent public safety monitoring system that combines cutting-edge AI technologies to provide real-time threat assessment and risk scoring. The system uses computer vision, pose detection, and facial analysis to monitor environments and identify potential safety concerns.

## ✨ Key Features

### 🤖 Advanced AI Pipeline
- **YOLOv8-Pose Detection**: GPU-accelerated human pose detection and tracking
- **DeepFace Analysis**: Age and gender recognition with confidence scoring
- **Distress Recognition**: Automated detection of distress signals from body language
- **Multi-Person Processing**: Simultaneous analysis of multiple individuals

### 🎯 Sophisticated Risk Assessment
- **Dynamic Risk Scoring**: Advanced algorithm considering multiple factors
- **Gender-based Vulnerability Analysis**: Context-aware risk calculation
- **Group Dynamics Assessment**: Male-to-female ratio analysis
- **Contextual Factors**: Time-based and location-based risk multipliers
- **Real-time Scoring**: Continuous risk assessment with 0-200 scale

### 🖥️ Visual Interface
- **Real-time Overlays**: Bounding boxes with age, gender, and confidence
- **Risk Indicators**: Color-coded threat levels and status displays
- **Single Window Management**: Optimized display architecture
- **Multi-person Visualization**: Simultaneous overlay for all detected individuals

### ⚡ Performance Optimization
- **GPU Acceleration**: CUDA-enabled YOLO processing
- **Selective Processing**: DeepFace analysis limited to 2 largest detections
- **Efficient Memory Management**: Optimized for real-time processing
- **Scalable Architecture**: Designed for production deployment

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.11+
# NVIDIA GPU with CUDA support (recommended)
# OpenCV with GUI support
```

### Installation
```bash
# Clone and navigate
git clone https://github.com/toprathamesh/smap.git
cd smap/surveillance_system

# Install dependencies
pip install -r requirements.txt

# Download YOLO models (automatic on first run)
```

### Usage

#### Video File Analysis
```bash
python main.py --video path/to/your/video.mp4
```

#### Webcam Monitoring
```bash
python main.py
```

#### Web Interface
```bash
python app.py
```

## 📊 Risk Scoring System

### Individual Risk Factors
- **Base Risk**: 5 points per detected person
- **Gender Vulnerability**: +10 for females, +2 for males
- **Confidence Weighting**: Adjusted by detection confidence
- **Distress Signals**: +50 points for detected distress
- **Surrounded Females**: +40 points when surrounded by 2+ males

### Group Dynamics
- **Male-to-Female Ratio**: Up to +25 points for high ratios
- **Lone Woman**: +20 points when alone with males
- **Large Groups**: +10 points for 5+ people
- **Unknown Faces**: +5 points per undetected face

### Contextual Multipliers
- **Night Time**: 1.5x risk multiplier (10 PM - 6 AM)
- **Location Risk**: Configurable location-based multiplier
- **Historical Data**: Future integration for location-specific risk

### Risk Levels
- **0-30**: 🟢 Low Risk
- **31-60**: 🟡 Medium Risk  
- **61-100**: 🟠 High Risk
- **101-200**: 🔴 Critical Risk

## 🏗️ Architecture

### Core Components
```
WatchHer/
├── ai_analyzer.py          # AI analysis pipeline
├── camera_processor.py     # Video processing & risk calculation
├── main.py                 # Main application entry point
├── app.py                  # Flask web interface
├── alert_system.py         # Alert management
├── database.py             # Data persistence
└── config.py               # Configuration management
```

### AI Pipeline Flow
1. **Video Input** → Camera/File processing
2. **YOLO Detection** → Person detection and pose analysis
3. **Face Analysis** → Age/gender recognition (top 2 largest)
4. **Risk Calculation** → Sophisticated multi-factor scoring
5. **Visual Output** → Real-time overlay and display

## 🎛️ Configuration

### Performance Tuning
```python
# ai_analyzer.py
max_deepface_calls = 2  # Limit DeepFace to largest detections

# camera_processor.py
frame_rate = 2.0  # Process 2 frames per second
```

### Risk Scoring Weights
```python
# Modify in _calculate_risk_score()
base_risk_per_person = 5.0
female_vulnerability_bonus = 10.0
distress_penalty = 50.0
surrounded_penalty = 40.0
```

## 🔧 Hardware Recommendations

### Minimum Requirements
- **CPU**: Intel i5 / AMD Ryzen 5
- **RAM**: 8GB
- **GPU**: Any CUDA-compatible NVIDIA GPU
- **Storage**: 2GB free space

### Recommended Setup
- **CPU**: Intel i7 / AMD Ryzen 7
- **RAM**: 16GB+
- **GPU**: NVIDIA RTX 3060 or better
- **Storage**: SSD recommended

### Performance Expectations
- **With GPU**: 5-15 FPS (depending on scene complexity)
- **CPU Only**: 0.5-2 FPS (not recommended for production)

## 🛠️ Troubleshooting

### Common Issues

#### Low FPS Performance
- Ensure NVIDIA GPU drivers are installed
- Verify CUDA installation: `nvidia-smi`
- Check GPU utilization in Task Manager

#### No Visual Overlays
- Verify OpenCV GUI support: `cv2.imshow` capability
- Check video file format compatibility
- Ensure proper file paths

#### Model Loading Errors
- Download YOLO models manually if automatic download fails
- Check internet connection for DeepFace model downloads
- Verify file permissions in model directories

## 📈 Future Enhancements

### Planned Features
- **Multi-Camera Support**: Simultaneous monitoring of multiple feeds
- **Cloud Integration**: Remote monitoring and alert management
- **Mobile App**: Companion mobile application
- **Advanced Analytics**: Historical data analysis and reporting
- **Custom Training**: Domain-specific model training

### AI Improvements
- **Emotion Recognition**: Enhanced emotional state detection
- **Behavior Analysis**: Advanced behavioral pattern recognition
- **Predictive Modeling**: Risk prediction based on historical data
- **3D Pose Estimation**: More accurate pose analysis

## 📝 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

For technical support or questions:
- Create an issue on GitHub
- Contact: [Your contact information]

---

**WatchHer v2.0** - Advanced AI Surveillance for Public Safety 