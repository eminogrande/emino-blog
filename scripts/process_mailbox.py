#!/usr/bin/env python3
import re
from datetime import datetime
import subprocess
import os
import base64

def extract_emails(mailbox_content):
    """Extract all emails from mailbox file"""
    emails = []
    current_email = []
    
    for line in mailbox_content.split('\n'):
        if line.startswith('From ') and current_email:
            emails.append('\n'.join(current_email))
            current_email = []
        current_email.append(line)
    
    if current_email:
        emails.append('\n'.join(current_email))
    
    return emails

def process_email(email_content):
    """Process a single email"""
    # Extract subject
    subject_match = re.search(r'^Subject: (.+)$', email_content, re.MULTILINE)
    subject = subject_match.group(1) if subject_match else 'Untitled'
    
    # Extract from
    from_match = re.search(r'^From: .+<(.+?)>', email_content, re.MULTILINE)
    if not from_match:
        from_match = re.search(r'^From: (.+?)\s', email_content, re.MULTILINE)
    sender = from_match.group(1) if from_match else 'unknown'
    
    # Extract content - handle both plain and HTML
    content = ''
    
    # Try to find plain text content
    plain_match = re.search(r'Content-Type: text/plain.*?\n\n(.+?)(?:\n--[0-9a-f]+|$)', email_content, re.DOTALL)
    if plain_match:
        content = plain_match.group(1).strip()
        # Remove quoted-printable encoding if present
        if '=' in content and re.search(r'=[0-9A-F]{2}', content):
            try:
                content = content.encode('utf-8').decode('quoted-printable')
            except:
                pass
    
    # Check for image attachments
    image_matches = re.findall(r'Content-Type: image/(jpeg|jpg|png|gif).*?filename="(.+?)".*?\n\n(.+?)\n--', email_content, re.DOTALL)
    
    return {
        'subject': subject,
        'sender': sender.lower().strip(),
        'content': content,
        'has_images': len(image_matches) > 0
    }

# Check authorized senders
authorized = ['emin@nuri.com', 'emin@emin.de', 'eminhenri@gmail.com']

# Read mailbox
try:
    with open('/var/mail/post', 'r') as f:
        mailbox_content = f.read()
except:
    print('No mail file found')
    exit(0)

if not mailbox_content.strip():
    print('No emails to process')
    exit(0)

# Extract all emails
emails = extract_emails(mailbox_content)
print(f'Found {len(emails)} emails')

processed_count = 0

for email_content in emails:
    try:
        email_data = process_email(email_content)
        
        # Skip if not authorized
        if email_data['sender'] not in authorized:
            print(f'Skipping unauthorized sender: {email_data["sender"]}')
            continue
        
        # Skip if no content
        if not email_data['content'] or email_data['content'] == 'No content':
            print(f'Skipping empty email: {email_data["subject"]}')
            continue
        
        print(f'Processing: {email_data["subject"]} from {email_data["sender"]}')
        
        # Create blog post
        slug = re.sub(r'[^a-z0-9-]', '-', email_data['subject'].lower())
        slug = re.sub(r'-+', '-', slug).strip('-')
        
        # Note about images if present
        image_note = '\n\n*Note: This email contained images that need to be manually added.*' if email_data['has_images'] else ''
        
        post_content = f'''+++
title = "{email_data['subject']}"
date = {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}Z
draft = false
author = "Emino"
tags = ["email-post"]
categories = ["blog"]
+++

{email_data['content']}{image_note}

---
*This post was created via email by {email_data['sender']}*
'''
        
        # Save post
        filename = f'/var/www/emino-blog/content/posts/{slug}.md'
        with open(filename, 'w') as f:
            f.write(post_content)
        
        print(f'Created post: {filename}')
        processed_count += 1
        
    except Exception as e:
        print(f'Error processing email: {e}')
        continue

if processed_count > 0:
    # Rebuild site
    print('Rebuilding site...')
    os.chdir('/var/www/emino-blog')
    subprocess.run(['./build.sh'], check=True)
    print('Site rebuilt!')
    
    # Sync to GitHub
    try:
        print('Syncing to GitHub...')
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', f'Added {processed_count} new post(s) via email'], check=True)
        subprocess.run(['git', 'push'], check=True)
        print('GitHub sync complete!')
    except Exception as e:
        print(f'GitHub sync failed: {e}')
    
    # Clear the mailbox
    with open('/var/mail/post', 'w') as f:
        f.write('')
    print(f'Processed {processed_count} emails and cleared mailbox')
else:
    print('No authorized emails to process')
