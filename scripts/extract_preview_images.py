#!/usr/bin/env python3
import os
import re
import glob

posts_dir = 'content/posts'

for post_file in glob.glob(f'{posts_dir}/*.md'):
    with open(post_file, 'r') as f:
        content = f.read()
    
    # Find first image in content
    image_match = re.search(r'!\[.*?\]\((/[^)]+)\)', content)
    
    if image_match:
        image_path = image_match.group(1)
        
        # Check if front matter already has image
        if 'image =' not in content and 'images =' not in content:
            # Add image to front matter
            content = re.sub(
                r'(\+\+\+.*?)(\n\+\+\+)',
                r'\1\nimage = "' + image_path + r'"\2',
                content,
                flags=re.DOTALL
            )
            
            with open(post_file, 'w') as f:
                f.write(content)
            
            print(f'Added preview image to {os.path.basename(post_file)}: {image_path}')

