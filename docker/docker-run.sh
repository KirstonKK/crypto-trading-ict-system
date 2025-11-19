#!/bin/bash

# Crypto Trading ICT - Docker Run Script
# This script loads credentials from .env and starts the Docker container

set -e

echo "🚀 Starting Crypto Trading ICT System..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "📝 Please create .env file with your Bybit API credentials"
    echo "   You can copy from .env.example and edit it"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | grep BYBIT | xargs)

# Stop and remove existing container if it exists
if [ "$(docker ps -a -q -f name=crypto-trading)" ]; then
    echo "🛑 Stopping existing container..."
    docker stop crypto-trading 2>/dev/null || true
    docker rm crypto-trading 2>/dev/null || true
fi

# Pull latest image
echo "📦 Pulling latest image..."
docker pull kirston/crypto-trading-ict:latest

# Start container
echo "🔧 Starting container..."
docker run -d \
  --name crypto-trading \
  -p 5001:5001 \
  -e BYBIT_API_KEY="${BYBIT_API_KEY}" \
  -e BYBIT_API_SECRET="${BYBIT_API_SECRET}" \
  -e BYBIT_TESTNET="${BYBIT_TESTNET}" \
  -e BYBIT_DEMO="${BYBIT_DEMO}" \
  -e BYBIT_BASE_URL="${BYBIT_BASE_URL}" \
  -v "$(pwd)/data":/app/data \
  --restart unless-stopped \
  kirston/crypto-trading-ict:latest

# Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 5

# Check status
if [ "$(docker ps -q -f name=crypto-trading)" ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              ✅ Container Started Successfully!              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📊 Dashboard: http://localhost:5001"
    echo "📈 Health Check: curl http://localhost:5001/health"
    echo "📋 View Logs: docker logs -f crypto-trading"
    echo "🛑 Stop: docker stop crypto-trading"
    echo ""
else
    echo "❌ Container failed to start. Check logs with: docker logs crypto-trading"
    exit 1
fi
