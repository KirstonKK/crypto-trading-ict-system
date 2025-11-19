# 🎯 TradingView Integration Guide

## Phase 2: Complete TradingView Setup for Your Trading Algorithm

### 📋 **Prerequisites**

✅ **Webhook server running locally** (Phase 1 complete)  
✅ **TradingView Pro/Pro+ account** (required for webhooks)  
✅ **Internet connection with open port** (or ngrok for testing)

---

## 🔧 **Step 1: Pine Script Indicator Setup**

### **A. Create the Market Phase Predictor**

1. **Open TradingView** → Pine Editor
2. **Create new script** → Paste this Pine Script:

```pinescript
//@version=5
indicator("Market Phase Predictor - Webhook Integration", shorttitle="MPP-WH", overlay=true)

// ============================================================================
// INPUT PARAMETERS
// ============================================================================
webhook_url = input.string("http://your-ngrok-url/webhook/tradingview",
    title="Webhook URL", group="🔗 Webhook Settings")

enable_alerts = input.bool(true, title="Enable Webhook Alerts", group="🔗 Webhook Settings")

// Timeframe Analysis (from your video)
ma_fast = input.int(20, title="Fast MA", group="📊 Indicators")
ma_slow = input.int(50, title="Slow MA", group="📊 Indicators")
rsi_period = input.int(14, title="RSI Period", group="📊 Indicators")
bb_period = input.int(20, title="BB Period", group="📊 Indicators")
bb_std = input.float(2.0, title="BB StdDev", group="📊 Indicators")

// Risk Management
position_size = input.float(1.0, title="Position Size %", group="🛡️ Risk", minval=0.1, maxval=5.0)
stop_loss_pct = input.float(3.0, title="Stop Loss %", group="🛡️ Risk", minval=1.0, maxval=10.0)

// ============================================================================
// TECHNICAL INDICATORS
// ============================================================================
// Moving averages for trend analysis
ma_fast_val = ta.sma(close, ma_fast)
ma_slow_val = ta.sma(close, ma_slow)

// RSI for momentum
rsi = ta.rsi(close, rsi_period)

// Bollinger Bands for volatility
bb_basis = ta.sma(close, bb_period)
bb_dev = bb_std * ta.stdev(close, bb_period)
bb_upper = bb_basis + bb_dev
bb_lower = bb_basis - bb_dev

// Volume analysis
volume_sma = ta.sma(volume, 20)
high_volume = volume > volume_sma * 1.5

// ============================================================================
// MARKET PHASE DETECTION (Based on your video algorithm)
// ============================================================================

// Phase 1: Trend Detection (Higher timeframe)
uptrend = ma_fast_val > ma_slow_val
downtrend = ma_fast_val < ma_slow_val

// Phase 2: Entry Signal Logic
// BUY CONDITIONS (Green line from video)
buy_signal = uptrend and
             rsi < 70 and rsi > 30 and  // Not overbought/oversold
             close > bb_lower and close < bb_upper and  // Within BB range
             high_volume and
             ta.crossover(close, ma_fast_val) // Price crosses above fast MA

// SELL CONDITIONS (Red line from video)
sell_signal = downtrend and
              rsi > 30 and rsi < 70 and  // Not oversold/overbought
              close > bb_lower and close < bb_upper and  // Within BB range
              high_volume and
              ta.crossunder(close, ma_fast_val) // Price crosses below fast MA

// Phase 3: Confidence Scoring (as mentioned in your strategy)
confidence_buy = 0.0
confidence_sell = 0.0

if buy_signal
    confidence_buy := 0.6  // Base confidence
    confidence_buy := rsi < 50 ? confidence_buy + 0.1 : confidence_buy  // RSI bonus
    confidence_buy := close < bb_basis ? confidence_buy + 0.1 : confidence_buy  // Below BB middle
    confidence_buy := volume > volume_sma * 2 ? confidence_buy + 0.1 : confidence_buy  // Volume bonus

if sell_signal
    confidence_sell := 0.6  // Base confidence
    confidence_sell := rsi > 50 ? confidence_sell + 0.1 : confidence_sell  // RSI bonus
    confidence_sell := close > bb_basis ? confidence_sell + 0.1 : confidence_sell  // Above BB middle
    confidence_sell := volume > volume_sma * 2 ? confidence_sell + 0.1 : confidence_sell  // Volume bonus

// ============================================================================
// VISUALIZATION
// ============================================================================
plot(ma_fast_val, color=color.blue, title="Fast MA", linewidth=2)
plot(ma_slow_val, color=color.red, title="Slow MA", linewidth=2)

// Bollinger Bands
p1 = plot(bb_upper, color=color.gray, title="BB Upper")
p2 = plot(bb_lower, color=color.gray, title="BB Lower")
fill(p1, p2, color=color.gray, transparency=90)

// Buy/Sell signals
plotshape(buy_signal, style=shape.labelup, location=location.belowbar,
          color=color.green, text="BUY", size=size.normal)
plotshape(sell_signal, style=shape.labeldown, location=location.abovebar,
          color=color.red, text="SELL", size=size.normal)

// ============================================================================
// WEBHOOK ALERTS
// ============================================================================
if buy_signal and enable_alerts
    alert('{"symbol":"' + syminfo.ticker + '","action":"BUY","price":' + str.tostring(close) +
          ',"timestamp":"' + str.tostring(timenow) + '","confidence":' + str.tostring(confidence_buy) +
          ',"timeframe":"' + timeframe.period + '","stop_loss_pct":' + str.tostring(stop_loss_pct) + '}',
          alert.freq_once_per_bar)

if sell_signal and enable_alerts
    alert('{"symbol":"' + syminfo.ticker + '","action":"SELL","price":' + str.tostring(close) +
          ',"timestamp":"' + str.tostring(timenow) + '","confidence":' + str.tostring(confidence_sell) +
          ',"timeframe":"' + timeframe.period + ',"stop_loss_pct":' + str.tostring(stop_loss_pct) + '}',
          alert.freq_once_per_bar)
```

