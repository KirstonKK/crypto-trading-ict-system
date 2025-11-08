# 🐳 Docker Deployment Guide

# Kirston's Crypto Trading System

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Volume Management](#volume-management)
- [Monitoring & Logs](#monitoring--logs)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)
- [Advanced Configuration](#advanced-configuration)

---

## 🎯 Overview

This Docker setup provides a **production-ready, containerized deployment** of Kirston's Crypto Trading System with:

- ✅ **Multi-stage builds** for optimized image size
- ✅ **Non-root user** for enhanced security
- ✅ **Persistent volumes** for data/logs/results
- ✅ **Health checks** for automatic recovery
- ✅ **Resource limits** to prevent system overload
- ✅ **Environment-based configuration** for flexibility

### What's Included

- **ICT Enhanced Monitor**: Real-time trading signal generation
- **Bybit Integration**: Live market data and demo trading
- **SQLite Database**: Persistent trading history and signals
- **Web Interface**: Dashboard on port 5001
- **Health Monitoring**: Automatic container health checks

---

## 🚀 Quick Start

```bash
# 1. Clone or navigate to the project directory
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# 2. Create environment file from template
cp .env.docker.example .env

# 3. Edit .env with your Bybit API credentials
nano .env  # or use your preferred editor

# 4. Create volume directories
mkdir -p docker-volumes/{data,logs,results}

# 5. Build and start the system
docker-compose up -d

# 6. Check status
docker-compose ps

# 7. View logs
docker-compose logs -f ict-monitor

# 8. Access web interface
open http://localhost:5001
```

---

## 📦 Prerequisites

### Required Software

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher

### Install Docker

**macOS:**

```bash
# Install Docker Desktop
brew install --cask docker
# Or download from: https://www.docker.com/products/docker-desktop
```

**Linux (Ubuntu/Debian):**

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin
```

### Verify Installation

```bash
docker --version        # Should show 20.10+
docker-compose --version # Should show 2.0+
```

---

## 🛠️ Installation

### Step 1: Prepare Environment File

```bash
# Copy the template
cp .env.docker.example .env

# Edit with your settings
nano .env
```

**Required Settings:**

```bash
BYBIT_API_KEY=your_actual_api_key_here
BYBIT_API_SECRET=your_actual_api_secret_here
BYBIT_ENVIRONMENT=demo_mainnet  # Start with demo mode!
```

### Step 2: Create Volume Directories

```bash
# Create persistent storage directories
mkdir -p docker-volumes/data
mkdir -p docker-volumes/logs
mkdir -p docker-volumes/results

# Set proper permissions
chmod -R 755 docker-volumes/
```

### Step 3: Build the Docker Image

```bash
# Build the image (first time or after code changes)
docker-compose build

# Or build without cache (if having issues)
docker-compose build --no-cache
```

---

## ⚙️ Configuration

### Environment Variables

Edit `.env` file to configure the system:

#### Critical Settings

| Variable            | Description           | Default        | Options                                   |
| ------------------- | --------------------- | -------------- | ----------------------------------------- |
| `BYBIT_API_KEY`     | Your Bybit API key    | _required_     | Get from Bybit                            |
| `BYBIT_API_SECRET`  | Your Bybit API secret | _required_     | Get from Bybit                            |
| `BYBIT_ENVIRONMENT` | Trading environment   | `demo_mainnet` | `testnet`, `demo_mainnet`, `live_mainnet` |

#### Trading Parameters

| Variable            | Description               | Default | Range    |
| ------------------- | ------------------------- | ------- | -------- |
| `RISK_PER_TRADE`    | Risk amount per trade ($) | `100.0` | 1-10000  |
| `MAX_LEVERAGE`      | Maximum leverage          | `10`    | 1-100    |
| `RISK_REWARD_RATIO` | Min risk/reward ratio     | `3.0`   | 1.0-10.0 |

#### System Configuration

| Variable           | Description            | Default      |
| ------------------ | ---------------------- | ------------ |
| `ENVIRONMENT`      | Deployment environment | `production` |
| `LOG_LEVEL`        | Logging level          | `INFO`       |
| `ICT_MONITOR_PORT` | Web interface port     | `5001`       |

---

## 🎮 Usage

### Start the System

```bash
# Start in background (detached mode)
docker-compose up -d

# Start in foreground (see logs in real-time)
docker-compose up
```

### Stop the System

```bash
# Graceful shutdown
docker-compose down

# Stop and remove volumes (⚠️ deletes all data!)
docker-compose down -v
```

### Restart the System

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart ict-monitor
```

### Check Status

```bash
# View running containers
docker-compose ps

# View resource usage
docker stats

# Check health status
docker inspect ict-trading-monitor | grep -A 10 "Health"
```

### Access Services

- **Web Dashboard**: http://localhost:5001
- **Health Endpoint**: http://localhost:5001/health
- **API Data**: http://localhost:5001/api/data

---

## 💾 Volume Management

### Volume Structure

```
docker-volumes/
├── data/           # Trading database and cache
│   ├── trading.db  # Main SQLite database
│   ├── cache/      # Price and market data cache
│   └── trading_sessions/  # Session data
├── logs/           # Application logs
│   └── ict_monitor.log
└── results/        # Analysis and reports
```

### Backup Data

```bash
# Backup database
docker exec ict-trading-monitor sqlite3 /app/data/trading.db ".backup '/app/data/backup_$(date +%Y%m%d).db'"

# Copy backup to host
docker cp ict-trading-monitor:/app/data/backup_$(date +%Y%m%d).db ./backups/

# Or backup entire volume
tar -czf backup_$(date +%Y%m%d).tar.gz docker-volumes/
```

### Restore Data

```bash
# Stop the container
docker-compose down

# Restore database
cp backups/backup_20251107.db docker-volumes/data/trading.db

# Start container
docker-compose up -d
```

### Clear Data (Fresh Start)

```bash
# ⚠️ WARNING: This deletes all trading history!

# Stop containers
docker-compose down

# Remove volumes
rm -rf docker-volumes/*

# Recreate directories
mkdir -p docker-volumes/{data,logs,results}

# Start fresh
docker-compose up -d
```

---

## 📊 Monitoring & Logs

### View Logs

```bash
# Follow logs in real-time
docker-compose logs -f ict-monitor

# View last 100 lines
docker-compose logs --tail=100 ict-monitor

# View logs for specific time
docker-compose logs --since 30m ict-monitor

# Export logs to file
docker-compose logs ict-monitor > system_logs_$(date +%Y%m%d).log
```

### Monitor System Resources

```bash
# Live resource monitoring
docker stats ict-trading-monitor

# Disk usage
docker system df

# Container details
docker inspect ict-trading-monitor
```

### Check Database

```bash
# Access SQLite database
docker exec -it ict-trading-monitor sqlite3 /app/data/trading.db

# Run SQL queries
docker exec ict-trading-monitor sqlite3 /app/data/trading.db "SELECT COUNT(*) FROM signals WHERE date(entry_time) = date('now');"

# Database integrity check
docker exec ict-trading-monitor sqlite3 /app/data/trading.db "PRAGMA integrity_check;"
```

---

## 🔧 Troubleshooting

### Container Won't Start

**Problem**: Container exits immediately

```bash
# Check logs
docker-compose logs ict-monitor

# Check container status
docker-compose ps

# Try starting in foreground to see errors
docker-compose up
```

**Common Fixes:**

- Verify `.env` file exists and has correct values
- Check volume directories exist: `ls docker-volumes/`
- Ensure ports 5001 is not in use: `lsof -i :5001`

### Database Errors

**Problem**: Database locked or corrupted

```bash
# Check database integrity
docker exec ict-trading-monitor sqlite3 /app/data/trading.db "PRAGMA integrity_check;"

# If corrupted, restore from backup
docker-compose down
cp backups/backup_latest.db docker-volumes/data/trading.db
docker-compose up -d
```

### API Connection Issues

**Problem**: Can't connect to Bybit

```bash
# Check environment variables
docker exec ict-trading-monitor env | grep BYBIT

# Test API connection
docker exec ict-trading-monitor python3 -c "
from bybit_integration.bybit_client import BybitClient
client = BybitClient()
print(client.get_current_price('BTCUSDT'))
"
```

### High Memory/CPU Usage

**Problem**: Container using too many resources

```bash
# Check current usage
docker stats ict-trading-monitor

# Adjust resource limits in docker-compose.yml
# Edit the deploy.resources section
```

### Permission Issues

**Problem**: Permission denied errors

```bash
# Fix volume permissions
sudo chown -R 1000:1000 docker-volumes/

# Or rebuild with correct user
docker-compose build --no-cache
```

### Health Check Failing

```bash
# Check health status
docker inspect ict-trading-monitor | grep -A 10 "Health"

# Test health endpoint manually
curl http://localhost:5001/health

# View health check logs
docker logs ict-trading-monitor 2>&1 | grep health
```

---

## 🔒 Security Best Practices

### 1. Protect API Credentials

```bash
# ❌ DON'T: Commit .env to git
# Add to .gitignore
echo ".env" >> .gitignore

# ✅ DO: Use environment variables or secrets
# On production, use Docker secrets or vault
```

### 2. Use Non-Root User

```bash
# Already configured in Dockerfile
# Verify:
docker exec ict-trading-monitor whoami
# Should output: trading
```

### 3. Network Security

```bash
# Limit external access
# Edit docker-compose.yml to bind to localhost only:
ports:
  - "127.0.0.1:5001:5001"  # Only accessible locally
```

### 4. Regular Updates

```bash
# Update base image
docker-compose build --pull

# Update dependencies
docker-compose build --no-cache
```

### 5. Backup Regularly

```bash
# Automated backup script
# Add to crontab: 0 2 * * * /path/to/backup_script.sh

#!/bin/bash
docker exec ict-trading-monitor sqlite3 /app/data/trading.db ".backup '/app/data/backup.db'"
docker cp ict-trading-monitor:/app/data/backup.db ./backups/backup_$(date +%Y%m%d).db
```

---

## 🚀 Advanced Configuration

### Custom Docker Compose Override

Create `docker-compose.override.yml` for local customizations:

```yaml
version: "3.8"
services:
  ict-monitor:
    environment:
      - LOG_LEVEL=DEBUG
    ports:
      - "5001:5001"
      - "5002:5002" # Add extra port
```

### Multi-Container Setup

Add additional services to `docker-compose.yml`:

```yaml
services:
  # ... existing ict-monitor ...

  fundamental-analysis:
    build: .
    command: python3 systems/fundamental_analysis/fundamental_analysis_server.py
    ports:
      - "5002:5002"
    volumes:
      - trading-data:/app/data
```

### Production Deployment

For production servers:

```bash
# Use production docker-compose file
docker-compose -f docker-compose.prod.yml up -d

# Enable automatic restart
# Already configured with: restart: unless-stopped

# Set up monitoring with Prometheus/Grafana
# Add monitoring services to docker-compose.yml
```

### Build Arguments

Customize build process:

```bash
# Build with specific Python version
docker-compose build --build-arg PYTHON_VERSION=3.11

# Build with custom user ID
docker-compose build --build-arg UID=1001
```

---

## 📚 Additional Resources

- **Bybit API Documentation**: https://bybit-exchange.github.io/docs/
- **Docker Documentation**: https://docs.docker.com/
- **Docker Compose Reference**: https://docs.docker.com/compose/compose-file/

---

## 🆘 Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify configuration: `docker exec ict-trading-monitor env`
3. Review this documentation
4. Check system requirements
5. Create an issue with logs and configuration details

---

## 📝 Notes

- **First Run**: May take 30-60 seconds to initialize database
- **Demo Mode**: Uses fake money but real market prices
- **Data Persistence**: All data stored in `docker-volumes/`
- **Automatic Recovery**: Health checks restart unhealthy containers
- **Resource Usage**: ~500MB RAM baseline, ~2GB under load

---

**Happy Trading! 🚀📈**
