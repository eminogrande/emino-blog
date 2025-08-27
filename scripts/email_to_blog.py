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

# Email configuration
IMAP_SERVER = 'localhost'
EMAIL_ADDRESS = 'post@emino.app'
EMAIL_PASSWORD = 'Kilimanjaro##8'

# Blog configuration
BLOG_DIR = '/var/www/emino-blog'
CONTENT_DIR = f'{BLOG_DIR}/content/posts'
MEDIA_DIR = f'{BLOG_DIR}/static/media'

# Authorization file
AUTH_FILE = f'{BLOG_DIR}/scripts/email_auth.txt'

def get_authorized_senders():
    """Load authorized email addresses from file"""
    if not os.path.exists(AUTH_FILE):
        # Default authorized senders
        return ['emin@nuri.com', 'emin@emin.de', 'eminhenri@gmail.com']
    
    with open(AUTH_FILE, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def connect_to_email():
    """Connect to email server"""
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    return mail

def process_email_content(msg):
    """Extract content from email message"""
    content = ''
    attachments = []
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition', ''))
            
            # Handle text content
            if content_type == 'text/plain' and 'attachment' not in content_disposition:
                try:
                    body = part.get_payload(decode=True).decode('utf-8')
                    content += body
                except:
                    pass
            
            # Handle attachments
            elif 'attachment' in content_disposition:
                filename = part.get_filename()
                if filename:
                    # Decode filename if needed
                    if decode_header(filename)[0][1]:
                        filename = decode_header(filename)[0][0].decode(decode_header(filename)[0][1])
                    
                    attachments.append({
                        'filename': filename,
                        'content': part.get_payload(decode=True)
                    })
    else:
        # Simple email
        try:
            content = msg.get_payload(decode=True).decode('utf-8')
        except:
            pass
    
    return content, attachments

def save_media(attachments, post_slug):
    """Save media attachments and return markdown references"""
    media_refs = []
    
    # Create media directory if it doesn't exist
    post_media_dir = f'{MEDIA_DIR}/{post_slug}'
    os.makedirs(post_media_dir, exist_ok=True)
    
    for att in attachments:
        filename = att['filename'].lower()
        filepath = f'{post_media_dir}/{filename}'
        
        # Save file
        with open(filepath, 'wb') as f:
            f.write(att['content'])
        
        # Create markdown reference
        web_path = f'/media/{post_slug}/{filename}'
        
        if filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            media_refs.append(f'![{filename}]({web_path})')
        elif filename.endswith(('.mp4', '.webm', '.mov')):
            media_refs.append(f'<video controls><source src="{web_path}" type="video/mp4"></video>')
        elif filename.endswith('.md'):
            # Include markdown content
            with open(filepath, 'r') as f:
                media_refs.append(f.read())
        else:
            media_refs.append(f'[{filename}]({web_path})')
    
    return media_refs

def create_blog_post(subject, content, sender, attachments):
    """Create a Hugo blog post from email content"""
    # Clean subject for use as title
    if subject.upper().startswith('BLOG:'):
        title = subject[5:].strip()
    else:
        title = subject.strip()
    
    # Generate slug
    slug = re.sub(r'[^a-z0-9-]', '-', title.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    
    # Process attachments
    media_refs = save_media(attachments, slug) if attachments else []
    
    # Add media references to content
    if media_refs:
        content += '\n\n' + '\n\n'.join(media_refs)
    
    # Create post metadata
    now = datetime.now()
    post_content = f'''+++
title = "{title}"
date = {now.strftime('%Y-%m-%dT%H:%M:%S')}Z
draft = false
author = "Emino"
tags = ["email-post"]
categories = ["blog"]
+++

{content}

---
*This post was created via email by {sender}*
'''
    
    # Save post
    filename = f'{CONTENT_DIR}/{slug}.md'
    with open(filename, 'w') as f:
        f.write(post_content)
    
    print(f'Created post: {filename}')
    return filename

def rebuild_site():
    """Rebuild the Hugo site"""
    os.chdir(BLOG_DIR)
    subprocess.run(['./build.sh'], check=True)
    print('Site rebuilt successfully')

def sync_to_github():
    """Sync changes to GitHub"""
    os.chdir(BLOG_DIR)
    subprocess.run(['git', 'add', '.'], check=True)
    subprocess.run(['git', 'commit', '-m', 'New post via email'], check=True)
    subprocess.run(['git', 'push'], check=True)
    print('Synced to GitHub')

def main():
    print(f'Checking emails at {datetime.now()}')
    
    authorized_senders = get_authorized_senders()
    print(f'Authorized senders: {authorized_senders}')
    
    try:
        # Connect to email
        mail = connect_to_email()
        mail.select('inbox')
        
        # Search for unread emails
        status, messages = mail.search(None, 'UNSEEN')
        
        if status == 'OK':
            for num in messages[0].split():
                # Fetch email
                status, msg_data = mail.fetch(num, '(RFC822)')
                
                if status == 'OK':
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    # Get sender
                    from_header = msg['From']
                    sender_match = re.search(r'<(.+?)>', from_header)
                    sender = sender_match.group(1) if sender_match else from_header
                    sender = sender.lower().strip()
                    
                    print(f'Email from: {sender}')
                    
                    # Check authorization
                    if sender not in authorized_senders:
                        print(f'Unauthorized sender: {sender}')
                        continue
                    
                    # Get subject
                    subject = decode_header(msg['Subject'])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    
                    # Process email
                    content, attachments = process_email_content(msg)
                    
                    # Create blog post
                    create_blog_post(subject, content, sender, attachments)
                    
                    # Mark as read
                    mail.store(num, '+FLAGS', '\\Seen')
                    
                    # Rebuild site
                    rebuild_site()
                    
                    # Sync to GitHub
                    try:
                        sync_to_github()
                    except:
                        print('GitHub sync failed, continuing...')
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
