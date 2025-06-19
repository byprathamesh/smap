#!/usr/bin/env python3
"""
WatchHer - Main Launcher Script
Easy entry point for the WatchHer surveillance system
"""

import sys
import os
import argparse

def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(description="WatchHer - Intelligent Public Safety Monitoring System")
    parser.add_argument('--app', '-a', 
                       choices=['watchher', 'standard'], 
                       default='watchher',
                       help='Choose application: watchher (full WatchHer app) or standard (basic surveillance)')
    parser.add_argument('--version', '-v', action='version', version='WatchHer v2.0')
    
    args = parser.parse_args()
    
    print("🚀 Starting WatchHer — Intelligent Public Safety Monitoring System")
    print("="*60)
    
    try:
        if args.app == 'watchher':
            print("🎯 Launching WatchHer Desktop Application...")
            from src.apps.watchher_desktop import main as watchher_main
            watchher_main()
        else:
            print("📱 Launching Standard Surveillance Application...")
            from src.apps.desktop_surveillance_fixed import main as standard_main
            standard_main()
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\n🔧 Please ensure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 