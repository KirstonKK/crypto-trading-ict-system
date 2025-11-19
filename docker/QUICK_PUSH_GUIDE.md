# Quick Push to Docker Hub Guide

This guide helps you quickly push the Crypto Trading ICT System to Docker Hub.

## 📦 Latest Version

**Current Image**: `kirston/crypto-trading-ict:latest`  
**Docker Hub**: https://hub.docker.com/r/kirston/crypto-trading-ict  
**Last Updated**: November 8, 2025  
**Status**: ✅ **WORKING** - All import errors fixed

### Recent Fixes (v2)

- ✅ Fixed `ModuleNotFoundError: No module named 'database.trading_database'`
- ✅ Added complete TradingDatabase wrapper class
- ✅ All database operations now working in container
- ✅ Ready for production deployment

## ✅ Prerequisites

1. **Docker Hub Account**: Create one at https://hub.docker.com
2. **Docker Installed**: Ensure Docker Desktop is installed and running
3. **Git Repository**: Have your code ready to push

## 🚀 Quick Start (Automated Script)

## Step-by-Step Instructions

### Step 1: Login to Docker Hub

```bash
/usr/local/bin/docker login
```

Enter your Docker Hub username and password when prompted.

### Step 2: Run the Automated Push Script

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm/docker"

# Option A: Use default username 'kirstonkk' and 'latest' tag
./push-to-dockerhub.sh

# Option B: Specify your Docker Hub username
./push-to-dockerhub.sh YOUR_DOCKERHUB_USERNAME

# Option C: Specify username and version tag
./push-to-dockerhub.sh YOUR_DOCKERHUB_USERNAME v1.0.0
```

### Step 3: Share with Your Team

Once pushed, share this command with other developers:

```bash
docker pull YOUR_DOCKERHUB_USERNAME/crypto-trading-ict:latest
```

## Alternative: Manual Steps

If you prefer to do it manually:

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm/docker"

# 1. Login
/usr/local/bin/docker login

# 2. Build the image
/usr/local/bin/docker build -t YOUR_DOCKERHUB_USERNAME/crypto-trading-ict:latest .

# 3. Tag with version (optional)
/usr/local/bin/docker tag YOUR_DOCKERHUB_USERNAME/crypto-trading-ict:latest YOUR_DOCKERHUB_USERNAME/crypto-trading-ict:v1.0.0

# 4. Push to Docker Hub
/usr/local/bin/docker push YOUR_DOCKERHUB_USERNAME/crypto-trading-ict:latest
/usr/local/bin/docker push YOUR_DOCKERHUB_USERNAME/crypto-trading-ict:v1.0.0
```

## For Other Developers

Once the image is on Docker Hub, other developers can use it:

```bash
# Clone the repo
git clone https://github.com/KirstonKK/crypto-trading-ict-system.git
cd crypto-trading-ict-system/docker

# Copy and configure environment
cp .env.docker.example .env
nano .env  # Add their Bybit API credentials

# Pull and run (no build needed!)
docker-compose -f docker-compose.registry.yml pull
docker-compose -f docker-compose.registry.yml up -d

# View logs
docker-compose -f docker-compose.registry.yml logs -f

# Access dashboard
open http://localhost:5001
```

## Troubleshooting

### Docker command not found

```bash
# Use full path:
/usr/local/bin/docker --version

# Or add to PATH in ~/.zshrc:
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Docker Desktop not running

```bash
# Start Docker Desktop
open -a Docker

# Wait 30-60 seconds for it to start
/usr/local/bin/docker info
```

### Authentication issues

```bash
# Logout and login again
/usr/local/bin/docker logout
/usr/local/bin/docker login
```

### Build errors

```bash
# Check Dockerfile syntax
cd docker
cat Dockerfile

# Build with verbose output
/usr/local/bin/docker build --progress=plain -t test-build .
```

## Update docker-compose.registry.yml

Don't forget to update the image name in `docker-compose.registry.yml`:

```yaml
services:
  ict-monitor:
    image: YOUR_DOCKERHUB_USERNAME/crypto-trading-ict:latest # Update this line
```

## Docker Hub Repository URL

After pushing, your image will be available at:

```
https://hub.docker.com/r/YOUR_DOCKERHUB_USERNAME/crypto-trading-ict
```

Share this URL with your team!
