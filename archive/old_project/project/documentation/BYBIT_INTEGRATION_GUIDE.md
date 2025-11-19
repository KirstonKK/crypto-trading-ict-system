# 🏦 Bybit Integration Guide

## Phase 3: Bybit Testnet & Live Trading Setup

### 📋 **Prerequisites**

✅ **TradingView alerts working** (Phase 2 complete)  
✅ **Bybit account** (create at bybit.com)  
✅ **Understanding of API trading risks** ⚠️

---

## 🧪 **Step 1: Bybit Testnet Setup (SAFE TESTING)**

### **A. Create Testnet Account**

1. Go to **https://testnet.bybit.com/**
2. **Register** or **login with main account**
3. **Get free testnet funds** (fake money for testing)

### **B. Generate API Keys**

1. **Account & Security** → **API Management**
2. **Create New Key**:
   - **Key Name:** `Trading Algorithm Testnet`
   - **Permissions:** ☑️ `Trade`, ☑️ `Read Position`, ☑️ `Read Wallet`
   - **IP Restriction:** Add your IP for security
3. **Save API Key & Secret** (you'll only see secret once!)

### **C. Configure Your Algorithm**

Update `config/api_settings.json`:

```json
{
  "bybit": {
    "testnet": true,
    "api_key": "your_testnet_api_key",
    "api_secret": "your_testnet_secret",
    "base_url": "https://api-testnet.bybit.com",
    "recv_window": 5000
  }
}
```

---

## 🔧 **Step 2: Test Bybit Connection**

### **A. Verify Account Access**

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"

# Test API connection (no real orders)
python -c "
import ccxt
exchange = ccxt.bybit({
    'apiKey': 'your_testnet_key',
    'secret': 'your_testnet_secret',
    'sandbox': True  # Testnet mode
})
print('Balance:', exchange.fetch_balance())
print('Markets:', list(exchange.markets.keys())[:5])
"
```

### **B. Test Order Placement (Testnet)**

```bash
# Place a tiny test order on testnet
python main.py --mode live --symbol BTCUSDT --enable-trading
```

**⚠️ Only fake money will be used - this is testnet!**

---

## 🎯 **Step 3: End-to-End Testing**

### **A. Complete Flow Test**

1. **TradingView generates signal** (manual or wait for market)
2. **Webhook receives alert** (check logs)
3. **Algorithm processes signal** (verify confidence, risk checks)
4. **Bybit testnet order placed** (fake money)
5. **Position management** (stop loss, take profit)

### **B. Monitor Everything**

```bash
# Watch logs in real-time
tail -f trading_algorithm.log

# Check webhook stats
curl http://localhost:8080/stats

# Monitor testnet positions
# (Check Bybit testnet interface)
```

---

## 🚨 **Step 4: Go Live (REAL MONEY - BE CAREFUL!)**

### **⚠️ CRITICAL SAFETY CHECKS:**

- [ ] **Tested thoroughly on testnet**
- [ ] **All signals validated**
- [ ] **Risk limits properly set**
- [ ] **Emergency stop procedures ready**
- [ ] **Small position sizes only**

### **A. Live Bybit Setup**

1. **Bybit main account** → **API Management**
2. **Create LIVE API keys:**
   - **Very restrictive IP whitelist**
   - **Minimal permissions needed**
   - **Short expiry time**

### **B. Live Configuration**

Update `config/api_settings.json`:

```json
{
  "bybit": {
    "testnet": false,
    "api_key": "your_LIVE_api_key",
    "api_secret": "your_LIVE_secret",
    "base_url": "https://api.bybit.com",
    "recv_window": 5000
  }
}
```

### **C. Start with Minimal Risk**

```json
// config/risk_parameters.json
{
  "risk_management": {
    "position_sizing": {
      "max_risk_per_trade": 0.005, // 0.5% max risk
      "max_position_size": 0.01, // 1% max position
      "daily_loss_limit": 0.02 // 2% daily loss limit
    }
  }
}
```

---

## 📊 **Step 5: Monitoring & Risk Management**

### **A. Real-Time Monitoring**

```bash
# Start live system with minimal risk
python main.py --mode live --enable-trading

# Monitor in separate terminal
watch -n 5 'curl -s http://localhost:8080/stats | jq'
```

### **B. Emergency Procedures**

```bash
# EMERGENCY STOP (stops all trading)
curl -X POST http://localhost:8080/emergency-stop

# Close all positions (if needed)
curl -X POST http://localhost:8080/close-all-positions
```

### **C. Daily Checklist**

- [ ] **Check overnight positions**
- [ ] **Review trading logs**
- [ ] **Verify balance changes**
- [ ] **Monitor risk metrics**
- [ ] **Check for any errors**

---

## 🎛️ **Advanced Configuration**

### **A. Symbol-Specific Settings**

```json
// config/crypto_pairs.json - customize per pair
{
  "BTCUSDT": {
    "enabled": true,
    "min_order_size": 0.001,
    "risk_multiplier": 1.0, // Conservative for BTC
    "max_leverage": 1 // Spot trading only
  },
  "ETHUSDT": {
    "enabled": true,
    "min_order_size": 0.01,
    "risk_multiplier": 1.2, // Slightly higher risk for ETH
    "max_leverage": 1
  }
}
```

### **B. Time-Based Controls**

```json
// config/trading.json
{
  "trading_hours": {
    "enabled": true,
    "start_time": "09:00", // Only trade during these hours
    "end_time": "17:00", // (your timezone)
    "timezone": "America/New_York"
  },
  "weekend_trading": false // Pause on weekends
}
```

---

## 📈 **Performance Tracking**

### **A. Key Metrics to Monitor**

- **Win Rate** (aim for >50%)
- **Profit Factor** (aim for >1.5)
- **Max Drawdown** (should be <10%)
- **Sharpe Ratio** (risk-adjusted returns)
- **Daily P&L** vs risk limits

### **B. Regular Reviews**

- **Weekly:** Review all trades, adjust parameters
- **Monthly:** Analyze overall performance
- **Quarterly:** Consider strategy improvements

---

## 🛡️ **Security Best Practices**

### **A. API Key Security**

- ✅ **Unique keys per system**
- ✅ **IP restrictions** always enabled
- ✅ **Minimal permissions** only
- ✅ **Regular key rotation** (monthly)

### **B. System Security**

- ✅ **Secure server** (VPS recommended for 24/7)
- ✅ **Regular backups** of configs
- ✅ **Monitor for unauthorized access**
- ✅ **Keep logs for audit trail**

### **C. Risk Controls**

- ✅ **Position size limits**
- ✅ **Daily loss limits**
- ✅ **Emergency stop mechanisms**
- ✅ **Manual override capabilities**

---

## 🔧 **Troubleshooting**

### **Common Issues:**

- **API connection failed:** Check keys, IP whitelist, network
- **Order rejected:** Verify balance, symbol availability, order size
- **Position not closed:** Check stop loss settings, market conditions
- **High slippage:** Use limit orders, check market volatility

### **Debug Tools:**

```bash
# Test API connection
python -c "import ccxt; print(ccxt.bybit({'apiKey':'KEY','secret':'SECRET'}).fetch_ticker('BTC/USDT'))"

# Check current positions
curl http://localhost:8080/positions

# Review trade history
curl http://localhost:8080/trades/history
```

---

## 🎯 **Success Criteria**

### **Before Going Live:**

- [ ] **100+ successful testnet trades**
- [ ] **All edge cases handled**
- [ ] **Risk management working perfectly**
- [ ] **Monitoring system operational**
- [ ] **Emergency procedures tested**

### **Live Trading Goals:**

- **Week 1:** Break even (learn system behavior)
- **Month 1:** Small consistent profits (1-2% monthly)
- **Month 3:** Optimize and scale (if profitable)

---

**🚀 You're now ready for professional algorithmic trading with proper risk management!**

Remember: **Start small, monitor closely, and never risk more than you can afford to lose.**
