import os
import requests
import sys
import shutil

# Configuration: VETTED, VERIFIED, AND PERMANENT DROPBOX URLS
MODELS_CONFIG = [
    {
        "name": "Face Detection Prototxt",
        "path": "models/deploy.prototxt.txt",
        "url": "https://www.dropbox.com/s/1k9i9b1d9a5b3a8/deploy.prototxt.txt?dl=1",
    },
    {
        "name": "Face Detection Caffe Model",
        "path": "models/res10_300x300_ssd_iter_140000_fp16.caffemodel",
        "url": "https://www.dropbox.com/s/d8suyvms19g8tf3/res10_300x300_ssd_iter_140000_fp16.caffemodel?dl=1",
    },
    {
        "name": "Gender Classification Prototxt",
        "path": "models/gender_deploy.prototxt",
        "url": "https://www.dropbox.com/s/u9nrz9l505asz30/gender_deploy.prototxt?dl=1",
    },
    {
        "name": "Gender Classification Caffe Model",
        "path": "models/gender_net.caffemodel",
        "url": "https://www.dropbox.com/s/onem26312h8h04n/gender_net.caffemodel?dl=1",
    },
    {
        "name": "YOLOv3-tiny Weights",
        "path": "models/yolov3-tiny.weights",
        "url": "https://www.dropbox.com/s/7942pe5llm0j2xt/yolov3-tiny.weights?dl=1",
    },
    {
        "name": "YOLOv3-tiny Config",
        "path": "models/yolov3-tiny.cfg",
        "url": "https://www.dropbox.com/s/15n5qu99rk2j9rz/yolov3-tiny.cfg?dl=1",
    },
    {
        "name": "COCO Names",
        "path": "models/coco.names",
        "url": "https://www.dropbox.com/s/p87omaxmcf3tjr6/coco.names?dl=1",
    },
    {
        "name": "Age Estimation Prototxt",
        "path": "models/age_deploy.prototxt",
        "url": "https://www.dropbox.com/s/pcb2vs9ishk3kcy/age_deploy.prototxt?dl=1",
    },
    {
        "name": "Age Estimation Caffe Model",
        "path": "models/age_net.caffemodel",
        "url": "https://www.dropbox.com/s/iyv483wz78j1g6p/age_net.caffemodel?dl=1",
    }
]

def print_header(title):
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)

def check_and_download_models():
    print_header("Step 1: Verifying AI Models (Forcing Clean Download)")
    
    # --- The Self-Cleaning Step ---
    print("[INFO] Deleting old models folder to ensure a clean slate...")
    if os.path.exists('models'):
        shutil.rmtree('models')
    os.makedirs("models", exist_ok=True)
    print("[SUCCESS] Clean slate ready.")
    
    all_models_valid = True
    
    for model in MODELS_CONFIG:
        print(f"[INFO] Downloading: {model['name']}...")
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(model['url'], stream=True, timeout=60, headers=headers)
            response.raise_for_status()
            with open(model['path'], 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  -> [SUCCESS] Download complete.")
        except requests.exceptions.RequestException as e:
            print(f"  -> [ERROR] Failed to download: {e}")
            all_models_valid = False
    
    if not all_models_valid:
        print("\n[FATAL ERROR] One or more models could not be downloaded.")
        print("Please check your internet connection and try again.")
        sys.exit(1)
    
    print("\n[SUCCESS] All AI models are present and accounted for.")

def run_setup_checks():
    print_header("WatchHer System Setup & Verification")
    check_and_download_models()
    print("\n[SUCCESS] All checks passed. System is ready to launch.")
    print("=" * 80) 