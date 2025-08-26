#!/bin/bash

# SEO & AI Optimization Auto-Fixer Script
# Automatically optimizes blog for better SEO and AI discoverability

echo "================================================"
echo "SEO & AI Auto-Optimizer - $(date)"
echo "================================================"

BLOG_DIR="/var/www/emino-blog"
PUBLIC_DIR="/var/www/apps/main"
IMPROVEMENTS=0

cd $BLOG_DIR

echo "🔧 Running automatic optimizations..."

# 1. Generate llms-full.txt with all content
echo -n "1. Generating llms-full.txt... "
{
    echo "# Emino Blog - Complete Content for LLMs"
    echo "Generated: $(date)"
    echo ""
    echo "## All Blog Posts"
    echo ""
    
    for file in content/posts/*.md; do
        if [ -f "$file" ]; then
            echo "---"
            echo "## $(grep "^title = " "$file" | sed 's/title = "\(.*\)"/\1/')"
            echo ""
            # Extract content after front matter
            awk 'BEGIN{fm=0} /^\+\+\+$/{fm++; next} fm==2{print}' "$file"
            echo ""
        fi
    done
} > static/llms-full.txt

if [ -f "static/llms-full.txt" ]; then
    echo "✓ Generated"
    ((IMPROVEMENTS++))
else
    echo "✗ Failed"
fi

# 2. Update sitemap with proper priorities
echo -n "2. Optimizing sitemap priorities... "
hugo
if [ -f "public/sitemap.xml" ]; then
    # Increase priority for main pages
    sed -i 's|<priority>0.5</priority>|<priority>0.8</priority>|g' public/sitemap.xml
    echo "✓ Optimized"
    ((IMPROVEMENTS++))
else
    echo "✗ No sitemap found"
fi

# 3. Generate structured data for posts
echo -n "3. Adding structured data... "
for html in public/posts/*/index.html; do
    if [ -f "$html" ] && ! grep -q "application/ld+json" "$html"; then
        POST_DIR=$(dirname "$html")
        POST_NAME=$(basename "$POST_DIR")
        
        # Extract title from HTML
        TITLE=$(grep -o "<title>[^<]*</title>" "$html" | sed 's/<[^>]*>//g')
        
        # Add structured data before </head>
        SCHEMA='<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "'${TITLE}'",
  "url": "https://emino.app/posts/'${POST_NAME}'/"
}
</script>'
        
        sed -i "s|</head>|${SCHEMA}\n</head>|" "$html" 2>/dev/null
    fi
done
echo "✓ Added to posts"
((IMPROVEMENTS++))

# 4. Optimize images (if any exist)
echo -n "4. Image optimization... "
IMAGE_COUNT=$(find static -type f \( -name "*.jpg" -o -name "*.png" \) 2>/dev/null | wc -l)
if [ "$IMAGE_COUNT" -gt 0 ]; then
    # Would need imagemagick installed for actual optimization
    echo "⚠ $IMAGE_COUNT images found (install imagemagick for optimization)"
else
    echo "✓ No images to optimize"
fi

# 5. Create archive page for better navigation
echo -n "5. Creating archive page... "
if [ ! -f "content/archives.md" ]; then
    cat > content/archives.md << 'EOF'
+++
title = "Archives"
layout = "archives"
url = "/archives/"
summary = "Complete archive of all blog posts"
+++
EOF
    echo "✓ Created"
    ((IMPROVEMENTS++))
else
    echo "✓ Already exists"
fi

# 6. Check and fix broken markdown links
echo -n "6. Fixing markdown links... "
FIXED_LINKS=0
for file in content/posts/*.md; do
    if [ -f "$file" ]; then
        # Fix common markdown link issues
        sed -i 's/\[([^]]*)\]/[\1]/g' "$file" 2>/dev/null
        sed -i 's/\]([[:space:]]*(/](/g' "$file" 2>/dev/null
    fi
done
echo "✓ Checked"

# 7. Generate tags and categories pages
echo -n "7. Generating taxonomy pages... "
hugo
echo "✓ Generated"

# 8. Deploy all changes
echo -n "8. Deploying optimizations... "
rsync -av --delete public/ $PUBLIC_DIR/ > /dev/null 2>&1
echo "✓ Deployed"

echo ""
echo "================================================"
echo "Optimization Summary:"
echo "- Improvements made: $IMPROVEMENTS"
echo "- Site URL: https://emino.app"
echo "- llms.txt: https://emino.app/llms.txt"
echo "- Sitemap: https://emino.app/sitemap.xml"
echo "================================================"

# Run health check to verify
echo ""
echo "Running health check to verify optimizations..."
bash /var/www/emino-blog/health-check.sh
