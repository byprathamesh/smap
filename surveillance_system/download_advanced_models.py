import os
import requests
import sys
from urllib.parse import urlparse


# Advanced model definitions with download URLs
ADVANCED_MODELS_TO_DOWNLOAD = [
    {
        "name": "YOLOv3-tiny Weights",
        "filename": "yolov3-tiny.weights",
        "url": "https://pjreddie.com/media/files/yolov3-tiny.weights"
    },
    {
        "name": "YOLOv3-tiny Config",
        "filename": "yolov3-tiny.cfg",
        "url": "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3-tiny.cfg"
    },
    {
        "name": "COCO Names",
        "filename": "coco.names",
        "url": "https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names"
    },
    {
        "name": "Age Estimation Prototxt",
        "filename": "age_deploy.prototxt",
        "url": "https://raw.githubusercontent.com/GilLevi/AgeGenderDeepLearning/master/age_deploy.prototxt"
    },
    {
        "name": "Age Estimation Caffe Model",
        "filename": "age_net.caffemodel",
        "url": "https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/age_net.caffemodel"
    }
]

# Target directory for models
MODELS_DIR = "models"


def create_models_directory():
    """
    Create the models directory if it doesn't exist.
    """
    if not os.path.exists(MODELS_DIR):
        print(f"[INFO] Creating models directory: {MODELS_DIR}")
        os.makedirs(MODELS_DIR, exist_ok=True)
    else:
        print(f"[INFO] Models directory already exists: {MODELS_DIR}")


def download_file_with_progress(url, filepath, filename):
    """
    Download a file from URL with progress indicator.
    
    Args:
        url: URL to download from
        filepath: Full path where to save the file
        filename: Name of the file for display purposes
        
    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        print(f"[INFO] Downloading {filename}...")
        print(f"[INFO] Source: {url}")
        
        # Send GET request with stream=True for large files
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Get total file size if available
        total_size = int(response.headers.get('content-length', 0))
        
        # Download and save file with progress indicator
        downloaded_size = 0
        chunk_size = 8192  # 8KB chunks
        
        with open(filepath, 'wb') as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # Show progress
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        print(f"\r[INFO] Progress: {progress:.1f}% ({downloaded_size}/{total_size} bytes)", end='', flush=True)
                    else:
                        print(f"\r[INFO] Downloaded: {downloaded_size} bytes", end='', flush=True)
        
        print()  # New line after progress
        print(f"[INFO] Successfully downloaded {filename}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Failed to download {filename}. Please check your internet connection and the URL.")
        print(f"[DEBUG] Network error details: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error downloading {filename}: {e}")
        return False


def verify_file_integrity(filepath, filename):
    """
    Verify that the downloaded file exists and has content.
    
    Args:
        filepath: Path to the file
        filename: Name of the file for display purposes
        
    Returns:
        bool: True if file is valid, False otherwise
    """
    try:
        if not os.path.exists(filepath):
            print(f"[ERROR] File does not exist: {filename}")
            return False
        
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            print(f"[ERROR] File is empty: {filename}")
            return False
        
        # Additional validation for specific file types
        if filename.endswith('.weights'):
            # YOLO weights files should be reasonably large (> 1MB)
            if file_size < 1024 * 1024:
                print(f"[ERROR] Weights file seems too small: {filename} ({file_size} bytes)")
                return False
        
        print(f"[INFO] File verification passed: {filename} ({file_size} bytes)")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error verifying file {filename}: {e}")
        return False


def download_advanced_models():
    """
    Main function to download all required advanced models.
    """
    print("=" * 80)
    print("                WatchHer Advanced Model Downloader")
    print("              Context-Aware Threat Analysis Models")
    print("=" * 80)
    
    # Create models directory
    create_models_directory()
    
    # Track download statistics
    total_models = len(ADVANCED_MODELS_TO_DOWNLOAD)
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    
    # Download each model
    for i, model_info in enumerate(ADVANCED_MODELS_TO_DOWNLOAD, 1):
        filename = model_info["filename"]
        url = model_info["url"]
        name = model_info["name"]
        filepath = os.path.join(MODELS_DIR, filename)
        
        print(f"\n[INFO] Processing model {i}/{total_models}: {name}")
        
        # Check if file already exists
        if os.path.exists(filepath):
            if verify_file_integrity(filepath, filename):
                print(f"[INFO] '{filename}' already exists and is valid. Skipping download.")
                skipped_count += 1
                continue
            else:
                print(f"[WARNING] '{filename}' exists but appears corrupted. Re-downloading...")
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"[ERROR] Could not remove corrupted file: {e}")
                    failed_count += 1
                    continue
        
        # Download the file
        if download_file_with_progress(url, filepath, filename):
            if verify_file_integrity(filepath, filename):
                downloaded_count += 1
            else:
                failed_count += 1
                # Remove corrupted download
                try:
                    os.remove(filepath)
                except:
                    pass
        else:
            failed_count += 1
    
    # Print summary
    print("\n" + "=" * 80)
    print("                     Advanced Download Summary")
    print("=" * 80)
    print(f"Total Models: {total_models}")
    print(f"Downloaded: {downloaded_count}")
    print(f"Skipped (already exist): {skipped_count}")
    print(f"Failed: {failed_count}")
    
    if failed_count == 0:
        print("\n[SUCCESS] All advanced models are ready!")
        print("[INFO] Context-Aware Threat Analysis System is now available.")
        print("[INFO] You can now run the upgraded surveillance system.")
    else:
        print(f"\n[WARNING] {failed_count} model(s) failed to download.")
        print("[INFO] Please check your internet connection and try again.")
        print("[INFO] The advanced threat analysis may not work properly without all models.")
    
    print("\n[INFO] Model Details:")
    print("  - YOLOv3-tiny: Fast object detection for person identification")
    print("  - COCO Names: Object class labels for YOLO detection")
    print("  - Age Estimation: Age classification for context-aware analysis")
    print("=" * 80)
    
    return failed_count == 0


def main():
    """
    Main entry point for the advanced model downloader.
    """
    try:
        success = download_advanced_models()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INFO] Download interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 