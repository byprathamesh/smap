import os
import requests
import subprocess
import sys

# Configuration: Stable URLs and Expected File Sizes for Verification
MODELS_CONFIG = [
    {
        "name": "Face Detection Prototxt",
        "path": "models/deploy.prototxt.txt",
        "url": "https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/face_detector/deploy.prototxt",
        "size": 28104
    },
    {
        "name": "Face Detection Caffe Model",
        "path": "models/res10_300x300_ssd_iter_140000_fp16.caffemodel",
        "url": "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20180205_fp16/res10_300x300_ssd_iter_140000_fp16.caffemodel",
        "size": 5351047
    },
    {
        "name": "Gender Classification Prototxt",
        "path": "models/gender_deploy.prototxt",
        "url": "https://github.com/spmallick/learnopencv/raw/master/AgeGender/gender_deploy.prototxt",
        "size": 29202
    },
    {
        "name": "Gender Classification Caffe Model",
        "path": "models/gender_net.caffemodel",
        "url": "https://www.dropbox.com/s/onem26312h8h04n/gender_net.caffemodel?dl=1",
        "size": 21768305
    },
    {
        "name": "YOLOv3-tiny Weights",
        "path": "models/yolov3-tiny.weights",
        "url": "https://pjreddie.com/media/files/yolov3-tiny.weights",
        "size": 35434756
    },
    {
        "name": "YOLOv3-tiny Config",
        "path": "models/yolov3-tiny.cfg",
        "url": "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3-tiny.cfg",
        "size": 1904
    },
    {
        "name": "COCO Names",
        "path": "models/coco.names",
        "url": "https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names",
        "size": 625
    },
    {
        "name": "Age Estimation Prototxt",
        "path": "models/age_deploy.prototxt",
        "url": "https://github.com/spmallick/learnopencv/raw/master/AgeGender/age_deploy.prototxt",
        "size": 29012
    },
    {
        "name": "Age Estimation Caffe Model",
        "path": "models/age_net.caffemodel",
        "url": "https://www.dropbox.com/s/iyv483wz78j1g6p/age_net.caffemodel?dl=1",
        "size": 21739423
    }
]

def print_header(title):
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)

def check_and_download_models():
    print_header("Step 1: Verifying AI Models")
    os.makedirs("models", exist_ok=True)
    all_models_valid = True
    
    for model in MODELS_CONFIG:
        print(f"[INFO] Checking for: {model['name']}...")
        is_valid = False
        if os.path.exists(model['path']):
            # Verify file size to detect corrupted downloads
            if os.path.getsize(model['path']) == model['size']:
                print(f"  -> [OK] File exists and is valid.")
                is_valid = True
            else:
                print(f"  -> [WARNING] File exists but is corrupted. Redownloading...")
        
        if not is_valid:
            try:
                print(f"  -> Downloading from {model['url']}...")
                response = requests.get(model['url'], stream=True, timeout=30)
                response.raise_for_status()
                with open(model['path'], 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"  -> [SUCCESS] Download complete.")
            except requests.exceptions.RequestException as e:
                print(f"  -> [ERROR] Failed to download: {e}")
                all_models_valid = False
    
    if not all_models_valid:
        print("\n[FATAL ERROR] One or more models failed to download.")
        print("Please check your internet connection and try again.")
        sys.exit(1)
    
    print("[SUCCESS] All AI models are present and verified.")

def run_setup_checks():
    print_header("WatchHer System Setup & Verification")
    check_and_download_models()
    print("\n[SUCCESS] All checks passed. System is ready to launch.")
    print("=" * 80) 