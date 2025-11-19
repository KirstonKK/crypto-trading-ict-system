#!/bin/bash

# Script to remove exposed API key from git history
# WARNING: This rewrites git history - USE WITH CAUTION

set -e

API_KEY="HB85thv3OT8WPqiTYu"
REPO_DIR="/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

echo "🔒 SECURITY: Removing exposed API key from git history"
echo "=================================================="
echo ""
echo "⚠️  WARNING: This will rewrite git history!"
echo "   - All commit SHAs will change"
echo "   - Collaborators will need to re-clone"
echo "   - Force push required"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

cd "$REPO_DIR"

# Create backup
echo ""
echo "📦 Creating backup..."
BACKUP_DIR="$HOME/Desktop/crypto-trading-backup-$(date +%Y%m%d_%H%M%S)"
cp -r "$REPO_DIR" "$BACKUP_DIR"
echo "✅ Backup created at: $BACKUP_DIR"

# Method 1: Using git filter-branch (built-in)
echo ""
echo "🧹 Removing API key from history..."
echo "Searching for: $API_KEY"

git filter-branch --force --index-filter \
  "git grep -l '$API_KEY' HEAD 2>/dev/null | xargs -I {} git update-index --remove {} 2>/dev/null || true" \
  --prune-empty --tag-name-filter cat -- --all

# Clean up refs
echo ""
echo "🧹 Cleaning up refs..."
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "✅ API key removed from git history!"
echo ""
echo "📋 Next steps:"
echo "1. Review the changes:"
echo "   git log --all --oneline -- docs/SAFETY_FEATURES.md | head -5"
echo ""
echo "2. Force push to GitHub:"
echo "   git push origin main --force"
echo ""
echo "3. Notify collaborators to re-clone the repo"
echo ""
echo "🔐 IMPORTANT: After force push, consider rotating API keys for maximum security"
