import os
import requests
import sys
from urllib.parse import urlparse


# Model definitions with download URLs
MODELS_TO_DOWNLOAD = [
    {
        "name": "Face Detection Prototxt",
        "filename": "deploy.prototxt.txt",
        "url": "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
    },
    {
        "name": "Face Detection Caffe Model",
        "filename": "res10_300x300_ssd_iter_140000_fp16.caffemodel",
        "url": "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20180205_fp16/res10_300x300_ssd_iter_140000_fp16.caffemodel"
    },
    {
        "name": "Gender Classification Prototxt",
        "filename": "gender_deploy.prototxt",
        "url": "https://github.com/arunponnusamy/cvlib-files/raw/master/gender_detection/gender_deploy.prototxt"
    },
    {
        "name": "Gender Classification Caffe Model",
        "filename": "gender_net.caffemodel",
        "url": "https://github.com/arunponnusamy/cvlib-files/raw/master/gender_detection/gender_net.caffemodel"
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
        response = requests.get(url, stream=True, timeout=30)
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
        print(f"[INFO] You can try downloading manually from: {url}")
        return False
    except (IOError, OSError) as e:
        print(f"\n[ERROR] File system error while downloading {filename}: {e}")
        print(f"[INFO] Check disk space and file permissions")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error downloading {filename}: {e}")
        print(f"[INFO] This may be due to a corrupted download or system issue")
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
        
        print(f"[INFO] File verification passed: {filename} ({file_size} bytes)")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error verifying file {filename}: {e}")
        return False


def download_models():
    """
    Main function to download all required models.
    """
    print("=" * 80)
    print("                    WatchHer Model Downloader")
    print("                   Downloading AI Model Files")
    print("=" * 80)
    
    # Create models directory
    create_models_directory()
    
    # Track download statistics
    total_models = len(MODELS_TO_DOWNLOAD)
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    
    # Download each model
    for i, model_info in enumerate(MODELS_TO_DOWNLOAD, 1):
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
    print("                        Download Summary")
    print("=" * 80)
    print(f"Total Models: {total_models}")
    print(f"Downloaded: {downloaded_count}")
    print(f"Skipped (already exist): {skipped_count}")
    print(f"Failed: {failed_count}")
    
    if failed_count == 0:
        print("\n[SUCCESS] All models are ready!")
        print("[INFO] You can now run the surveillance system.")
    else:
        print(f"\n[WARNING] {failed_count} model(s) failed to download.")
        print("[INFO] Please check your internet connection and try again.")
        print("[INFO] The surveillance system may not work properly without all models.")
    
    print("=" * 80)
    
    return failed_count == 0


def main():
    """
    Main entry point for the model downloader.
    """
    try:
        success = download_models()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INFO] Download interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 