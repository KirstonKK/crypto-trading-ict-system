# 🐳 Docker Deployment Files

This directory contains all Docker-related files for deploying Kirston's Crypto Trading System.

## 📁 Files

- **`Dockerfile`** - Multi-stage production image
- **`docker-compose.yml`** - Service orchestration
- **`docker-entrypoint.sh`** - Container initialization script
- **`docker-setup.sh`** - Automated setup script
- **`.dockerignore`** - Build optimization
- **`.env.docker.example`** - Environment template

## 📚 Documentation

- **`DOCKER_README.md`** - Complete deployment guide
- **`DOCKER_DEPLOYMENT_SUMMARY.md`** - Quick reference

## 🚀 Quick Start

From the **project root** directory:

```bash
# 1. Create environment file
cp docker/.env.docker.example docker/.env

# 2. Edit with your API credentials
nano docker/.env

# 3. Build and start
docker-compose -f docker/docker-compose.yml up -d

# 4. View logs
docker-compose -f docker/docker-compose.yml logs -f
```

Or use the setup script:

```bash
cd docker
./docker-setup.sh
```

## 📖 Full Documentation

See **`DOCKER_README.md`** for complete instructions.
