#!/bin/bash

# Quick Start Script for Development
# Starts the system in development mode with hot reloading

set -e

echo "🚀 Starting ICT Trading System (Development Mode)..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file"
fi

# Kill existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "api_server.py" || true
pkill -f "ict_enhanced_monitor.py" || true
pkill -f "vite" || true

sleep 2

# Start API server
echo -e "${BLUE}🔧 Starting API server...${NC}"
python3 api_server.py > logs/api_server.log 2>&1 &
API_PID=$!

sleep 3

# Start trading monitor
echo -e "${BLUE}📊 Starting trading monitor...${NC}"
python3 src/monitors/ict_enhanced_monitor.py > logs/monitor.log 2>&1 &
MONITOR_PID=$!

sleep 2

# Start frontend dev server
echo -e "${BLUE}🎨 Starting frontend (dev mode)...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

sleep 3

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ SYSTEM STARTED (Dev Mode)${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📊 Access Points:${NC}"
echo "   Dashboard:  http://localhost:3000"
echo "   API:        http://localhost:5001"
echo ""
echo -e "${BLUE}🔑 Demo Login:${NC}"
echo "   Email:      demo@ict.com"
echo "   Password:   demo123"
echo ""
echo -e "${BLUE}📝 PIDs:${NC}"
echo "   API:     $API_PID"
echo "   Monitor: $MONITOR_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping services...'; pkill -f 'api_server.py'; pkill -f 'ict_enhanced_monitor.py'; pkill -f 'vite'; echo '✅ All services stopped'; exit 0" INT

# Keep script running
tail -f /dev/null
