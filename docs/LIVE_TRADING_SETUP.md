# 🚨 LIVE TRADING SETUP GUIDE - REAL MONEY

**⚠️ CRITICAL: This document describes the transition from demo/paper trading to LIVE trading with REAL MONEY on Bybit Mainnet.**

## 📋 PRE-FLIGHT CHECKLIST

Before enabling live trading, ensure you have:

- [ ] **Bybit Account** with KYC verification completed
- [ ] **Mainnet API Keys** created with trading permissions
- [ ] **IP Whitelist** configured (recommended for security)
- [ ] **2FA Enabled** on your Bybit account
- [ ] **Sufficient Funds** deposited in your Bybit account
- [ ] **Risk Management** parameters reviewed and understood
- [ ] **Emergency Stop** procedure documented
- [ ] **Backup** of all databases and configurations created

## 🔐 SECURITY REQUIREMENTS

### API Key Configuration

1. **Create Mainnet API Keys**:

   - Go to Bybit Mainnet: https://www.bybit.com
   - Navigate to: API Management
   - Create new API key with **ONLY** these permissions:
     - ✅ Read position
     - ✅ Read wallet balance
     - ✅ Place order
     - ✅ Cancel order
     - ❌ Transfer (DISABLE)
     - ❌ Withdraw (DISABLE)

2. **IP Whitelist** (Highly Recommended):

   - Add your server/trading machine IP address
   - This prevents unauthorized access even if keys are compromised

3. **Store Credentials Securely**:
   ```bash
   # Create .env file (NEVER commit to git)
   cp .env.example .env
   chmod 600 .env  # Restrict file permissions
   ```

## ⚙️ CONFIGURATION CHANGES

### 1. Update Environment Variables (.env)

```bash
# Bybit Mainnet API Configuration (LIVE TRADING - REAL MONEY)
BYBIT_API_KEY=your_mainnet_api_key_here
BYBIT_API_SECRET=your_mainnet_api_secret_here
BYBIT_TESTNET=false           # FALSE = Mainnet (real money)
BYBIT_DEMO=false              # FALSE = No demo mode

# Trading Mode
TRADING_MODE=live             # live = real money, paper = demo money
AUTO_TRADING=false            # Start with manual approval recommended

# Risk Management (Conservative Settings for Live Trading)
MAX_RISK_PER_TRADE=0.01       # 1% of account per trade
MAX_PORTFOLIO_RISK=0.03       # 3% total exposure maximum
MAX_POSITION_SIZE=100.0       # Maximum $100 per position (start small!)
MIN_CONFIDENCE=0.75           # 75% minimum confidence for live trades
MAX_POSITIONS=2               # Maximum 2 concurrent positions (start conservative)
MAX_DAILY_LOSS=0.05           # 5% daily loss limit - stops trading for the day

# Safety Mechanisms
ENABLE_EMERGENCY_STOP=true    # Emergency stop switch
REQUIRE_TRADE_CONFIRMATION=true  # Require manual confirmation before placing orders
ENABLE_DAILY_LOSS_LIMIT=true  # Stop trading after daily loss limit
ENABLE_DRAWDOWN_PROTECTION=true  # Protect against large drawdowns

# Stop Loss & Take Profit
USE_STOP_LOSS=true            # ALWAYS true for live trading
USE_TAKE_PROFIT=true          # ALWAYS true for live trading
DEFAULT_STOP_LOSS_PCT=0.01    # 1% stop loss
DYNAMIC_TAKE_PROFIT=true      # 1:2 to 1:5 RR based on signal quality
MIN_TAKE_PROFIT_PCT=0.02      # 1:2 RR minimum
MAX_TAKE_PROFIT_PCT=0.05      # 1:5 RR maximum

# Monitoring & Alerts
ENABLE_TRADE_NOTIFICATIONS=true  # Get notified of all trades
TELEGRAM_BOT_TOKEN=your_telegram_bot_token  # For trade alerts
TELEGRAM_CHAT_ID=your_telegram_chat_id      # Your Telegram chat ID
```

### 2. Update api_settings.json

The system will automatically use mainnet endpoints when `BYBIT_TESTNET=false`:

- REST API: `https://api.bybit.com`
- WebSocket: `wss://stream.bybit.com/v5/public/spot`

## 🛡️ SAFETY MECHANISMS

### Built-in Protections

1. **Position Size Limits**:

   - Start with small positions ($100 max recommended)
   - System prevents oversized trades
   - Respects account balance limits

2. **Daily Loss Limit**:

   - Trading stops automatically after 5% daily loss
   - Requires manual reset next day
   - Prevents revenge trading

3. **Maximum Portfolio Risk**:

   - Total exposure capped at 3% of account
   - Prevents over-leverage
   - Multiple positions must fit within limit

4. **Stop Loss Mandatory**:

   - Every trade MUST have a stop loss
   - Cannot be disabled in live mode
   - Protects against catastrophic losses

5. **Signal Quality Filter**:
   - Minimum 75% confidence required
   - Only high-quality setups traded
   - Reduces false signals

### Emergency Procedures

**EMERGENCY STOP (Market Hours):**

```bash
# Method 1: Set environment variable
export EMERGENCY_STOP=true

# Method 2: Create emergency stop file
touch /tmp/trading_emergency_stop

# Method 3: Stop the container
docker stop crypto-trading-ict

# Method 4: Close all positions manually on Bybit website
https://www.bybit.com/en/trade/spot/
```

**After Market Close:**

```bash
# Review all open positions
curl http://localhost:5001/api/positions

# Check P&L
curl http://localhost:5001/api/stats

# Export trading log
curl http://localhost:5001/api/export/trades > trades_$(date +%Y%m%d).json
```

