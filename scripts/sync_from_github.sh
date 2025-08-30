#!/bin/bash

# Sync from GitHub and handle deletions

cd /var/www/emino-blog

# Pull latest changes from GitHub
git fetch origin main
git reset --hard origin/main

# Rebuild Hugo site
hugo --cleanDestinationDir

# Sync to web directory with delete flag to remove deleted files
rsync -av --delete public/ /var/www/apps/main/

# Reload nginx
nginx -s reload

echo "Sync complete at $(date)"
