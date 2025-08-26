#!/bin/bash
# Hugo Blog Deployment Script

echo "Starting deployment..."

# Pull latest changes
git pull origin main

# Build the site
hugo --minify

# Deploy to nginx directory
rsync -av --delete public/ /var/www/apps/main/

# Generate llms-full.txt (all content in one file)
echo "# Emino Blog - Full Content for LLMs" > public/llms-full.txt
echo "" >> public/llms-full.txt
for file in content/posts/*.md; do
    if [ -f "$file" ]; then
        echo "---" >> public/llms-full.txt
        cat "$file" >> public/llms-full.txt
        echo "" >> public/llms-full.txt
    fi
done

# Copy to main directory
cp public/llms-full.txt /var/www/apps/main/

echo "Deployment complete!"
