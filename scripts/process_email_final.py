#!/usr/bin/env python3
import imaplib
import email
from email.header import decode_header
import os
import re
from datetime import datetime
import subprocess
import base64
from pathlib import Path
from PIL import Image
import io
from html.parser import HTMLParser

# Email configuration
BLOG_DIR = '/var/www/emino-blog'
CONTENT_DIR = f'{BLOG_DIR}/content/posts'
MEDIA_DIR = f'{BLOG_DIR}/static/media'

# Image settings
MAX_WIDTH = 1920
MAX_HEIGHT = 1080
JPEG_QUALITY = 85

# Authorization
AUTH_FILE = f'{BLOG_DIR}/scripts/email_auth.txt'

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
    
    def handle_data(self, data):
        text = data.strip()
        if text:
            self.text.append(text)
    
    def get_text(self):
        return ' '.join(self.text)

def get_authorized_senders():
    if not os.path.exists(AUTH_FILE):
        return ['emin@nuri.com', 'emin@emin.de', 'eminhenri@gmail.com']
    with open(AUTH_FILE, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def resize_image(image_data, filename):
    try:
        img = Image.open(io.BytesIO(image_data))
        
        # Convert RGBA to RGB
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                rgb_img.paste(img, mask=img.split()[3])
            else:
                rgb_img.paste(img)
            img = rgb_img
        
        # Calculate new size maintaining aspect ratio
        if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
            img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)
            print(f'Resized {filename} to {img.width}x{img.height}')
        
        # Save optimized
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f'Error resizing {filename}: {e}')
        return image_data

def process_email_message(msg):
    # Get sender
    from_header = msg.get('From', '')
    sender_match = re.search(r'<(.+?)>', from_header)
    sender = sender_match.group(1) if sender_match else from_header
    sender = sender.lower().strip()
    
    # Get subject
    subject = msg.get('Subject', 'Untitled')
    try:
        decoded = decode_header(subject)
        if decoded[0][1]:
            subject = decoded[0][0].decode(decoded[0][1])
    except:
        pass
    
    if subject.upper().startswith('BLOG:'):
        subject = subject[5:].strip()
    
    content = ''
    images = []
    
    # Walk through message parts
    for part in msg.walk():
        content_type = part.get_content_type()
        
        # Extract text from plain text parts
        if content_type == 'text/plain':
            try:
                payload = part.get_payload(decode=True)
                if payload:
                    text = payload.decode('utf-8', errors='ignore').strip()
                    if text:
                        content = text
            except:
                pass
        
        # Extract text from HTML if no plain text
        elif content_type == 'text/html' and not content:
            try:
                payload = part.get_payload(decode=True)
                if payload:
                    html = payload.decode('utf-8', errors='ignore')
                    parser = HTMLTextExtractor()
                    parser.feed(html)
                    extracted = parser.get_text()
                    if extracted:
                        content = extracted
            except:
                pass
        
        # Extract images
        elif content_type.startswith('image/'):
            filename = part.get_filename()
            if not filename:
                # Generate filename based on content type
                ext = content_type.split('/')[-1]
                filename = f'image_{len(images)+1}.{ext}'
            
            # Decode filename if needed
            try:
                decoded = decode_header(filename)
                if decoded[0][1]:
                    filename = decoded[0][0].decode(decoded[0][1])
            except:
                pass
            
            # Clean filename
            filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                filename += '.jpg'
            
            image_data = part.get_payload(decode=True)
            if image_data:
                images.append({
                    'filename': filename,
                    'data': image_data
                })
                print(f'Found image: {filename} ({len(image_data)} bytes)')
    
    # If no content but has images, create minimal content
    if not content and images:
        content = f'[Image post]'
    
    return {
        'sender': sender,
        'subject': subject,
        'content': content.strip() if content else '',
        'images': images
    }

def create_blog_post(email_data):
    slug = re.sub(r'[^a-z0-9-]', '-', email_data['subject'].lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    
    # Create media directory
    if email_data['images']:
        post_media_dir = f'{MEDIA_DIR}/{slug}'
        os.makedirs(post_media_dir, exist_ok=True)
    
    # Process images
    image_markdown = []
    for i, img in enumerate(email_data['images']):
        try:
            # Ensure unique filename
            filename = img['filename']
            if not filename:
                filename = f'image_{i+1}.jpg'
            
            # Resize and save
            resized_data = resize_image(img['data'], filename)
            img_path = f'{MEDIA_DIR}/{slug}/{filename}'
            
            with open(img_path, 'wb') as f:
                f.write(resized_data)
            
            # Create markdown
            web_path = f'/media/{slug}/{filename}'
            alt_text = filename.replace('_', ' ').replace('.jpg', '').replace('.png', '')
            image_markdown.append(f'![{alt_text}]({web_path})')
            print(f'Saved image: {img_path}')
        except Exception as e:
            print(f'Error saving image: {e}')
    
    # Build post content
    post_content = f'''+++
title = "{email_data['subject']}"
date = {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}Z
draft = false
author = "Emino"
tags = ["email-post", "photos"]
categories = ["blog"]
+++

{email_data['content'] if email_data['content'] else ''}
'''
    
    if image_markdown:
        if email_data['content']:
            post_content += '\n\n'
        post_content += '\n\n'.join(image_markdown)
    
    post_content += f'''

---
*This post was created via email by {email_data['sender']}*
'''
    
    # Save post
    filename = f'{CONTENT_DIR}/{slug}.md'
    with open(filename, 'w') as f:
        f.write(post_content)
    
    print(f'Created post: {filename}')
    return True

def main():
    print(f'\nChecking emails at {datetime.now()}')
    
    authorized = get_authorized_senders()
    print(f'Authorized senders: {authorized}')
    
    # Read mailbox
    try:
        with open('/var/mail/post', 'rb') as f:
            raw_content = f.read()
    except:
        print('No mailbox file')
        return
    
    if not raw_content:
        print('Empty mailbox')
        return
    
    # Parse email
    try:
        msg = email.message_from_bytes(raw_content)
        email_data = process_email_message(msg)
        
        print(f"Email from: {email_data['sender']}")
        print(f"Subject: {email_data['subject']}")
        print(f"Content length: {len(email_data['content'])}")
        print(f"Images: {len(email_data['images'])}")
        
        # Check authorization
        if email_data['sender'] not in authorized:
            print(f'Unauthorized sender: {email_data["sender"]}')
            return
        
        # Process if has content or images
        if email_data['content'] or email_data['images']:
            if create_blog_post(email_data):
                # Rebuild site
                print('\nRebuilding site...')
                os.chdir(BLOG_DIR)
                subprocess.run(['./build.sh'], check=True)
                
                # Clear mailbox
                with open('/var/mail/post', 'w') as f:
                    f.write('')
                print('Mailbox cleared')
                
                # Try GitHub sync
                try:
                    subprocess.run(['git', 'add', '.'], check=True)
                    subprocess.run(['git', 'commit', '-m', f'New post: {email_data["subject"]}'], check=True)
                    subprocess.run(['git', 'push'], check=True)
                    print('GitHub sync complete')
                except:
                    print('GitHub sync failed')
        else:
            print('No content or images to process')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
