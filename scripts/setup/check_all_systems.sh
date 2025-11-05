#!/bin/bash

# 🔍 CHECK UNIFIED TRADING SYSTEM STATUS
# =====================================
# Checks status of unified ICT Enhanced Monitor - Port 5001
# Integrated Features: Day Trading, Fundamental Analysis, Auto Trading

echo "🔍 UNIFIED TRADING SYSTEM STATUS CHECK"
echo "========================================"

# Function to check if a process is running
check_process() {
    local process_name=$1
    local display_name=$2
    local port=$3
    
    if ps aux | grep -q "[$process_name]" || pgrep -f "$process_name" > /dev/null; then
        local pid=$(pgrep -f "$process_name")
        echo "✅ $display_name: RUNNING (PID: $pid)"
        
        # Check port if specified
        if [ ! -z "$port" ]; then
            if lsof -i :$port >/dev/null 2>&1; then
                echo "   🌐 Port $port: ACTIVE"
            else
                echo "   ⚠️  Port $port: NOT LISTENING"
            fi
        fi
        return 0
    else
        echo "❌ $display_name: NOT RUNNING"
        
        # Check if port is still occupied
        if [ ! -z "$port" ] && lsof -i :$port >/dev/null 2>&1; then
            echo "   ⚠️  Port $port: OCCUPIED BY OTHER PROCESS"
        fi
        return 1
    fi
}

# Function to test API endpoints
test_endpoint() {
    local url=$1
    local name=$2
    
    if curl -s --connect-timeout 3 "$url" >/dev/null 2>&1; then
        echo "   ✅ $name: RESPONDING"
        return 0
    else
        echo "   ❌ $name: NOT RESPONDING"
        return 1
    fi
}

echo "🎯 UNIFIED ICT TRADING SYSTEM:"
echo "----------------------------------------"
check_process "ict_enhanced_monitor.py" "Unified Trading System" "5001"
SYSTEM_RUNNING=$?

if [ $SYSTEM_RUNNING -eq 0 ]; then
    echo ""
    echo "🧪 TESTING INTEGRATED FEATURES:"
    echo "----------------------------------------"
    test_endpoint "http://localhost:5001/health" "Health Check"
    test_endpoint "http://localhost:5001/api/fundamental" "Fundamental Analysis API"
    test_endpoint "http://localhost:5001/" "Main Dashboard"
fi

echo ""
echo "🌐 WEB INTERFACES:"
echo "========================================"
echo "🎯 Main Dashboard:        http://localhost:5001"
echo "� Fundamental Analysis:  http://localhost:5001/fundamental"
echo "💼 Trading Signals:       http://localhost:5001/"

echo ""
echo "🔌 PORT STATUS:"
echo "========================================"

if lsof -i :5001 >/dev/null 2>&1; then
    local process_info=$(lsof -i :5001 | tail -n 1 | awk '{print $1, $2}')
    echo "🟢 Port 5001: IN USE ($process_info)"
else
    echo "⚪ Port 5001: FREE"
fi

echo ""
echo "📊 SYSTEM RESOURCES:"
echo "========================================"

# Check memory and CPU usage for trading process
if pgrep -f "ict_enhanced_monitor" > /dev/null; then
    echo "🖥️  Resource Usage:"
    ps -o pid,ppid,cmd,%mem,%cpu -p $(pgrep -f "ict_enhanced_monitor" | tr '\n' ',' | sed 's/,$//') 2>/dev/null | head -10
else
    echo "ℹ️  No trading process found for resource monitoring"
fi

echo ""
echo "📋 SYSTEM STATUS:"
echo "========================================"

if [ $SYSTEM_RUNNING -eq 0 ]; then
    echo "� Status: SYSTEM OPERATIONAL"
    echo "💡 To stop: ./scripts/setup/stop_all_systems.sh"
else
    echo "� Status: SYSTEM DOWN"
    echo "💡 To start: ./scripts/setup/start_all_systems.sh"
fi

# Check database status if ICT Monitor is running
if ps aux | grep -q "[i]ct_enhanced_monitor.py"; then
    echo ""
    echo "💾 DATABASE QUICK CHECK:"
    echo "========================================"
    
    if [ -f "databases/trading_data.db" ]; then
        echo "✅ Database file exists"
        
        # Quick database stats
        python3 -c "
import sqlite3
from datetime import date
try:
    conn = sqlite3.connect('databases/trading_data.db')
    cursor = conn.cursor()
    today = date.today().isoformat()
    
    cursor.execute('SELECT COUNT(*) FROM signals WHERE date(entry_time) = ?', (today,))
    signals = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM paper_trades WHERE date(entry_time) = ?', (today,))
    trades = cursor.fetchone()[0]
    
    print(f'📊 Today: {signals} signals, {trades} trades')
    conn.close()
except Exception as e:
    print(f'❌ Database error: {e}')
" 2>/dev/null || echo "⚠️  Could not check database stats"
    else
        echo "❌ Database file not found"
    fi
fi

echo ""
echo "========================================"
echo "🕐 Last checked: $(date)"
echo "========================================"