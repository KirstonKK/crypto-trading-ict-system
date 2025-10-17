#!/bin/bash

# 🔍 CHECK ALL TRADING SYSTEMS STATUS
# ===================================
# Checks status of all three systems:
# 1. ICT Enhanced Monitor (Day Trading) - Port 5001
# 2. Demo Trading System (Auto Trading)
# 3. Fundamental Analysis System (Long-term) - Port 5002

echo "🔍 TRADING SYSTEMS STATUS CHECK"
echo "==============================="

# Function to check if a process is running
check_process() {
    local process_name=$1
    local display_name=$2
    local port=$3
    
    if ps aux | grep -q "[i]ct_enhanced_monitor.py"; then
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
        echo "   ✅ API: RESPONDING"
        return 0
    else
        echo "   ❌ API: NOT RESPONDING"
        return 1
    fi
}

echo "🎯 ICT ENHANCED MONITOR (Day Trading):"
echo "-------------------------------------"
check_process "ict_enhanced_monitor.py" "ICT Enhanced Monitor" "5001"
if [ $? -eq 0 ]; then
    test_endpoint "http://localhost:5001/health" "ICT Monitor"
fi

echo ""
echo "📊 DEMO TRADING SYSTEM (Auto Trading):"
echo "--------------------------------------"
check_process "demo_trading_system.py" "Demo Trading System"

echo ""
echo "🔍 FUNDAMENTAL ANALYSIS (Long-term):"
echo "------------------------------------"
check_process "fundamental_analysis_server.py" "Fundamental Analysis System" "5002"
if [ $? -eq 0 ]; then
    test_endpoint "http://localhost:5002/api/health" "Fundamental Analysis"
fi

echo ""
echo "🌐 WEB INTERFACES:"
echo "==============================="
echo "🎯 ICT Day Trading:     http://localhost:5001"
echo "🔍 Fundamental Analysis: http://localhost:5002"

echo ""
echo "🔌 PORT USAGE:"
echo "==============================="

for port in 5001 5002 8000; do
    if lsof -i :$port >/dev/null 2>&1; then
        local process_info=$(lsof -i :$port | tail -n 1 | awk '{print $1, $2}')
        echo "🟢 Port $port: IN USE ($process_info)"
    else
        echo "⚪ Port $port: FREE"
    fi
done

echo ""
echo "📊 SYSTEM RESOURCES:"
echo "==============================="

# Check memory and CPU usage for trading processes
if pgrep -f "ict_enhanced_monitor\|demo_trading_system\|fundamental_analysis" > /dev/null; then
    echo "🖥️  Resource Usage:"
    ps -o pid,ppid,cmd,%mem,%cpu -p $(pgrep -f "ict_enhanced_monitor\|demo_trading_system\|fundamental_analysis" | tr '\n' ',' | sed 's/,$//') 2>/dev/null | head -10
else
    echo "ℹ️  No trading processes found for resource monitoring"
fi

echo ""
echo "📋 QUICK STATS:"
echo "==============================="

RUNNING_COUNT=0
TOTAL_SYSTEMS=3

# Count running systems
ps aux | grep -q "[i]ct_enhanced_monitor.py" && RUNNING_COUNT=$((RUNNING_COUNT + 1))
ps aux | grep -q "[d]emo_trading_system.py" && RUNNING_COUNT=$((RUNNING_COUNT + 1))
ps aux | grep -q "[f]undamental_analysis_server.py" && RUNNING_COUNT=$((RUNNING_COUNT + 1))

echo "🎯 Systems Running: $RUNNING_COUNT/$TOTAL_SYSTEMS"

if [ $RUNNING_COUNT -eq 0 ]; then
    echo "🔴 Status: ALL SYSTEMS DOWN"
    echo "💡 To start all: ./start_all_systems.sh"
elif [ $RUNNING_COUNT -eq $TOTAL_SYSTEMS ]; then
    echo "🟢 Status: ALL SYSTEMS OPERATIONAL"
    echo "💡 To stop all: ./stop_all_systems.sh"
else
    echo "🟡 Status: PARTIAL OPERATION"
    echo "💡 Some systems need attention"
fi

# Check database status if ICT Monitor is running
if ps aux | grep -q "[i]ct_enhanced_monitor.py"; then
    echo ""
    echo "💾 DATABASE QUICK CHECK:"
    echo "==============================="
    
    if [ -f "trading_data.db" ]; then
        echo "✅ Database file exists"
        
        # Quick database stats
        python3 -c "
import sqlite3
from datetime import date
try:
    conn = sqlite3.connect('trading_data.db')
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
echo "==============================="
echo "🕐 Last checked: $(date)"
echo "==============================="