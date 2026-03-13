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
from PIL import Image, ImageOps
import io
from html.parser import HTMLParser

# Blog configuration
BLOG_DIR = '/var/www/emino-blog'
CONTENT_DIR = f'{BLOG_DIR}/content/posts'
MEDIA_DIR = f'{BLOG_DIR}/static/media'
AUTH_FILE = f'{BLOG_DIR}/scripts/email_auth.txt'

# Image settings
MAX_WIDTH = 1920
MAX_HEIGHT = 1080
JPEG_QUALITY = 85

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
        return ['emin@nuri.com', 'emin@emin.de', 'eminhenri@gmail.com', 'proud@me.com', 'proud@me.com']
    with open(AUTH_FILE, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def extract_email_address(from_header):
    """Extract email address from From header"""
    match = re.search(r'<([^>]+)>', from_header)
    if match:
        return match.group(1).lower()
    return from_header.lower().strip()

def resize_image(image_data, filename):
    try:
        img = Image.open(io.BytesIO(image_data))
        
        # Handle EXIF orientation
        try:
            img = ImageOps.exif_transpose(img)
        except:
            pass
        
        # Convert RGBA to RGB
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                rgb_img.paste(img, mask=img.split()[3])
            else:
                rgb_img.paste(img)
            img = rgb_img
        
        # Resize if needed
        if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
            img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f'Error resizing {filename}: {e}')
        return image_data

def process_email_message(msg):
    """Process email message and extract content"""
    from_header = msg.get('From', '')
    sender = extract_email_address(from_header)
    
    subject = msg.get('Subject', 'Untitled')
    if subject:
        decoded = decode_header(subject)
        parts = []
        for text, encoding in decoded:
            if isinstance(text, bytes):
                text = text.decode(encoding or 'utf-8', errors='ignore')
            parts.append(text)
        subject = ''.join(parts)
    
    content = ''
    images = []
    media = []  # audio/video attachments
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition', ''))
            
            if content_type == 'text/plain' and 'attachment' not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    text = payload.decode('utf-8', errors='ignore')
                    content = text.strip()
            
            elif content_type == 'text/html' and not content and 'attachment' not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    html = payload.decode('utf-8', errors='ignore')
                    parser = HTMLTextExtractor()
                    parser.feed(html)
                    content = parser.get_text()
            

            elif content_type.startswith('audio/') or content_type.startswith('video/'):
                payload = part.get_payload(decode=True)
                if payload:
                    filename = part.get_filename()
                    if filename:
                        decoded = decode_header(filename)
                        parts = []
                        for text, encoding in decoded:
                            if isinstance(text, bytes):
                                text = text.decode(encoding or 'utf-8', errors='ignore')
                            parts.append(text)
                        filename = ''.join(parts)
                        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
                    else:
                        ext = content_type.split('/')[-1]
                        prefix = 'audio' if content_type.startswith('audio/') else 'video'
                        filename = f'{prefix}_{len(media)+1}.{ext}'

                    media.append({'filename': filename, 'data': payload, 'content_type': content_type})

            elif content_type.startswith('image/'):
                payload = part.get_payload(decode=True)
                if payload:
                    filename = part.get_filename()
                    if filename:
                        decoded = decode_header(filename)
                        parts = []
                        for text, encoding in decoded:
                            if isinstance(text, bytes):
                                text = text.decode(encoding or 'utf-8', errors='ignore')
                            parts.append(text)
                        filename = ''.join(parts)
                        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
                    else:
                        ext = content_type.split('/')[-1]
                        filename = f'image_{len(images)+1}.{ext}'
                    
                    images.append({'filename': filename, 'data': payload})
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            content = payload.decode('utf-8', errors='ignore').strip()
    
    return {
        'sender': sender,
        'subject': subject,
        'content': content,
        'images': images,
        'media': media
    }

