#!/bin/bash

# 🛑 STOP ALL TRADING SYSTEMS - ONE COMMAND
# =========================================
# Stops all three systems gracefully:
# 1. ICT Enhanced Monitor (Day Trading)
# 2. Demo Trading System (Auto Trading)
# 3. Fundamental Analysis System (Long-term)

echo "🛑 STOPPING ALL TRADING SYSTEMS"
echo "==============================="
echo "🎯 Stopping ICT Enhanced Monitor..."
echo "📊 Stopping Demo Trading System..."
echo "🔍 Stopping Fundamental Analysis System..."
echo "==============================="

# Function to gracefully stop a process by name
stop_process() {
    local process_name=$1
    local display_name=$2
    
    if pgrep -f "$process_name" > /dev/null; then
        echo "🔄 Stopping $display_name..."
        pkill -f "$process_name"
        sleep 2
        
        # Check if process is still running
        if pgrep -f "$process_name" > /dev/null; then
            echo "⚠️  Force killing $display_name..."
            pkill -9 -f "$process_name"
            sleep 1
        fi
        
        # Final check
        if ! pgrep -f "$process_name" > /dev/null; then
            echo "✅ $display_name stopped"
            return 0
        else
            echo "❌ Failed to stop $display_name"
            return 1
        fi
    else
        echo "ℹ️  $display_name was not running"
        return 0
    fi
}

# Function to kill process on specific port
kill_port() {
    local port=$1
    local name=$2
    
    if lsof -i :$port >/dev/null 2>&1; then
        echo "🔄 Killing process on port $port ($name)..."
        lsof -ti:$port | xargs kill -9 2>/dev/null
        sleep 1
        
        if ! lsof -i :$port >/dev/null 2>&1; then
            echo "✅ Port $port freed"
        else
            echo "❌ Failed to free port $port"
        fi
    fi
}

STOPPED_COUNT=0

# Stop ICT Enhanced Monitor
stop_process "ict_enhanced_monitor.py" "ICT Enhanced Monitor"
if [ $? -eq 0 ]; then
    STOPPED_COUNT=$((STOPPED_COUNT + 1))
fi

# Stop Demo Trading System
stop_process "demo_trading_system.py" "Demo Trading System"
if [ $? -eq 0 ]; then
    STOPPED_COUNT=$((STOPPED_COUNT + 1))
fi

# Stop Fundamental Analysis System
stop_process "fundamental_analysis_server.py" "Fundamental Analysis System"
if [ $? -eq 0 ]; then
    STOPPED_COUNT=$((STOPPED_COUNT + 1))
fi

echo ""
echo "🔌 FREEING PORTS:"
echo "==============================="

# Kill any remaining processes on specific ports
kill_port 5001 "ICT Monitor"
kill_port 5002 "Fundamental Analysis"
kill_port 8000 "Demo Trading (if applicable)"

echo ""
echo "🧹 CLEANUP:"
echo "==============================="

# Kill any remaining Python trading processes
if pgrep -f "python.*trading" > /dev/null; then
    echo "🔄 Cleaning up remaining trading processes..."
    pkill -f "python.*trading"
    sleep 1
fi

# Kill any remaining launch scripts
if pgrep -f "launch_fundamental_analysis" > /dev/null; then
    echo "🔄 Stopping launch scripts..."
    pkill -f "launch_fundamental_analysis"
    sleep 1
fi

echo ""
echo "🔍 FINAL STATUS CHECK:"
echo "==============================="

STILL_RUNNING=0

if ps aux | grep -q "[i]ct_enhanced_monitor.py"; then
    echo "❌ ICT Enhanced Monitor: STILL RUNNING"
    STILL_RUNNING=$((STILL_RUNNING + 1))
else
    echo "✅ ICT Enhanced Monitor: STOPPED"
fi

if ps aux | grep -q "[d]emo_trading_system.py"; then
    echo "❌ Demo Trading System: STILL RUNNING"
    STILL_RUNNING=$((STILL_RUNNING + 1))
else
    echo "✅ Demo Trading System: STOPPED"
fi

if ps aux | grep -q "[f]undamental_analysis_server.py"; then
    echo "❌ Fundamental Analysis: STILL RUNNING"
    STILL_RUNNING=$((STILL_RUNNING + 1))
else
    echo "✅ Fundamental Analysis: STOPPED"
fi

# Check ports
echo ""
echo "🔌 PORT STATUS:"
echo "==============================="

for port in 5001 5002 8000; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo "❌ Port $port: STILL IN USE"
    else
        echo "✅ Port $port: FREE"
    fi
done

echo "==============================="

if [ $STILL_RUNNING -eq 0 ]; then
    echo "🎉 ALL SYSTEMS SUCCESSFULLY STOPPED!"
    echo ""
    echo "📝 To start all systems: ./start_all_systems.sh"
    echo "🔍 To check status: ./check_all_systems.sh"
else
    echo "⚠️  WARNING: $STILL_RUNNING system(s) still running"
    echo "💡 You may need to manually kill remaining processes:"
    echo "   sudo pkill -9 -f python"
    echo "   sudo lsof -ti:5001,5002,8000 | xargs kill -9"
fi

echo "==============================="