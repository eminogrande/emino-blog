#!/bin/bash
# Script to create favicon from Bitcoin laser eyes image

if [ -z "$1" ]; then
    echo "Usage: ./create_favicon.sh <path-to-image>"
    echo "Example: ./create_favicon.sh bitcoin-laser-eyes.png"
    exit 1
fi

IMAGE="$1"
STATIC_DIR="/var/www/emino-blog/static"

echo "Creating favicon from $IMAGE..."

# Create multiple sizes for best browser support
convert "$IMAGE" -resize 16x16 "$STATIC_DIR/favicon-16x16.png"
convert "$IMAGE" -resize 32x32 "$STATIC_DIR/favicon-32x32.png"
convert "$IMAGE" -resize 180x180 "$STATIC_DIR/apple-touch-icon.png"
convert "$IMAGE" -resize 192x192 "$STATIC_DIR/android-chrome-192x192.png"
convert "$IMAGE" -resize 512x512 "$STATIC_DIR/android-chrome-512x512.png"

# Create ICO file with multiple sizes
convert "$IMAGE" -resize 16x16 -resize 32x32 -resize 48x48 "$STATIC_DIR/favicon.ico"

echo "Favicon created successfully!"
echo "Now updating site configuration..."
