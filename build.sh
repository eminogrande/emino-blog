#!/bin/bash
echo "Cleaning old build..."
rm -rf public/*
echo "Building site with Hugo..."
hugo --minify
echo "Syncing to web root with deletion of removed files..."
rsync -av --delete public/ /var/www/apps/main/
echo "Build complete!"
