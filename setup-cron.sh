#!/bin/bash

# Setup cron jobs for blog health monitoring

echo "Setting up automated blog monitoring..."

# Add cron jobs
(crontab -l 2>/dev/null; echo "# Blog Health Monitoring") | crontab -
(crontab -l 2>/dev/null; echo "0 */6 * * * /var/www/emino-blog/health-check.sh > /var/log/blog-health.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "0 3 * * * /var/www/emino-blog/seo-optimizer.sh > /var/log/blog-seo.log 2>&1") | crontab -

echo "Cron jobs added:"
echo "- Health check: Every 6 hours"
echo "- SEO optimization: Daily at 3 AM"
echo ""
echo "Logs will be saved to:"
echo "- /var/log/blog-health.log"
echo "- /var/log/blog-seo.log"
