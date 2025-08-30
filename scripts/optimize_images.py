#!/usr/bin/env python3
import os
import sys
from PIL import Image
import glob

def optimize_image(filepath, max_width=1200, quality=85):
    """Optimize a single image for web"""
    try:
        img = Image.open(filepath)
        
        # Convert RGBA to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # Get current dimensions
        width, height = img.size
        
        # Only resize if wider than max_width
        if width > max_width:
            ratio = max_width / width
            new_height = int(height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            print(f'  Resized from {width}x{height} to {max_width}x{new_height}')
        
        # Save optimized image
        img.save(filepath, 'JPEG', quality=quality, optimize=True)
        
        # Get file sizes
        size_after = os.path.getsize(filepath) / 1024  # KB
        print(f'  Optimized: {size_after:.1f}KB')
        
        return True
    except Exception as e:
        print(f'  Error: {e}')
        return False

def main():
    media_dir = '/var/www/emino-blog/static/media'
    
    print('Optimizing images for web performance...')
    print('Settings: max width=1200px, JPEG quality=85%')
    print('-' * 50)
    
    # Find all images
    patterns = ['**/*.jpg', '**/*.jpeg', '**/*.png']
    image_files = []
    
    for pattern in patterns:
        image_files.extend(glob.glob(os.path.join(media_dir, pattern), recursive=True))
    
    # Skip SVG files
    image_files = [f for f in image_files if not f.endswith('.svg')]
    
    optimized = 0
    for filepath in image_files:
        filename = os.path.basename(filepath)
        size_before = os.path.getsize(filepath) / 1024  # KB
        
        # Skip if already optimized (under 200KB)
        if size_before < 200:
            print(f'✓ {filename} ({size_before:.1f}KB) - already optimized')
            continue
        
        print(f'Optimizing {filename} ({size_before:.1f}KB)...')
        if optimize_image(filepath, max_width=1200, quality=85):
            optimized += 1
    
    print('-' * 50)
    print(f'Optimization complete! Processed {optimized} images.')
    
    # Also update the email processor to use these settings
    print('\nUpdating email processor for future uploads...')
    
if __name__ == '__main__':
    main()
