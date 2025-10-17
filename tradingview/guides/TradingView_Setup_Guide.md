# 🚀 TradingView Pine Script Setup Guide

## 📋 Step-by-Step Instructions

### **Step 1: Open TradingView**

1. Go to [TradingView.com](https://www.tradingview.com)
2. Sign in to your account (free account works fine)
3. Open a crypto chart (recommended: **BINANCE:BTCUSDT** or **BINANCE:ETHUSDT**)

### **Step 2: Add the Pine Script**

1. Click the **"Pine Editor"** tab at the bottom of the screen
2. Clear any existing code
3. Copy and paste the entire Pine Script from `TradingView_Pine_Script.pine`
4. Click **"Save"** and give it a name like "Crypto Trading Bot Pro"
5. Click **"Add to Chart"**

### **Step 3: Configure the Indicator**

The Pine Script has many customizable settings:

#### **Technical Indicators**

- **RSI Length**: 14 (default, good for most timeframes)
- **RSI Overbought**: 70 (sell signal threshold)
- **RSI Oversold**: 30 (buy signal threshold)
- **Fast MA**: 9 (short-term trend)
- **Slow MA**: 21 (long-term trend)

#### **Alert Settings**

- **Enable RSI Alerts**: ✅ (recommended)
- **Enable MA Cross Alerts**: ✅ (recommended)
- **Enable BB Alerts**: ✅ (recommended)
- **Enable Volume Alerts**: ✅ (recommended)
- **Minimum Confidence**: 0.6 (60% confidence minimum)

### **Step 4: Create Webhook Alert**

1. Right-click on the chart → **"Add Alert"**
2. **Condition**: Select your indicator "Crypto Trading Bot Pro"
3. **Options**:
   - ✅ **"Once Per Bar Close"** (recommended to avoid spam)
   - ✅ **"Only Once"** if you want single alerts
4. **Webhook URL**:
   ```
   https://semiorganically-unexaminable-dessie.ngrok-free.dev/webhook/tradingview
   ```
5. **Message**: Leave empty (Pine Script provides JSON automatically)
6. Click **"Create"**

### **Step 5: Verify Setup**

Your chart should now show:

- 🔵 **Blue line** (Fast MA)
- 🔴 **Red line** (Slow MA)
- 🟨 **Gray bands** (Bollinger Bands)
- 🟢 **BUY signals** with confidence %
- 🔴 **SELL signals** with confidence %
- 🔊 **Volume spike indicators**
- 📊 **Info table** (top-right corner)

---

## 🎯 What Each Signal Means

### **BUY Signals** 🟢

Triggered when:

- RSI crosses above oversold (30)
- Fast MA crosses above Slow MA (bullish trend)
- Price touches lower Bollinger Band (oversold)
- Volume spike confirms the move
- Confidence ≥ 60%

### **SELL Signals** 🔴

Triggered when:

- RSI crosses below overbought (70)
- Fast MA crosses below Slow MA (bearish trend)
- Price touches upper Bollinger Band (overbought)
- Volume spike confirms the move
- Confidence ≥ 60%

### **Confidence Score** 📊

- **60-70%**: Moderate signal
- **70-80%**: Strong signal
- **80%+**: Very strong signal

---

## 📈 Best Timeframes for Different Trading Styles

### **Scalping** (Quick trades)

- **1m, 5m**: Very fast signals
- **High frequency**, more false signals
- **Risk**: Higher, requires tight stop-losses

### **Day Trading** (Recommended)

- **15m, 1h**: Good balance of signals and accuracy
- **Medium frequency**, better quality signals
- **Risk**: Moderate, good for beginners

### **Swing Trading**

- **4h, 1d**: Fewer but higher quality signals
- **Low frequency**, best accuracy
- **Risk**: Lower, longer-term positions

---

## 🔧 Recommended Settings by Asset

### **Bitcoin (BTCUSDT)**

```
RSI Length: 14
RSI Oversold: 30
RSI Overbought: 70
Fast MA: 9
Slow MA: 21
Min Confidence: 0.7
```

### **Ethereum (ETHUSDT)**

```
RSI Length: 14
RSI Oversold: 25
RSI Overbought: 75
Fast MA: 7
Slow MA: 25
Min Confidence: 0.6
```

### **Altcoins (More volatile)**

```
RSI Length: 10
RSI Oversold: 20
RSI Overbought: 80
Fast MA: 5
Slow MA: 15
Min Confidence: 0.8
```

---

## 🚨 Alert JSON Format

Your webhook will receive this JSON structure:

```json
{
  "symbol": "BTCUSDT",
  "action": "BUY",
  "price": 65432.5,
  "timestamp": "2025-09-28T13:45:00Z",
  "confidence": 0.75,
  "timeframe": "1h",
  "rsi": 28.5,
  "macd": -125.3,
  "volume_spike": true,
  "atr": 890.25,
  "stop_loss_pct": 3.2,
  "ma_fast": 65200.0,
  "ma_slow": 64800.0,
  "bb_upper": 66500.0,
  "bb_lower": 64000.0,
  "exchange": "BINANCE",
  "source": "TRADINGVIEW_PINE",
  "strategy": "MULTI_INDICATOR"
}
```

---

## 🎮 Testing Your Setup

### **Option 1: Web Dashboard**

- Open: http://localhost:5001
- Watch for real-time alerts
- See all signal data visualized

### **Option 2: Check Webhook Server**

- Monitor webhook server terminal
- Should show incoming POST requests
- JSON alerts will be logged

### **Option 3: TradingView Alert History**

- Check TradingView alerts panel
- Verify alerts are being sent
- Debug any connection issues

---

## 🔧 Troubleshooting

### **No Alerts Received**

1. Check ngrok is running: `ps aux | grep ngrok`
2. Verify webhook URL in TradingView alert
3. Test webhook: http://localhost:5001 → "Simulate BUY"
4. Check TradingView alert history for errors

### **Too Many/Few Alerts**

1. Adjust **Minimum Confidence** (higher = fewer alerts)
2. Change **timeframe** (higher = fewer, better quality)
3. Modify **RSI levels** (wider range = fewer signals)

### **ngrok Disconnected**

```bash
# Quick restart ngrok
pkill ngrok
ngrok http 8080 --log=stdout
# Update webhook URL in TradingView
```

---

## 🎯 Next Steps After Setup

1. **Test on paper trading** first
2. **Monitor signal quality** for 24-48 hours
3. **Adjust confidence thresholds** based on performance
4. **Add Bybit integration** for automatic trading
5. **Scale up position sizes** gradually

## 📞 Support

If you need help:

1. Check the web dashboard: http://localhost:5001
2. Verify webhook server is receiving data
3. Test with simulation buttons first
4. Monitor TradingView alert panel for delivery status

---

**🚀 Ready to trade with real-time signals!**
