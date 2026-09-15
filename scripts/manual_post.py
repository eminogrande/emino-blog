#!/usr/bin/env python3
'''
Manual blog post creator
Usage: python3 manual_post.py "Title" "Content"
'''
import sys
import os
from datetime import datetime
import re

def create_blog_post(title, content):
    # Sanitize title for filename
    safe_title = re.sub(r'[^a-zA-Z0-9-]', '-', title.lower())
    safe_title = re.sub(r'-+', '-', safe_title).strip('-')
    
    # Create filename with date
    date_str = datetime.now().strftime('%Y-%m-%d')
    filename = f'{date_str}-{safe_title}.md'
    filepath = f'/var/www/emino-blog/content/posts/{filename}'
    
    # Create frontmatter
    frontmatter = f'''---
title: "{title}"
date: {datetime.now().isoformat()}
draft: false
tags: ["email-post", "blog"]
author: "Emin"
---

'''
    
    # Write post
    with open(filepath, 'w') as f:
        f.write(frontmatter)
        f.write(content)
    
    print(f'✅ Blog post created: {filename}')
    
    # Rebuild Hugo site
    os.chdir('/var/www/emino-blog')
    os.system('hugo --minify')
    print('✅ Site rebuilt')
    
    return filepath

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python3 manual_post.py "Title" "Content"')
        sys.exit(1)
    
    title = sys.argv[1]
    content = ' '.join(sys.argv[2:])
    create_blog_post(title, content)
