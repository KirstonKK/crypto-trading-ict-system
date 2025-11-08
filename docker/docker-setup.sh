#!/bin/bash
# =============================================================================
# Docker Quick Setup Script
# Kirston's Crypto Trading System
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║        🐳 DOCKER SETUP - KIRSTON'S TRADING SYSTEM 🐳            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# -----------------------------------------------------------------------------
# Step 1: Check Prerequisites
# -----------------------------------------------------------------------------
echo -e "${BLUE}📋 Step 1: Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo -e "${GREEN}✅ Docker found: $(docker --version)${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed!${NC}"
    echo "Please install Docker Compose"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose found: $(docker-compose --version)${NC}"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo "Please start Docker Desktop"
    exit 1
fi
echo -e "${GREEN}✅ Docker daemon is running${NC}"

# -----------------------------------------------------------------------------
# Step 2: Create Environment File
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}📄 Step 2: Setting up environment file...${NC}"

if [ -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file already exists${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing .env file"
    else
        cp .env.docker.example .env
        echo -e "${GREEN}✅ Created new .env from template${NC}"
    fi
else
    cp .env.docker.example .env
    echo -e "${GREEN}✅ Created .env from template${NC}"
fi

echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env with your Bybit API credentials!${NC}"
echo "   nano .env  # or use your preferred editor"

# -----------------------------------------------------------------------------
# Step 3: Create Volume Directories
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}📁 Step 3: Creating volume directories...${NC}"

mkdir -p docker-volumes/data
mkdir -p docker-volumes/logs
mkdir -p docker-volumes/results

chmod -R 755 docker-volumes/

echo -e "${GREEN}✅ Volume directories created:${NC}"
echo "   - docker-volumes/data    (database & cache)"
echo "   - docker-volumes/logs    (application logs)"
echo "   - docker-volumes/results (trading results)"

# -----------------------------------------------------------------------------
# Step 4: Build Docker Image
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}🔨 Step 4: Building Docker image...${NC}"
echo "This may take a few minutes on first run..."

if docker-compose build; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Docker build failed!${NC}"
    exit 1
fi

# -----------------------------------------------------------------------------
# Step 5: Configuration Summary
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}📊 Setup Complete!${NC}"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo ""
echo "1. Edit your API credentials:"
echo "   ${YELLOW}nano .env${NC}"
echo ""
echo "2. Start the system:"
echo "   ${YELLOW}docker-compose up -d${NC}"
echo ""
echo "3. Check status:"
echo "   ${YELLOW}docker-compose ps${NC}"
echo ""
echo "4. View logs:"
echo "   ${YELLOW}docker-compose logs -f ict-monitor${NC}"
echo ""
echo "5. Access dashboard:"
echo "   ${YELLOW}http://localhost:5001${NC}"
echo ""
echo -e "${BLUE}📚 For more details, see: DOCKER_README.md${NC}"
echo ""

# -----------------------------------------------------------------------------
# Optional: Offer to start immediately
# -----------------------------------------------------------------------------
read -p "Do you want to start the system now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}🚀 Starting Kirston's Trading System...${NC}"
    docker-compose up -d
    echo ""
    echo -e "${GREEN}✅ System started!${NC}"
    echo ""
    echo "Dashboard: http://localhost:5001"
    echo "View logs: docker-compose logs -f"
    echo ""
fi

echo -e "${GREEN}Happy Trading! 🚀📈${NC}"