---

## 🌐 **Step 2: Expose Local Webhook (For Testing)**

### **Option A: Using ngrok (Recommended for testing)**

```bash
# Install ngrok (if not installed)
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Expose your local webhook server
ngrok http 8080

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Update your Pine Script webhook_url with: https://abc123.ngrok.io/webhook/tradingview
```

### **Option B: Direct Port Forwarding (Advanced)**

- Configure your router to forward port 8080 to your machine
- Use your public IP + port 8080
- **⚠️ Security risk** - only for testing

---

## 🔔 **Step 3: Configure TradingView Alerts**

### **A. Create Alert**

1. **Add indicator** to your chart (BTC/USDT or preferred pair)
2. **Right-click chart** → "Add Alert"
3. **Configure Alert:**
   - **Condition:** `Market Phase Predictor - Webhook Integration`
   - **Options:** `Once Per Bar Close`
   - **Actions:** ✅ `Webhook URL`
   - **Webhook URL:** Your ngrok URL + `/webhook/tradingview`
   - **Message:** `{{strategy.order.alert_message}}`

### **B. Alert Message Format**

The Pine Script will send JSON like:

```json
{
  "symbol": "BTCUSDT",
  "action": "BUY",
  "price": 65000,
  "timestamp": "1695123456789",
  "confidence": 0.75,
  "timeframe": "1h",
  "stop_loss_pct": 3.0
}
```

---

## 🧪 **Step 4: Test the Integration**

### **A. Start Your Webhook Server**

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"
python main.py --mode webhook --port 8080
```

### **B. Test with Manual Alert**

1. **TradingView chart** → Wait for signal
2. **Check webhook server logs** for received alerts
3. **Verify signal processing** in your algorithm

### **C. Monitor Integration**

```bash
# Check webhook stats
curl http://localhost:8080/stats

# Check health
curl http://localhost:8080/health
```

---

## 🎯 **Step 5: Multi-Timeframe Setup (From Your Video)**

### **Multiple Charts for Different Timeframes:**

1. **Daily Chart** - Main trend direction
2. **4H Chart** - Swing analysis
3. **1H Chart** - Entry timing
4. **15M Chart** - Fine-tuned entries

**Set up alerts on each timeframe with different confidence thresholds.**

---

## ⚠️ **Safety & Best Practices**

### **🛡️ Security**

- ✅ Use HTTPS (ngrok provides this)
- ✅ Implement webhook signatures (already in your code)
- ✅ Rate limiting enabled
- ✅ IP whitelisting for production

### **🧪 Testing Protocol**

1. ✅ **Paper trading first** - TradingView paper trading
2. ✅ **Small position sizes** - Start with 0.1% risk
3. ✅ **Monitor all alerts** - Log everything
4. ✅ **Validate signals** - Cross-check with backtests

### **📊 Risk Management**

- ✅ **Stop losses** on every trade
- ✅ **Position sizing** based on volatility
- ✅ **Daily loss limits** configured
- ✅ **Emergency stop** mechanisms

---

## 🔄 **Next Phase: Bybit Integration**

Once TradingView alerts are working:

1. **Set up Bybit testnet account**
2. **Configure API keys**
3. **Test order placement**
4. **Full end-to-end testing**
5. **Go live with minimal risk**

---

## 🆘 **Troubleshooting**

### **Common Issues:**

- **No alerts received:** Check ngrok URL, webhook permissions
- **Alert parsing errors:** Verify JSON format in Pine Script
- **Connection timeouts:** Check firewall, network connectivity
- **Signal not processed:** Review logs, check symbol mapping

### **Debug Commands:**

```bash
# Check webhook server logs
tail -f trading_algorithm.log

# Test webhook manually
curl -X POST http://localhost:8080/webhook/tradingview \
     -H "Content-Type: application/json" \
     -d '{"symbol":"BTCUSDT","action":"BUY","price":65000,"confidence":0.75}'
```

---

**🎉 Ready for live testing!** Your Market Phase Predictor algorithm is now connected to TradingView!
