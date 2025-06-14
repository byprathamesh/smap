import os
import requests
import sys
import shutil

# Configuration: Vetted URLs and VERIFIED FILE SIZES for integrity check
MODELS_CONFIG = [
    {"path": "models/deploy.prototxt.txt", "url": "https://www.dropbox.com/s/1k9i9b1d9a5b3a8/deploy.prototxt.txt?dl=1", "size": 28104},
    {"path": "models/res10_300x300_ssd_iter_140000_fp16.caffemodel", "url": "https://www.dropbox.com/s/d8suyvms19g8tf3/res10_300x300_ssd_iter_140000_fp16.caffemodel?dl=1", "size": 5351047},
    {"path": "models/gender_deploy.prototxt", "url": "https://www.dropbox.com/s/u9nrz9l505asz30/gender_deploy.prototxt?dl=1", "size": 29202},
    {"path": "models/gender_net.caffemodel", "url": "https://www.dropbox.com/s/onem26312h8h04n/gender_net.caffemodel?dl=1", "size": 21768305},
    {"path": "models/yolov3-tiny.weights", "url": "https://www.dropbox.com/s/7942pe5llm0j2xt/yolov3-tiny.weights?dl=1", "size": 35434756},
    {"path": "models/yolov3-tiny.cfg", "url": "https://www.dropbox.com/s/15n5qu99rk2j9rz/yolov3-tiny.cfg?dl=1", "size": 1904},
    {"path": "models/coco.names", "url": "https://www.dropbox.com/s/p87omaxmcf3tjr6/coco.names?dl=1", "size": 625},
    {"path": "models/age_deploy.prototxt", "url": "https://www.dropbox.com/s/pcb2vs9ishk3kcy/age_deploy.prototxt?dl=1", "size": 29012},
    {"path": "models/age_net.caffemodel", "url": "https://www.dropbox.com/s/iyv483wz78j1g6p/age_net.caffemodel?dl=1", "size": 21739423}
]

def print_header(title):
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)

def check_and_download_models():
    print_header("Step 1: Verifying AI Models (Forcing Clean Download with Size Check)")
    
    # --- The Self-Cleaning Step ---
    print("[INFO] Deleting old models folder to ensure a clean slate...")
    if os.path.exists('models'):
        shutil.rmtree('models')
    os.makedirs("models", exist_ok=True)
    print("[SUCCESS] Clean slate ready.")
    
    all_models_valid = True
    
    for model in MODELS_CONFIG:
        print(f"[INFO] Downloading: {os.path.basename(model['path'])}...")
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(model['url'], stream=True, timeout=60, headers=headers)
            response.raise_for_status()
            with open(model['path'], 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # --- The Paranoid Verification Step ---
            downloaded_size = os.path.getsize(model['path'])
            if downloaded_size == model['size']:
                print(f"  -> [SUCCESS] Download complete and file size verified ({downloaded_size} bytes).")
            else:
                print(f"  -> [ERROR] Download corrupted! Expected size {model['size']} but got {downloaded_size}.")
                all_models_valid = False

        except requests.exceptions.RequestException as e:
            print(f"  -> [ERROR] Failed to download: {e}")
            all_models_valid = False
    
    if not all_models_valid:
        print("\n[FATAL ERROR] One or more models could not be downloaded or verified correctly.")
        print("Please check your internet connection and try again.")
        sys.exit(1)
    
    print("\n[SUCCESS] All AI models are downloaded and verified.")

def run_setup_checks():
    print_header("WatchHer System Setup & Verification")
    check_and_download_models()
    print("\n[SUCCESS] All checks passed. System is ready to launch.")
    print("=" * 80) 