def create_blog_post(email_data):
    """Create blog post from email data"""
    subject = email_data['subject']
    slug = re.sub(r'[^a-z0-9-]', '', subject.lower().replace(' ', '-'))[:50]
    if not slug:
        slug = f"email-post-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Create media directory if needed
    if email_data['images']:
        media_path = f"{MEDIA_DIR}/{slug}"
        os.makedirs(media_path, exist_ok=True)
        
        image_markdown = []
        for i, img in enumerate(email_data['images']):
            try:
                filename = img['filename']
                if not filename:
                    filename = f'image_{i+1}.jpg'
                
                resized_data = resize_image(img['data'], filename)
                img_path = f'{media_path}/{filename}'
                
                with open(img_path, 'wb') as f:
                    f.write(resized_data)
                
                web_path = f'/media/{slug}/{filename}'
                alt_text = filename.replace('_', ' ').replace('.jpg', '').replace('.png', '')
                image_markdown.append(f'![{alt_text}]({web_path})')
                print(f'Saved image: {img_path}')
            except Exception as e:
                print(f'Error saving image: {e}')
    else:
        image_markdown = []


    # Save audio/video attachments
    media_markdown = []
    if email_data.get('media'):
        media_path = f"{MEDIA_DIR}/{slug}"
        os.makedirs(media_path, exist_ok=True)

        for m in email_data['media']:
            try:
                filename = m.get('filename') or f"media_{len(media_markdown)+1}"
                data = m.get('data')
                ctype = (m.get('content_type') or '').lower()
                out_path = f"{media_path}/{filename}"

                with open(out_path, 'wb') as f:
                    f.write(data)

                web_path = f"/media/{slug}/{filename}"

                if ctype.startswith('video/') or filename.lower().endswith(('.mp4','.mov','.webm')):
                    media_markdown.append(
                        f"<video controls playsinline preload=\"metadata\" style=\"max-width:100%;height:auto\">\n"
                        f"  <source src=\"{web_path}\" type=\"video/mp4\" />\n"
                        f"</video>"
                    )
                elif ctype.startswith('audio/') or filename.lower().endswith(('.m4a','.mp3','.wav','.ogg')):
                    media_markdown.append(
                        f"<audio controls preload=\"metadata\" style=\"width:100%\">\n"
                        f"  <source src=\"{web_path}\" type=\"audio/mp4\" />\n"
                        f"</audio>"
                    )
                else:
                    media_markdown.append(f"[{filename}]({web_path})")

                print(f"Saved media: {out_path}")
            except Exception as e:
                print(f"Error saving media: {e}")

    
    # Build post content
    post_content = f'''+++
title = "{email_data['subject']}"
date = {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}Z
draft = false
author = "Emin"
tags = ["email-post"]
categories = ["blog"]
+++

{email_data['content'] if email_data['content'] else ''}'''
    
    if image_markdown:
        if email_data['content']:
            post_content += '\n\n'
        post_content += '\n\n'.join(image_markdown)

    if media_markdown:
        post_content += '\n\n'
        post_content += '\n\n'.join(media_markdown)
    
    post_content += f'''

---
*This post was created via email by {email_data['sender']}*
'''
    
    # Save post
    filename = f'{CONTENT_DIR}/{slug}.md'
    with open(filename, 'w') as f:
        f.write(post_content)
    
    print(f'Created blog post: {filename}')
    return True

def check_mailbox_file():
    """Check /var/mail/post for new emails"""
    mailbox_path = '/var/mail/post'
    if not os.path.exists(mailbox_path):
        return None
    
    with open(mailbox_path, 'rb') as f:
        content = f.read()
    
    if not content:
        return None
    
    return content

def check_imap_mailbox():
    """Check IMAP mailbox for new emails"""
    try:
        # Try plain authentication first
        mail = imaplib.IMAP4('localhost', 143)
        mail.login('post', 'Kilimanjaro##8')
        mail.select('INBOX')
        
        result, data = mail.search(None, 'ALL')
        if result != 'OK':
            return None
        
        email_ids = data[0].split()
        if not email_ids:
            mail.logout()
            return None
        
        # Get first email
        result, data = mail.fetch(email_ids[0], '(RFC822)')
        if result != 'OK':
            mail.logout()
            return None
        
        raw_email = data[0][1]
        
        # Delete the email after fetching
        mail.store(email_ids[0], '+FLAGS', '\\Deleted')
        # mail.expunge()  # DISABLED - Keep emails for tracking
        mail.logout()
        
        return raw_email
    except Exception as e:
        print(f'IMAP check failed: {e}')
        return None

def main():
    print(f'\n=== Email Check at {datetime.now()} ===')
    
    authorized = get_authorized_senders()
    print(f'Authorized senders: {authorized}')
    
    # Try mailbox file first
    raw_content = check_mailbox_file()
    source = 'mailbox file'
    
    # If no mail in file, try IMAP
    if not raw_content:
        raw_content = check_imap_mailbox()
        source = 'IMAP'
    
    if not raw_content:
        print('No emails to process')
        return
    
    print(f'Found email from {source}')
    
    try:
        msg = email.message_from_bytes(raw_content)
        email_data = process_email_message(msg)
        
        print(f"Email from: {email_data['sender']}")
        print(f"Subject: {email_data['subject']}")
        
        if email_data['sender'] not in authorized:
            print(f'REJECTED: Unauthorized sender')
            # Clear mailbox if from file
            if source == 'mailbox file':
                with open('/var/mail/post', 'w') as f:
                    f.write('')
            return
        
        if email_data['content'] or email_data['images']:
            if create_blog_post(email_data):
                # Rebuild site
                print('Rebuilding Hugo site...')
                os.chdir(BLOG_DIR)
                subprocess.run(['hugo', '--cleanDestinationDir'], check=True)
                subprocess.run(['rsync', '-av', '--delete', 'public/', '/var/www/emino.app/'], check=True)
                
                # Clear mailbox
                if source == 'mailbox file':
                    with open('/var/mail/post', 'w') as f:
                        f.write('')
                
                # Git operations
                try:
                    subprocess.run(['git', 'add', '.'], check=True)
                    subprocess.run(['git', 'commit', '-m', f'New post: {email_data["subject"]}'], check=True)
                    print('Ready to push to GitHub (needs auth configuration)')
                except:
                    pass
                
                print('EMAIL SUCCESSFULLY PROCESSED!')
    except Exception as e:
        print(f'Error processing email: {e}')

if __name__ == '__main__':
    main()
