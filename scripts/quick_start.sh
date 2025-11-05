#!/bin/bash

# Simple startup script without error checking

echo "🚀 Starting Trading System..."

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Ensure FLASK_SECRET_KEY
if [ -z "$FLASK_SECRET_KEY" ]; then
    export FLASK_SECRET_KEY="dev-secret-key-$(date +%s)"
fi

# Kill existing
pkill -f "api_server.py" 2>/dev/null
pkill -f "ict_enhanced_monitor.py" 2>/dev/null  
pkill -f "vite" 2>/dev/null
sleep 2

# Start API server
echo "🔧 Starting API server on port 5001..."
nohup python3 api_server.py > logs/api_server.log 2>&1 &
sleep 3

# Start ICT monitor
echo "📊 Starting ICT monitor on port 5002..."
nohup python3 core/monitors/ict_enhanced_monitor.py --port 5002 > logs/monitor.log 2>&1 &
sleep 2

# Start frontend
echo "🎨 Starting frontend on port 5000..."
cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
cd ..

sleep 3

echo ""
echo "✅ System started!"
echo ""
echo "📊 Dashboard: http://localhost:5000"
echo "🔑 Login: demo@ict.com / demo123"
echo ""
echo "📝 Logs:"
echo "   API: tail -f logs/api_server.log"
echo "   Monitor: tail -f logs/monitor.log"  
echo "   Frontend: tail -f logs/frontend.log"
echo ""
