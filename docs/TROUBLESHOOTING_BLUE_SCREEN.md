# 🔍 Troubleshooting Blue Screen Dashboard Issue

## Problem: Developer Sees Only Blue Screen (No Dashboard)

When your team member pulls and runs the Docker image but sees only a blank blue screen instead of the trading dashboard.

---

## 🚨 Quick Diagnostic Steps

### Step 1: Check Container is Actually Running

```bash
# Check if container is running
docker ps | grep crypto-trading-ict

# Expected output: Should show container running with port 5001 mapped
# If not running, check why:
docker ps -a | grep crypto-trading-ict
docker logs crypto-trading-ict --tail 50
```

**If container isn't running:**

- Check logs for startup errors
- Verify .env file exists with API credentials
- Check port 5001 isn't already in use

---

### Step 2: Test Direct HTTP Response

```bash
# Test if server responds (NOT in browser)
curl -I http://localhost:5001/

# ✅ GOOD: HTTP/1.1 200 OK
# ❌ BAD: Connection refused / timeout / redirect
```

**If curl works but browser shows blue screen:**
→ This is a **browser-side issue**, not server issue

---

### Step 3: Check Browser Console for Errors

Tell your dev to:

1. Open the dashboard: `http://localhost:5001/`
2. Open browser DevTools: `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
3. Go to **Console** tab
4. Look for RED errors

**Common Errors to Report:**

```javascript
// ❌ WebSocket connection failed
WebSocket connection to 'ws://localhost:5001/socket.io/' failed

// ❌ CORS policy error
Access to fetch at 'http://localhost:5001/api/data' blocked by CORS policy

// ❌ 404 Not Found
GET http://localhost:5001/static/... 404 (Not Found)

// ❌ CSP violation
Refused to load the script because it violates Content Security Policy
```

---

### Step 4: Check Network Tab

In DevTools → **Network** tab:

1. Refresh the page
2. Look at the first request to `http://localhost:5001/`
3. Check:
   - **Status Code**: Should be `200`
   - **Response**: Should contain HTML (not empty)
   - **Size**: Should be ~48KB (not 0 bytes)

**Screenshots to Request:**

- Network tab showing the request
- Response preview/response body

---

## 🔧 Common Causes & Fixes

### Cause 1: Browser Cache (Most Common!)

**Symptom**: Worked before, suddenly blue screen  
**Fix**:

```bash
# Clear browser cache completely
# Chrome: Ctrl+Shift+Delete → Clear cached images and files
# Firefox: Ctrl+Shift+Delete → Cached Web Content

# Or try incognito/private mode
# Chrome: Ctrl+Shift+N
# Firefox: Ctrl+Shift+P
```

---

### Cause 2: Docker Network Issue

**Symptom**: Container running but can't access dashboard  
**Fix**:

```bash
# Check Docker network
docker network ls
docker network inspect tradingalgoithm_trading-network

# Restart Docker networking
docker compose down
docker compose up -d

# Or use Docker bridge IP instead of localhost
docker inspect crypto-trading-ict | grep IPAddress
# Then access: http://172.18.0.2:5001 (use actual IP shown)
```

---

### Cause 3: Port Conflict

**Symptom**: Another service using port 5001  
**Fix**:

```bash
# Check what's using port 5001
lsof -i :5001

# If something else is using it, either:
# 1. Stop the other service
# 2. Or change docker-compose.yml ports:
ports:
  - "5002:5001"  # Map to different host port
```

---

### Cause 4: Firewall Blocking

**Symptom**: curl works but browser doesn't  
**Fix**:

```bash
# macOS: Check firewall settings
# System Preferences → Security & Privacy → Firewall

# Allow Docker Desktop through firewall
# Or temporarily disable firewall for testing
```

---

### Cause 5: Wrong URL

**Symptom**: Dev using wrong address  
**Fix**:

```bash
# ✅ CORRECT URLs:
http://localhost:5001/
http://127.0.0.1:5001/
http://0.0.0.0:5001/  # May not work on all systems

# ❌ WRONG URLs:
https://localhost:5001/  # No HTTPS in container
http://localhost:5001/monitor/  # Wrong path (redirect happens)
```

---

## 📋 Information to Collect from Developer

Ask your dev to run these commands and send you the output:

### Command 1: Docker Status

```bash
docker ps -a | grep crypto-trading-ict
```

### Command 2: Container Logs

```bash
docker logs crypto-trading-ict --tail 100 > docker_logs.txt
# Send docker_logs.txt
```

### Command 3: Curl Test

```bash
curl -v http://localhost:5001/ > curl_output.txt 2>&1
# Send curl_output.txt
```

### Command 4: Port Check

```bash
lsof -i :5001 > port_check.txt 2>&1
# Or on Windows:
netstat -ano | findstr :5001
```

### Command 5: Browser Info

- Browser name and version
- Operating system
- Screenshot of blue screen
- Screenshot of DevTools Console (F12)
- Screenshot of DevTools Network tab

---

## 🎯 Step-by-Step Debugging Protocol

### For Developer Experiencing Issue:

