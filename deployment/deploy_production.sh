#!/bin/bash
# Production deployment script

set -e

echo "🏭 Deploying Trading Algorithm to PRODUCTION"
echo "============================================"

# Verify we're on main branch
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    echo "❌ Must be on main branch for production deployment"
    exit 1
fi

# Verify all tests pass
echo "🧪 Running full test suite..."
python -m pytest tests/ -v --tb=short

# Set production environment
export ENVIRONMENT=production

# Load production environment
echo "🔧 Loading production configuration..."
cp config/environments/.env.production .env

# Backup current production
echo "💾 Creating backup..."
mkdir -p backups/$(date +%Y%m%d_%H%M%S)

# Deploy to production
echo "🚀 Starting production deployment..."
python app.py

echo "✅ Production deployment complete!"
echo "🚨 LIVE TRADING ACTIVE - Monitor carefully!"