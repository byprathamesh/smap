import os
import requests
import sys

# Configuration: VETTED, VERIFIED, AND STABLE URLS
MODELS_CONFIG = [
    {
        "name": "Face Detection Prototxt",
        "path": "models/deploy.prototxt.txt",
        "url": "https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/face_detector/deploy.prototxt",
    },
    {
        "name": "Face Detection Caffe Model",
        "path": "models/res10_300x300_ssd_iter_140000_fp16.caffemodel",
        "url": "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20180205_fp16/res10_300x300_ssd_iter_140000_fp16.caffemodel",
    },
    {
        "name": "Gender Classification Prototxt",
        "path": "models/gender_deploy.prototxt",
        "url": "https://github.com/spmallick/learnopencv/raw/master/AgeGender/gender_deploy.prototxt",
    },
    {
        "name": "Gender Classification Caffe Model",
        "path": "models/gender_net.caffemodel",
        "url": "https://www.dropbox.com/s/onem26312h8h04n/gender_net.caffemodel?dl=1",
    },
    {
        "name": "YOLOv3-tiny Weights",
        "path": "models/yolov3-tiny.weights",
        "url": "https://github.com/arunponnusamy/cvlib-files/raw/master/yolo/yolov3-tiny.weights",
    },
    {
        "name": "YOLOv3-tiny Config",
        "path": "models/yolov3-tiny.cfg",
        "url": "https://github.com/arunponnusamy/cvlib-files/raw/master/yolo/yolov3-tiny.cfg",
    },
    {
        "name": "COCO Names",
        "path": "models/coco.names",
        "url": "https://github.com/arunponnusamy/cvlib-files/raw/master/yolo/coco.names",
    },
    {
        "name": "Age Estimation Prototxt",
        "path": "models/age_deploy.prototxt",
        "url": "https://github.com/spmallick/learnopencv/raw/master/AgeGender/age_deploy.prototxt",
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
    print_header("Step 1: Verifying AI Models")
    os.makedirs("models", exist_ok=True)
    all_models_valid = True
    
    for model in MODELS_CONFIG:
        print(f"[INFO] Checking for: {model['name']}...")
        if os.path.exists(model['path']):
            print(f"  -> [OK] File already exists. Skipping.")
            continue
        
        try:
            print(f"  -> Downloading from {model['url']}...")
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