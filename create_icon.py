#!/usr/bin/env python3
"""
Simple icon creator for the Real-time Voice Translator
Creates a basic icon if none exists
"""

import os
from PIL import Image, ImageDraw, ImageFont
import sys

def create_default_icon():
    """Create a simple default icon"""
    try:
        # Create a 256x256 image with a gradient background
        size = 256
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Create gradient background
        for i in range(size):
            color = int(255 * (1 - i / size))
            draw.line([(0, i), (size, i)], fill=(74, 158, 255, 255))
        
        # Draw a microphone icon
        # Microphone body
        mic_width = 60
        mic_height = 80
        mic_x = (size - mic_width) // 2
        mic_y = 60
        
        draw.rounded_rectangle(
            [mic_x, mic_y, mic_x + mic_width, mic_y + mic_height],
            radius=30,
            fill=(255, 255, 255, 255),
            outline=(0, 0, 0, 100),
            width=3
        )
        
        # Microphone stand
        stand_width = 4
        stand_height = 40
        stand_x = (size - stand_width) // 2
        stand_y = mic_y + mic_height
        
        draw.rectangle(
            [stand_x, stand_y, stand_x + stand_width, stand_y + stand_height],
            fill=(100, 100, 100, 255)
        )
        
        # Base
        base_width = 40
        base_height = 8
        base_x = (size - base_width) // 2
        base_y = stand_y + stand_height
        
        draw.rounded_rectangle(
            [base_x, base_y, base_x + base_width, base_y + base_height],
            radius=4,
            fill=(100, 100, 100, 255)
        )
        
        # Add translation symbol (globe)
        globe_size = 30
        globe_x = mic_x + mic_width + 10
        globe_y = mic_y + 10
        
        draw.ellipse(
            [globe_x, globe_y, globe_x + globe_size, globe_y + globe_size],
            outline=(255, 255, 255, 200),
            width=3
        )
        
        # Globe lines
        draw.line(
            [(globe_x + globe_size//2, globe_y), (globe_x + globe_size//2, globe_y + globe_size)],
            fill=(255, 255, 255, 200),
            width=2
        )
        draw.line(
            [(globe_x, globe_y + globe_size//2), (globe_x + globe_size, globe_y + globe_size//2)],
            fill=(255, 255, 255, 200),
            width=2
        )
        
        # Save as PNG
        img.save('icon.png', 'PNG')
        
        # Convert to ICO (multiple sizes)
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save('icon.ico', format='ICO', sizes=icon_sizes)
        
        return True
        
    except ImportError:
        print("⚠️  PIL (Pillow) not installed. Creating placeholder icon files...")
        # Create empty placeholder files
        with open('icon.png', 'w') as f:
            f.write('')
        with open('icon.ico', 'w') as f:
            f.write('')
        return False
    except Exception as e:
        print(f"❌ Error creating icon: {e}")
        return False

def main():
    print("🎨 Icon Creator for Real-time Voice Translator")
    print("=" * 50)
    
    # Check if icons already exist
    has_png = os.path.exists('icon.png')
    has_ico = os.path.exists('icon.ico')
    
    if has_png and has_ico:
        print("✅ Icon files already exist:")
        print(f"   • icon.png ({os.path.getsize('icon.png')} bytes)")
        print(f"   • icon.ico ({os.path.getsize('icon.ico')} bytes)")
        
        choice = input("\nOverwrite existing icons? (y/N): ").strip().lower()
        if choice != 'y':
            print("🚫 Keeping existing icons.")
            return
    
    print("🔨 Creating default microphone/translation icon...")
    
    success = create_default_icon()
    
    if success:
        print("✅ Icon files created successfully!")
        print("   • icon.png - High quality PNG version")
        print("   • icon.ico - Windows ICO format (multiple sizes)")
        print("\n💡 Tip: You can replace these with your own custom icons")
        print("   (keep the same filenames: icon.png and icon.ico)")
    else:
        print("⚠️  Basic placeholder files created.")
        print("   Add your own icon.png and icon.ico files for custom icons.")
    
    print("\n🚀 Ready for compilation! Run compile_fast.bat or python compile_optimized.py")

if __name__ == "__main__":
    main()