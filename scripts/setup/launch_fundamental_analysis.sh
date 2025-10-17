#!/bin/bash

# 🚀 LAUNCH CRYPTO FUNDAMENTAL ANALYSIS SYSTEM
# ============================================
# Standalone system for long-term crypto investment analysis
# Runs independently on port 5002 with real-time dashboard

echo "🚀 CRYPTO FUNDAMENTAL ANALYSIS SYSTEM"
echo "======================================"
echo "🎯 Purpose: Long-term investment analysis"
echo "📊 Features: Supply/demand fundamentals, news sentiment"
echo "🌐 Dashboard: http://localhost:5002"
echo "🔄 Background: Hourly analysis updates"
echo "======================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if required packages are installed
echo "🔍 Checking dependencies..."
python3 -c "import flask, flask_socketio, textblob, aiohttp" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing required packages..."
    python3 -m pip install flask flask-socketio textblob aiohttp
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

echo "✅ Dependencies ready"

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export FLASK_ENV=production

# Check for Telegram Bot Token
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "⚠️  TELEGRAM_BOT_TOKEN not set - WatcherGuru monitoring disabled"
    echo "💡 To enable: export TELEGRAM_BOT_TOKEN='your_bot_token'"
    export ENABLE_TELEGRAM_MONITORING=false
else
    echo "✅ Telegram Bot Token configured - WatcherGuru monitoring enabled"
    export ENABLE_TELEGRAM_MONITORING=true
fi

# Create logs directory if it doesn't exist
mkdir -p logs

echo "🚀 Starting Enhanced Fundamental Analysis Server..."
echo "📍 Location: $(pwd)"
echo "🌐 Dashboard: http://localhost:5002"
echo "🔗 API Health: http://localhost:5002/api/health"
echo "📡 WatcherGuru Telegram: ${ENABLE_TELEGRAM_MONITORING:-false}"
echo ""
echo "🎯 Features Active:"
echo "   • Multi-source news integration"
echo "   • Real-time price monitoring"
echo "   • Supply/demand analysis"
if [ "$ENABLE_TELEGRAM_MONITORING" = "true" ]; then
    echo "   • WatcherGuru Telegram monitoring"
    echo "   • Bitcoin price alert detection"
else
    echo "   • WatcherGuru Telegram: DISABLED (no token)"
fi
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================="

# Start the server
python3 systems/fundamental_analysis/fundamental_analysis_server.py

echo ""
echo "🛑 Fundamental Analysis Server stopped"