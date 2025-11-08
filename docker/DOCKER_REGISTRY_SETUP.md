# Docker Registry Setup & Image Sharing

## 🚫 Current Status
The Docker image was **NOT pushed to any registry**. It only exists in your local setup documentation.

## 📦 How to Share the Docker Image with Other Developers

### Option 1: Push to Docker Hub (Recommended) ⭐

#### 1. Install Docker Desktop
```bash
# macOS
brew install --cask docker

# Or download from: https://www.docker.com/products/docker-desktop
```

#### 2. Create Docker Hub Account
- Go to: https://hub.docker.com/signup
- Create free account (username: e.g., `kirstonkk`)

#### 3. Login to Docker Hub
```bash
docker login
# Enter your Docker Hub username and password
```

#### 4. Build and Tag the Image
```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm/docker"

# Build the image with your Docker Hub username
docker build -t kirstonkk/crypto-trading-ict:latest .

# Optional: Tag with version
docker tag kirstonkk/crypto-trading-ict:latest kirstonkk/crypto-trading-ict:v1.0.0
```

#### 5. Push to Docker Hub
```bash
# Push latest version
docker push kirstonkk/crypto-trading-ict:latest

# Push versioned tag
docker push kirstonkk/crypto-trading-ict:v1.0.0
```

#### 6. Share the Registry URL
```
Registry URL: https://hub.docker.com/r/kirstonkk/crypto-trading-ict
Pull Command: docker pull kirstonkk/crypto-trading-ict:latest
```

#### 7. Update docker-compose.yml
```yaml
services:
  ict-monitor:
    image: kirstonkk/crypto-trading-ict:latest  # Use registry image
    # Remove build section, or keep for local development
```

### Option 2: Push to GitHub Container Registry (GHCR)

#### 1. Create GitHub Personal Access Token
- Go to: https://github.com/settings/tokens
- Generate token with `write:packages` scope

#### 2. Login to GHCR
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u KirstonKK --password-stdin
```

#### 3. Build and Push
```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm/docker"

# Build with GHCR naming
docker build -t ghcr.io/kirstonkk/crypto-trading-ict:latest .

# Push to GHCR
docker push ghcr.io/kirstonkk/crypto-trading-ict:latest
```

#### 4. Share the Registry URL
```
Registry URL: https://github.com/KirstonKK/crypto-trading-ict-system/pkgs/container/crypto-trading-ict
Pull Command: docker pull ghcr.io/kirstonkk/crypto-trading-ict:latest
```

### Option 3: Export/Import as TAR File (Offline Sharing)

#### 1. Build the Image Locally
```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm/docker"
docker build -t kirstons-trading-system:latest .
```

#### 2. Export Image to TAR
```bash
docker save kirstons-trading-system:latest -o crypto-trading-ict.tar

# Compress for smaller file size
gzip crypto-trading-ict.tar
```

#### 3. Share the TAR File
- Upload to Google Drive, Dropbox, or file sharing service
- Share link with other developers

#### 4. Other Developer Imports
```bash
# Download the tar file, then:
docker load -i crypto-trading-ict.tar.gz
```

## 🎯 Quick Setup for Other Developers

### If You Push to Docker Hub (Recommended):

Other developers can simply run:

```bash
# Clone the repository
git clone https://github.com/KirstonKK/crypto-trading-ict-system.git
cd crypto-trading-ict-system/docker

# Copy environment template
cp .env.docker.example .env

# Edit with their API credentials
nano .env

# Pull and start (no build needed!)
docker-compose pull
docker-compose up -d

# Or use docker-compose.registry.yml
docker-compose -f docker-compose.registry.yml up -d
```

## 📝 Recommended Workflow

### For You (Maintainer):
```bash
# 1. Make changes to code
# 2. Build and test locally
docker build -t kirstonkk/crypto-trading-ict:latest ./docker

# 3. Tag with version
docker tag kirstonkk/crypto-trading-ict:latest kirstonkk/crypto-trading-ict:v1.0.1

# 4. Push both tags
docker push kirstonkk/crypto-trading-ict:latest
docker push kirstonkk/crypto-trading-ict:v1.0.1

# 5. Update git
git tag v1.0.1
git push origin v1.0.1
```

### For Other Developers:
```bash
# Just pull and run
docker pull kirstonkk/crypto-trading-ict:latest
docker-compose up -d
```

## 🔐 Important Notes

1. **Private vs Public Repository**:
   - Docker Hub free tier: 1 private repo, unlimited public
   - GHCR: Unlimited private repos for free
   - Consider if your trading code should be public

2. **API Credentials**:
   - Never include API keys in Docker images
   - Always use `.env` files (gitignored)
   - Other developers need their own Bybit API credentials

3. **Image Size**:
   - Current image: ~300MB
   - Consider multi-stage builds to reduce size (already implemented)

4. **Update Strategy**:
   - Use version tags (v1.0.0, v1.1.0) for stability
   - Use `latest` for development/testing
   - Pin versions in production: `kirstonkk/crypto-trading-ict:v1.0.0`

## 🚀 Next Steps

1. **Install Docker Desktop** (if not already)
2. **Choose Option 1 (Docker Hub)** - easiest for team sharing
3. **Build and push the image**
4. **Share the pull command** with your team
5. **Update README.md** with registry information

## 📞 Share This with Your Team

**Docker Image Pull Command:**
```bash
# Option 1: Docker Hub (once pushed)
docker pull kirstonkk/crypto-trading-ict:latest

# Option 2: GitHub Container Registry (once pushed)
docker pull ghcr.io/kirstonkk/crypto-trading-ict:latest
```

**Quick Start for Developers:**
```bash
git clone https://github.com/KirstonKK/crypto-trading-ict-system.git
cd crypto-trading-ict-system/docker
cp .env.docker.example .env
# Edit .env with your Bybit API credentials
docker-compose up -d
```