```bash
# 1. Stop everything
docker compose down

# 2. Pull latest image (Python 3.12 security update)
docker pull kirston/crypto-trading-ict:latest

# 3. Verify image pulled
docker images | grep crypto-trading-ict

# 4. Start fresh
docker compose up -d

# 5. Wait 15 seconds for startup
sleep 15

# 6. Check container health
docker ps | grep crypto-trading-ict

# 7. Check logs for errors
docker logs crypto-trading-ict --tail 50

# 8. Test with curl
curl -I http://localhost:5001/

# 9. If curl works, try browser in incognito mode
# Chrome: Ctrl+Shift+N
# Firefox: Ctrl+Shift+P

# 10. Access: http://localhost:5001/
```

---

## 🔍 Advanced Diagnostics

### Check Flask is Serving Correctly

```bash
# Execute command inside container
docker exec -it crypto-trading-ict curl -I http://localhost:5001/

# Should return:
# HTTP/1.1 200 OK
# Server: Werkzeug/3.1.3 Python/3.12.12
# Content-Type: text/html; charset=utf-8
```

### Check HTML Content

```bash
# Get first 100 lines of HTML response
curl -s http://localhost:5001/ | head -100

# Should show HTML starting with <!DOCTYPE html>
# If empty or shows error, server issue
# If shows HTML but browser is blue, browser issue
```

### Test from Different Client

```bash
# Test from another machine on same network
# Find your Docker host IP
ifconfig | grep inet  # macOS/Linux
ipconfig              # Windows

# From another machine:
curl -I http://<YOUR_IP>:5001/
```

---

## 🚀 Nuclear Option: Complete Reset

If nothing else works:

```bash
# 1. Stop and remove everything
docker compose down -v

# 2. Remove old images
docker rmi kirston/crypto-trading-ict:latest

# 3. Pull fresh image
docker pull kirston/crypto-trading-ict:latest

# 4. Verify .env file exists
ls -la .env
cat .env | grep BYBIT  # Should show API keys

# 5. Start fresh
docker compose up -d

# 6. Watch logs live
docker logs -f crypto-trading-ict

# 7. In new terminal, test after startup
sleep 20
curl http://localhost:5001/
```

---

## 📊 Expected Behavior (Working System)

### Correct Startup Sequence:

```log
INFO:__main__:🚀 ICT Trading System - Starting Up
INFO:database.trading_database:✅ Connected to database
INFO:__main__:✅ Demo user ready: demo@ict.com
INFO:__main__:🌐 Starting monitor on port 5001...
INFO:__main__:🚀 ICT Enhanced Trading Monitor starting on port 5001
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5001
```

### Correct curl Output:

```
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.12.12
Content-Type: text/html; charset=utf-8
Content-Length: 48779
Access-Control-Allow-Origin: *
```

### Correct Browser Behavior:

- Dashboard loads immediately (no redirect)
- Shows "Kirston's Crypto Bot - ICT Enhanced" title
- Displays 4 crypto pairs (BTC, SOL, ETH, XRP)
- Real-time price updates via WebSocket
- No console errors in DevTools

---

## 💡 Platform-Specific Issues

### macOS

```bash
# Check Docker Desktop is running
# Menu bar should show Docker icon

# Verify Docker resources
docker info | grep CPUs
docker info | grep Memory

# If Docker Desktop just updated:
# Restart Docker Desktop
```

### Windows

```bash
# Run PowerShell as Administrator

# Check Docker Desktop is running
docker version

# If using WSL2:
wsl --list --verbose
# Docker Desktop should be integrated with WSL2

# Check Windows Firewall
# Allow Docker Desktop through firewall
```

### Linux

```bash
# Check Docker service
systemctl status docker

# Check if user is in docker group
groups | grep docker

# If not, add user:
sudo usermod -aG docker $USER
# Then logout and login again
```

---

## 📞 What to Report Back

When your dev contacts you, ask for:

1. **Operating System**: macOS / Windows / Linux + version
2. **Docker Version**: `docker --version`
3. **Browser**: Chrome / Firefox / Safari + version
4. **Curl Test Result**: Did `curl -I http://localhost:5001/` return 200?
5. **Container Status**: Is it running? (`docker ps`)
6. **Console Errors**: Any red errors in browser DevTools?
7. **Screenshot**: Blue screen with DevTools open

---

## ✅ Success Criteria

Dashboard is working when:

- ✅ Container shows "Running" status
- ✅ curl returns HTTP/1.1 200 OK
- ✅ Browser shows dashboard (not blue screen)
- ✅ Real-time prices update every ~30 seconds
- ✅ No console errors in DevTools
- ✅ WebSocket shows "connected" in Network tab

---

## 🔐 Security Note

After upgrading to Python 3.12-slim:

- ✅ Fixed 65 CVE vulnerabilities in golang/stdlib
- ✅ Using latest Python 3.12.12
- ✅ Reduced attack surface
- ✅ All security patches applied

**Latest Image**: `kirston/crypto-trading-ict:latest`  
**Digest**: `sha256:e564071dc319a45f7fb71308940270e66c743e134ac29985ad8e211cce2e1708`  
**Python Version**: 3.12.12  
**Push Date**: November 19, 2025
