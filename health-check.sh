#!/bin/bash

# Blog Health Check & SEO Monitoring Script
# Run this script regularly via cron to ensure optimal performance

echo "================================================"
echo "Blog Health Check - $(date)"
echo "================================================"

# Colors for output
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

# Variables
SITE_URL="https://emino.app"
BLOG_DIR="/var/www/emino-blog"
PUBLIC_DIR="/var/www/apps/main"
ERRORS=0
WARNINGS=0

echo -e "\n📋 Running Health Checks..."

# 1. Check if site is accessible
echo -n "1. Site HTTPS Accessibility: "
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $SITE_URL)
if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ OK${NC} (HTTP $HTTP_STATUS)"
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $HTTP_STATUS)"
    ((ERRORS++))
fi

# 2. Check SSL certificate expiry
echo -n "2. SSL Certificate Status: "
CERT_EXPIRY=$(echo | openssl s_client -servername emino.app -connect emino.app:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null | grep notAfter | cut -d= -f2)
if [ ! -z "$CERT_EXPIRY" ]; then
    echo -e "${GREEN}✓ Valid${NC} (Expires: $CERT_EXPIRY)"
else
    echo -e "${YELLOW}⚠ Warning${NC} - Could not check certificate"
    ((WARNINGS++))
fi

# 3. Check critical files existence
echo -n "3. Critical Files: "
MISSING_FILES=()
[ ! -f "$PUBLIC_DIR/llms.txt" ] && MISSING_FILES+=("llms.txt")
[ ! -f "$PUBLIC_DIR/robots.txt" ] && MISSING_FILES+=("robots.txt")
[ ! -f "$PUBLIC_DIR/sitemap.xml" ] && MISSING_FILES+=("sitemap.xml")
[ ! -f "$PUBLIC_DIR/index.html" ] && MISSING_FILES+=("index.html")

