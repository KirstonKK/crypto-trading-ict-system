# 🎯 Bybit Demo Trading API Setup Guide

## Current Issue

❌ **API Key Invalid** - The API keys you created are for Testnet, not Demo Trading

## What is Demo Trading?

- **Real market prices** (live BTC, ETH prices from mainnet)
- **Fake money** (100,000 USDT virtual balance)
- **Zero risk** (no real money involved)
- **Perfect for testing** strategies with real market conditions

## Why We Need This

Your ICT trading system needs **real market prices** to:

1. Generate accurate signals based on actual price movements
2. Train ML models on real market data
3. Simulate realistic trading conditions
4. Prepare for live trading deployment

## How to Get Demo Trading API Keys

### Step 1: Access Demo Trading

1. Go to https://www.bybit.com/
2. Log into your Bybit account
3. Look for **"Demo Trading"** in the top menu OR
4. Go directly to: https://demo.bybit.com/

### Step 2: Navigate to API Management

1. In Demo Trading portal, click your profile (top right)
2. Select **"API"** or **"API Management"**
3. You should see: **"Demo Trading API Keys"** section

### Step 3: Create API Keys

1. Click **"Create New Key"**
2. **Name**: "ICT Trading System"
3. **Permissions** (CHECK ALL):
   - ✅ Read-Write (for orders)
   - ✅ Contract Trading
   - ✅ Wallet
   - ✅ Asset Exchange
4. **IP Restriction**: Leave blank for now (add your IP later for security)
5. **Verify** with 2FA code
6. **IMPORTANT**: Copy both keys immediately:
   - API Key (starts with letters/numbers)
   - API Secret (long string)

### Step 4: Update .env File

Once you have the Demo Trading API keys, update `.env`:

```bash
# Replace these with your Demo Trading API keys
BYBIT_API_KEY=your_demo_api_key_here
BYBIT_API_SECRET=your_demo_api_secret_here
BYBIT_DEMO=true
BYBIT_BASE_URL=https://api-demo.bybit.com
```

### Step 5: Test Connection

Run this command to verify:

```bash
cd /Users/kirstonkwasi-kumah/Desktop/Trading\ Algoithm
.venv/bin/python << 'EOF'
import asyncio
import os
from dotenv import load_dotenv
from bybit_integration.bybit_client import BybitDemoClient

load_dotenv('/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm/.env')

async def test():
    client = BybitDemoClient(
        api_key=os.getenv('BYBIT_API_KEY'),
        api_secret=os.getenv('BYBIT_API_SECRET'),
        demo=True
    )

    print(f"Testing: {client.base_url}")
    balance = await client.get_balance()
    print(f"Balance: {balance}")

    if client.session:
        await client.session.close()

asyncio.run(test())
EOF
```

Expected output:

```
Testing: https://api-demo.bybit.com
Balance: {'USDT': 100000.0, 'BTC': 0.0, ...}
```

## Quick Reference

| Environment         | URL                   | Purpose              | Money             |
| ------------------- | --------------------- | -------------------- | ----------------- |
| **Demo Trading** ✅ | api-demo.bybit.com    | Real prices, testing | Fake ($100k USDT) |
| Testnet             | api-testnet.bybit.com | Fake prices, testing | Fake              |
| Live Mainnet ⚠️     | api.bybit.com         | Real prices, live    | **Real money**    |

## Troubleshooting

### "API key is invalid"

- **Cause**: Using Testnet keys with Demo Trading URL
- **Fix**: Create new keys in Demo Trading portal

### "IP restriction"

- **Cause**: API key restricted to specific IP
- **Fix**: Add your IP or disable IP restriction

### "Insufficient permissions"

- **Cause**: API key missing trading permissions
- **Fix**: Recreate key with all trading permissions

## Security Notes

- ✅ Demo Trading = Safe (fake money)
- ✅ Keep API secret secure
- ✅ Don't share API keys publicly
- ✅ Add IP restriction once working

## Next Steps After Setup

1. ✅ Verify Demo Trading connection
2. Test balance retrieval
3. Test BTC/USDT price feed
4. Place test order
5. Integrate with ICT signals

---

**Need Help?**
If you can't find Demo Trading portal:

- Try: https://demo.bybit.com/
- Or contact Bybit support: "How do I access Demo Trading API keys?"
