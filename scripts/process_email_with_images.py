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

# Email configuration
IMAP_SERVER = 'localhost'
EMAIL_ADDRESS = 'post@emino.app'
EMAIL_PASSWORD = 'Kilimanjaro##8'

# Blog configuration
BLOG_DIR = '/var/www/emino-blog'
CONTENT_DIR = f'{BLOG_DIR}/content/posts'
MEDIA_DIR = f'{BLOG_DIR}/static/media'

# Image settings
MAX_WIDTH = 1920
MAX_HEIGHT = 1080
JPEG_QUALITY = 85

# Authorization file
AUTH_FILE = f'{BLOG_DIR}/scripts/email_auth.txt'

def get_authorized_senders():
    """Load authorized email addresses from file"""
    if not os.path.exists(AUTH_FILE):
        return ['emin@nuri.com', 'emin@emin.de', 'eminhenri@gmail.com']
    
    with open(AUTH_FILE, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def resize_image(image_data, filename):
    """Resize image for web if needed"""
    try:
        img = Image.open(io.BytesIO(image_data))
        
        # Convert RGBA to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                rgb_img.paste(img, mask=img.split()[3])
            else:
                rgb_img.paste(img)
            img = rgb_img
        
        # Resize if too large
        if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
            img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)
            print(f'Resized {filename} to {img.width}x{img.height}')
        
        # Save to bytes
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f'Error resizing image {filename}: {e}')
        return image_data

def extract_emails_from_mailbox():
    """Extract emails from /var/mail/post file"""
    emails = []
    
    try:
        with open('/var/mail/post', 'rb') as f:
            raw_content = f.read()
        
        if not raw_content:
            return emails
        
        # Split by 'From ' at start of line (mbox format)
        parts = raw_content.split(b'\nFrom ')
        
        for i, part in enumerate(parts):
            if i > 0:
                part = b'From ' + part
            
            try:
                msg = email.message_from_bytes(part)
                emails.append(msg)
            except:
                continue
    except Exception as e:
        print(f'Error reading mailbox: {e}')
    
    return emails

def process_email_message(msg):
    """Process a single email message"""
    # Get sender
    from_header = msg.get('From', '')
    sender_match = re.search(r'<(.+?)>', from_header)
    sender = sender_match.group(1) if sender_match else from_header
    sender = sender.lower().strip()
    
    # Get subject
    subject = msg.get('Subject', 'Untitled')
    if decode_header(subject)[0][1]:
        subject = decode_header(subject)[0][0].decode(decode_header(subject)[0][1])
    
    # Remove 'BLOG:' prefix if present
    if subject.upper().startswith('BLOG:'):
        subject = subject[5:].strip()
    
    content = ''
    images = []
    
    # Process multipart message
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition', ''))
            
            # Handle text content
            if content_type == 'text/plain' and 'attachment' not in content_disposition:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        text = payload.decode('utf-8', errors='ignore')
                        content += text
                except Exception as e:
                    print(f'Error processing text: {e}')
            
            # Handle image attachments
            elif content_type.startswith('image/'):
                filename = part.get_filename()
                if filename:
                    # Decode filename if needed
                    if decode_header(filename)[0][1]:
                        filename = decode_header(filename)[0][0].decode(decode_header(filename)[0][1])
                    
                    # Clean filename
                    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
                    
                    # Get image data
                    image_data = part.get_payload(decode=True)
                    if image_data:
                        images.append({
                            'filename': filename,
                            'data': image_data
                        })
    else:
        # Simple message
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                content = payload.decode('utf-8', errors='ignore')
        except:
            pass
    
    return {
        'sender': sender,
        'subject': subject,
        'content': content.strip(),
        'images': images
    }

def create_blog_post(email_data):
    """Create a blog post from email data"""
    # Generate slug
    slug = re.sub(r'[^a-z0-9-]', '-', email_data['subject'].lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    
    # Create media directory for this post
    if email_data['images']:
        post_media_dir = f'{MEDIA_DIR}/{slug}'
        os.makedirs(post_media_dir, exist_ok=True)
    
    # Process and save images
    image_markdown = []
    for img in email_data['images']:
        try:
            # Resize image
            resized_data = resize_image(img['data'], img['filename'])
            
            # Save image
            img_path = f'{MEDIA_DIR}/{slug}/{img["filename"]}'
            with open(img_path, 'wb') as f:
                f.write(resized_data)
            
            # Create markdown reference
            web_path = f'/media/{slug}/{img["filename"]}'
            image_markdown.append(f'![{img["filename"]}]({web_path})')
            print(f'Saved image: {img_path}')
        except Exception as e:
            print(f'Error saving image {img["filename"]}: {e}')
    
    # Build post content
    post_content = f'''+++
title = "{email_data['subject']}"
date = {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}Z
draft = false
author = "Emino"
tags = ["email-post"]
categories = ["blog"]
+++

{email_data['content']}
'''
    
    # Add images to post
    if image_markdown:
        post_content += '\n\n' + '\n\n'.join(image_markdown)
    
    post_content += f'''

---
*This post was created via email by {email_data['sender']}*
'''
    
    # Save post
    filename = f'{CONTENT_DIR}/{slug}.md'
    with open(filename, 'w') as f:
        f.write(post_content)
    
    print(f'Created post: {filename}')
    return filename

def main():
    print(f'Checking emails at {datetime.now()}')
    
    authorized_senders = get_authorized_senders()
    print(f'Authorized senders: {authorized_senders}')
    
    # Get emails from mailbox
    emails = extract_emails_from_mailbox()
    print(f'Found {len(emails)} emails in mailbox')
    
    processed_count = 0
    
    for msg in emails:
        try:
            email_data = process_email_message(msg)
            
            # Check authorization
            if email_data['sender'] not in authorized_senders:
                print(f'Skipping unauthorized sender: {email_data["sender"]}')
                continue
            
            # Skip if no content
            if not email_data['content']:
                print(f'Skipping email with no content: {email_data["subject"]}')
                continue
            
            print(f'Processing: {email_data["subject"]} from {email_data["sender"]} with {len(email_data["images"])} images')
            
            # Create blog post
            create_blog_post(email_data)
            processed_count += 1
            
        except Exception as e:
            print(f'Error processing email: {e}')
            import traceback
            traceback.print_exc()
    
    if processed_count > 0:
        # Rebuild site
        print('Rebuilding site...')
        os.chdir(BLOG_DIR)
        subprocess.run(['./build.sh'], check=True)
        print('Site rebuilt!')
        
        # Sync to GitHub
        try:
            print('Syncing to GitHub...')
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', f'Added {processed_count} new post(s) via email with images'], check=True)
            subprocess.run(['git', 'push'], check=True)
            print('GitHub sync complete!')
        except Exception as e:
            print(f'GitHub sync failed: {e}')
        
        # Clear mailbox
        with open('/var/mail/post', 'w') as f:
            f.write('')
        print(f'Processed {processed_count} emails and cleared mailbox')
    else:
        print('No authorized emails to process')

if __name__ == '__main__':
    main()