if [ ${#MISSING_FILES[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All present${NC}"
else
    echo -e "${RED}✗ Missing: ${MISSING_FILES[*]}${NC}"
    ((ERRORS++))
fi

# 4. Check broken internal links
echo -n "4. Internal Link Check: "
cd $PUBLIC_DIR
BROKEN_LINKS=$(grep -r "href=\"/" *.html 2>/dev/null | sed "s/.*href=\"\([^\"]*\)\".*/\1/" | sort -u | while read link; do
    if [[ $link == /* ]] && [ ! -f "${PUBLIC_DIR}${link}" ] && [ ! -f "${PUBLIC_DIR}${link}index.html" ] && [ ! -d "${PUBLIC_DIR}${link}" ]; then
        echo $link
    fi
done | wc -l)

if [ "$BROKEN_LINKS" -eq 0 ]; then
    echo -e "${GREEN}✓ No broken links${NC}"
else
    echo -e "${YELLOW}⚠ $BROKEN_LINKS broken links found${NC}"
    ((WARNINGS++))
fi

# 5. Check response time
echo -n "5. Site Response Time: "
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" $SITE_URL)
RESPONSE_MS=$(echo "$RESPONSE_TIME * 1000" | bc | cut -d. -f1)
if [ "$RESPONSE_MS" -lt 1000 ]; then
    echo -e "${GREEN}✓ Fast${NC} (${RESPONSE_MS}ms)"
elif [ "$RESPONSE_MS" -lt 3000 ]; then
    echo -e "${YELLOW}⚠ Moderate${NC} (${RESPONSE_MS}ms)"
else
    echo -e "${RED}✗ Slow${NC} (${RESPONSE_MS}ms)"
    ((WARNINGS++))
fi

# 6. Check disk space
echo -n "6. Disk Space: "
DISK_USAGE=$(df -h /var/www | awk 'NR==2 {print $5}' | sed "s/%//")
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓ OK${NC} ($DISK_USAGE% used)"
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}⚠ Warning${NC} ($DISK_USAGE% used)"
    ((WARNINGS++))
else
    echo -e "${RED}✗ Critical${NC} ($DISK_USAGE% used)"
    ((ERRORS++))
fi

# 7. Check Hugo build
echo -n "7. Hugo Build Status: "
cd $BLOG_DIR
if hugo check 2>/dev/null; then
    echo -e "${GREEN}✓ No issues${NC}"
else
    echo -e "${YELLOW}⚠ Build warnings${NC}"
    ((WARNINGS++))
fi

# 8. Check for recent content
echo -n "8. Content Freshness: "
LATEST_POST=$(find $BLOG_DIR/content -name "*.md" -type f -exec stat -c %Y {} \; | sort -n | tail -1)
CURRENT_TIME=$(date +%s)
DAYS_OLD=$(( ($CURRENT_TIME - $LATEST_POST) / 86400 ))
if [ "$DAYS_OLD" -lt 30 ]; then
    echo -e "${GREEN}✓ Fresh${NC} ($DAYS_OLD days since last post)"
elif [ "$DAYS_OLD" -lt 90 ]; then
    echo -e "${YELLOW}⚠ Getting stale${NC} ($DAYS_OLD days since last post)"
    ((WARNINGS++))
else
    echo -e "${RED}✗ Stale${NC} ($DAYS_OLD days since last post)"
    ((WARNINGS++))
fi

echo -e "\n📊 SEO & AI Optimization Checks..."

# 9. Check meta descriptions
echo -n "9. Meta Descriptions: "
META_CHECK=$(grep -l "description =" $BLOG_DIR/content/posts/*.md 2>/dev/null | wc -l)
TOTAL_POSTS=$(ls $BLOG_DIR/content/posts/*.md 2>/dev/null | wc -l)
if [ "$META_CHECK" -eq "$TOTAL_POSTS" ] && [ "$TOTAL_POSTS" -gt 0 ]; then
    echo -e "${GREEN}✓ All posts have descriptions${NC}"
else
    echo -e "${YELLOW}⚠ $META_CHECK/$TOTAL_POSTS posts have descriptions${NC}"
    ((WARNINGS++))
fi

# 10. Check AI crawler access
echo -n "10. AI Crawler Access: "
if grep -q "GPTBot" $PUBLIC_DIR/robots.txt && grep -q "Claude-Web" $PUBLIC_DIR/robots.txt; then
    echo -e "${GREEN}✓ AI crawlers allowed${NC}"
else
    echo -e "${RED}✗ AI crawlers not properly configured${NC}"
    ((ERRORS++))
fi

# 11. Check llms.txt formatting
echo -n "11. llms.txt Validity: "
if [ -f "$PUBLIC_DIR/llms.txt" ] && grep -q "^# " $PUBLIC_DIR/llms.txt; then
    echo -e "${GREEN}✓ Properly formatted${NC}"
else
    echo -e "${YELLOW}⚠ Check formatting${NC}"
    ((WARNINGS++))
fi

# 12. Check page load resources
echo -n "12. Page Weight: "
PAGE_SIZE=$(curl -s $SITE_URL | wc -c)
PAGE_SIZE_KB=$(( $PAGE_SIZE / 1024 ))
if [ "$PAGE_SIZE_KB" -lt 100 ]; then
    echo -e "${GREEN}✓ Lightweight${NC} (${PAGE_SIZE_KB}KB)"
elif [ "$PAGE_SIZE_KB" -lt 500 ]; then
    echo -e "${YELLOW}⚠ Moderate${NC} (${PAGE_SIZE_KB}KB)"
    ((WARNINGS++))
else
    echo -e "${RED}✗ Heavy${NC} (${PAGE_SIZE_KB}KB)"
    ((ERRORS++))
fi

echo -e "\n================================================"
echo "Summary:"
echo -e "Errors: ${ERRORS} | Warnings: ${WARNINGS}"

if [ "$ERRORS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e "${GREEN}✓ Blog is in perfect health!${NC}"
    exit 0
elif [ "$ERRORS" -eq 0 ]; then
    echo -e "${YELLOW}⚠ Blog is healthy with some warnings${NC}"
    exit 1
else
    echo -e "${RED}✗ Blog has critical issues that need attention${NC}"
    exit 2
fi
