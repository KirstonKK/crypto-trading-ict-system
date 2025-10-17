#!/bin/bash

# 🚀 PROFESSIONAL TRADING SYSTEM LAUNCHER
# =======================================
# Updated for new directory structure

echo "🚀 PROFESSIONAL CRYPTO TRADING SYSTEM"
echo "====================================="
echo "🎯 ICT Enhanced Monitor: Day trading (Port 5001)"
echo "📊 Demo Trading System: Auto execution"
echo "🔍 Fundamental Analysis: Long-term (Port 5002)"
echo "====================================="

# Check if we're in the correct directory
if [ ! -f "trade_system.py" ]; then
    echo "❌ Please run from the Trading Algorithm root directory"
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

# Check ports
echo "🔍 Checking ports..."
check_port 5001 || echo "   ICT Monitor may already be running"
check_port 5002 || echo "   Fundamental Analysis may already be running"

# Start ICT Enhanced Monitor
echo "🎯 Starting ICT Enhanced Monitor..."
python3 core/monitors/ict_enhanced_monitor.py > logs/ict_monitor.log 2>&1 &
ICT_PID=$!
sleep 3

# Check if ICT Monitor started
if kill -0 $ICT_PID 2>/dev/null; then
    echo "✅ ICT Enhanced Monitor started (PID: $ICT_PID)"
else
    echo "❌ Failed to start ICT Enhanced Monitor"
fi

# Start Demo Trading System
echo "📊 Starting Demo Trading System..."
python3 systems/demo_trading/demo_trading_system.py --auto-trading > logs/demo_trading.log 2>&1 &
DEMO_PID=$!
sleep 3

# Check if Demo Trading started
if kill -0 $DEMO_PID 2>/dev/null; then
    echo "✅ Demo Trading System started (PID: $DEMO_PID)"
else
    echo "❌ Failed to start Demo Trading System"
fi

# Start Fundamental Analysis System
echo "🔍 Starting Fundamental Analysis System..."
cd systems/fundamental_analysis
python3 fundamental_analysis_server.py > ../../logs/fundamental_analysis.log 2>&1 &
FUND_PID=$!
cd ../..
sleep 5

# Check if Fundamental Analysis started
if kill -0 $FUND_PID 2>/dev/null; then
    echo "✅ Fundamental Analysis System started (PID: $FUND_PID)"
else
    echo "❌ Failed to start Fundamental Analysis System"
fi

echo ""
echo "🌐 WEB INTERFACES:"
echo "====================================="
echo "🎯 ICT Day Trading:     http://localhost:5001"
echo "🔍 Fundamental Analysis: http://localhost:5002"
echo ""

echo "🔍 FINAL STATUS:"
echo "====================================="

RUNNING_COUNT=0

# Check all systems
if ps aux | grep -q "[i]ct_enhanced_monitor.py"; then
    echo "✅ ICT Enhanced Monitor: RUNNING"
    RUNNING_COUNT=$((RUNNING_COUNT + 1))
else
    echo "❌ ICT Enhanced Monitor: NOT RUNNING"
fi

if ps aux | grep -q "[d]emo_trading_system.py"; then
    echo "✅ Demo Trading System: RUNNING"
    RUNNING_COUNT=$((RUNNING_COUNT + 1))
else
    echo "❌ Demo Trading System: NOT RUNNING"
fi

if ps aux | grep -q "[f]undamental_analysis_server.py"; then
    echo "✅ Fundamental Analysis: RUNNING"
    RUNNING_COUNT=$((RUNNING_COUNT + 1))
else
    echo "❌ Fundamental Analysis: NOT RUNNING"
fi

echo "====================================="
echo "📊 SUMMARY: $RUNNING_COUNT/3 systems running"

if [ $RUNNING_COUNT -eq 3 ]; then
    echo "🎉 ALL SYSTEMS OPERATIONAL!"
    echo ""
    echo "📝 Commands:"
    echo "  python3 trade_system.py --stop-all    # Stop all systems"
    echo "  python3 trade_system.py --status      # Check status"
    echo "  ./scripts/setup/stop_all_systems.sh   # Alternative stop"
elif [ $RUNNING_COUNT -gt 0 ]; then
    echo "⚠️  PARTIAL SUCCESS: Some systems failed"
else
    echo "❌ STARTUP FAILED: No systems running"
fi

echo "====================================="