#!/usr/bin/env python3
"""
Test YOLO Model Classes
Check what objects YOLO can actually detect
"""

from ultralytics import YOLO

def test_yolo_classes():
    """Test what classes YOLO models can detect"""
    print("🔍 Testing YOLO Model Classes")
    print("=" * 50)
    
    # Test YOLOv8n general object detection
    print("📦 Loading YOLOv8n (general object detection)...")
    model = YOLO('yolov8n.pt')
    
    print(f"✅ Model loaded! Can detect {len(model.names)} classes:")
    print()
    
    # Look for harmful objects
    harmful_keywords = ['knife', 'gun', 'weapon', 'scissors', 'bat', 'club', 'sword']
    
    print("🎯 Looking for harmful objects in YOLO classes:")
    found_harmful = []
    
    for class_id, class_name in model.names.items():
        for keyword in harmful_keywords:
            if keyword.lower() in class_name.lower():
                found_harmful.append((class_id, class_name))
                print(f"   ✅ Class {class_id}: {class_name}")
    
    print(f"\n📊 Found {len(found_harmful)} potentially harmful classes")
    
    # Show all classes
    print(f"\n📋 All {len(model.names)} YOLO classes:")
    for class_id, class_name in model.names.items():
        print(f"   {class_id:2d}: {class_name}")
    
    # Check for kitchen items that might be sharp
    print(f"\n🔪 Kitchen/Tool items that might be used as weapons:")
    kitchen_keywords = ['fork', 'spoon', 'bowl', 'cup', 'bottle']
    for class_id, class_name in model.names.items():
        for keyword in kitchen_keywords:
            if keyword.lower() in class_name.lower():
                print(f"   {class_id:2d}: {class_name}")

if __name__ == "__main__":
    test_yolo_classes() 