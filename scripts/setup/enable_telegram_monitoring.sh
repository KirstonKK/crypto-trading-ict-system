#!/bin/bash

# 🚀 ENABLE WATCHERGURU TELEGRAM MONITORING
# =========================================
# Sets up Telegram bot monitoring for Bitcoin price alerts

echo "📡 ENABLING WATCHERGURU TELEGRAM MONITORING"
echo "=========================================="

# Check if in correct directory
if [ ! -f "systems/fundamental_analysis/fundamental_analysis_server.py" ]; then
    echo "❌ Please run from Trading Algorithm root directory"
    exit 1
fi

# Check if Telegram token is provided
if [ -z "$1" ]; then
    echo "🤖 Telegram Bot Setup Required"
    echo ""
    echo "📋 Steps to enable WatcherGuru monitoring:"
    echo "1. Create a Telegram bot via @BotFather"
    echo "2. Get your bot token"
    echo "3. Run this script with your token:"
    echo ""
    echo "   $0 'YOUR_BOT_TOKEN_HERE'"
    echo ""
    echo "💡 Example:"
    echo "   $0 '123456789:ABCdefGHIjklMNOpqrSTUvwxYZ'"
    echo ""
    echo "🎯 This will enable real-time Bitcoin $105K alert detection!"
    exit 1
fi

TELEGRAM_TOKEN="$1"

# Validate token format (basic check)
if [[ ! "$TELEGRAM_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
    echo "❌ Invalid Telegram bot token format"
    echo "💡 Should look like: 123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
    exit 1
fi

echo "✅ Valid token format detected"

# Create environment file
ENV_FILE=".env"
echo "📝 Setting up environment configuration..."

# Remove existing Telegram settings
grep -v "TELEGRAM" "$ENV_FILE" 2>/dev/null > "${ENV_FILE}.tmp" || touch "${ENV_FILE}.tmp"

# Add new settings
echo "" >> "${ENV_FILE}.tmp"
echo "# WatcherGuru Telegram Monitoring" >> "${ENV_FILE}.tmp"
echo "TELEGRAM_BOT_TOKEN='$TELEGRAM_TOKEN'" >> "${ENV_FILE}.tmp"
echo "ENABLE_TELEGRAM_MONITORING=true" >> "${ENV_FILE}.tmp"

mv "${ENV_FILE}.tmp" "$ENV_FILE"

echo "✅ Environment configured"

# Set current session variables
export TELEGRAM_BOT_TOKEN="$TELEGRAM_TOKEN"
export ENABLE_TELEGRAM_MONITORING=true

echo ""
echo "🎯 TELEGRAM MONITORING ENABLED!"
echo "==============================="
echo "🤖 Bot Token: ${TELEGRAM_TOKEN:0:10}...${TELEGRAM_TOKEN: -10}"
echo "📡 WatcherGuru Monitoring: ENABLED"
echo "🚨 Bitcoin $105K Alerts: ENABLED"
echo ""

echo "🚀 Starting systems with Telegram monitoring..."

# Stop any running fundamental analysis
echo "🛑 Stopping existing fundamental analysis..."
pkill -f fundamental_analysis_server.py 2>/dev/null
sleep 2

# Start enhanced fundamental analysis
echo "📡 Starting enhanced fundamental analysis with Telegram monitoring..."
./scripts/setup/launch_fundamental_analysis.sh &

sleep 5

# Check if it started successfully
if ps aux | grep -q "[f]undamental_analysis_server.py"; then
    echo ""
    echo "🎉 SUCCESS! WatcherGuru Telegram monitoring is now ACTIVE!"
    echo "========================================================="
    echo "🌐 Dashboard: http://localhost:5002"
    echo "📊 Real-time monitoring: Bitcoin price alerts"
    echo "🎯 Will catch alerts like: 'Bitcoin falls below $105,000'"
    echo ""
    echo "📝 To check alert status:"
    echo "   python3 check_bitcoin_alert.py"
    echo ""
    echo "🛑 To stop:"
    echo "   ./scripts/setup/stop_all_systems.sh"
else
    echo ""
    echo "❌ Failed to start with Telegram monitoring"
    echo "💡 Check logs for errors:"
    echo "   tail -f fundamental_analysis.log"
fi

echo ""
echo "🔐 Your settings are saved in .env file"
echo "📡 Future startups will automatically enable Telegram monitoring"