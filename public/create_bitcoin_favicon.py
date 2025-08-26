#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os

# Create a Bitcoin-themed favicon with lightning bolt
size = 512
img = Image.new("RGB", (size, size), "#f7931a")  # Bitcoin orange background
draw = ImageDraw.Draw(img)

# Draw a simple Bitcoin B logo
center = size // 2
radius = int(size * 0.35)

# White circle background for B
draw.ellipse(
    [center - radius, center - radius, center + radius, center + radius],
    fill="white"
)

# Draw Bitcoin B (simplified)
try:
    # Try to use a bold font if available
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(size * 0.5))
except:
    font = ImageFont.load_default()

# Draw B in Bitcoin orange
draw.text((center, center), "B", fill="#f7931a", font=font, anchor="mm")

# Add a small lightning bolt overlay (simplified)
bolt_color = "#ffff00"  # Yellow for lightning
bolt_points = [
    (center + radius * 0.5, center - radius * 0.3),
    (center + radius * 0.2, center),
    (center + radius * 0.3, center),
    (center - radius * 0.1, center + radius * 0.5),
    (center + radius * 0.1, center),
    (center, center),
    (center + radius * 0.5, center - radius * 0.3)
]
draw.polygon(bolt_points, fill=bolt_color)

# Save in multiple sizes
sizes = {
    "favicon.ico": [(16, 16), (32, 32), (48, 48)],
    "favicon-16x16.png": (16, 16),
    "favicon-32x32.png": (32, 32),
    "apple-touch-icon.png": (180, 180),
    "android-chrome-192x192.png": (192, 192),
    "android-chrome-512x512.png": (512, 512),
}

for filename, dimensions in sizes.items():
    if filename == "favicon.ico":
        # Create ICO with multiple sizes
        resized_images = []
        for dim in dimensions:
            resized = img.resize(dim, Image.Resampling.LANCZOS)
            resized_images.append(resized)
        resized_images[0].save(filename, format="ICO", sizes=dimensions)
    else:
        resized = img.resize(dimensions, Image.Resampling.LANCZOS)
        resized.save(filename, "PNG")

print("Bitcoin favicon created successfully!")
