#!/bin/bash
# =============================================================================
# Docker Dashboard Diagnostic Script
# =============================================================================
# Run this script if you're seeing a blue screen instead of the dashboard
# Usage: ./diagnose_blue_screen.sh
# =============================================================================

echo "🔍 DOCKER TRADING DASHBOARD DIAGNOSTICS"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASS=0
FAIL=0

# Function to print test result
check_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        ((FAIL++))
    fi
}

# Test 1: Docker installed and running
echo "Test 1: Docker Installation"
echo "----------------------------"
if command -v docker &> /dev/null; then
    check_result 0 "Docker is installed"
    docker version > /dev/null 2>&1
    check_result $? "Docker daemon is running"
else
    check_result 1 "Docker is NOT installed"
fi
echo ""

# Test 2: Container status
echo "Test 2: Container Status"
echo "------------------------"
CONTAINER_RUNNING=$(docker ps | grep crypto-trading-ict | wc -l)
if [ $CONTAINER_RUNNING -gt 0 ]; then
    check_result 0 "Container 'crypto-trading-ict' is running"
    
    # Get container details
    CONTAINER_ID=$(docker ps | grep crypto-trading-ict | awk '{print $1}')
    echo "   Container ID: $CONTAINER_ID"
    
    # Check uptime
    UPTIME=$(docker ps --format "{{.Status}}" --filter "name=crypto-trading-ict")
    echo "   Uptime: $UPTIME"
else
    check_result 1 "Container 'crypto-trading-ict' is NOT running"
    
    # Check if container exists but stopped
    CONTAINER_EXISTS=$(docker ps -a | grep crypto-trading-ict | wc -l)
    if [ $CONTAINER_EXISTS -gt 0 ]; then
        echo -e "   ${YELLOW}⚠️  Container exists but is stopped${NC}"
        echo "   Run: docker compose up -d"
    else
        echo -e "   ${YELLOW}⚠️  Container does not exist${NC}"
        echo "   Run: docker pull kirston/crypto-trading-ict:latest"
        echo "   Then: docker compose up -d"
    fi
fi
echo ""

# Test 3: Port accessibility
echo "Test 3: Port 5001 Accessibility"
echo "--------------------------------"
if command -v lsof &> /dev/null; then
    PORT_IN_USE=$(lsof -i :5001 2>/dev/null | grep LISTEN | wc -l)
    if [ $PORT_IN_USE -gt 0 ]; then
        check_result 0 "Port 5001 is listening"
        lsof -i :5001 | grep LISTEN
    else
        check_result 1 "Port 5001 is NOT listening"
    fi
elif command -v netstat &> /dev/null; then
    PORT_IN_USE=$(netstat -an | grep :5001 | grep LISTEN | wc -l)
    if [ $PORT_IN_USE -gt 0 ]; then
        check_result 0 "Port 5001 is listening"
    else
        check_result 1 "Port 5001 is NOT listening"
    fi
else
    echo -e "${YELLOW}⚠️  Cannot check port (lsof/netstat not found)${NC}"
fi
echo ""

