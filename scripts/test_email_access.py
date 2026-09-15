#!/usr/bin/env python3
import imaplib
import os
from datetime import datetime

print(f'Testing email access at {datetime.now()}')

# Test IMAP access
try:
    mail = imaplib.IMAP4('localhost', 143)
    mail.login('post', 'Kilimanjaro##8')
    print('✓ IMAP login successful')
    
    # Check all folders
    result, folders = mail.list()
    print(f'Available folders: {folders}')
    
    # Check INBOX
    mail.select('INBOX')
    result, data = mail.search(None, 'ALL')
    if data[0]:
        print(f'✓ Found {len(data[0].split())} emails in INBOX')
    else:
        print('✗ INBOX is empty')
    
    mail.logout()
except Exception as e:
    print(f'✗ IMAP error: {e}')

# Check Maildir
maildir = '/home/post/Maildir'
if os.path.exists(maildir):
    new_mails = os.listdir(f'{maildir}/new') if os.path.exists(f'{maildir}/new') else []
    cur_mails = os.listdir(f'{maildir}/cur') if os.path.exists(f'{maildir}/cur') else []
    print(f'Maildir: {len(new_mails)} new, {len(cur_mails)} current')
else:
    print('✗ Maildir not found')

# Check mail spool
if os.path.exists('/var/mail/post'):
    size = os.path.getsize('/var/mail/post')
    print(f'Mail spool size: {size} bytes')
