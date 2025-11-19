# 🐳 Docker Quick Start Guide

## 🚀 Two Ways to Run the System

### ✅ **Method 1: Docker Compose (RECOMMENDED - Automatic Credentials)**

This method **automatically loads** all credentials from your `.env` file. No manual `-e` flags needed!

```bash
# 1. Make sure you're in the project directory
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# 2. Stop any existing containers
docker stop crypto-trading-ict 2>/dev/null || true
docker rm crypto-trading-ict 2>/dev/null || true

# 3. Start with Docker Compose (loads .env automatically!)
docker-compose up -d

# 4. View logs
docker-compose logs -f

# 5. Check status
docker-compose ps

# 6. Access dashboard
open http://localhost:5001
```

**To Stop:**

```bash
docker-compose down
```

**To Restart:**

```bash
docker-compose restart
```

**To Update to Latest Image:**

```bash
docker-compose pull
docker-compose up -d
```

---

### ⚙️ **Method 2: Docker Run (Manual - For Advanced Users)**

If you prefer `docker run` instead of compose:

```bash
# Stop existing container
docker stop crypto-trading-ict 2>/dev/null || true
docker rm crypto-trading-ict 2>/dev/null || true

# Pull latest image
docker pull kirston/crypto-trading-ict:latest

# Run with credentials from .env file
docker run -d \
  --name crypto-trading-ict \
  -p 5001:5001 \
  -p 5002:5002 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/results:/app/results \
  --restart unless-stopped \
  kirston/crypto-trading-ict:latest

# View logs
docker logs -f crypto-trading-ict
```

---

## 📊 Your Current Configuration

Your `.env` file contains:

```properties
# Bybit API Credentials (Demo Mainnet - Real prices, Fake money)
BYBIT_API_KEY=yWBB88xfcEgMVAGPCY
BYBIT_API_SECRET=VE7vieUUhpQz8KqHYa8ygu8ByorocZPhrfZ5
BYBIT_DEMO=true
BYBIT_BASE_URL=https://api-demo.bybit.com

# Trading Configuration
AUTO_TRADING_ENABLED=false
MAX_RISK_PER_TRADE=0.01
PAPER_TRADING=true
```

✅ These credentials are automatically loaded when using docker-compose!

---

## 🔧 Common Commands

### View Running Containers

```bash
docker ps
```

### View All Containers (including stopped)

```bash
docker ps -a
```

### View Container Logs

```bash
# Last 100 lines
docker logs --tail 100 crypto-trading-ict

# Follow logs (live)
docker logs -f crypto-trading-ict

# With docker-compose
docker-compose logs -f
```

### Check Container Health

```bash
docker inspect crypto-trading-ict | grep -A 5 "Health"
```

### Restart Container

```bash
# With docker-compose
docker-compose restart

# With docker run
docker restart crypto-trading-ict
```

### Stop and Remove Container

```bash
# With docker-compose
docker-compose down

# With docker run
docker stop crypto-trading-ict
docker rm crypto-trading-ict
```

### Update to Latest Image

```bash
# With docker-compose
docker-compose pull
docker-compose up -d

# With docker run
docker pull kirston/crypto-trading-ict:latest
# Then stop, remove, and start new container
```

---

## 🔍 Troubleshooting

### Quick Diagnostic Tool

Run the automated diagnostic script from inside your running container:

```bash
# Run diagnostic script
docker exec crypto-trading-ict diagnose_blue_screen.sh
```

This comprehensive diagnostic checks:

- ✅ Docker installation and daemon status
- ✅ Container health and uptime
- ✅ Port 5001 accessibility
- ✅ HTTP response codes (200 OK expected)
- ✅ Container error logs
- ✅ Environment variables and configuration
- ✅ Docker image version

**For detailed troubleshooting guide, see:** `docs/TROUBLESHOOTING_BLUE_SCREEN.md`

### Problem: "Missing Bybit API credentials" error

**Solution:** Make sure your `.env` file exists and contains credentials:

```bash
# Check if .env file exists
ls -la .env

# View contents (first few lines)
head -n 10 .env

# If using docker-compose, restart to reload .env
docker-compose down
docker-compose up -d
```

### Problem: Container starts but no data/signals

**Possible causes:**

1. Credentials not loaded properly
2. API connection issue
3. System still initializing

**Check logs:**

```bash
docker logs crypto-trading-ict | grep -E "(ERROR|WARNING|Bybit|credentials)"
```

**Look for:**

- ✅ "Bybit Client initialized successfully"
- ✅ "Fetched klines for BTCUSDT"
- ❌ "Missing Bybit API credentials"

### Problem: Port already in use

```bash
# Find what's using port 5001
lsof -i :5001

# Kill the process
lsof -ti:5001 | xargs kill -9

# Or stop the container
docker stop crypto-trading-ict
```

### Problem: Database errors

```bash
# Backup current database
cp data/trading.db data/trading.db.backup

# Check database integrity inside container
docker exec crypto-trading-ict sqlite3 /app/data/trading.db "PRAGMA integrity_check;"
```

---

## 📱 Dashboard Access

Once running, access the dashboard at:

- **Main Dashboard:** http://localhost:5001
- **Login Credentials:**
  - Email: `demo@ict.com`
  - Password: `demo123`

---

## 🔄 Team Members Setup

Share these instructions with your team:

1. **Pull the image:**

   ```bash
   docker pull kirston/crypto-trading-ict:latest
   ```

2. **Create your own `.env` file with YOUR credentials:**

   ```bash
   BYBIT_API_KEY=your_api_key_here
   BYBIT_API_SECRET=your_api_secret_here
   BYBIT_DEMO=true
   BYBIT_BASE_URL=https://api-demo.bybit.com
   AUTO_TRADING_ENABLED=false
   PAPER_TRADING=true
   ```

3. **Start with docker-compose:**

   ```bash
   docker-compose up -d
   ```

4. **Access dashboard:**
   - Open: http://localhost:5001
   - Login: demo@ict.com / demo123

⚠️ **IMPORTANT:** Each team member should get their own Bybit API credentials. Never share API keys!

---

## 📝 Notes

- **Credentials:** Automatically loaded from `.env` file when using docker-compose
- **Data Persistence:** `/data`, `/logs`, and `/results` folders are mounted as volumes
- **Auto-restart:** Container automatically restarts if it crashes (unless manually stopped)
- **Health Checks:** Docker monitors container health every 30 seconds
- **Resource Limits:** 2 CPU cores max, 2GB RAM max (configurable in docker-compose.yml)

---

## 🆘 Need Help?

Check the main documentation:

- **TEAM_SETUP_GUIDE.md** - Full team deployment guide
- **SYSTEM_COMMANDS.md** - All system commands
- **docs/BYBIT_SETUP_GUIDE.md** - Bybit account/API setup

Or view container logs for errors:

```bash
docker logs --tail 200 crypto-trading-ict
```
