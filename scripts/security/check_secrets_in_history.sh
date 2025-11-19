#!/bin/bash

# Simple script to verify if API key still exists in git history
# Safe to run - does not modify anything

API_KEY="HB85thv3OT8WPqiTYu"
REPO_DIR="/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

echo "🔍 Scanning git history for exposed API key..."
echo "=============================================="
echo ""

cd "$REPO_DIR"

# Search all commits
echo "Commits containing API key:"
git log --all -S "$API_KEY" --oneline

echo ""
echo "Files containing API key in latest commit:"
git grep "$API_KEY" HEAD 2>/dev/null || echo "✅ No matches in HEAD"

echo ""
echo "Files containing API key in previous commit:"
git grep "$API_KEY" HEAD~1 2>/dev/null || echo "✅ No matches in HEAD~1"

echo ""
echo "=============================================="
echo "Analysis complete."
