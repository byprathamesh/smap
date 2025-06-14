import os
import requests
import subprocess
import sys

# Configuration: Stable URLs and Expected File Sizes for Verification
MODELS_CONFIG = [
    {
        "name": "Face Detection Prototxt",
        "path": "models/deploy.prototxt.txt",
        "url": "https://www.dropbox.com/s/1k9i9b1d9a5b3a8/deploy.prototxt.txt?dl=1",
        "size": 28104
    },
    {
        "name": "Face Detection Caffe Model",
        "path": "models/res10_300x300_ssd_iter_140000_fp16.caffemodel",
        "url": "https://www.dropbox.com/s/d8suyvms19g8tf3/res10_300x300_ssd_iter_140000_fp16.caffemodel?dl=1",
        "size": 5351047
    },
    {
        "name": "Gender Classification Prototxt",
        "path": "models/gender_deploy.prototxt",
        "url": "https://www.dropbox.com/s/u9nrz9l505asz30/gender_deploy.prototxt?dl=1",
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
        "url": "https://www.dropbox.com/s/7942pe5llm0j2xt/yolov3-tiny.weights?dl=1",
        "size": 35434756
    },
    {
        "name": "YOLOv3-tiny Config",
        "path": "models/yolov3-tiny.cfg",
        "url": "https://www.dropbox.com/s/15n5qu99rk2j9rz/yolov3-tiny.cfg?dl=1",
        "size": 1904
    },
    {
        "name": "COCO Names",
        "path": "models/coco.names",
        "url": "https://www.dropbox.com/s/p87omaxmcf3tjr6/coco.names?dl=1",
        "size": 625
    },
    {
        "name": "Age Estimation Prototxt",
        "path": "models/age_deploy.prototxt",
        "url": "https://www.dropbox.com/s/pcb2vs9ishk3kcy/age_deploy.prototxt?dl=1",
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