## 📊 DATABASE SCHEMA CHANGES

The system now uses real account balance instead of paper balance:

### Trades Table

```sql
-- New columns for live trading
ALTER TABLE paper_trades ADD COLUMN trade_type TEXT DEFAULT 'live';  -- 'live' or 'paper'
ALTER TABLE paper_trades ADD COLUMN order_id TEXT;                   -- Bybit order ID
ALTER TABLE paper_trades ADD COLUMN order_link_id TEXT;              -- Our tracking ID
ALTER TABLE paper_trades ADD COLUMN execution_price REAL;            -- Actual fill price
ALTER TABLE paper_trades ADD COLUMN commission REAL;                 -- Trading fees
ALTER TABLE paper_trades ADD COLUMN commission_asset TEXT;           -- Fee currency
```

### Balance Tracking

```sql
-- Real balance is fetched from Bybit API, not stored locally
-- Daily stats tracks realized P&L only
```

## 🚀 DEPLOYMENT STEPS

### Step 1: Prepare Environment

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# 1. Stop current system
docker compose down

# 2. Backup current state
./scripts/maintenance/backup_system.sh

# 3. Update .env with Mainnet credentials
nano .env
# Set BYBIT_TESTNET=false, BYBIT_DEMO=false, add real API keys

# 4. Verify configuration
python3 -c "from bybit_integration.config import load_config_from_env, validate_config; config = load_config_from_env(); is_valid, errors = validate_config(config); print('✅ Valid' if is_valid else f'❌ Errors: {errors}')"
```

### Step 2: Test Connection (Read-Only)

```bash
# Test API connection without trading
python3 scripts/testing/test_bybit_connection.py

# Expected output:
# ✅ Connected to Bybit Mainnet
# ✅ API Key valid
# ✅ Account balance: $XXXX.XX
# ✅ No open positions
```

### Step 3: Enable Live Trading (Start Conservative)

```bash
# Build new Docker image with live trading config
docker build -t kirston/crypto-trading-ict:live -f docker/Dockerfile .

# Start with manual approval mode first
docker compose -f docker-compose.live.yml up -d

# Monitor logs closely
docker logs -f crypto-trading-ict

# Access dashboard
open http://localhost:5001
```

### Step 4: First Live Trade Checklist

Before the first trade:

- [ ] Verified Bybit balance matches dashboard
- [ ] Confirmed stop loss is set correctly
- [ ] Reviewed signal quality (>75% confidence)
- [ ] Checked position size (<$100 to start)
- [ ] Emergency stop procedure ready
- [ ] Monitoring dashboard actively

After the first trade:

- [ ] Order executed successfully on Bybit
- [ ] Dashboard shows correct position
- [ ] Stop loss visible on Bybit
- [ ] Take profit visible on Bybit
- [ ] Position tracking accurate

## 📈 MONITORING & ALERTS

### Dashboard Endpoints

```bash
# Real-time balance
curl http://localhost:5001/api/balance

# Open positions
curl http://localhost:5001/api/positions

# Today's P&L
curl http://localhost:5001/api/stats

# Recent trades
curl http://localhost:5001/api/trades/recent

# System health
curl http://localhost:5001/health
```

### Telegram Alerts (Optional)

Set up Telegram bot for trade notifications:

1. Create bot with @BotFather
2. Get bot token
3. Get your chat ID: https://t.me/userinfobot
4. Add to .env file
5. System will send alerts for:
   - Trade entries
   - Stop loss hits
   - Take profit hits
   - Daily loss limit reached
   - System errors

## 🔄 ROLLBACK PROCEDURE

If issues arise, rollback to paper trading:

```bash
# Stop live trading
docker compose down

# Restore backup
cp backups/pre_live_trading_YYYYMMDD_HHMMSS/.env .env

# Rebuild with paper trading
docker compose up -d

# Verify paper trading mode
curl http://localhost:5001/health | grep "trading_mode"
```

## ⚠️ IMPORTANT WARNINGS

1. **START SMALL**: Use minimum position sizes until confident
2. **NEVER DISABLE STOP LOSS**: This is your insurance policy
3. **RESPECT DAILY LOSS LIMIT**: Don't try to "make it back"
4. **MONITOR ACTIVELY**: Especially during first week
5. **TEST EMERGENCY STOP**: Make sure you can stop trading quickly
6. **REVIEW DAILY**: Check all trades and P&L every day
7. **KEEP RECORDS**: Export trade logs regularly

## 📞 SUPPORT & TROUBLESHOOTING

### Common Issues

**Issue: "Insufficient balance" error**

- Check Bybit account balance
- Verify position size calculation
- Ensure USD is available (not just crypto)

**Issue: "Order rejected" error**

- Check symbol format (e.g., BTCUSDT not BTC)
- Verify minimum order size on Bybit
- Check API key permissions

**Issue: Position not showing on Bybit**

- Check if order was filled
- Look for order in Order History
- Verify symbol and market type

**Issue: Stop loss not triggering**

- Verify stop loss was placed on Bybit
- Check order type (stop market vs stop limit)
- Ensure price hasn't changed dramatically

### Emergency Contacts

- **Bybit Support**: https://www.bybit.com/en/help-center
- **System Admin**: [Your contact info]
- **Emergency Stop File**: `/tmp/trading_emergency_stop`

## 📝 CHANGELOG

### Version 1.0 - Live Trading Release

- Removed paper trading balance tracking
- Integrated real Bybit account balance
- Added live order execution
- Implemented safety mechanisms
- Added emergency stop procedures
- Enhanced monitoring and alerts

---

**🚨 FINAL REMINDER: You are trading with REAL MONEY. All losses are REAL. Trade responsibly.**
