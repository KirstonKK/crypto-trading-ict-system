#!/usr/bin/env python3
"""
🚀 PROACTIVE CRYPTO MONITOR - WEB DASHBOARD
Real-time web interface for the proactive monitoring system
"""

import asyncio
import aiohttp
import json
import time
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
import ta
from dataclasses import dataclass, asdict
from flask import Flask, render_template_string, jsonify, make_response
from flask_socketio import SocketIO, emit
import threading
import requests
import joblib
import numpy as np

# Add machine learning directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../machine_learning/scripts'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    symbol: str
    timeframe: str
    action: str  # 'BUY' or 'SELL'
    confidence: float
    price: float
    timestamp: str
    indicators: Dict[str, Any]

class ProactiveCryptoMonitor:
    def __init__(self):
        # Configuration - Your selected crypto pairs
        self.symbols = ['BTCUSDT', 'SOLUSDT', 'ETHUSDT', 'XRPUSDT']
        self.timeframes = ['1m', '5m', '15m', '1h', '4h']  # Added 5m for balanced signal detection
        self.min_confidence = 0.60  # 60% minimum confidence (lowered to catch more opportunities)
        self.high_confidence = 0.75  # 75% for premium signals (lowered from 85%)
        self.webhook_url = "http://localhost:8080/webhook/tradingview"
        self.scan_interval = 180  # 3 minutes during market hours (more frequent scanning)
        
        # ML Model Integration
        self.ml_model = None
        self.ml_scaler = None
        self.ml_features = None
        self.load_ml_model()
        
        # Trading Journal Settings
        self.risk_per_trade = 100.0  # $100 risk per trade
        self.risk_reward_ratio = 3.0  # 1:3 RR
        
        # Market Hours (GMT) - Optimized for global trading sessions
        self.active_hours = {
            'start': 7,   # 7:00 GMT (Asian/London overlap)
            'end': 23     # 23:00 GMT (Extended NY session)
        }
        
        # Trading Sessions (GMT)
        self.trading_sessions = {
            'Asia': {'start': 0, 'end': 9, 'name': 'Asia (Tokyo)', 'timezone': 'JST'},
            'London': {'start': 8, 'end': 17, 'name': 'London', 'timezone': 'GMT'},
            'New_York': {'start': 13, 'end': 22, 'name': 'New York', 'timezone': 'EST'}
        }
        
        # State tracking with persistence
        self.last_signals = []
        self.stats_file = "monitoring_stats.json"
        self.scan_count = 0
        self.last_scan_time = None
        self.signals_today = 0
        self.total_signals = 0
        self.trading_journal = []
        self.daily_pnl = 0.0
        self.risk_percentage = 1.0  # 1% of account per trade
        
        # Load persistent stats
        self.load_stats()
        
        logger.info("🚀 PROACTIVE CRYPTO MONITOR INITIALIZED")
        logger.info(f"📊 Monitoring {len(self.symbols)} crypto pairs: {', '.join([s.replace('USDT', '') for s in self.symbols])}")
        logger.info(f"⏰ Active during market hours: 7am - 11pm GMT")
        logger.info(f"🎯 Risk per trade: ${self.risk_per_trade} | RR: 1:{self.risk_reward_ratio}")
        logger.info(f"⚡ Minimum confidence: {self.min_confidence:.1%} | High confidence: {self.high_confidence:.1%}")
        logger.info(f"🤖 ML Model: {'Loaded' if self.ml_model else 'Not Available'}")
        logger.info(f"🎯 Enhanced ATH detection with ML integration")

    def load_ml_model(self):
        """Load the trained ML model for enhanced signal detection"""
        try:
            model_dir = os.path.join(os.path.dirname(__file__), '../../machine_learning/models')
            
            model_path = os.path.join(model_dir, 'crypto_predictor_model.pkl')
            scaler_path = os.path.join(model_dir, 'crypto_predictor_scaler.pkl')
            features_path = os.path.join(model_dir, 'crypto_predictor_features.pkl')
            
            if all(os.path.exists(path) for path in [model_path, scaler_path, features_path]):
                self.ml_model = joblib.load(model_path)
                self.ml_scaler = joblib.load(scaler_path)
                self.ml_features = joblib.load(features_path)
                logger.info("🤖 ML Model loaded successfully")
            else:
                logger.warning("⚠️ ML Model files not found, using technical analysis only")
        except Exception as e:
            logger.error(f"❌ Failed to load ML model: {e}")
            self.ml_model = None

    def load_stats(self):
        """Load persistent statistics from file"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    stats = json.load(f)
                    self.scan_count = stats.get('scan_count', 0)
                    self.signals_today = stats.get('signals_today', 0)
                    self.total_signals = stats.get('total_signals', 0)
                    self.trading_journal = stats.get('trading_journal', [])
                    logger.info(f"📁 Loaded stats: {self.scan_count} scans, {self.total_signals} total signals")
        except Exception as e:
            logger.warning(f"Could not load stats: {e}")
    
    def save_stats(self):
        """Save persistent statistics to file"""
        try:
            stats = {
                'scan_count': self.scan_count,
                'signals_today': self.signals_today,
                'total_signals': self.total_signals,
                'trading_journal': self.trading_journal[-50:]  # Keep last 50 trades
            }
            with open(self.stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save stats: {e}")
    
    def calculate_scan_signal_ratio(self) -> str:
        """Calculate scans per signal ratio"""
        if self.total_signals == 0:
            return "No signals"
        ratio = self.scan_count / self.total_signals
        return f"{ratio:.1f}:1"

    def is_market_hours(self):
        """Check if current time is within active trading hours"""
        current_hour = datetime.now(timezone.utc).hour
        return self.active_hours['start'] <= current_hour <= self.active_hours['end']
        
    def get_trading_sessions_status(self):
        """Get current status of all trading sessions"""
        current_hour = datetime.now(timezone.utc).hour
        sessions_status = {}
        
        for session_key, session_info in self.trading_sessions.items():
            is_open = session_info['start'] <= current_hour <= session_info['end']
            sessions_status[session_key] = {
                'name': session_info['name'],
                'timezone': session_info['timezone'],
                'hours': f"{session_info['start']:02d}:00-{session_info['end']:02d}:00 GMT",
                'status': 'OPEN' if is_open else 'CLOSED',
                'is_open': is_open
            }
            
        return sessions_status
    
    def calculate_trade_metrics(self, signal: 'TradingSignal'):
        """Calculate trade metrics for journal"""
        entry_price = signal.price
        risk_amount = self.risk_per_trade
        
        # Calculate position size based on risk
        # Assuming 1% stop loss for simplicity
        stop_loss_percent = 0.01
        stop_price = entry_price * (1 - stop_loss_percent) if signal.action == 'BUY' else entry_price * (1 + stop_loss_percent)
        
        position_size = risk_amount / (abs(entry_price - stop_price))
        
        # Calculate targets
        profit_amount = risk_amount * self.risk_reward_ratio
        if signal.action == 'BUY':
            target_price = entry_price + (profit_amount / position_size)
        else:
            target_price = entry_price - (profit_amount / position_size)
            
        return {
            'position_size': round(position_size, 6),
            'stop_price': round(stop_price, 2),
            'target_price': round(target_price, 2),
            'risk_amount': risk_amount,
            'profit_target': profit_amount
        }

    async def get_klines(self, symbol: str, interval: str, limit: int = 100):
        """Fetch kline data from Binance"""
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        df = pd.DataFrame(data, columns=[
                            'timestamp', 'open', 'high', 'low', 'close', 'volume',
                            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                            'taker_buy_quote', 'ignored'
                        ])
                        
                        # Convert to numeric
                        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
                        for col in numeric_columns:
                            df[col] = pd.to_numeric(df[col])
                        
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        return df
                    else:
                        logger.error(f"Failed to fetch data for {symbol} {interval}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching {symbol} {interval}: {e}")
            return None

    def get_ml_prediction(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get ML model prediction for enhanced signal confidence"""
        if self.ml_model is None or len(df) < 50:
            return {"ml_confidence": 0.0, "ml_prediction": "NEUTRAL", "ml_score": 0.0}
        
        try:
            # Calculate technical indicators for ML model
            df_ml = df.copy()
            
            # Add technical indicators that ML model expects
            df_ml['rsi'] = ta.momentum.rsi(df_ml['close'], window=14)
            df_ml['macd'] = ta.trend.macd_diff(df_ml['close'])
            df_ml['macd_signal'] = ta.trend.macd_signal(df_ml['close'])
            df_ml['ema_9'] = ta.trend.ema_indicator(df_ml['close'], window=9)
            df_ml['ema_21'] = ta.trend.ema_indicator(df_ml['close'], window=21)
            df_ml['bb_high'] = ta.volatility.bollinger_hband(df_ml['close'])
            df_ml['bb_low'] = ta.volatility.bollinger_lband(df_ml['close'])
            df_ml['bb_mid'] = ta.volatility.bollinger_mavg(df_ml['close'])
            
            # Price change features
            df_ml['price_change_1'] = df_ml['close'].pct_change(1)
            df_ml['price_change_5'] = df_ml['close'].pct_change(5)
            df_ml['volume_sma'] = df_ml['volume'].rolling(window=20).mean()
            df_ml['volume_ratio'] = df_ml['volume'] / df_ml['volume_sma']
            
            # Get latest values for prediction
            latest = df_ml.iloc[-1]
            
            # Prepare features (match the training features)
            features = [
                latest['rsi'],
                latest['macd'],
                latest['macd_signal'],
                latest['ema_9'],
                latest['ema_21'],
                (latest['close'] - latest['bb_low']) / (latest['bb_high'] - latest['bb_low']),  # BB position
                latest['price_change_1'],
                latest['price_change_5'],
                latest['volume_ratio']
            ]
            
            # Handle NaN values
            features = [0.0 if np.isnan(x) else x for x in features]
            features_array = np.array(features).reshape(1, -1)
            
            # Scale features
            features_scaled = self.ml_scaler.transform(features_array)
            
            # Get prediction
            prediction = self.ml_model.predict(features_scaled)[0]
            
            # Convert prediction to confidence and direction
            current_price = latest['close']
            predicted_change = (prediction - current_price) / current_price
            
            ml_confidence = min(abs(predicted_change) * 100, 0.95)  # Cap at 95%
            
            if predicted_change > 0.005:  # >0.5% predicted increase
                ml_prediction = "BULLISH"
                ml_score = ml_confidence
            elif predicted_change < -0.005:  # >0.5% predicted decrease
                ml_prediction = "BEARISH"
                ml_score = ml_confidence
            else:
                ml_prediction = "NEUTRAL"
                ml_score = 0.0
            
            return {
                "ml_confidence": ml_confidence,
                "ml_prediction": ml_prediction,
                "ml_score": ml_score,
                "predicted_price": prediction,
                "predicted_change": predicted_change
            }
            
        except Exception as e:
            logger.error(f"ML prediction error: {e}")
            return {"ml_confidence": 0.0, "ml_prediction": "NEUTRAL", "ml_score": 0.0}

    def calculate_signal_strength(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate trading signal strength using professional indicators + ML"""
        if len(df) < 50:
            return {"confidence": 0.0, "action": "HOLD", "indicators": {}}
        
        try:
            # Get ML prediction first
            ml_result = self.get_ml_prediction(df)
            
            # Calculate technical indicators
            df['ema_9'] = ta.trend.ema_indicator(df['close'], window=9)
            df['ema_21'] = ta.trend.ema_indicator(df['close'], window=21)
            df['ema_50'] = ta.trend.ema_indicator(df['close'], window=50)
            df['rsi'] = ta.momentum.rsi(df['close'], window=14)
            df['macd'] = ta.trend.macd_diff(df['close'])
            df['bb_high'] = ta.volatility.bollinger_hband(df['close'])
            df['bb_low'] = ta.volatility.bollinger_lband(df['close'])
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            
            # Get latest values
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Initialize scoring with higher total weight for ML integration
            buy_signals = 0
            sell_signals = 0
            total_weight = 0
            
            indicators = {}
            
            # 1. ML Model Analysis (Weight: 30% - Highest priority)
            ml_weight = 30
            if ml_result["ml_prediction"] == "BULLISH" and ml_result["ml_confidence"] > 0.3:
                buy_signals += ml_weight * ml_result["ml_confidence"]
                indicators['ml_signal'] = f'ML_BULLISH_{ml_result["ml_confidence"]:.1%}'
            elif ml_result["ml_prediction"] == "BEARISH" and ml_result["ml_confidence"] > 0.3:
                sell_signals += ml_weight * ml_result["ml_confidence"]
                indicators['ml_signal'] = f'ML_BEARISH_{ml_result["ml_confidence"]:.1%}'
            else:
                indicators['ml_signal'] = f'ML_NEUTRAL_{ml_result["ml_confidence"]:.1%}'
            total_weight += ml_weight
            
            # 2. EMA Crossover Analysis (Weight: 20% - Reduced to accommodate ML)
            ema_weight = 20
            if latest['ema_9'] > latest['ema_21'] > latest['ema_50']:
                if prev['ema_9'] <= prev['ema_21'] or prev['ema_21'] <= prev['ema_50']:
                    buy_signals += ema_weight
                    indicators['ema_trend'] = 'STRONG_BULLISH_CROSSOVER'
                else:
                    buy_signals += ema_weight * 0.7
                    indicators['ema_trend'] = 'BULLISH'
            elif latest['ema_9'] < latest['ema_21'] < latest['ema_50']:
                if prev['ema_9'] >= prev['ema_21'] or prev['ema_21'] >= prev['ema_50']:
                    sell_signals += ema_weight
                    indicators['ema_trend'] = 'STRONG_BEARISH_CROSSOVER'
                else:
                    sell_signals += ema_weight * 0.7
                    indicators['ema_trend'] = 'BEARISH'
            else:
                indicators['ema_trend'] = 'NEUTRAL'
            total_weight += ema_weight
            
            # 3. RSI Analysis (Weight: 15% - Reduced)
            rsi_weight = 15
            rsi = latest['rsi']
            # More sensitive RSI thresholds for better signal detection
            if rsi < 35 and prev['rsi'] >= 35:  # RSI breaking below oversold (more sensitive)
                buy_signals += rsi_weight
                indicators['rsi_signal'] = f'OVERSOLD_BREAKOUT_{rsi:.1f}'
            elif rsi > 65 and prev['rsi'] <= 65:  # RSI breaking above overbought (more sensitive)
                sell_signals += rsi_weight
                indicators['rsi_signal'] = f'OVERBOUGHT_BREAKOUT_{rsi:.1f}'
            elif rsi < 30:  # Extreme oversold
                buy_signals += rsi_weight * 0.8
                indicators['rsi_signal'] = f'EXTREME_OVERSOLD_{rsi:.1f}'
            elif rsi > 70:  # Extreme overbought
                sell_signals += rsi_weight * 0.8
                indicators['rsi_signal'] = f'EXTREME_OVERBOUGHT_{rsi:.1f}'
            elif 45 <= rsi <= 55:
                indicators['rsi_signal'] = f'NEUTRAL_{rsi:.1f}'
            else:
                indicators['rsi_signal'] = f'NORMAL_{rsi:.1f}'
            total_weight += rsi_weight
            
            # 4. MACD Analysis (Weight: 15% - Reduced)
            macd_weight = 15
            macd_current = latest['macd']
            macd_prev = prev['macd']
            if macd_current > 0 and macd_prev <= 0:  # MACD crossing above zero
                buy_signals += macd_weight
                indicators['macd_signal'] = 'BULLISH_CROSSOVER'
            elif macd_current < 0 and macd_prev >= 0:  # MACD crossing below zero
                sell_signals += macd_weight
                indicators['macd_signal'] = 'BEARISH_CROSSOVER'
            elif macd_current > macd_prev and macd_current > 0:
                buy_signals += macd_weight * 0.6  # Increased sensitivity
                indicators['macd_signal'] = 'BULLISH_MOMENTUM'
            elif macd_current < macd_prev and macd_current < 0:
                sell_signals += macd_weight * 0.6  # Increased sensitivity
                indicators['macd_signal'] = 'BEARISH_MOMENTUM'
            else:
                indicators['macd_signal'] = 'NEUTRAL'
            total_weight += macd_weight
            
            # 5. Bollinger Bands Analysis (Weight: 10% - Reduced)
            bb_weight = 10
            price = latest['close']
            if price <= latest['bb_low'] and prev['close'] > prev['bb_low']:
                buy_signals += bb_weight
                indicators['bb_signal'] = 'OVERSOLD_BOUNCE'
            elif price >= latest['bb_high'] and prev['close'] < prev['bb_high']:
                sell_signals += bb_weight
                indicators['bb_signal'] = 'OVERBOUGHT_REVERSAL'
            else:
                indicators['bb_signal'] = 'NORMAL'
            total_weight += bb_weight
            
            # 6. Enhanced Volume Confirmation (Weight: 10% - Reduced)
            volume_weight = 10
            volume_ratio = latest['volume'] / latest['volume_sma'] if latest['volume_sma'] > 0 else 1
            volume_trend = latest['volume'] / prev['volume'] if prev['volume'] > 0 else 1
            
            # More sensitive volume thresholds
            if volume_ratio > 1.5 and volume_trend > 1.1:  # Lowered from 2.0 and 1.2
                current_signals = buy_signals - sell_signals
                if current_signals > 0:  # Confirm bullish signals
                    buy_signals += volume_weight
                    indicators['volume_signal'] = f'VOLUME_CONFIRM_BUY_{volume_ratio:.1f}x'
                elif current_signals < 0:  # Confirm bearish signals
                    sell_signals += volume_weight
                    indicators['volume_signal'] = f'VOLUME_CONFIRM_SELL_{volume_ratio:.1f}x'
                else:
                    indicators['volume_signal'] = f'HIGH_VOLUME_NEUTRAL_{volume_ratio:.1f}x'
            elif volume_ratio > 1.2:  # Moderate volume confirmation (lowered from 1.3)
                current_signals = buy_signals - sell_signals
                if current_signals > 0:
                    buy_signals += volume_weight * 0.6
                    indicators['volume_signal'] = f'MODERATE_VOLUME_BUY_{volume_ratio:.1f}x'
                elif current_signals < 0:
                    sell_signals += volume_weight * 0.6
                    indicators['volume_signal'] = f'MODERATE_VOLUME_SELL_{volume_ratio:.1f}x'
                else:
                    indicators['volume_signal'] = f'MODERATE_VOLUME_{volume_ratio:.1f}x'
            elif volume_ratio < 0.6:  # Low volume - reduce signal strength (increased from 0.5)
                buy_signals *= 0.9  # Less penalty (increased from 0.8)
                sell_signals *= 0.9
                indicators['volume_signal'] = f'LOW_VOLUME_WARNING_{volume_ratio:.1f}x'
            else:
                indicators['volume_signal'] = f'NORMAL_VOLUME_{volume_ratio:.1f}x'
            total_weight += volume_weight
            
            # 7. Trend Strength Confirmation (Weight: 10% - Reduced)
            trend_weight = 10
            ema_9_trend = (latest['ema_9'] - df['ema_9'].iloc[-5]) / df['ema_9'].iloc[-5] * 100
            ema_21_trend = (latest['ema_21'] - df['ema_21'].iloc[-5]) / df['ema_21'].iloc[-5] * 100
            
            if ema_9_trend > 1.5 and ema_21_trend > 0.8:  # Lowered from 2% and 1%
                buy_signals += trend_weight
                indicators['trend_strength'] = f'STRONG_UPTREND_{ema_9_trend:.1f}%'
            elif ema_9_trend < -1.5 and ema_21_trend < -0.8:  # Lowered thresholds
                sell_signals += trend_weight
                indicators['trend_strength'] = f'STRONG_DOWNTREND_{ema_9_trend:.1f}%'
            elif abs(ema_9_trend) < 0.3 and abs(ema_21_trend) < 0.2:  # Sideways trend
                # Less penalty for sideways market
                buy_signals *= 0.85  # Increased from 0.7
                sell_signals *= 0.85
                indicators['trend_strength'] = f'SIDEWAYS_{ema_9_trend:.1f}%'
            else:
                indicators['trend_strength'] = f'MODERATE_TREND_{ema_9_trend:.1f}%'
            total_weight += trend_weight
            
            # Calculate final confidence and action
            buy_confidence = buy_signals / total_weight
            sell_confidence = sell_signals / total_weight
            
            if buy_confidence > sell_confidence and buy_confidence >= self.min_confidence:
                action = "BUY"
                confidence = buy_confidence
            elif sell_confidence > buy_confidence and sell_confidence >= self.min_confidence:
                action = "SELL"
                confidence = sell_confidence
            else:
                action = "HOLD"
                confidence = max(buy_confidence, sell_confidence)
            
            # Add ML data to indicators
            indicators.update({
                'price': float(latest['close']),
                'rsi': float(rsi),
                'macd': float(macd_current),
                'volume_ratio': float(volume_ratio),
                'ema_9': float(latest['ema_9']),
                'ema_21': float(latest['ema_21']),
                'buy_score': float(buy_confidence),
                'sell_score': float(sell_confidence),
                'ml_confidence': ml_result.get("ml_confidence", 0.0),
                'ml_prediction': ml_result.get("ml_prediction", "NEUTRAL"),
                'predicted_change': ml_result.get("predicted_change", 0.0)
            })
            
            return {
                "confidence": confidence,
                "action": action,
                "indicators": indicators
            }
            
        except Exception as e:
            logger.error(f"Error calculating signal: {e}")
            return {"confidence": 0.0, "action": "HOLD", "indicators": {}}

    async def scan_symbol_timeframe(self, symbol: str, timeframe: str) -> TradingSignal:
        """Scan a specific symbol and timeframe for signals"""
        df = await self.get_klines(symbol, timeframe, 100)
        if df is None:
            return None
        
        signal_data = self.calculate_signal_strength(df)
        
        if signal_data['action'] != 'HOLD' and signal_data['confidence'] >= self.min_confidence:
            signal = TradingSignal(
                symbol=symbol,
                timeframe=timeframe,
                action=signal_data['action'],
                confidence=signal_data['confidence'],
                price=signal_data['indicators']['price'],
                timestamp=datetime.now().isoformat(),
                indicators=signal_data['indicators']
            )
            
            # Add to trading journal with enhanced columns
            trade_metrics = self.calculate_trade_metrics(signal)
            self.total_signals += 1
            journal_entry = {
                'id': len(self.trading_journal) + 1,
                'timestamp': signal.timestamp,
                'symbol': symbol,
                'action': signal_data['action'],
                'entry_price': signal.price,
                'confidence': signal_data['confidence'],
                'timeframe': timeframe,  # TF column
                'position': 'Long' if signal_data['action'] == 'BUY' else 'Short',  # Position column
                'risk_percentage': self.risk_percentage,  # Risk % column
                'position_size': trade_metrics['position_size'],
                'stop_loss': trade_metrics['stop_price'],
                'take_profit': trade_metrics['target_price'],
                'risk_amount': trade_metrics['risk_amount'],
                'profit_target': trade_metrics['profit_target'],
                'status': 'PENDING',  # Will be updated to Win/Loss
                'pnl': 0.0,  # PnL column - will be updated when trade closes
                'scan_signal_ratio': self.calculate_scan_signal_ratio(),  # Scans/Signal ratio
                'confluences': self.get_signal_confluences(signal_data['indicators'])
            }
            
            self.trading_journal.append(journal_entry)
            self.save_stats()  # Save after adding new journal entry
            
            return signal
        return None

    def get_signal_confluences(self, indicators):
        """Extract the confluences that triggered the signal"""
        confluences = []
        
        if 'ema_trend' in indicators:
            if 'BULLISH' in indicators['ema_trend']:
                confluences.append(f"📈 EMA Alignment: {indicators['ema_trend']}")
            elif 'BEARISH' in indicators['ema_trend']:
                confluences.append(f"📉 EMA Alignment: {indicators['ema_trend']}")
        
        if 'rsi_signal' in indicators:
            if 'OVERSOLD' in indicators['rsi_signal']:
                confluences.append(f"🎯 RSI Oversold: {indicators['rsi_signal']}")
            elif 'OVERBOUGHT' in indicators['rsi_signal']:
                confluences.append(f"⚠️ RSI Overbought: {indicators['rsi_signal']}")
        
        if 'macd_signal' in indicators:
            if 'BULLISH' in indicators['macd_signal']:
                confluences.append(f"🚀 MACD Bullish: {indicators['macd_signal']}")
            elif 'BEARISH' in indicators['macd_signal']:
                confluences.append(f"🔻 MACD Bearish: {indicators['macd_signal']}")
        
        if 'bb_signal' in indicators:
            if indicators['bb_signal'] != 'NORMAL':
                confluences.append(f"📊 Bollinger: {indicators['bb_signal']}")
        
        if 'volume_signal' in indicators:
            if 'HIGH_VOLUME' in indicators['volume_signal']:
                confluences.append(f"📢 {indicators['volume_signal']}")
                
        return confluences

    async def scan_all_pairs(self):
        """Scan all symbol-timeframe combinations for signals"""
        # Check if within active hours
        if not self.is_market_hours():
            logger.info(f"⏰ Outside active hours (7am-11pm GMT), skipping scan")
            return []
        
        self.scan_count += 1
        self.save_stats()  # Save scan count immediately
        self.last_scan_time = datetime.now()
        signals_found = []
        
        logger.info(f"🔍 Starting scan #{self.scan_count} - Market Hours Active")
        
        # Create tasks for all symbol-timeframe combinations
        tasks = []
        for symbol in self.symbols:
            for timeframe in self.timeframes:
                task = self.scan_symbol_timeframe(symbol, timeframe)
                tasks.append(task)
        
        # Execute all scans concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, TradingSignal):
                signals_found.append(result)
                await self.send_webhook_alert(result)
        
        self.last_signals = signals_found
        self.signals_today += len(signals_found)
        
        logger.info(f"✅ Scan #{self.scan_count} completed - Found {len(signals_found)} high-confidence signals")
        return signals_found

    async def send_webhook_alert(self, signal: TradingSignal):
        """Send webhook alert to your existing system"""
        webhook_data = {
            "symbol": signal.symbol,
            "action": signal.action,
            "price": signal.price,
            "confidence": signal.confidence,
            "timeframe": signal.timeframe,
            "timestamp": signal.timestamp,
            "source": "proactive_monitor",
            "indicators": signal.indicators
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

    def get_status(self):
        """Get current monitor status"""
        current_time = datetime.now(timezone.utc)
        market_status = "ACTIVE" if self.is_market_hours() else "CLOSED"
        
        return {
            'scan_count': self.scan_count,
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'signals_today': self.signals_today,
            'total_signals': self.total_signals,
            'scan_signal_ratio': self.calculate_scan_signal_ratio(),
            'last_signals': [asdict(signal) for signal in self.last_signals],
            'symbols_monitored': self.symbols,
            'timeframes_monitored': self.timeframes,
            'total_combinations': len(self.symbols) * len(self.timeframes),
            'min_confidence': self.min_confidence,
            'scan_interval': self.scan_interval,
            'market_status': market_status,
            'active_hours': '7am-11pm GMT',
            'trading_sessions': self.get_trading_sessions_status(),
            'trading_journal': self.trading_journal[-10:],  # Last 10 trades
            'daily_pnl': self.daily_pnl,
            'risk_per_trade': self.risk_per_trade,
            'risk_reward_ratio': self.risk_reward_ratio,
            'current_time_gmt': current_time.strftime('%H:%M GMT')
        }

# Global monitor instance
monitor = ProactiveCryptoMonitor()

# Flask app for web dashboard
app = Flask(__name__)
app.config['SECRET_KEY'] = 'proactive_crypto_monitor_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# HTML template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
        <title>Kirston's Crypto Bot - Live Trading Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 15px;
            background: linear-gradient(135deg, #0f1419 0%, #1a2332 50%, #2d4a68 100%);
            color: white;
            min-height: 100vh;
            font-size: 14px;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .card {
            background: rgba(255,255,255,0.08);
            padding: 20px;
            border-radius: 12px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .stat-card {
            background: rgba(255,255,255,0.08);
            padding: 15px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            text-align: center;
        }
        .stat-number {
            font-size: 1.8em;
            font-weight: bold;
            color: #00ff88;
        }
        .stat-label {
            color: rgba(255,255,255,0.7);
            margin-top: 5px;
        }
        .market-status {
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        .market-active {
            background: #00ff88;
            color: black;
        }
        .market-closed {
            background: #ff4757;
            color: white;
        }
        .signal-item {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid;
        }
        .signal-buy {
            border-left-color: #00ff88;
        }
        .signal-sell {
            border-left-color: #ff4757;
        }
        .journal-entry {
            background: rgba(255,255,255,0.05);
            padding: 12px;
            margin: 8px 0;
            border-radius: 8px;
            border-left: 3px solid;
            font-size: 13px;
        }
        .trade-buy {
            border-left-color: #00ff88;
        }
        .trade-sell {
            border-left-color: #ff4757;
        }
        .trade-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .trade-symbol {
            font-weight: bold;
            color: #00ff88;
        }
        .trade-action {
            padding: 2px 8px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 0.8em;
        }
        .action-buy {
            background: #00ff88;
            color: black;
        }
        .action-sell {
            background: #ff4757;
            color: white;
        }
        .trade-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 8px;
            font-size: 12px;
        }
        .confluences {
            margin-top: 8px;
        }
        .confluence-tag {
            display: inline-block;
            background: rgba(0,255,136,0.2);
            color: #00ff88;
            padding: 2px 6px;
            border-radius: 10px;
            margin: 2px;
            font-size: 11px;
        }
        .confidence-bar {
            height: 4px;
            background: rgba(255,255,255,0.2);
            border-radius: 2px;
            overflow: hidden;
            margin: 5px 0;
        }
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #ffd700, #00ff88);
            transition: width 0.3s ease;
        }
        .no-data {
            text-align: center;
            padding: 30px;
            color: rgba(255,255,255,0.5);
            font-style: italic;
        }
        .refresh-btn {
            background: #00ff88;
            color: black;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            margin: 5px;
            font-size: 12px;
        }
        .refresh-btn:hover {
            background: #00cc6a;
        }
        .section-title {
            color: #00ff88;
            margin-bottom: 15px;
            font-weight: bold;
            border-bottom: 1px solid rgba(0,255,136,0.3);
            padding-bottom: 5px;
        }
        .price-target {
            color: #ffd700;
            font-weight: bold;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #00ff88;
            animation: pulse 2s infinite;
            margin-right: 5px;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .crypto-symbols {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 10px 0;
        }
        .crypto-symbol {
            background: rgba(255,255,255,0.1);
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
        }
        .signals-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .signals-table th {
            padding: 8px;
            text-align: left;
            color: #00ff88;
            font-size: 12px;
            background: rgba(0,255,136,0.2);
            border-bottom: 2px solid rgba(0,255,136,0.5);
        }
        .signals-table td {
            padding: 6px 8px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            font-size: 11px;
        }
        .signals-table tr:hover {
            background: rgba(255,255,255,0.05);
        }
        .table-crypto {
            font-weight: bold;
            color: #00ff88;
        }
        .table-buy {
            color: #00ff88;
            font-weight: bold;
        }
        .table-sell {
            color: #ff4757;
            font-weight: bold;
        }
        .table-price {
            color: #ffd700;
            font-weight: bold;
        }
        .table-confidence {
            font-weight: bold;
        }
        .table-time {
            color: rgba(255,255,255,0.8);
        }
        .status-badge {
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status-pending {
            background-color: rgba(255, 193, 7, 0.2);
            color: #ffc107;
            border: 1px solid rgba(255, 193, 7, 0.3);
        }
        .status-win {
            background-color: rgba(0, 255, 136, 0.2);
            color: #00ff88;
            border: 1px solid rgba(0, 255, 136, 0.3);
        }
        .status-loss {
            background-color: rgba(255, 71, 87, 0.2);
            color: #ff4757;
            border: 1px solid rgba(255, 71, 87, 0.3);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Kirston's Crypto Bot</h1>
        <div class="crypto-symbols">
            <span class="crypto-symbol">₿ BTC</span>
            <span class="crypto-symbol">◎ SOL</span>
            <span class="crypto-symbol">Ξ ETH</span>
            <span class="crypto-symbol">✕ XRP</span>
        </div>
        <p><span class="status-indicator"></span> <span id="market-status">Monitoring Active</span> | <span id="current-time">--:-- GMT</span></p>
        <button class="refresh-btn" onclick="requestUpdate()">🔄 Refresh</button>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number" id="scan-count">0</div>
            <div class="stat-label">Total Scans</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="signals-today">0</div>
            <div class="stat-label">Signals Today</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="daily-pnl">$0</div>
            <div class="stat-label">Daily P&L</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="active-hours">08:00-22:00</div>
            <div class="stat-label">Active Hours GMT</div>
        </div>
    </div>

    <div class="main-grid">
        <div class="card">
            <h2 class="section-title">🎯 Live Trading Signals</h2>
            <div id="signals-list">
                <div class="no-data">🔍 Scanning for high-confidence signals during market hours...</div>
            </div>
        </div>

        <div class="card">
            <h2 class="section-title">📊 Trading Journal</h2>
            <div style="margin-bottom: 10px; font-size: 12px; color: rgba(255,255,255,0.7);">
                Risk per trade: $<span id="risk-per-trade">100</span> (<span id="risk-percentage">1</span>%) | RR: 1:<span id="risk-reward">3</span> | Scans/Signal: <span id="scan-signal-ratio">No signals</span>
            </div>
            <div style="overflow-x: auto;">
                <table id="journal-table" style="width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px;">
                    <thead>
                        <tr style="background: rgba(0,150,255,0.2); border-bottom: 2px solid rgba(0,150,255,0.5);">
                            <th style="padding: 8px 6px; text-align: left; color: #0096ff; font-size: 11px; min-width: 50px;">Symbol</th>
                            <th style="padding: 8px 6px; text-align: center; color: #0096ff; font-size: 11px; min-width: 35px;">TF</th>
                            <th style="padding: 8px 6px; text-align: center; color: #0096ff; font-size: 11px; min-width: 50px;">Position</th>
                            <th style="padding: 8px 6px; text-align: center; color: #0096ff; font-size: 11px; min-width: 45px;">Risk %</th>
                            <th style="padding: 8px 6px; text-align: center; color: #0096ff; font-size: 11px; min-width: 60px;">Entry</th>
                            <th style="padding: 8px 6px; text-align: center; color: #0096ff; font-size: 11px; min-width: 60px;">Status</th>
                            <th style="padding: 8px 6px; text-align: center; color: #0096ff; font-size: 11px; min-width: 60px;">PnL</th>
                        </tr>
                    </thead>
                    <tbody id="journal-table-body">
                        <tr>
                            <td colspan="7" style="padding: 20px; text-align: center; color: rgba(255,255,255,0.6); font-style: italic;">📝 No trades logged yet</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="card">
        <h2 class="section-title">🌍 Global Trading Sessions Status</h2>
        <div style="overflow-x: auto;">
            <table id="sessions-table" style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <thead>
                    <tr style="background: rgba(0,255,136,0.2); border-bottom: 2px solid rgba(0,255,136,0.5);">
                        <th style="padding: 10px; text-align: left; color: #00ff88; font-size: 13px;">Session</th>
                        <th style="padding: 10px; text-align: left; color: #00ff88; font-size: 13px;">Hours (GMT)</th>
                        <th style="padding: 10px; text-align: left; color: #00ff88; font-size: 13px;">Timezone</th>
                        <th style="padding: 10px; text-align: center; color: #00ff88; font-size: 13px;">Status</th>
                    </tr>
                </thead>
                <tbody id="sessions-table-body">
                    <!-- Session data will be populated by JavaScript -->
                </tbody>
            </table>
        </div>
    </div>

    <div class="card">
        <h2 class="section-title">📅 Signals Summary Table (Ghana Time)</h2>
        <div style="overflow-x: auto;">
            <table id="signals-table" style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <thead>
                    <tr style="background: rgba(0,255,136,0.2); border-bottom: 2px solid rgba(0,255,136,0.5);">
                        <th style="padding: 8px; text-align: left; color: #00ff88; font-size: 12px;">#</th>
                        <th style="padding: 8px; text-align: left; color: #00ff88; font-size: 12px;">Crypto</th>
                        <th style="padding: 8px; text-align: left; color: #00ff88; font-size: 12px;">Action</th>
                        <th style="padding: 8px; text-align: left; color: #00ff88; font-size: 12px;">Entry Price</th>
                        <th style="padding: 8px; text-align: left; color: #00ff88; font-size: 12px;">Confidence</th>
                        <th style="padding: 8px; text-align: left; color: #00ff88; font-size: 12px;">Ghana Date & Time</th>
                        <th style="padding: 8px; text-align: left; color: #00ff88; font-size: 12px;">Timeframe</th>
                    </tr>
                </thead>
                <tbody id="signals-table-body">
                    <tr>
                        <td colspan="7" style="padding: 20px; text-align: center; color: rgba(255,255,255,0.5); font-style: italic;">
                            No signals recorded yet today
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to trading monitor');
            requestUpdate();
        });

        socket.on('status_update', function(data) {
            updateDashboard(data);
        });

        socket.on('new_signal', function(signal) {
            console.log('New signal received:', signal);
            addSignalToList(signal);
            // Request full update to refresh the table with journal data
            requestUpdate();
        });

        function requestUpdate() {
            socket.emit('request_update');
        }

        function updateDashboard(status) {
            // Update stats
            document.getElementById('scan-count').textContent = status.scan_count;
            document.getElementById('signals-today').textContent = status.signals_today;
            document.getElementById('daily-pnl').textContent = '$' + status.daily_pnl.toFixed(0);
            document.getElementById('active-hours').textContent = status.active_hours;
            document.getElementById('risk-per-trade').textContent = status.risk_per_trade;
            document.getElementById('risk-reward').textContent = status.risk_reward_ratio;
            document.getElementById('current-time').textContent = status.current_time_gmt;
            
            // Update scan signal ratio
            if (document.getElementById('scan-signal-ratio')) {
                document.getElementById('scan-signal-ratio').textContent = status.scan_signal_ratio || 'No signals';
            }
            
            // Update market status
            const marketStatusElement = document.getElementById('market-status');
            const marketStatus = status.market_status === 'ACTIVE' ? 'Market Active' : 'Market Closed';
            marketStatusElement.textContent = marketStatus;
            marketStatusElement.className = status.market_status === 'ACTIVE' ? 'market-active' : 'market-closed';

            // Update signals
            updateSignals(status.last_signals);
            
            // Update trading sessions table
            updateSessionsTable(status.trading_sessions);
            
            // Update trading journal
            updateJournal(status.trading_journal);
            
            // Update signals table
            updateSignalsTable(status.trading_journal);
        }

        function updateSignalsTable(journal) {
            const tableBody = document.getElementById('signals-table-body');
            if (journal && journal.length > 0) {
                tableBody.innerHTML = '';
                journal.forEach((trade, index) => {
                    const row = document.createElement('tr');
                    
                    // Convert UTC timestamp to Ghana time (GMT+0, same as UTC)
                    const timestamp = new Date(trade.timestamp);
                    const ghanaDate = timestamp.toLocaleDateString('en-GB', { timeZone: 'GMT' });
                    const ghanaTime = timestamp.toLocaleTimeString('en-GB', { 
                        timeZone: 'GMT',
                        hour12: false,
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                    
                    const cryptoName = trade.symbol.replace('USDT', '');
                    const cryptoEmoji = getCryptoEmoji(cryptoName);
                    
                    row.innerHTML = `
                        <td style="color: rgba(255,255,255,0.7);">${trade.id}</td>
                        <td class="table-crypto">${cryptoEmoji} ${cryptoName}</td>
                        <td class="table-${trade.action.toLowerCase()}">${trade.action}</td>
                        <td class="table-price">$${trade.entry_price.toFixed(4)}</td>
                        <td class="table-confidence">${(trade.confidence * 100).toFixed(1)}%</td>
                        <td class="table-time">${ghanaDate} ${ghanaTime}</td>
                        <td style="color: rgba(255,255,255,0.7);">${trade.timeframe}</td>
                    `;
                    
                    tableBody.appendChild(row);
                });
            } else {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="7" style="padding: 20px; text-align: center; color: rgba(255,255,255,0.5); font-style: italic;">
                            No signals recorded yet today
                        </td>
                    </tr>
                `;
            }
        }

        function getCryptoEmoji(crypto) {
            const emojis = {
                'BTC': '₿',
                'SOL': '◎', 
                'ETH': 'Ξ',
                'XRP': '✕'
            };
            return emojis[crypto] || '🪙';
        }

        function updateSignals(signals) {
            const signalsList = document.getElementById('signals-list');
            if (signals && signals.length > 0) {
                signalsList.innerHTML = '';
                signals.forEach(signal => {
                    addSignalToList(signal);
                });
            } else {
                signalsList.innerHTML = '<div class="no-data">✅ No high-confidence signals found in recent scans</div>';
            }
        }

        function updateJournal(journal) {
            const journalTableBody = document.getElementById('journal-table-body');
            if (journal && journal.length > 0) {
                journalTableBody.innerHTML = '';
                journal.reverse().forEach(trade => {
                    addTradeToJournalTable(trade);
                });
            } else {
                journalTableBody.innerHTML = '<tr><td colspan="7" style="padding: 20px; text-align: center; color: rgba(255,255,255,0.6); font-style: italic;">📝 No trades logged yet</td></tr>';
            }
        }

        function addTradeToJournalTable(trade) {
            const journalTableBody = document.getElementById('journal-table-body');
            const row = document.createElement('tr');
            row.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
            
            const statusClass = trade.status === 'PENDING' ? 'pending' : 
                               trade.status === 'WIN' ? 'win' : 
                               trade.status === 'LOSS' ? 'loss' : 'pending';
            
            const pnlColor = trade.pnl > 0 ? '#00ff88' : 
                            trade.pnl < 0 ? '#ff4757' : 
                            'rgba(255,255,255,0.7)';
            
            row.innerHTML = `
                <td style="padding: 8px 6px; font-weight: bold; color: #ffffff;">${trade.symbol.replace('USDT', '')}</td>
                <td style="padding: 8px 6px; text-align: center; font-size: 11px; color: rgba(255,255,255,0.8);">${trade.timeframe}</td>
                <td style="padding: 8px 6px; text-align: center; font-size: 11px; color: ${trade.position === 'Long' ? '#00ff88' : '#ff4757'};">${trade.position}</td>
                <td style="padding: 8px 6px; text-align: center; font-size: 11px; color: rgba(255,255,255,0.8);">${trade.risk_percentage}%</td>
                <td style="padding: 8px 6px; text-align: center; font-size: 11px; color: rgba(255,255,255,0.8);">$${trade.entry_price.toFixed(4)}</td>
                <td style="padding: 8px 6px; text-align: center; font-size: 11px;">
                    <span class="status-badge status-${statusClass}" style="padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold;">
                        ${trade.status}
                    </span>
                </td>
                <td style="padding: 8px 6px; text-align: center; font-size: 11px; font-weight: bold; color: ${pnlColor};">
                    ${trade.pnl === 0 ? '--' : '$' + trade.pnl.toFixed(2)}
                </td>
            `;
            
            journalTableBody.appendChild(row);
        }

        function addSignalToList(signal) {
            const signalsList = document.getElementById('signals-list');
            
            if (signalsList.querySelector('.no-data')) {
                signalsList.innerHTML = '';
            }

            const timestamp = new Date(signal.timestamp);
            const timeStr = timestamp.toLocaleTimeString();
            
            const signalDiv = document.createElement('div');
            signalDiv.className = `signal-item signal-${signal.action.toLowerCase()}`;
            
            signalDiv.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div style="font-size: 1.1em; font-weight: bold;">${signal.symbol.replace('USDT', '')} (${signal.timeframe})</div>
                    <div class="trade-action action-${signal.action.toLowerCase()}">${signal.action}</div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <div>Entry: <span class="price-target">$${signal.price.toFixed(4)}</span></div>
                    <div>Confidence: ${(signal.confidence * 100).toFixed(1)}%</div>
                </div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${signal.confidence * 100}%"></div>
                </div>
                <div style="font-size: 0.85em; color: rgba(255,255,255,0.7);">
                    ${timeStr}
                </div>
            `;
            
            signalsList.insertBefore(signalDiv, signalsList.firstChild);
            
            // Keep only latest 5 signals
            const signals = signalsList.querySelectorAll('.signal-item');
            if (signals.length > 5) {
                signalsList.removeChild(signals[signals.length - 1]);
            }
        }

        function addTradeToJournal(trade) {
            const journalList = document.getElementById('journal-list');
            
            if (journalList.querySelector('.no-data')) {
                journalList.innerHTML = '';
            }

            const timestamp = new Date(trade.timestamp);
            const timeStr = timestamp.toLocaleTimeString();
            
            const tradeDiv = document.createElement('div');
            tradeDiv.className = `journal-entry trade-${trade.action.toLowerCase()}`;
            
            tradeDiv.innerHTML = `
                <div class="trade-header">
                    <div class="trade-symbol">#${trade.id} ${trade.symbol.replace('USDT', '')}</div>
                    <div class="trade-action action-${trade.action.toLowerCase()}">${trade.action}</div>
                </div>
                <div class="trade-details">
                    <div>Entry: <span class="price-target">$${trade.entry_price.toFixed(4)}</span></div>
                    <div>Size: ${trade.position_size.toFixed(6)}</div>
                    <div>Stop: $${trade.stop_loss.toFixed(4)}</div>
                    <div>Target: <span class="price-target">$${trade.take_profit.toFixed(4)}</span></div>
                    <div>Risk: $${trade.risk_amount}</div>
                    <div>Reward: $${trade.profit_target}</div>
                </div>
                <div class="confluences">
                    ${trade.confluences.map(conf => `<span class="confluence-tag">${conf}</span>`).join('')}
                </div>
                <div style="font-size: 0.8em; color: rgba(255,255,255,0.6); margin-top: 5px;">
                    ${timeStr} | ${trade.timeframe} | ${(trade.confidence * 100).toFixed(1)}%
                </div>
            `;
            
            journalList.insertBefore(tradeDiv, journalList.firstChild);
        }

        function updateSessionsTable(sessions) {
            const tableBody = document.getElementById('sessions-table-body');
            if (sessions) {
                tableBody.innerHTML = '';
                
                // Order sessions: Asia, London, New York
                const sessionOrder = ['Asia', 'London', 'New_York'];
                sessionOrder.forEach(sessionKey => {
                    if (sessions[sessionKey]) {
                        const session = sessions[sessionKey];
                        const statusColor = session.is_open ? '#00ff88' : '#ff6b6b';
                        const statusBg = session.is_open ? 'rgba(0,255,136,0.2)' : 'rgba(255,107,107,0.2)';
                        
                        const row = `
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                <td style="padding: 12px; color: rgba(255,255,255,0.9); font-weight: 500;">
                                    ${session.name}
                                </td>
                                <td style="padding: 12px; color: rgba(255,255,255,0.8); font-family: 'Courier New', monospace;">
                                    ${session.hours}
                                </td>
                                <td style="padding: 12px; color: rgba(255,255,255,0.7);">
                                    ${session.timezone}
                                </td>
                                <td style="padding: 12px; text-align: center;">
                                    <span style="
                                        padding: 4px 12px; 
                                        border-radius: 20px; 
                                        background: ${statusBg}; 
                                        color: ${statusColor}; 
                                        font-weight: bold; 
                                        font-size: 11px; 
                                        text-transform: uppercase;
                                    ">
                                        ${session.status}
                                    </span>
                                </td>
                            </tr>
                        `;
                        tableBody.innerHTML += row;
                    }
                });
            }
        }

        // Auto-refresh every 2 minutes
        setInterval(requestUpdate, 120000);
        
        // Initial load
        setTimeout(requestUpdate, 1000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    response = make_response(render_template_string(DASHBOARD_HTML))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/status')
def api_status():
    return jsonify(monitor.get_status())

@socketio.on('connect')
def handle_connect():
    print('Client connected to dashboard')
    emit('status_update', monitor.get_status())

@socketio.on('request_update')
def handle_update_request():
    emit('status_update', monitor.get_status())

# Background monitoring task
async def background_monitor():
    """Background task that runs the monitoring loop"""
    while True:
        try:
            signals = await monitor.scan_all_pairs()
            
            # Emit new signals to web dashboard
            if signals:
                for signal in signals:
                    socketio.emit('new_signal', asdict(signal))
            
            # Emit status update
            socketio.emit('status_update', monitor.get_status())
            
            # Check if we're in active hours
            if monitor.is_market_hours():
                logger.info(f"⏳ Waiting {monitor.scan_interval}s before next scan...")
                await asyncio.sleep(monitor.scan_interval)
            else:
                # Check every 10 minutes when market is closed
                logger.info("💤 Market closed, checking again in 10 minutes...")
                await asyncio.sleep(600)
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error

def run_monitor():
    """Run the async monitor in a separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(background_monitor())

if __name__ == "__main__":
    # Start the background monitor in a separate thread
    monitor_thread = threading.Thread(target=run_monitor, daemon=True)
    monitor_thread.start()
    
    # Print startup info
    print("""
🤖 KIRSTON'S CRYPTO BOT - ML ENHANCED
===============================

✅ Monitoring: BTC, SOL, ETH, XRP
✅ Timeframes: 1m, 5m, 15m, 1h, 4h (comprehensive signal detection)
✅ ML Integration: Gradient boosting model for 15min predictions
✅ Risk Management: $100 per trade | RR 1:3
✅ Market Hours: 7am-11pm GMT (Optimized global sessions)
✅ Enhanced Sensitivity: 60% confidence threshold
✅ Scans every 3 minutes during active hours
✅ Web dashboard with trading journal

Features:
📊 ML-enhanced signal detection (30% weight)
📝 Automated trading journal with confluences
🤖 Real-time price predictions
⏰ Smart market hours monitoring
🎯 60%+ confidence signals (improved from 75%)
📈 Increased sensitivity for better opportunity detection

Open your browser to: http://localhost:5001
""")
    
    # Start Flask-SocketIO server
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)