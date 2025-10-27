#!/bin/bash

# 🚀 START ALL TRADING SYSTEMS - ONE COMMAND
# ==========================================
# Starts all three systems:
# 1. ICT Enhanced Monitor (Day Trading) - Port 5001
# 2. Demo Trading System (Auto Trading)
# 3. Fundamental Analysis System (Long-term) - Port 5002

echo "🚀 STARTING ALL TRADING SYSTEMS"
echo "==============================="
echo "🎯 ICT Enhanced Monitor: Day trading signals (Port 5001)"
echo "📊 Demo Trading System: Auto trading execution"
echo "🔍 Fundamental Analysis: Long-term investment analysis (Port 5002)"
echo "==============================="

# Check if we're in the right directory
if [ ! -f "src/monitors/ict_enhanced_monitor.py" ]; then
    echo "❌ Not in the correct directory. Please run from Trading Algorithm folder."
    echo "💡 Current directory: $(pwd)"
    echo "💡 Expected file: src/monitors/ict_enhanced_monitor.py"
    exit 1
fi

# Check if virtual environment exists
if [ ! -f ".venv/bin/python" ]; then
    echo "❌ Virtual environment not found. Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        echo "⚠️  Port $port is already in use"
        return 1
    fi
    return 0
}

# Check if ports are available
echo "🔍 Checking ports..."
check_port 5001 || echo "   ICT Monitor may already be running"
check_port 5002 || echo "   Fundamental Analysis may already be running"

# Set Flask secret key if not already set
if [ -z "$FLASK_SECRET_KEY" ]; then
    export FLASK_SECRET_KEY="trading-system-secret-$(openssl rand -hex 32)"
    echo "🔐 Generated Flask secret key"
fi

# Start ICT Enhanced Monitor
echo "🎯 Starting ICT Enhanced Monitor (single-flow mode)..."
.venv/bin/python src/monitors/ict_enhanced_monitor.py &
ICT_PID=$!
sleep 3

# Check if ICT Monitor started successfully
if kill -0 $ICT_PID 2>/dev/null; then
    echo "✅ ICT Enhanced Monitor started (PID: $ICT_PID)"
else
    echo "❌ Failed to start ICT Enhanced Monitor"
fi

# By default we now start only the ICT monitor to enforce a single authoritative
# monitoring -> signal generation -> execution -> persistence flow.
# To start the demo trading system and the fundamental analysis system as well,
# either set environment variable START_EXTRAS=true or pass --include-extras
# Example: START_EXTRAS=true ./start_all_systems.sh

# Parse optional argument --include-extras
INCLUDE_EXTRAS="false"
if [ "$1" = "--include-extras" ]; then
    INCLUDE_EXTRAS="true"
fi
if [ "$START_EXTRAS" = "true" ]; then
    INCLUDE_EXTRAS="true"
fi

if [ "$INCLUDE_EXTRAS" = "true" ]; then
    echo "📊 Starting Demo Trading System (extras enabled)..."
    .venv/bin/python src/trading/demo_trading_system.py --dry-run &
    DEMO_PID=$!
    sleep 3

    if kill -0 $DEMO_PID 2>/dev/null; then
        echo "✅ Demo Trading System started (PID: $DEMO_PID)"
    else
        echo "❌ Failed to start Demo Trading System"
    fi

    echo "🔍 Starting Enhanced Fundamental Analysis System (extras enabled)..."
    ./scripts/setup/start_enhanced_fundamental.sh > /dev/null 2>&1 &
    FUND_PID=$!
    sleep 5

    if kill -0 $FUND_PID 2>/dev/null; then
        echo "✅ Enhanced Fundamental Analysis System started (PID: $FUND_PID)"
        echo "📡 WatcherGuru Telegram monitoring capability: ENABLED"
    else
        echo "❌ Failed to start Enhanced Fundamental Analysis System"
    fi
else
    echo "ℹ️  Extras (Demo Trading + Fundamental Analysis) skipped by default." 
    echo "   To include them: START_EXTRAS=true ./scripts/setup/start_all_systems.sh"
    echo "   Or: ./scripts/setup/start_all_systems.sh --include-extras"
fi

echo ""
echo "🌐 WEB INTERFACES:"
echo "==============================="
echo "🎯 ICT Day Trading:     http://localhost:5001"
echo "🔍 Fundamental Analysis: http://localhost:5002"
echo "📡 Bitcoin Alert Detection: ENABLED"
echo ""

echo "🔍 SYSTEM STATUS:"
echo "==============================="

# Check all systems
RUNNING_SYSTEMS=0

if ps aux | grep -q "[i]ct_enhanced_monitor.py"; then
    echo "✅ ICT Enhanced Monitor: RUNNING"
    RUNNING_SYSTEMS=$((RUNNING_SYSTEMS + 1))
else
    echo "❌ ICT Enhanced Monitor: NOT RUNNING"
fi

if ps aux | grep -q "[d]emo_trading_system.py"; then
    echo "✅ Demo Trading System: RUNNING"
    RUNNING_SYSTEMS=$((RUNNING_SYSTEMS + 1))
else
    echo "❌ Demo Trading System: NOT RUNNING"
fi

if ps aux | grep -q "[f]undamental_analysis_server.py"; then
    echo "✅ Fundamental Analysis: RUNNING"
    RUNNING_SYSTEMS=$((RUNNING_SYSTEMS + 1))
else
    echo "❌ Fundamental Analysis: NOT RUNNING"
fi

echo "==============================="
echo "📊 SUMMARY: $RUNNING_SYSTEMS/3 systems running"

if [ $RUNNING_SYSTEMS -eq 3 ]; then
    echo "🎉 ALL SYSTEMS SUCCESSFULLY STARTED!"
    echo ""
    echo "📝 To stop all systems: ./stop_all_systems.sh"
    echo "🔍 To check status: ./check_all_systems.sh"
elif [ $RUNNING_SYSTEMS -gt 0 ]; then
    echo "⚠️  PARTIAL SUCCESS: Some systems failed to start"
    echo "💡 Try running individual systems manually"
else
    echo "❌ STARTUP FAILED: No systems are running"
    echo "💡 Check dependencies and try again"
fi

echo "==============================="