#!/bin/bash

# 🚀 START ENHANCED FUNDAMENTAL ANALYSIS WITH TELEGRAM CAPABILITY
# ===============================================================
# Starts fundamental analysis with Telegram monitoring capability
# Can run with or without Telegram token

echo "🚀 STARTING ENHANCED FUNDAMENTAL ANALYSIS"
echo "========================================"

# Set environment for enhanced features
export ENABLE_TELEGRAM_MONITORING=true
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if token is available
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "✅ Telegram Bot Token found - WatcherGuru monitoring ENABLED"
    echo "📡 Will monitor: Bitcoin $105K alerts in real-time"
else
    echo "⚠️  No Telegram Bot Token - Demo mode only"
    echo "💡 To enable: export TELEGRAM_BOT_TOKEN='your_token'"
    echo "📋 Telegram features will be simulated"
fi

echo ""
echo "🎯 Enhanced Features:"
echo "   • Multi-source news integration"
echo "   • Real-time price monitoring" 
echo "   • Supply/demand analysis"
echo "   • Bitcoin price alert detection system"
echo "   • WatcherGuru news integration"
echo ""

# Stop any existing fundamental analysis
pkill -f fundamental_analysis_server.py 2>/dev/null
sleep 2

# Start the enhanced system
echo "🚀 Starting enhanced fundamental analysis server..."

# Use virtual environment if available, otherwise use system python3
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
else
    PYTHON_CMD="python3"
fi

$PYTHON_CMD systems/fundamental_analysis/fundamental_analysis_server.py &

FUND_PID=$!
sleep 5

# Check if started successfully
if kill -0 $FUND_PID 2>/dev/null; then
    echo ""
    echo "🎉 ENHANCED FUNDAMENTAL ANALYSIS STARTED!"
    echo "========================================"
    echo "🌐 Dashboard: http://localhost:5002"
    echo "📊 API: http://localhost:5002/api/analysis"
    echo "🔍 Health: http://localhost:5002/api/health"
    echo ""
    
    if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
        echo "📡 WatcherGuru Telegram: ACTIVE"
        echo "🚨 Bitcoin Alert Detection: ENABLED"
        echo "🎯 Will catch alerts like: 'Bitcoin falls below $105,000'"
    else
        echo "📡 WatcherGuru Telegram: DEMO MODE"
        echo "💡 Set TELEGRAM_BOT_TOKEN to enable real monitoring"
    fi
    
    echo ""
    echo "📝 To test Bitcoin alert detection:"
    echo "   python3 scripts/testing/check_bitcoin_alert.py"
    echo ""
    echo "🛑 To stop: pkill -f fundamental_analysis_server.py"
    echo "========================================"
else
    echo "❌ Failed to start enhanced fundamental analysis"
    echo "💡 Check dependencies and try again"
fi