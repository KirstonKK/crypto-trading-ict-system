#!/bin/bash

# 🚀 START UNIFIED TRADING SYSTEM - ONE COMMAND
# =============================================
# Starts the unified ICT Enhanced Monitor with:
# 1. ICT Trading Signals & Execution
# 2. Real-time Price Monitoring
# 3. Fundamental Analysis (Integrated)
# 4. Trading Journal & Dashboard
# ALL on Port 5001

echo "🚀 STARTING UNIFIED TRADING SYSTEM"
echo "===================================="
echo "✅ ICT Trading Monitor (Unified System)"
echo "   ├─ Day Trading Signals & Execution"
echo "   ├─ Real-time Price Updates"
echo "   ├─ Fundamental Analysis (Integrated)"
echo "   ├─ Trading Journal & Dashboard"
echo "   └─ ALL on Port 5001"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "core/monitors/ict_enhanced_monitor.py" ]; then
    echo "❌ Not in the correct directory. Please run from Trading Algorithm folder."
    echo "💡 Current directory: $(pwd)"
    echo "💡 Expected file: core/monitors/ict_enhanced_monitor.py"
    exit 1
fi

# Check for Python - use virtual environment if available, otherwise use system python3
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
    echo "✅ Using virtual environment Python"
else
    PYTHON_CMD="python3"
    echo "✅ Using system Python3"
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

# Check if port is available
echo "🔍 Checking port 5001..."
check_port 5001 || echo "   ICT Monitor may already be running"

# Set Flask secret key if not already set
if [ -z "$FLASK_SECRET_KEY" ]; then
    export FLASK_SECRET_KEY="trading-system-secret-$(openssl rand -hex 32)"
    echo "🔐 Generated Flask secret key"
fi

# Set PYTHONPATH to include the project root
export PYTHONPATH="$(pwd):$PYTHONPATH"
echo "📂 Set PYTHONPATH to: $(pwd)"

# Ensure logs directory exists
mkdir -p logs
echo "📁 Logs directory ready"

# Start Unified ICT Enhanced Monitor (includes fundamental analysis)
echo "🎯 Starting Unified ICT Trading System..."
$PYTHON_CMD core/monitors/ict_enhanced_monitor.py > logs/ict_monitor.log 2>&1 &
ICT_PID=$!
sleep 3

# Check if ICT Monitor started successfully
if kill -0 $ICT_PID 2>/dev/null; then
    echo "✅ Unified Trading System started (PID: $ICT_PID)"
else
    echo "❌ Failed to start Unified Trading System"
    echo "💡 Check logs/ict_monitor.log for details"
    exit 1
fi

echo ""
echo "🌐 WEB INTERFACES:"
echo "===================================="
echo "🎯 Main Dashboard:         http://localhost:5001"
echo "� Fundamental Analysis:   http://localhost:5001/fundamental"
echo "� API Endpoint:           http://localhost:5001/api/data"
echo "📈 Fundamental API:        http://localhost:5001/api/fundamental"
echo "🩺 Health Check:           http://localhost:5001/health"
echo ""

echo "🔍 SYSTEM STATUS:"
echo "===================================="

if ps aux | grep -q "[i]ct_enhanced_monitor.py"; then
    echo "✅ Unified Trading System: RUNNING ✨"
    echo "   ├─ ICT Trading Signals: Active"
    echo "   ├─ Real-time Prices: Active"
    echo "   ├─ Fundamental Analysis: Integrated"
    echo "   └─ Dashboard: http://localhost:5001"
    echo ""
    echo "🎉 SYSTEM SUCCESSFULLY STARTED!"
    echo ""
    echo "📝 Commands:"
    echo "   Stop:   ./scripts/setup/stop_all_systems.sh"
    echo "   Status: ./scripts/setup/check_all_systems.sh"
    echo "   Logs:   tail -f logs/ict_monitor.log"
else
    echo "❌ Unified Trading System: NOT RUNNING"
    echo "💡 Check logs/ict_monitor.log for error details"
    exit 1
fi

echo "===================================="