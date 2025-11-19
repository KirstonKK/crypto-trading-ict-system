# 🚀 Pre-Launch Checklist - Live Trading Setup

**Created**: November 19, 2025  
**Status**: Ready for Final Steps  
**Starting Capital**: $50

---

## ✅ COMPLETED (Code & Infrastructure)

- [x] **Bybit Client Refactoring** - BybitClient live-ready
- [x] **Order Placement** - place_order_sync() and get_order_status_sync() operational
- [x] **Safety Features** - 4-layer protection (20/20 tests passing)
- [x] **Database Migration** - 6 live trading columns added
- [x] **ICT Monitor** - Live trade execution integrated
- [x] **Dashboard UI** - Updated for live trading
- [x] **Risk Configuration** - Set for $50 account
- [x] **API Connection** - Tested successfully ($0 balance confirmed)
- [x] **GitHub & Docker** - All changes deployed
- [x] **Security Fix** - Exposed API key removed from docs

---

## 🔒 SECURITY STATUS

**API Key Exposure**: ✅ RESOLVED  
- Only API KEY was exposed (not SECRET)
- Risk Level: LOW (key alone cannot execute trades)
- Current code is clean
- Will rotate keys before funding

---

## 📋 PRE-FUNDING CHECKLIST (DO BEFORE DEPOSITING $50)

### Step 1: Enable Symbol Whitelist on Bybit ⚠️ CRITICAL

**Why**: Prevents accidental trading on wrong pairs

