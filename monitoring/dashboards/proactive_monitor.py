"""
🚀 PROACTIVE CRYPTO SIGNAL MONITOR
==================================
This system proactively monitors multiple timeframes and crypto pairs 24/7
Sends alerts even when you're not watching charts
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
import ta
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    symbol: str
    timeframe: str
    action: str
    price: float
    confidence: float
    timestamp: datetime
    conditions_met: List[str]

class ProactiveCryptoMonitor:
    def __init__(self):
        self.symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]
        self.timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
        self.min_confidence = 0.85
        self.webhook_url = "http://localhost:8080/webhook/tradingview"
        self.running = False
        
    async def fetch_klines(self, session: aiohttp.ClientSession, symbol: str, interval: str, limit: int = 100):
        """Fetch historical price data from Binance"""
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        try:
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ])
                
                # Convert to numeric
                numeric_columns = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col])
                
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol} {interval}: {e}")
            return None

    def analyze_signals(self, df: pd.DataFrame, symbol: str, timeframe: str) -> TradingSignal:
        """Apply the same professional signal logic from Pine Script"""
        if df is None or len(df) < 55:
            return None
            
        # Calculate indicators (same as Pine Script)
        ema21 = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
        ema55 = ta.trend.EMAIndicator(df['close'], window=55).ema_indicator()
        rsi = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        volume_ma = ta.trend.SMAIndicator(df['volume'], window=20).sma_indicator()
        
        # MACD
        macd = ta.trend.MACD(df['close'])
        macd_line = macd.macd()
        signal_line = macd.macd_signal()
        
        # Current values
        current_close = df['close'].iloc[-1]
        current_ema21 = ema21.iloc[-1]
        current_ema55 = ema55.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_volume = df['volume'].iloc[-1]
        current_volume_ma = volume_ma.iloc[-1]
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        
        # Previous values for crossover detection
        prev_ema21 = ema21.iloc[-2]
        prev_ema55 = ema55.iloc[-2]
        
        # Signal conditions (same as Pine Script logic)
        golden_cross = (current_ema21 > current_ema55) and (prev_ema21 <= prev_ema55)
        death_cross = (current_ema21 < current_ema55) and (prev_ema21 >= prev_ema55)
        rsi_healthy_buy = 40 < current_rsi < 60
        rsi_healthy_sell = 40 < current_rsi < 70
        price_above_ema21 = current_close > current_ema21
        price_below_ema21 = current_close < current_ema21
        strong_volume = current_volume > current_volume_ma * 1.8
        macd_bullish = current_macd > current_signal and current_macd > 0
        
        # Buy signal analysis
        buy_conditions = []
        buy_score = 0
        
        if golden_cross:
            buy_conditions.append("Golden Cross (EMA21 > EMA55)")
            buy_score += 1
        if rsi_healthy_buy:
            buy_conditions.append(f"RSI Healthy ({current_rsi:.1f})")
            buy_score += 1
        if price_above_ema21:
            buy_conditions.append("Price Above Fast EMA")
            buy_score += 1
        if strong_volume:
            buy_conditions.append("Strong Volume")
            buy_score += 1
        if macd_bullish:
            buy_conditions.append("MACD Bullish")
            buy_score += 1
            
        # Sell signal analysis
        sell_conditions = []
        sell_score = 0
        
        if death_cross:
            sell_conditions.append("Death Cross (EMA21 < EMA55)")
            sell_score += 1
        if rsi_healthy_sell:
            sell_conditions.append(f"RSI Healthy ({current_rsi:.1f})")
            sell_score += 1
        if price_below_ema21:
            sell_conditions.append("Price Below Fast EMA")
            sell_score += 1
        if strong_volume:
            sell_conditions.append("Strong Volume")
            sell_score += 1
        if not macd_bullish:
            sell_conditions.append("MACD Bearish")
            sell_score += 1
        
        # Generate signals (need 4/5 conditions + min confidence)
        buy_confidence = buy_score / 5.0
        sell_confidence = sell_score / 5.0
        
        if buy_score >= 4 and buy_confidence >= self.min_confidence:
            return TradingSignal(
                symbol=symbol,
                timeframe=timeframe,
                action="BUY",
                price=current_close,
                confidence=buy_confidence,
                timestamp=datetime.now(),
                conditions_met=buy_conditions
            )
        elif sell_score >= 4 and sell_confidence >= self.min_confidence:
            return TradingSignal(
                symbol=symbol,
                timeframe=timeframe,
                action="SELL",
                price=current_close,
                confidence=sell_confidence,
                timestamp=datetime.now(),
                conditions_met=sell_conditions
            )
        
        return None

    async def send_webhook_alert(self, signal: TradingSignal):
        """Send webhook alert to your existing system"""
        webhook_data = {
            "symbol": signal.symbol,
            "action": signal.action,
            "price": signal.price,
            "confidence": signal.confidence,
            "timeframe": signal.timeframe,
            "timestamp": signal.timestamp.isoformat(),
            "conditions_met": signal.conditions_met,
            "source": "PROACTIVE_MONITOR",
            "alert_type": "HIGH_CONFIDENCE_SIGNAL"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=webhook_data) as response:
                    if response.status == 200:
                        logger.info(f"✅ Webhook sent: {signal.action} {signal.symbol} ({signal.timeframe}) - {signal.confidence:.1%}")
                    else:
                        logger.error(f"❌ Webhook failed: {response.status}")
        except Exception as e:
            logger.error(f"❌ Webhook error: {e}")

    async def monitor_symbol_timeframe(self, session: aiohttp.ClientSession, symbol: str, timeframe: str):
        """Monitor a specific symbol/timeframe combination"""
        try:
            # Fetch latest data
            df = await self.fetch_klines(session, symbol, timeframe)
            if df is None:
                return
            
            # Analyze for signals
            signal = self.analyze_signals(df, symbol, timeframe)
            
            if signal:
                logger.info(f"🎯 SIGNAL DETECTED: {signal.action} {signal.symbol} ({signal.timeframe}) - {signal.confidence:.1%}")
                logger.info(f"   Conditions: {', '.join(signal.conditions_met)}")
                
                # Send webhook alert
                await self.send_webhook_alert(signal)
                
        except Exception as e:
            logger.error(f"Error monitoring {symbol} {timeframe}: {e}")

    async def scan_all_pairs(self):
        """Proactively scan all symbol/timeframe combinations"""
        logger.info("🔍 Starting proactive scan of all pairs and timeframes...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for symbol in self.symbols:
                for timeframe in self.timeframes:
                    task = self.monitor_symbol_timeframe(session, symbol, timeframe)
                    tasks.append(task)
            
            # Run all monitoring tasks concurrently
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("✅ Scan completed")

    async def run_proactive_monitoring(self):
        """Main monitoring loop - runs 24/7"""
        self.running = True
        logger.info("🚀 PROACTIVE CRYPTO MONITOR STARTED")
        logger.info(f"📊 Monitoring {len(self.symbols)} symbols across {len(self.timeframes)} timeframes")
        logger.info(f"⚡ Minimum confidence: {self.min_confidence:.1%}")
        
        while self.running:
            try:
                await self.scan_all_pairs()
                
                # Wait before next scan (adjust frequency as needed)
                scan_interval = 60  # seconds
                logger.info(f"⏳ Waiting {scan_interval}s before next scan...")
                await asyncio.sleep(scan_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    def stop(self):
        """Stop the monitoring"""
        self.running = False

# Example usage
async def main():
    monitor = ProactiveCryptoMonitor()
    
    try:
        await monitor.run_proactive_monitoring()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down proactive monitor...")
        monitor.stop()

if __name__ == "__main__":
    print("""
🚀 PROACTIVE CRYPTO SIGNAL MONITOR
==================================

This system will:
✅ Monitor 6 major crypto pairs 24/7
✅ Scan across 6 timeframes (1m, 5m, 15m, 1h, 4h, 1d)
✅ Use your professional signal logic
✅ Send webhook alerts to your existing system
✅ Run even when you're not watching charts

Press Ctrl+C to stop monitoring
""")
    
    asyncio.run(main())