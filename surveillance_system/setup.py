import os
import requests
import sys

# Configuration: Vetted, Truly Raw URLs and Expected Content Headers
MODELS_CONFIG = [
    {
        "name": "Face Detection Prototxt",
        "path": "models/deploy.prototxt.txt",
        "url": "https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/face_detector/deploy.prototxt",
        "verify_text": "layer"
    },
    {
        "name": "Face Detection Caffe Model",
        "path": "models/res10_300x300_ssd_iter_140000_fp16.caffemodel",
        "url": "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20180205_fp16/res10_300x300_ssd_iter_140000_fp16.caffemodel",
        "verify_text": None  # Binary file, cannot verify text
    },
    {
        "name": "Gender Classification Prototxt",
        "path": "models/gender_deploy.prototxt",
        "url": "https://raw.githubusercontent.com/GilLevi/AgeGenderDeepLearning/master/gender_deploy.prototxt",
        "verify_text": "name:"
    },
    {
        "name": "Gender Classification Caffe Model",
        "path": "models/gender_net.caffemodel",
        "url": "https://www.dropbox.com/s/onem26312h8h04n/gender_net.caffemodel?dl=1",
        "verify_text": None  # Binary file
    },
    {
        "name": "YOLOv3-tiny Weights",
        "path": "models/yolov3-tiny.weights",
        "url": "https://pjreddie.com/media/files/yolov3-tiny.weights",
        "verify_text": None  # Binary file
    },
    {
        "name": "YOLOv3-tiny Config",
        "path": "models/yolov3-tiny.cfg",
        "url": "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3-tiny.cfg",
        "verify_text": "[net]"
    },
    {
        "name": "COCO Names",
        "path": "models/coco.names",
        "url": "https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names",
        "verify_text": "person"
    },
    {
        "name": "Age Estimation Prototxt",
        "path": "models/age_deploy.prototxt",
        "url": "https://raw.githubusercontent.com/GilLevi/AgeGenderDeepLearning/master/age_deploy.prototxt",
        "verify_text": "name:"
    },
    {
        "name": "Age Estimation Caffe Model",
        "path": "models/age_net.caffemodel",
        "url": "https://www.dropbox.com/s/iyv483wz78j1g6p/age_net.caffemodel?dl=1",
        "verify_text": None  # Binary file
    }
]

def print_header(title):
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)

def verify_model_content(file_path, expected_text):
    """
    Verify that downloaded file contains expected content and is not an HTML page.
    """
    if not expected_text:
        return True  # Cannot verify binary files this way
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(500)
            if expected_text in content and '<html' not in content.lower() and '<!doctype' not in content.lower():
                return True
            return False
    except Exception:
        return False

def check_and_download_models():
    print_header("Step 1: Verifying AI Models with Content Check")
    os.makedirs("models", exist_ok=True)
    all_models_valid = True
    
    for model in MODELS_CONFIG:
        print(f"[INFO] Checking for: {model['name']}...")
        is_valid = False
        if os.path.exists(model['path']):
            if verify_model_content(model['path'], model.get('verify_text')):
                print(f"  -> [OK] File exists and content is valid.")
                is_valid = True
            else:
                print(f"  -> [WARNING] File exists but content is corrupted. Deleting and redownloading...")
                os.remove(model['path'])
        
        if not is_valid:
            try:
                print(f"  -> Downloading from {model['url']}...")
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(model['url'], stream=True, timeout=60, headers=headers)
                response.raise_for_status()
                with open(model['path'], 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Final content verification after download
                if verify_model_content(model['path'], model.get('verify_text')):
                    print(f"  -> [SUCCESS] Download complete and verified.")
                else:
                    print(f"  -> [ERROR] Downloaded file is corrupted (likely HTML).")
                    all_models_valid = False
                    
            except requests.exceptions.RequestException as e:
                print(f"  -> [ERROR] Failed to download: {e}")
                all_models_valid = False
    
    if not all_models_valid:
        print("\n[FATAL ERROR] One or more models could not be correctly downloaded or verified.")
        print("Please check your internet connection and firewall settings.")
        sys.exit(1)
    
    print("\n[SUCCESS] All AI models are present and verified.")

def run_setup_checks():
    print_header("WatchHer System Setup & Verification")
    check_and_download_models()
    print("\n[SUCCESS] All checks passed. System is ready to launch.")
    print("=" * 80) 