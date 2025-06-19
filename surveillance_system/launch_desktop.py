#!/usr/bin/env python3
"""
Desktop Surveillance Launcher
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

try:
    from desktop_surveillance import main
    print("🚀 Launching Desktop Surveillance System...")
    main()
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install opencv-python pillow ultralytics torch")
except Exception as e:
    print(f"❌ Error: {e}")
    input("Press Enter to exit...") 