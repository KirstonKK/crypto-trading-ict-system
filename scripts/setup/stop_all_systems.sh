#!/bin/bash

# 🛑 STOP UNIFIED TRADING SYSTEM - ONE COMMAND
# ============================================
# Stops the unified ICT Enhanced Monitor

echo "🛑 STOPPING UNIFIED TRADING SYSTEM"
echo "===================================="
echo "🎯 Stopping ICT Trading Monitor..."
echo "===================================="

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

# Stop Unified ICT Enhanced Monitor
stop_process "ict_enhanced_monitor.py" "Unified Trading System"
STOPPED=$?

echo ""
echo "🔌 FREEING PORT:"
echo "===================================="

# Kill any remaining processes on port 5001
kill_port 5001 "ICT Monitor"

echo ""
echo "🧹 CLEANUP:"
echo "===================================="

# Kill any remaining Python trading processes
if pgrep -f "python.*trading" > /dev/null; then
    echo "🔄 Cleaning up remaining trading processes..."
    pkill -f "python.*trading"
    sleep 1
fi

echo ""
echo "🔍 FINAL STATUS CHECK:"
echo "===================================="

if ps aux | grep -q "[i]ct_enhanced_monitor.py"; then
    echo "❌ Unified Trading System: STILL RUNNING"
    STILL_RUNNING=1
else
    echo "✅ Unified Trading System: STOPPED"
    STILL_RUNNING=0
fi

# Check port
echo ""
echo "🔌 PORT STATUS:"
echo "===================================="

if lsof -i :5001 >/dev/null 2>&1; then
    echo "❌ Port 5001: STILL IN USE"
else
    echo "✅ Port 5001: FREE"
fi

echo "===================================="

if [ $STILL_RUNNING -eq 0 ]; then
    echo "🎉 SYSTEM SUCCESSFULLY STOPPED!"
    echo ""
    echo "📝 To start system: ./scripts/setup/start_all_systems.sh"
    echo "🔍 To check status: ./scripts/setup/check_all_systems.sh"
else
    echo "⚠️  WARNING: System still running"
    echo "💡 You may need to manually kill remaining processes:"
    echo "   sudo pkill -9 -f ict_enhanced_monitor.py"
    echo "   sudo lsof -ti:5001 | xargs kill -9"
fi

echo "===================================="