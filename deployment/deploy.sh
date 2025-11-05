#!/bin/bash

# ICT Trading System - Production Deployment Script
# Deploys the full system with authentication, dashboard, and notifications

set -e

echo "🚀 Deploying ICT Trading System..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============ Step 1: Environment Setup ============
echo -e "${BLUE}📋 Step 1: Setting up environment...${NC}"

if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file. Please configure it before continuing.${NC}"
    exit 1
fi

# Load environment
source .env

# ============ Step 2: Install Python Dependencies ============
echo -e "${BLUE}📦 Step 2: Installing Python dependencies...${NC}"

python3 -m pip install --upgrade pip
pip3 install -r requirements.txt

echo -e "${GREEN}✅ Python dependencies installed${NC}"

# ============ Step 3: Install Frontend Dependencies ============
echo -e "${BLUE}📦 Step 3: Installing frontend dependencies...${NC}"

cd frontend
npm install
echo -e "${GREEN}✅ Frontend dependencies installed${NC}"

# ============ Step 4: Build Frontend ============
echo -e "${BLUE}🔨 Step 4: Building frontend...${NC}"

npm run build
echo -e "${GREEN}✅ Frontend built successfully${NC}"

cd ..

# ============ Step 5: Database Setup ============
echo -e "${BLUE}💾 Step 5: Setting up database...${NC}"

# Create data directory if it doesn't exist
mkdir -p data

# Run database initialization (this will be done by api_server.py on first run)
echo -e "${GREEN}✅ Database directory ready${NC}"

# ============ Step 6: Create Logs Directory ============
echo -e "${BLUE}📝 Step 6: Creating logs directory...${NC}"

mkdir -p logs
echo -e "${GREEN}✅ Logs directory created${NC}"

# ============ Step 7: Start Services ============
echo -e "${BLUE}🚀 Step 7: Starting services...${NC}"

# Kill existing processes
pkill -f "api_server.py" || true
pkill -f "ict_enhanced_monitor.py" || true
pkill -f "vite" || true

echo "Starting API server..."
nohup python3 api_server.py > logs/api_server.log 2>&1 &
API_PID=$!
echo "API Server PID: $API_PID"

sleep 3

echo "Starting trading monitor..."
nohup python3 src/monitors/ict_enhanced_monitor.py > logs/monitor.log 2>&1 &
MONITOR_PID=$!
echo "Monitor PID: $MONITOR_PID"

sleep 2

echo "Starting frontend (production preview)..."
cd frontend
nohup npm run preview > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
cd ..

# ============ Step 8: Verify Services ============
echo -e "${BLUE}🔍 Step 8: Verifying services...${NC}"

sleep 5

# Check if API is running
if curl -s http://localhost:5001/api/health > /dev/null; then
    echo -e "${GREEN}✅ API Server is running${NC}"
else
    echo -e "${YELLOW}⚠️  API Server may not be running properly${NC}"
fi

# Check if frontend is accessible
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✅ Frontend is running${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend may not be running properly${NC}"
fi

# ============ Deployment Complete ============
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  🎉 DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📊 Access Points:${NC}"
echo -e "   Dashboard:  ${GREEN}http://localhost:3000${NC}"
echo -e "   API:        ${GREEN}http://localhost:5001${NC}"
echo -e "   Health:     ${GREEN}http://localhost:5001/api/health${NC}"
echo ""
echo -e "${BLUE}🔑 Demo Credentials:${NC}"
echo -e "   Email:      ${GREEN}demo@ict.com${NC}"
echo -e "   Password:   ${GREEN}demo123${NC}"
echo ""
echo -e "${BLUE}📝 Service PIDs:${NC}"
echo -e "   API Server:  ${API_PID}"
echo -e "   Monitor:     ${MONITOR_PID}"
echo -e "   Frontend:    ${FRONTEND_PID}"
echo ""
echo -e "${BLUE}📋 Logs Location:${NC}"
echo -e "   API:         logs/api_server.log"
echo -e "   Monitor:     logs/monitor.log"
echo -e "   Frontend:    logs/frontend.log"
echo ""
echo -e "${YELLOW}💡 To stop services:${NC}"
echo -e "   pkill -f 'api_server.py'"
echo -e "   pkill -f 'ict_enhanced_monitor.py'"
echo -e "   pkill -f 'vite'"
echo ""
