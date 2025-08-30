#!/bin/bash

# Submit sitemap to search engines
SITEMAP="https://emino.app/sitemap.xml"

echo "Submitting sitemap to search engines..."

# Google
echo "Submitting to Google..."
curl -s "https://www.google.com/ping?sitemap=${SITEMAP}"

# Bing (also submits to DuckDuckGo)
echo "Submitting to Bing..."
curl -s "https://www.bing.com/ping?sitemap=${SITEMAP}"

# Yandex
echo "Submitting to Yandex..."
curl -s "https://webmaster.yandex.com/ping?sitemap=${SITEMAP}"

# IndexNow (Bing, Yandex, Seznam.cz, and others)
echo "Submitting via IndexNow protocol..."
curl -s -X POST "https://api.indexnow.org/indexnow" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "emino.app",
    "key": "emino2025indexkey",
    "urlList": [
      "https://emino.app/",
      "https://emino.app/posts/",
      "https://emino.app/tags/",
      "https://emino.app/archives/"
    ]
  }'

echo ""
echo "Search engine submission complete!"
echo "Note: For full indexing:"
echo "1. Google Search Console: https://search.google.com/search-console"
echo "2. Bing Webmaster Tools: https://www.bing.com/webmasters"
echo "3. Brave Search: https://brave.com/webmasters/"
