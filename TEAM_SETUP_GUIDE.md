# 🚀 TEAM SETUP GUIDE - Docker Deployment

## � Security Notice

**Each team member MUST get their own Bybit API credentials. Never share API keys!**

This guide will show you how to:

1. Create your own FREE Bybit Demo Trading account
2. Generate your personal API credentials
3. Run the Docker container with your credentials

---

## �📦 Quick Start for Team Members

### Step 1: Pull the Docker Image

```bash
docker pull kirston/crypto-trading-ict:latest
```

### Step 2: Get Your Bybit API Credentials

**IMPORTANT**: Each team member needs their own Bybit API credentials. Do not share credentials.

#### How to Create Bybit Demo Trading API Keys:

1. **Create Bybit Account** (if you don't have one)

   - Go to https://www.bybit.com
   - Click "Sign Up" → Create account → Verify email

2. **Access API Management**

   - Login to Bybit
   - Click your profile icon (top right)
   - Select "API Management" or go to: https://www.bybit.com/app/user/api-management

3. **Create Demo Trading API Key**

   - Click "Create New Key"
   - Choose **"System-generated API Keys"**
   - **IMPORTANT**: Select **"Demo Trading"** mode (NOT Mainnet!)
   - Name it: "Crypto Trading Bot" or similar

4. **Set Permissions**

   - Enable: **Read** and **Write** permissions
   - Enable: **Contract Trading** and **Spot Trading**
   - No withdrawals needed (keep disabled for security)

5. **Save Your Credentials**
   - Copy your **API Key** (e.g., `yWBB88xfcEgMVAGPCY`)
   - Copy your **API Secret** (e.g., `VE7vieUUhpQz8KqHYa...`)
   - ⚠️ **Save these immediately** - you cannot view the secret again!

#### Why Demo Trading?

- ✅ **FREE** - No money required
- ✅ **Real Prices** - Live market data from actual exchanges
- ✅ **Fake Money** - Virtual $100,000 USDT for testing
- ✅ **Zero Risk** - Cannot lose real funds
- ✅ **Full Features** - All trading features work exactly like real trading

### Step 3: Run the Container

```bash
# Create a .env file with your credentials
cat > .env << EOF
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
BYBIT_TESTNET=false
BYBIT_DEMO=true
BYBIT_BASE_URL=https://api-demo.bybit.com
EOF

# Run the container
docker run -d \
  --name crypto-trading \
  -p 5001:5001 \
  -e BYBIT_API_KEY=$(grep BYBIT_API_KEY .env | cut -d'=' -f2) \
  -e BYBIT_API_SECRET=$(grep BYBIT_API_SECRET .env | cut -d'=' -f2) \
  -e BYBIT_TESTNET=$(grep BYBIT_TESTNET .env | cut -d'=' -f2) \
  -e BYBIT_DEMO=$(grep BYBIT_DEMO .env | cut -d'=' -f2) \
  -e BYBIT_BASE_URL=$(grep BYBIT_BASE_URL .env | cut -d'=' -f2) \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  kirston/crypto-trading-ict:latest
```

### Step 4: Access the Dashboard

```bash
# Open in browser
open http://localhost:5001

# Or check it's running
curl http://localhost:5001/health
```

### Step 5: Login to Dashboard

Once the page loads, you'll see a login form. Use these credentials:

- **Email**: `demo@ict.com`
- **Password**: `demo123`

> **Note**: If you can't login, check the logs to ensure the demo user was created successfully.

---

## � Default Login Credentials

**The dashboard REQUIRES login**. Once the container is running properly, you'll see a login page at `http://localhost:5001`.

**Default Credentials**:

- **Email**: `demo@ict.com`
- **Password**: `demo123`

> **Important**: These credentials are automatically created when the system starts for the first time. If you see "Invalid credentials" errors, it means the container didn't start properly (usually due to missing Bybit API credentials).

---

## 🔍 Troubleshooting "Demo Login Failed" Error

### What This Error Means

The "Demo Login Failed" error has **two possible meanings**:

#### 1. **Bybit API Connection Failed** (Most Common)

- The system cannot connect to Bybit's Demo Trading API
- Container started but missing Bybit API credentials
- You'll see this in the container logs, not on the login page

#### 2. **Dashboard Login Failed**

- You're on the login page at `http://localhost:5001`
- Entered wrong credentials or database not initialized
- Use: `demo@ict.com` / `demo123`

### Why Container Fails to Start

The Docker container requires Bybit API credentials to:

- Connect to Bybit's Demo Trading API
- Fetch real-time cryptocurrency prices
- Initialize the database with demo user
- Start the trading system properly

**Without Bybit credentials → Container fails → Database not initialized → Can't login**

### Can't Access Dashboard at localhost:5001

**Check if container is running:**

```bash
docker ps --filter "name=crypto-trading"
```

**View container logs:**

```bash
docker logs crypto-trading | tail -50
```

**Check if port is in use:**

```bash
# macOS/Linux
lsof -i :5001

# If port 5001 is taken, use a different port:
docker run -d --name crypto-trading -p 5002:5001 \
  -e BYBIT_API_KEY=your_key \
  -e BYBIT_API_SECRET=your_secret \
  kirston/crypto-trading-ict:latest

# Then access at http://localhost:5002
```

### Container Keeps Stopping

**Check logs for errors:**

```bash
docker logs crypto-trading
```

**Common issues:**

- Missing Bybit credentials
- Port conflict (5001 already in use)
- Insufficient memory/resources

---

## 📊 **Verify It's Working**

After starting the container, you should see logs like this:

```
INFO:bybit_integration.bybit_client:🔗 Bybit Client initialized - Demo Mainnet ✅
INFO:__main__:📊 Fetching 1H klines for BTCUSDT (200 candles = ~8 days)
INFO:__main__:✅ Fetched 200 1H candles for BTCUSDT
INFO:__main__:✅ Created demo user: demo@ict.com / demo123
INFO:__main__:🌐 Starting monitor on port 5001...
INFO:__main__:✅ Analysis Complete - Scan #1 | Signals: 0
```

**Good signs:**

- ✅ "Bybit Client initialized" - API connected
- ✅ "Fetched 200 1H candles" - Getting real data
- ✅ "Created demo user" - Database initialized with login credentials
- ✅ "Starting monitor on port 5001" - Web server running
- ✅ "Analysis Complete" - System is scanning

**Bad signs:**

- ❌ "Missing Bybit API credentials" - Need to pass credentials
- ❌ "Demo login failed" - Invalid Bybit API credentials (not dashboard login)
- ❌ "Connection refused" - Container not running
- ❌ No "Created demo user" message - Database not initialized, can't login

---

## 🆘 **Still Having Issues?**

### Option 1: Check Your Setup

```bash
# 1. Verify Docker is running
docker --version

# 2. Check if container is healthy
docker inspect crypto-trading | grep -A 5 "Health"

# 3. Check environment variables inside container
docker exec crypto-trading env | grep BYBIT
```

### Option 2: Fresh Start

```bash
# Stop and remove everything
docker stop crypto-trading
docker rm crypto-trading

# Pull latest image
docker pull kirston/crypto-trading-ict:latest

# Start fresh with credentials
docker run -d --name crypto-trading -p 5001:5001 \
  -e BYBIT_API_KEY=YOUR_ACTUAL_KEY \
  -e BYBIT_API_SECRET=YOUR_ACTUAL_SECRET \
  -e BYBIT_TESTNET=false \
  -e BYBIT_DEMO=true \
  -e BYBIT_BASE_URL=https://api-demo.bybit.com \
  kirston/crypto-trading-ict:latest

# Watch logs in real-time
docker logs -f crypto-trading
```

---

## 📝 **Important Notes**

1. **Demo Trading Mode**: The system uses Bybit Demo Mainnet by default

   - Real prices, fake money
   - Virtual $100,000 USDT balance
   - Safe for testing
   - No real funds at risk

2. **API Credentials**: Each team member needs their own Bybit API credentials

   - **DO NOT share credentials** between team members
   - Each person creates their own FREE account
   - Takes only 5 minutes to set up
   - Instructions provided above in Step 2

3. **Dashboard Access**: Requires login with demo credentials

   - Email: `demo@ict.com`
   - Password: `demo123`
   - These are automatically created when container starts
   - Consider changing credentials for security in production

4. **Data Persistence**: Trading data is stored in the container
   - Use `-v $(pwd)/data:/app/data` to persist data locally
   - Data survives container restarts

---

## ✅ Success Checklist

Your setup is complete when you can confirm:

- [ ] Container is running (`docker ps` shows healthy status)
- [ ] Logs show "Bybit Client initialized ✅"
- [ ] Logs show "Created demo user: demo@ict.com / demo123"
- [ ] Logs show candle data being fetched for BTC, ETH, SOL, XRP
- [ ] No "Missing Bybit API credentials" errors
- [ ] Dashboard accessible at http://localhost:5001
- [ ] Can login with `demo@ict.com` / `demo123`
- [ ] Real-time market data displayed on dashboard after login

---

## 💡 **Pro Tips**

1. **View Real-time Logs**: `docker logs -f crypto-trading`
2. **Restart Container**: `docker restart crypto-trading`
3. **Stop Container**: `docker stop crypto-trading`
4. **Check Health**: `curl http://localhost:5001/health`
5. **Access Inside Container**: `docker exec -it crypto-trading /bin/bash`

---

## 📞 **Need Help?**

If you're still having issues after following this guide:

1. Share the output of: `docker logs crypto-trading | tail -100`
2. Share the output of: `docker ps --filter "name=crypto-trading"`
3. Confirm you've created Bybit API credentials
4. Confirm you're passing credentials when starting the container

---

**Repository**: https://github.com/KirstonKK/crypto-trading-ict-system
**Docker Hub**: https://hub.docker.com/r/kirston/crypto-trading-ict
