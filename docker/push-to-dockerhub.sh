#!/bin/bash

# =============================================================================
# Push Trading System Docker Image to Docker Hub
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Docker Hub configuration
DOCKER_HUB_USERNAME="${1:-kirstonkk}"  # Pass username as first argument or use default
IMAGE_NAME="crypto-trading-ict"
VERSION="${2:-latest}"  # Pass version as second argument or use 'latest'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Push Trading System to Docker Hub                       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is running
echo -e "${YELLOW}[1/6]${NC} Checking Docker status..."
if ! /usr/local/bin/docker info >/dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check if logged in to Docker Hub
echo -e "${YELLOW}[2/6]${NC} Checking Docker Hub authentication..."
if ! /usr/local/bin/docker info 2>&1 | grep -q "Username:"; then
    echo -e "${YELLOW}⚠ Not logged in to Docker Hub${NC}"
    echo "Please login with your Docker Hub credentials:"
    /usr/local/bin/docker login
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Login failed${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ Authenticated with Docker Hub${NC}"
echo ""

# Navigate to docker directory
cd "$(dirname "$0")"

# Build the Docker image
echo -e "${YELLOW}[3/6]${NC} Building Docker image..."
echo "Image: ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${VERSION}"
/usr/local/bin/docker build -t ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${VERSION} .
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Image built successfully${NC}"
echo ""

# Tag with 'latest' if version is specified
if [ "$VERSION" != "latest" ]; then
    echo -e "${YELLOW}[4/6]${NC} Tagging image as 'latest'..."
    /usr/local/bin/docker tag ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${VERSION} ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest
    echo -e "${GREEN}✓ Tagged as latest${NC}"
    echo ""
else
    echo -e "${YELLOW}[4/6]${NC} Using 'latest' tag (skipping additional tagging)"
    echo ""
fi

# Push versioned image
echo -e "${YELLOW}[5/6]${NC} Pushing ${VERSION} image to Docker Hub..."
/usr/local/bin/docker push ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${VERSION}
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Push failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Pushed ${VERSION} successfully${NC}"
echo ""

# Push latest tag if different from version
if [ "$VERSION" != "latest" ]; then
    echo -e "${YELLOW}[6/6]${NC} Pushing 'latest' tag to Docker Hub..."
    /usr/local/bin/docker push ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Push failed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Pushed 'latest' successfully${NC}"
    echo ""
else
    echo -e "${YELLOW}[6/6]${NC} Latest tag already pushed (same as ${VERSION})"
    echo ""
fi

# Success summary
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  ✓ SUCCESS!                                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📦 Docker Hub Repository:${NC}"
echo "   https://hub.docker.com/r/${DOCKER_HUB_USERNAME}/${IMAGE_NAME}"
echo ""
echo -e "${BLUE}🚀 Share this with your team:${NC}"
echo "   docker pull ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest"
echo ""
echo -e "${BLUE}📋 Quick Start for Other Developers:${NC}"
echo "   git clone https://github.com/KirstonKK/crypto-trading-ict-system.git"
echo "   cd crypto-trading-ict-system/docker"
echo "   cp .env.docker.example .env"
echo "   # Edit .env with API credentials"
echo "   docker-compose -f docker-compose.registry.yml up -d"
echo ""
echo -e "${YELLOW}💡 Tip:${NC} Update docker-compose.registry.yml with your Docker Hub username if different"
echo ""

# List local images
echo -e "${BLUE}📦 Local Images:${NC}"
/usr/local/bin/docker images | grep ${IMAGE_NAME} || echo "No local images found"
echo ""
