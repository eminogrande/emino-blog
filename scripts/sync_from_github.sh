#!/bin/bash

set -euo pipefail

BLOG_DIR="${EMINO_BLOG_DIR:-/var/www/emino-blog}"
BRANCH="${EMINO_GIT_BRANCH:-main}"

echo "=== GitHub Sync at $(date) ==="

if [ ! -d "$BLOG_DIR/.git" ]; then
    echo "Error: $BLOG_DIR is not a git repository."
    exit 1
fi

cd "$BLOG_DIR"

# Bail out if there are uncommitted changes so we do not destroy work in progress.
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Local changes detected. Commit or stash them before running the sync."
    exit 0
fi

git fetch origin "$BRANCH"

# Make sure the branch exists locally.
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    git checkout "$BRANCH"
else
    git checkout -b "$BRANCH" "origin/$BRANCH"
fi

if ! git merge --ff-only "origin/$BRANCH"; then
    echo "Fast-forward merge failed, attempting rebase..."
    git rebase "origin/$BRANCH"
fi

echo "Rebuilding Hugo site..."
hugo --minify --cleanDestinationDir
echo "Sync complete!"
