#!/usr/bin/env python3
"""
Enhanced compilation script for Real-time Voice Translator
Allows user to choose between optimized and full builds
Shows compilation time and file sizes
"""

import subprocess
import time
import os
import sys
from datetime import datetime

def print_banner():
    print("=" * 70)
    print("    Real-time Voice Translator - Smart Compilation Tool")
    print("=" * 70)

def get_file_size_mb(filepath):
    """Get file size in MB"""
    if os.path.exists(filepath):
        size_bytes = os.path.getsize(filepath)
        return size_bytes / (1024 * 1024)
    return 0

def check_icon_files():
    """Check if icon files exist and create them if needed"""
    icon_ico_exists = os.path.exists("icon.ico")
    icon_png_exists = os.path.exists("icon.png")
    
    if not icon_ico_exists and not icon_png_exists:
        print("⚠️  No icon files found. Creating default icon files...")
        # Create a simple default icon placeholder
        with open("icon.ico", "w") as f:
            f.write("")  # Placeholder - PyInstaller will use default
        with open("icon.png", "w") as f:
            f.write("")  # Placeholder
        return False
    
    return icon_ico_exists or icon_png_exists

def get_build_choice():
    """Get user's choice for build type"""
    print("🔧 BUILD TYPE SELECTION")
    print("-" * 30)
    print("1. 🚀 OPTIMIZED BUILD (Recommended)")
    print("   • File size: ~45 MB")
    print("   • Compile time: ~3 minutes")
    print("   • Excludes heavy ML libraries")
    print("   • All core features included")
    print()
    print("2. 📦 FULL BUILD")
    print("   • File size: ~690 MB")
    print("   • Compile time: ~15-20 minutes")
    print("   • Includes all dependencies")
    print("   • Complete feature set")
    print()
    
    while True:
        choice = input("Choose build type (1 for Optimized, 2 for Full) [1]: ").strip()
        if choice == "" or choice == "1":
            return "optimized"
        elif choice == "2":
            return "full"
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

def run_compilation():
    print_banner()
    
    # Check icon files
    has_icons = check_icon_files()
    if has_icons:
        print("✅ Icon files found - executable will have custom icon")
    else:
        print("ℹ️  Using default icon (add icon.ico/icon.png for custom icon)")
    print()
    
    # Get user's build choice
    build_type = get_build_choice()
    
    # Record start time
    start_time = time.time()
    start_datetime = datetime.now()
    
    print()
    print("=" * 70)
    print(f"🕐 Compilation started at: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if build_type == "optimized":
        print("🔧 Using OPTIMIZED build configuration...")
        print("📦 Excluding heavy dependencies (matplotlib, scipy, torch, etc.)")
        print("⚡ Enabling UPX compression and debug symbol stripping")
        spec_file = "optimized_translator.spec"
        exe_name = "RealTimeVoiceTranslator_Optimized.exe"
        expected_size = 45
    else:
        print("🔧 Using FULL build configuration...")
        print("📦 Including all available dependencies")
        print("⚡ Enabling UPX compression")
        spec_file = "full_translator.spec"
        exe_name = "RealTimeVoiceTranslator_Full.exe"
        expected_size = 690
    
    print()
    
    try:
        # Clean previous builds
        print("🧹 Cleaning previous builds...")
        if os.path.exists("build"):
            subprocess.run(["rmdir", "/s", "/q", "build"], shell=True, check=False)
        if os.path.exists("dist"):
            subprocess.run(["rmdir", "/s", "/q", "dist"], shell=True, check=False)
        
        # Run PyInstaller with selected spec
        print("🚀 Starting PyInstaller compilation...")
        print("   (This may take a few minutes for optimized, longer for full build...)")
        print()
        
        result = subprocess.run([
            "pyinstaller", 
            spec_file,
            "--clean",
            "--noconfirm"
        ], capture_output=True, text=True)
        
        # Record end time
        end_time = time.time()
        end_datetime = datetime.now()
        compilation_time = end_time - start_time
        
        print("=" * 70)
        print("📊 COMPILATION RESULTS")
        print("=" * 70)
        print(f"🔧 Build type:      {build_type.upper()}")
        print(f"🕐 Start time:      {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🕑 End time:        {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Total time:      {compilation_time:.1f} seconds ({compilation_time/60:.1f} minutes)")
        
        if result.returncode == 0:
            print("✅ Compilation: SUCCESS")
            
            # Check file sizes
            exe_path = f"dist/{exe_name}"
            if os.path.exists(exe_path):
                file_size = get_file_size_mb(exe_path)
                print(f"📦 File size:       {file_size:.1f} MB")
                print(f"📁 Location:        {os.path.abspath(exe_path)}")
                
                # Size comparison for optimized build
                if build_type == "optimized":
                    original_size = 691  # MB from full build
                    reduction = ((original_size - file_size) / original_size) * 100
                    print(f"📉 Size reduction:  {reduction:.1f}% smaller than full build")
                else:
                    print(f"📊 Full build:      Complete with all dependencies")
                
                # Performance indicator
                if file_size < expected_size * 1.2:  # Within 20% of expected
                    print("🎯 Size target:     ✅ Within expected range")
                else:
                    print("⚠️  Size target:     Larger than expected (check dependencies)")
            
            print()
            if build_type == "optimized":
                print("🎉 Your optimized executable is ready!")
                print("   • Fast compilation ✅")
                print("   • Small file size ✅") 
                print("   • All core features ✅")
            else:
                print("🎉 Your full-featured executable is ready!")
                print("   • Complete feature set ✅")
                print("   • All dependencies included ✅")
            
            print("   You can now distribute the 'dist' folder to users.")
            
        else:
            print("❌ Compilation: FAILED")
            print("Error output:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Compilation failed with error: {e}")
        return False
    
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = run_compilation()
    if success:
        print("\n✨ Compilation completed successfully!")
        try:
            input("Press Enter to exit...")
        except (EOFError, KeyboardInterrupt):
            pass
    else:
        print("\n💥 Compilation failed. Check the error messages above.")
        try:
            input("Press Enter to exit...")
        except (EOFError, KeyboardInterrupt):
            pass
        sys.exit(1)