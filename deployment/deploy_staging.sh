#!/bin/bash
# Deployment script for staging environment

set -e

echo "🚀 Deploying Trading Algorithm to STAGING"
echo "========================================"

# Set environment
export ENVIRONMENT=staging

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Load staging environment
echo "🔧 Loading staging configuration..."
cp config/environments/.env.staging .env

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Check API connectivity
echo "🔌 Testing API connectivity..."
python tests/integration/test_api_activation.py

# Start staging deployment
echo "🚀 Starting staging deployment..."
nohup python app.py > logs/staging.log 2>&1 &

echo "✅ Staging deployment complete!"
echo "📊 Monitor: http://localhost:5001"
echo "📝 Logs: tail -f logs/staging.log"