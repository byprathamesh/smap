#!/usr/bin/env python3
"""
AI Model Downloader for WatchHer Surveillance System
Downloads and verifies all required AI models with size validation.
"""

import os
import requests
import sys
from pathlib import Path

# Model configuration with URLs and expected file sizes
MODELS_CONFIG = [
    {
        "name": "Face Detection Prototxt",
        "filename": "deploy.prototxt.txt",
        "url": "https://www.dropbox.com/s/1k9i9b1d9a5b3a8/deploy.prototxt.txt?dl=1",
        "expected_size": 28104
    },
    {
        "name": "Face Detection Caffe Model",
        "filename": "res10_300x300_ssd_iter_140000_fp16.caffemodel",
        "url": "https://www.dropbox.com/s/d8suyvms19g8tf3/res10_300x300_ssd_iter_140000_fp16.caffemodel?dl=1",
        "expected_size": 5351047
    },
    {
        "name": "Gender Classification Prototxt",
        "filename": "gender_deploy.prototxt",
        "url": "https://www.dropbox.com/s/u9nrz9l505asz30/gender_deploy.prototxt?dl=1",
        "expected_size": 29202
    },
    {
        "name": "Gender Classification Caffe Model",
        "filename": "gender_net.caffemodel",
        "url": "https://www.dropbox.com/s/onem26312h8h04n/gender_net.caffemodel?dl=1",
        "expected_size": 21768305
    },
    {
        "name": "YOLOv3-tiny Weights",
        "filename": "yolov3-tiny.weights",
        "url": "https://www.dropbox.com/s/7942pe5llm0j2xt/yolov3-tiny.weights?dl=1",
        "expected_size": 35434756
    },
    {
        "name": "YOLOv3-tiny Config",
        "filename": "yolov3-tiny.cfg",
        "url": "https://www.dropbox.com/s/15n5qu99rk2j9rz/yolov3-tiny.cfg?dl=1",
        "expected_size": 1904
    },
    {
        "name": "COCO Names",
        "filename": "coco.names",
        "url": "https://www.dropbox.com/s/p87omaxmcf3tjr6/coco.names?dl=1",
        "expected_size": 625
    },
    {
        "name": "Age Estimation Prototxt",
        "filename": "age_deploy.prototxt",
        "url": "https://www.dropbox.com/s/pcb2vs9ishk3kcy/age_deploy.prototxt?dl=1",
        "expected_size": 29012
    },
    {
        "name": "Age Estimation Caffe Model",
        "filename": "age_net.caffemodel",
        "url": "https://www.dropbox.com/s/iyv483wz78j1g6p/age_net.caffemodel?dl=1",
        "expected_size": 21739423
    }
]

def print_header(title):
    """Print a formatted header."""
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)

def format_size(size_bytes):
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def verify_file_size(file_path, expected_size):
    """Verify that a file has the expected size."""
    if not os.path.exists(file_path):
        return False, 0
    
    actual_size = os.path.getsize(file_path)
    return actual_size == expected_size, actual_size

def download_file(url, file_path, expected_size):
    """Download a file with progress indication and size verification."""
    try:
        print(f"  -> Downloading from: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, stream=True, timeout=60, headers=headers)
        response.raise_for_status()
        
        # Download the file
        with open(file_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
        
        # Verify the downloaded file size
        actual_size = os.path.getsize(file_path)
        if actual_size == expected_size:
            print(f"  -> [SUCCESS] Downloaded and verified: {format_size(actual_size)}")
            return True
        else:
            print(f"  -> [ERROR] Size mismatch! Expected: {format_size(expected_size)}, Got: {format_size(actual_size)}")
            # Delete the corrupted file
            os.remove(file_path)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  -> [ERROR] Download failed: {e}")
        # Clean up partial download
        if os.path.exists(file_path):
            os.remove(file_path)
        return False
    except Exception as e:
        print(f"  -> [ERROR] Unexpected error: {e}")
        # Clean up partial download
        if os.path.exists(file_path):
            os.remove(file_path)
        return False

def setup_models():
    """Main function to download and verify all AI models."""
    print_header("AI Model Setup for WatchHer Surveillance System")
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    print(f"[INFO] Models directory: {models_dir.absolute()}")
    
    all_successful = True
    
    for i, model in enumerate(MODELS_CONFIG, 1):
        print(f"\n[{i}/{len(MODELS_CONFIG)}] Processing: {model['name']}")
        
        file_path = models_dir / model['filename']
        
        # Check if file already exists and has correct size
        is_valid, actual_size = verify_file_size(file_path, model['expected_size'])
        
        if is_valid:
            print(f"  -> [OK] File exists and verified: {format_size(actual_size)}")
            continue
        elif os.path.exists(file_path):
            print(f"  -> [WARNING] File exists but wrong size: {format_size(actual_size)} (expected: {format_size(model['expected_size'])})")
            print(f"  -> [INFO] Deleting corrupted file and re-downloading...")
            os.remove(file_path)
        
        # Download the file
        success = download_file(model['url'], file_path, model['expected_size'])
        
        if not success:
            print(f"  -> [FATAL] Failed to download {model['name']}")
            all_successful = False
            break
    
    # Final status
    print("\n" + "=" * 80)
    if all_successful:
        print("[SUCCESS] All AI models downloaded and verified successfully!")
        print("The surveillance system is ready to run.")
    else:
        print("[FATAL ERROR] One or more models failed to download.")
        print("Please check your internet connection and try again.")
        sys.exit(1)
    print("=" * 80)

if __name__ == "__main__":
    setup_models() 