# Test 4: HTTP Response
echo "Test 4: HTTP Response Test"
echo "---------------------------"
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/ 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        check_result 0 "Server responds with HTTP 200 OK"
        
        # Check content length
        CONTENT_LENGTH=$(curl -s -I http://localhost:5001/ 2>/dev/null | grep -i content-length | awk '{print $2}' | tr -d '\r')
        if [ ! -z "$CONTENT_LENGTH" ]; then
            echo "   Content-Length: $CONTENT_LENGTH bytes"
            if [ $CONTENT_LENGTH -gt 10000 ]; then
                echo -e "   ${GREEN}✅ Response has content (HTML dashboard)${NC}"
            else
                echo -e "   ${RED}❌ Response too small (possibly error page)${NC}"
            fi
        fi
    else
        check_result 1 "Server responds with HTTP $HTTP_CODE (expected 200)"
    fi
else
    echo -e "${YELLOW}⚠️  curl not installed, cannot test HTTP${NC}"
fi
echo ""

# Test 5: Container logs for errors
echo "Test 5: Container Error Check"
echo "------------------------------"
if [ $CONTAINER_RUNNING -gt 0 ]; then
    ERROR_COUNT=$(docker logs crypto-trading-ict --tail 100 2>&1 | grep -i error | wc -l)
    if [ $ERROR_COUNT -eq 0 ]; then
        check_result 0 "No errors in recent container logs"
    else
        check_result 1 "Found $ERROR_COUNT error(s) in container logs"
        echo ""
        echo "Recent errors:"
        docker logs crypto-trading-ict --tail 100 2>&1 | grep -i error | tail -5
    fi
fi
echo ""

# Test 6: .env file check
echo "Test 6: Environment Configuration"
echo "----------------------------------"
if [ -f .env ]; then
    check_result 0 ".env file exists"
    
    # Check for required variables
    if grep -q "BYBIT_API_KEY" .env; then
        check_result 0 "BYBIT_API_KEY found in .env"
    else
        check_result 1 "BYBIT_API_KEY NOT found in .env"
    fi
    
    if grep -q "BYBIT_API_SECRET" .env; then
        check_result 0 "BYBIT_API_SECRET found in .env"
    else
        check_result 1 "BYBIT_API_SECRET NOT found in .env"
    fi
else
    check_result 1 ".env file does NOT exist"
    echo "   Create .env file with Bybit API credentials"
fi
echo ""

# Test 7: Docker image version
echo "Test 7: Docker Image Version"
echo "-----------------------------"
IMAGE_EXISTS=$(docker images | grep crypto-trading-ict | wc -l)
if [ $IMAGE_EXISTS -gt 0 ]; then
    check_result 0 "Docker image exists locally"
    
    # Get image details
    IMAGE_ID=$(docker images kirston/crypto-trading-ict:latest --format "{{.ID}}")
    IMAGE_SIZE=$(docker images kirston/crypto-trading-ict:latest --format "{{.Size}}")
    IMAGE_CREATED=$(docker images kirston/crypto-trading-ict:latest --format "{{.CreatedSince}}")
    
    echo "   Image ID: $IMAGE_ID"
    echo "   Size: $IMAGE_SIZE"
    echo "   Created: $IMAGE_CREATED"
    
    # Check if using latest
    echo ""
    echo "   Checking for updates..."
    docker pull kirston/crypto-trading-ict:latest > /dev/null 2>&1
    echo "   ✅ Image is up to date"
else
    check_result 1 "Docker image NOT found locally"
    echo "   Run: docker pull kirston/crypto-trading-ict:latest"
fi
echo ""

# Summary
echo "========================================"
echo "DIAGNOSTIC SUMMARY"
echo "========================================"
echo -e "Tests Passed: ${GREEN}$PASS${NC}"
echo -e "Tests Failed: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    echo ""
    echo "Your Docker container should be working correctly."
    echo "If you still see a blue screen:"
    echo ""
    echo "1. Clear your browser cache (Ctrl+Shift+Delete)"
    echo "2. Try incognito/private mode (Ctrl+Shift+N)"
    echo "3. Check browser console for errors (F12)"
    echo "4. Try accessing: http://127.0.0.1:5001/"
    echo ""
    echo "If problem persists, send this output to the team lead."
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Recommended actions:"
    echo ""
    
    if [ $CONTAINER_RUNNING -eq 0 ]; then
        echo "1. Start the container:"
        echo "   docker compose up -d"
        echo ""
    fi
    
    if [ ! -f .env ]; then
        echo "2. Create .env file with Bybit credentials"
        echo ""
    fi
    
    if [ "$HTTP_CODE" != "200" ]; then
        echo "3. Check container logs for errors:"
        echo "   docker logs crypto-trading-ict --tail 50"
        echo ""
    fi
    
    echo "4. For full troubleshooting guide, see:"
    echo "   docs/TROUBLESHOOTING_BLUE_SCREEN.md"
    echo ""
    echo "5. Send this diagnostic output to your team lead"
fi

echo ""
echo "========================================"
echo "ADDITIONAL INFORMATION"
echo "========================================"
echo "Operating System: $(uname -s)"
echo "Docker Version: $(docker --version 2>/dev/null || echo 'Not found')"
echo "Current Directory: $(pwd)"
echo "Date: $(date)"
echo ""

# Offer to save report
echo "💾 Save this diagnostic report? (y/n)"
read -r -n 1 SAVE_REPORT
echo ""

if [[ $SAVE_REPORT =~ ^[Yy]$ ]]; then
    REPORT_FILE="diagnostic_report_$(date +%Y%m%d_%H%M%S).txt"
    $0 > "$REPORT_FILE" 2>&1
    echo "Report saved to: $REPORT_FILE"
    echo "Send this file to your team lead for analysis"
fi

echo ""
echo "🔍 Diagnostics complete!"