**Steps**:
1. Login to [Bybit.com](https://www.bybit.com)
2. Navigate to: **API Management**
3. Find your API key
4. Click **Edit** or **Manage**
5. Enable **"Symbol Restrictions"** or **"Symbol Whitelist"**
6. Add ONLY these symbols:
   - `BTCUSDT`
   - `ETHUSDT`
   - `SOLUSDT`
   - `XRPUSDT`
7. Click **Save**
8. Verify: Only 4 symbols are whitelisted

**Verification**:
```bash
# Test that other symbols are blocked (should fail)
# Will add verification script if needed
```

---

### Step 2: Rotate API Keys (RECOMMENDED) 🔄

**Why**: Fresh start with keys that were never exposed

**Steps**:
1. Login to Bybit → API Management
2. **Revoke** current API key
3. Click **Create New Key**
4. Set permissions:
   - ✅ Contract → Orders
   - ✅ Contract → Positions  
   - ✅ Spot → Orders
   - ✅ Wallet → Read
   - ❌ Wallet → Withdraw (NEVER enable)
5. Enable **Symbol Whitelist** (BTC, ETH, SOL, XRP)
6. Optional: Add **IP Restrictions** (your home/VPS IP)
7. Save new API Key and Secret
8. Update local `.env`:
   ```bash
   BYBIT_API_KEY=<new_key>
   BYBIT_API_SECRET=<new_secret>
   ```
9. Test connection:
   ```bash
   python3 scripts/testing/test_bybit_connection.py
   ```

---

### Step 3: Test Emergency Stop 🚨

**Why**: Verify you can halt trading instantly if needed

**Test Steps**:
```bash
# Set emergency stop
echo "EMERGENCY_STOP=true" >> .env

# Try to execute trade (should be blocked)
# System should reject all new trades

# Clear emergency stop
# Edit .env: EMERGENCY_STOP=false
```

**Expected Result**: 
- System logs: "🚨 EMERGENCY STOP ACTIVE"
- All new trades blocked
- Dashboard shows emergency stop warning

---

### Step 4: Verify Risk Parameters ⚙️

**Current Settings** (in `config/risk_parameters.json`):

```json
{
  "position_size_percent": 0.20,      // 20% of $50 = $10 max
  "risk_per_trade": 0.01,             // 1% of $50 = $0.50 risk
  "max_positions": 1,                  // One trade at a time
  "min_confidence": 0.80,              // 80% signal confidence
  "daily_loss_limit_percent": 0.05    // 5% daily = $2.50 max loss
}
```

**Verification**:
- Max position: $10 ✅
- Risk per trade: $0.50 ✅
- Daily loss limit: $2.50 ✅
- Stop if balance drops from $50 → $47.50 ✅

---

## 💰 FUNDING & FIRST TRADE

### Step 5: Fund Account

1. **Deposit $50** to Bybit Mainnet
   - Use USDT or convert to USDT
   - Wait for deposit confirmation
2. **Verify Balance**:
   ```bash
   python3 scripts/testing/test_bybit_connection.py
   ```
   - Should show: `Balance: $50.00 USDT`
3. **Check Dashboard**:
   - Open: `dashboard/ict_dashboard.py`
   - Verify: "Account Balance: $50.00"

---

### Step 6: Execute First Test Trade (MANUAL MODE)

**Configuration**:
- ✅ `AUTO_TRADING=false` (manual approval required)
- ✅ `BYBIT_TESTNET=false` (live mainnet)
- ✅ `EMERGENCY_STOP=false` (trading enabled)

**First Trade Parameters**:
- Symbol: BTC or ETH only (highest liquidity)
- Position Size: $10 (20% of capital)
- Risk: $0.50 (1% risk)
- Stop Loss: Set by system
- Take Profit: 2:1 R/R minimum

**Execution**:
1. Wait for high-confidence signal (80%+)
2. System will prompt: "Approve trade? (yes/no)"
3. Review details carefully
4. Type `yes` to execute
5. Monitor order on Bybit exchange

**What to Watch**:
- Order appears on Bybit immediately ✅
- Entry price matches system price ✅
- Stop loss is set correctly ✅
- Take profit is set correctly ✅
- Commission is < $0.10 ✅

---

### Step 7: First 24 Hours Monitoring

**Monitor Closely**:
- Trade execution
- P&L calculations
- Safety feature triggers
- Daily loss tracking
- Commission accuracy

**Daily Checks**:
```bash
# Check database
sqlite3 data/persistence/trading_system.db "
  SELECT * FROM live_trades 
  ORDER BY entry_time DESC 
  LIMIT 5;
"

# Check logs
tail -50 logs/ict_monitor_YYYYMMDD.log

# Check balance
python3 scripts/testing/test_bybit_connection.py
```

---

## 🎯 SUCCESS CRITERIA

### After First Trade:
- [ ] Order executed on Bybit successfully
- [ ] Stop loss placed correctly
- [ ] Take profit placed correctly  
- [ ] Database logged correctly
- [ ] P&L calculations match Bybit
- [ ] Commission fees are accurate
- [ ] No safety feature false positives

### After First Day:
- [ ] System ran without errors
- [ ] Daily loss limit works correctly
- [ ] Emergency stop is accessible
- [ ] No unexpected behavior

### After First Week:
- [ ] Net P&L is tracked accurately
- [ ] Win rate is reasonable (40%+)
- [ ] Risk management is working
- [ ] Ready to continue or adjust

---

## 🚨 EMERGENCY PROCEDURES

### If Something Goes Wrong:

1. **Immediate Stop**:
   ```bash
   echo "EMERGENCY_STOP=true" >> .env
   ```

2. **Close All Positions** (Bybit.com):
   - Login → Positions
   - Close all open positions manually

3. **Check Database**:
   ```bash
   sqlite3 data/persistence/trading_system.db "
     SELECT symbol, side, quantity, entry_price, 
            pnl, status 
     FROM live_trades 
     WHERE status IN ('OPEN', 'PENDING');
   "
   ```

4. **Review Logs**:
   ```bash
   tail -100 logs/ict_monitor_$(date +%Y%m%d).log
   ```

5. **Contact Support** (if needed):
   - Bybit Support: support@bybit.com
   - Check GitHub issues

---

## 📚 DOCUMENTATION REFERENCES

- **Safety Features**: `docs/SAFETY_FEATURES.md`
- **Order Placement**: `docs/ORDER_PLACEMENT_COMPLETE.md`
- **Live Trading Setup**: `docs/LIVE_TRADING_SETUP.md`
- **Risk Parameters**: `config/risk_parameters.json`
- **Environment Config**: `.env.example`

---

## ✅ FINAL CHECKLIST (Complete Before Funding)

- [ ] Symbol Whitelist enabled on Bybit (4 symbols only)
- [ ] New API keys created and tested (optional but recommended)
- [ ] Emergency stop tested and working
- [ ] Risk parameters verified ($10 max, $0.50 risk)
- [ ] Dashboard shows correct information
- [ ] All safety tests passing (20/20)
- [ ] Backup of `.env` file created
- [ ] Understand how to halt system immediately

**When ALL above complete** → Proceed to fund with $50 → Execute first test trade

---

**READY TO GO LIVE!** 🚀

*Last Updated: November 19, 2025*
