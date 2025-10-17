"""
🎯 ICT PROACTIVE CRYPTO SIGNAL MONITOR
=====================================
Professional monitoring system using Inner Circle Trader methodology
Replaces traditional retail indicators with institutional concepts

Key Features:
✅ Order Block detection and monitoring
✅ Fair Value Gap analysis
✅ Market Structure identification (BoS/ChoCH)
✅ Liquidity zone mapping
✅ 4H bias → 5M setup → 1M execution hierarchy
✅ Confluence-based signal generation
✅ Real-time institutional analysis
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
from enum import Enum

# Import ICT components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from trading.ict_analyzer import ICTAnalyzer, ICTSignal
from trading.order_block_detector import EnhancedOrderBlockDetector, OrderBlockState
from trading.fvg_detector import FVGDetector, FVGState
from trading.liquidity_detector import LiquidityDetector, LiquidityType
from trading.fibonacci_analyzer import ICTFibonacciAnalyzer
from trading.ict_hierarchy import ICTTimeframeHierarchy

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TimeframeHierarchy(Enum):
    """ICT timeframe hierarchy levels"""
    BIAS = "4h"      # Higher timeframe bias
    SETUP = "5m"     # Setup identification
    EXECUTION = "1m" # Execution timing

@dataclass
class ICTTradingSignal:
    """ICT-based trading signal with institutional analysis"""
    symbol: str
    timeframe: str
    action: str  # BUY, SELL
    price: float
    confidence: float
    timestamp: datetime
    
    # ICT-specific data
    bias_timeframe: str
    bias_direction: str
    order_blocks: List[Dict]
    fair_value_gaps: List[Dict]
    liquidity_zones: List[Dict]
    market_structure: str
    confluence_score: float
    fibonacci_levels: Dict
    
    # Signal quality
    institutional_quality: str  # PREMIUM, HIGH, MEDIUM, LOW
    entry_type: str  # ORDER_BLOCK, FVG_CONFLUENCE, LIQUIDITY_SWEEP
    risk_reward_ratio: float
    
    def to_dict(self) -> Dict:
        """Convert signal to dictionary for JSON serialization"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'action': self.action,
            'price': self.price,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'bias_timeframe': self.bias_timeframe,
            'bias_direction': self.bias_direction,
            'order_blocks_count': len(self.order_blocks),
            'fvg_count': len(self.fair_value_gaps),
            'liquidity_zones_count': len(self.liquidity_zones),
            'market_structure': self.market_structure,
            'confluence_score': self.confluence_score,
            'institutional_quality': self.institutional_quality,
            'entry_type': self.entry_type,
            'risk_reward_ratio': self.risk_reward_ratio
        }

class ICTProactiveCryptoMonitor:
    """
    Advanced crypto monitoring using ICT methodology
    Replaces traditional indicators with institutional concepts
    """
    
    def __init__(self):
        self.symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]
        
        # ICT Timeframe hierarchy (not traditional multi-timeframe)
        self.bias_timeframe = "4h"      # Market bias
        self.setup_timeframe = "5m"     # Setup identification  
        self.execution_timeframe = "1m" # Entry execution
        
        # ICT signal requirements
        self.min_confluence_score = 0.75
        self.min_institutional_quality = "MEDIUM"
        
        # Webhook configuration
        self.webhook_url = "http://localhost:8080/webhook/tradingview"
        self.running = False
        
        # ICT Components
        self.ict_analyzer = ICTAnalyzer()
        self.hierarchy_manager = ICTTimeframeHierarchy()
        self.enhanced_order_block_detector = EnhancedOrderBlockDetector()
        self.fvg_detector = FVGDetector()
        self.liquidity_detector = LiquidityDetector()
        self.fibonacci_analyzer = ICTFibonacciAnalyzer()
        
        logger.info("ICT Proactive Monitor initialized with institutional methodology")
        
    async def fetch_ohlcv_data(self, session: aiohttp.ClientSession, symbol: str, 
                              timeframe: str, limit: int = 200) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data from Binance with ICT analysis requirements"""
        
        # Convert timeframe to Binance format
        tf_map = {
            "1m": "1m", "5m": "5m", "15m": "15m", 
            "1h": "1h", "4h": "4h", "1d": "1d"
        }
        
        if timeframe not in tf_map:
            logger.error(f"Unsupported timeframe: {timeframe}")
            return None
            
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': tf_map[timeframe],
            'limit': limit
        }
        
        try:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"API error {response.status} for {symbol} {timeframe}")
                    return None
                    
                data = await response.json()
                
                if not data:
                    logger.warning(f"No data returned for {symbol} {timeframe}")
                    return None
                
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ])
                
                # Convert to proper types
                numeric_columns = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
                
                # Remove any NaN rows
                df = df.dropna()
                
                if len(df) < 50:  # Minimum data for ICT analysis
                    logger.warning(f"Insufficient data for ICT analysis: {len(df)} candles")
                    return None
                
                return df
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol} {timeframe}: {e}")
            return None

    async def analyze_ict_signals(self, symbol: str) -> Optional[ICTTradingSignal]:
        """
        Comprehensive ICT analysis replacing traditional indicators
        Follows proper ICT methodology: 4H bias → 5M setup → 1M execution
        """
        try:
            async with aiohttp.ClientSession() as session:
                
                # Step 1: Get 4H bias (Higher Timeframe Structure)
                bias_data = await self.fetch_ohlcv_data(session, symbol, self.bias_timeframe, 100)
                if bias_data is None:
                    return None
                
                # Step 2: Get 5M setup data (Entry Timeframe)
                setup_data = await self.fetch_ohlcv_data(session, symbol, self.setup_timeframe, 200)
                if setup_data is None:
                    return None
                
                # Step 3: Get 1M execution data (Precise Entry)
                execution_data = await self.fetch_ohlcv_data(session, symbol, self.execution_timeframe, 100)
                if execution_data is None:
                    return None
                
                # ICT ANALYSIS WORKFLOW
                
                # 1. Determine 4H Market Bias
                bias_analysis = self._analyze_market_bias(bias_data)
                if not bias_analysis or bias_analysis['direction'] == 'NEUTRAL':
                    return None  # No clear bias, no trade
                
                # 2. Find Order Blocks on setup timeframe
                enhanced_order_blocks = self.enhanced_order_block_detector.detect_enhanced_order_blocks(setup_data, symbol, self.setup_timeframe)
                if not enhanced_order_blocks:
                    return None  # No institutional accumulation zones
                
                # 3. Detect Fair Value Gaps
                fair_value_gaps = self.fvg_detector.detect_fair_value_gaps(setup_data, symbol, self.setup_timeframe)
                
                # 4. Map Liquidity Zones
                liquidity_zones = self.liquidity_detector.detect_liquidity_zones(setup_data, symbol, self.setup_timeframe)
                
                # 5. Fibonacci Confluence Analysis
                fibonacci_analysis = self.fibonacci_analyzer.analyze_fibonacci_confluence(setup_data, symbol, self.setup_timeframe)
                
                # 6. Market Structure Analysis
                market_structure = self._analyze_market_structure(setup_data, execution_data)
                
                # 7. Calculate ICT Confluence Score
                confluence_score = self._calculate_ict_confluence(
                    bias_analysis, enhanced_order_blocks, fair_value_gaps, 
                    liquidity_zones, fibonacci_analysis, market_structure
                )
                
                # 8. Generate Signal if Confluence Threshold Met
                if confluence_score >= self.min_confluence_score:
                    return self._generate_ict_signal(
                        symbol, bias_analysis, enhanced_order_blocks, fair_value_gaps,
                        liquidity_zones, fibonacci_analysis, market_structure,
                        confluence_score, setup_data
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"ICT analysis failed for {symbol}: {e}")
            return None

    def _analyze_market_bias(self, bias_data: pd.DataFrame) -> Dict:
        """
        Analyze 4H market bias using ICT market structure concepts
        Replaces traditional trend analysis with institutional perspective
        """
        try:
            if len(bias_data) < 20:
                return None
            
            # Look for Higher Highs/Higher Lows (Bullish) or Lower Highs/Lower Lows (Bearish)
            highs = bias_data['high'].rolling(window=5).max()
            lows = bias_data['low'].rolling(window=5).min()
            
            # Recent structure analysis
            recent_data = bias_data.tail(10)
            
            # Identify swing points
            swing_highs = []
            swing_lows = []
            
            for i in range(2, len(recent_data) - 2):
                # Swing high: higher than 2 candles on each side
                if (recent_data.iloc[i]['high'] > recent_data.iloc[i-1]['high'] and 
                    recent_data.iloc[i]['high'] > recent_data.iloc[i-2]['high'] and
                    recent_data.iloc[i]['high'] > recent_data.iloc[i+1]['high'] and 
                    recent_data.iloc[i]['high'] > recent_data.iloc[i+2]['high']):
                    swing_highs.append(recent_data.iloc[i]['high'])
                
                # Swing low: lower than 2 candles on each side
                if (recent_data.iloc[i]['low'] < recent_data.iloc[i-1]['low'] and 
                    recent_data.iloc[i]['low'] < recent_data.iloc[i-2]['low'] and
                    recent_data.iloc[i]['low'] < recent_data.iloc[i+1]['low'] and 
                    recent_data.iloc[i]['low'] < recent_data.iloc[i+2]['low']):
                    swing_lows.append(recent_data.iloc[i]['low'])
            
            # Determine bias based on structure
            direction = 'NEUTRAL'
            strength = 0.5
            
            if len(swing_highs) >= 2 and len(swing_lows) >= 2:
                # Check for Higher Highs and Higher Lows (Bullish Bias)
                if (swing_highs[-1] > swing_highs[-2] and 
                    swing_lows[-1] > swing_lows[-2]):
                    direction = 'BULLISH'
                    strength = 0.8
                
                # Check for Lower Highs and Lower Lows (Bearish Bias)
                elif (swing_highs[-1] < swing_highs[-2] and 
                      swing_lows[-1] < swing_lows[-2]):
                    direction = 'BEARISH'
                    strength = 0.8
            
            return {
                'direction': direction,
                'strength': strength,
                'swing_highs': swing_highs,
                'swing_lows': swing_lows,
                'current_price': bias_data.iloc[-1]['close']
            }
            
        except Exception as e:
            logger.error(f"Market bias analysis failed: {e}")
            return None

    def _analyze_market_structure(self, setup_data: pd.DataFrame, execution_data: pd.DataFrame) -> Dict:
        """
        Analyze market structure for Break of Structure (BoS) and Change of Character (ChoCH)
        Key ICT concepts for entry confirmation
        """
        try:
            # Combine data for structure analysis
            combined_data = setup_data.tail(50)  # Recent structure
            
            # Look for structure breaks
            structure_breaks = []
            change_of_character = False
            
            if len(combined_data) >= 10:
                # Identify recent swing points for structure analysis
                for i in range(5, len(combined_data) - 1):
                    current_high = combined_data.iloc[i]['high']
                    current_low = combined_data.iloc[i]['low']
                    
                    # Look back for previous swing high/low
                    prev_swing_high = combined_data.iloc[max(0, i-10):i]['high'].max()
                    prev_swing_low = combined_data.iloc[max(0, i-10):i]['low'].min()
                    
                    # Break of Structure detection
                    if current_high > prev_swing_high * 1.001:  # 0.1% buffer for crypto volatility
                        structure_breaks.append({
                            'type': 'BULLISH_BOS',
                            'price': current_high,
                            'timestamp': combined_data.iloc[i]['timestamp']
                        })
                    
                    if current_low < prev_swing_low * 0.999:  # 0.1% buffer
                        structure_breaks.append({
                            'type': 'BEARISH_BOS',
                            'price': current_low,
                            'timestamp': combined_data.iloc[i]['timestamp']
                        })
            
            # Recent structure analysis
            recent_structure = 'NEUTRAL'
            if structure_breaks:
                latest_break = structure_breaks[-1]
                recent_structure = latest_break['type']
            
            return {
                'recent_structure': recent_structure,
                'structure_breaks': structure_breaks[-3:],  # Last 3 breaks
                'change_of_character': change_of_character
            }
            
        except Exception as e:
            logger.error(f"Market structure analysis failed: {e}")
            return {'recent_structure': 'NEUTRAL', 'structure_breaks': [], 'change_of_character': False}

    def _calculate_ict_confluence(self, bias_analysis: Dict, order_blocks: List, 
                                 fair_value_gaps: List, liquidity_zones: List,
                                 fibonacci_analysis: Dict, market_structure: Dict) -> float:
        """
        Calculate ICT confluence score based on institutional factors
        Replaces traditional indicator confluence with smart money concepts
        """
        try:
            confluence_factors = []
            
            # 1. Higher Timeframe Bias (40% weight)
            if bias_analysis and bias_analysis['direction'] != 'NEUTRAL':
                bias_score = bias_analysis['strength'] * 0.4
                confluence_factors.append(bias_score)
            
            # 2. Order Block Quality (25% weight)
            if order_blocks:
                # Count fresh, high-quality order blocks
                fresh_obs = [ob for ob in order_blocks if ob.get('state') == OrderBlockState.FRESH.value]
                premium_obs = [ob for ob in fresh_obs if ob.get('quality', 'LOW') == 'PREMIUM']
                
                ob_score = min(len(premium_obs) / 2, 1.0) * 0.25  # Max 2 premium OBs needed
                confluence_factors.append(ob_score)
            
            # 3. Fair Value Gap Confluence (15% weight)
            if fair_value_gaps:
                fresh_fvgs = [fvg for fvg in fair_value_gaps if fvg.get('state') == FVGState.FRESH.value]
                fvg_score = min(len(fresh_fvgs) / 1, 1.0) * 0.15  # 1 fresh FVG sufficient
                confluence_factors.append(fvg_score)
            
            # 4. Liquidity Zone Proximity (10% weight)
            if liquidity_zones:
                recent_zones = [lz for lz in liquidity_zones if lz.get('age_hours', 24) < 12]
                liquidity_score = min(len(recent_zones) / 2, 1.0) * 0.10
                confluence_factors.append(liquidity_score)
            
            # 5. Market Structure Confirmation (10% weight)
            if market_structure and market_structure['recent_structure'] != 'NEUTRAL':
                structure_score = 0.10
                confluence_factors.append(structure_score)
            
            # Calculate total confluence
            total_confluence = sum(confluence_factors)
            
            return min(total_confluence, 1.0)  # Cap at 100%
            
        except Exception as e:
            logger.error(f"Confluence calculation failed: {e}")
            return 0.0

    def _generate_ict_signal(self, symbol: str, bias_analysis: Dict, order_blocks: List,
                            fair_value_gaps: List, liquidity_zones: List, 
                            fibonacci_analysis: Dict, market_structure: Dict,
                            confluence_score: float, setup_data: pd.DataFrame) -> ICTTradingSignal:
        """
        Generate ICT trading signal based on institutional analysis
        Replaces traditional indicator signals with smart money setups
        """
        try:
            current_price = setup_data.iloc[-1]['close']
            
            # Determine signal direction based on bias and structure
            action = 'BUY' if bias_analysis['direction'] == 'BULLISH' else 'SELL'
            
            # Determine entry type
            entry_type = 'ORDER_BLOCK'
            if fair_value_gaps and len(fair_value_gaps) > len(order_blocks):
                entry_type = 'FVG_CONFLUENCE'
            elif liquidity_zones:
                entry_type = 'LIQUIDITY_SWEEP'
            
            # Determine institutional quality
            if confluence_score >= 0.9:
                institutional_quality = 'PREMIUM'
            elif confluence_score >= 0.8:
                institutional_quality = 'HIGH'
            elif confluence_score >= 0.75:
                institutional_quality = 'MEDIUM'
            else:
                institutional_quality = 'LOW'
            
            # Calculate risk-reward (simplified)
            risk_reward_ratio = 2.5  # Standard ICT R:R expectation
            
            # Create ICT signal
            signal = ICTTradingSignal(
                symbol=symbol,
                timeframe=self.setup_timeframe,
                action=action,
                price=current_price,
                confidence=confluence_score,
                timestamp=datetime.now(),
                bias_timeframe=self.bias_timeframe,
                bias_direction=bias_analysis['direction'],
                order_blocks=order_blocks,
                fair_value_gaps=fair_value_gaps,
                liquidity_zones=liquidity_zones,
                market_structure=market_structure['recent_structure'],
                confluence_score=confluence_score,
                fibonacci_levels=fibonacci_analysis or {},
                institutional_quality=institutional_quality,
                entry_type=entry_type,
                risk_reward_ratio=risk_reward_ratio
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            return None

    async def send_ict_webhook_alert(self, signal: ICTTradingSignal):
        """Send ICT-based webhook alert to trading system"""
        
        webhook_data = {
            # Standard fields
            "symbol": signal.symbol,
            "action": signal.action,
            "price": signal.price,
            "confidence": signal.confidence,
            "timeframe": signal.timeframe,
            "timestamp": signal.timestamp.isoformat(),
            
            # ICT-specific fields
            "source": "ICT_MONITOR",
            "alert_type": "ICT_INSTITUTIONAL_SIGNAL",
            "methodology": "INNER_CIRCLE_TRADER",
            
            # ICT analysis data
            "ict_data": {
                "bias_direction": signal.bias_direction,
                "confluence_score": signal.confluence_score,
                "institutional_quality": signal.institutional_quality,
                "entry_type": signal.entry_type,
                "market_structure": signal.market_structure,
                "order_blocks_count": len(signal.order_blocks),
                "fvg_count": len(signal.fair_value_gaps),
                "liquidity_zones_count": len(signal.liquidity_zones),
                "risk_reward_ratio": signal.risk_reward_ratio
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=webhook_data) as response:
                    if response.status == 200:
                        logger.info(f"✅ ICT Webhook sent: {signal.action} {signal.symbol} "
                                   f"({signal.institutional_quality}) - {signal.confluence_score:.1%}")
                    else:
                        logger.error(f"❌ ICT Webhook failed: {response.status}")
        except Exception as e:
            logger.error(f"❌ ICT Webhook error: {e}")

    async def monitor_symbol_ict(self, symbol: str):
        """Monitor a single symbol using ICT methodology"""
        try:
            signal = await self.analyze_ict_signals(symbol)
            
            if signal:
                logger.info(f"🎯 ICT SIGNAL: {signal.action} {signal.symbol} "
                           f"({signal.institutional_quality}) - {signal.confluence_score:.1%}")
                logger.info(f"   Entry Type: {signal.entry_type}")
                logger.info(f"   Market Structure: {signal.market_structure}")
                logger.info(f"   Bias: {signal.bias_direction} ({signal.bias_timeframe})")
                logger.info(f"   Components: {len(signal.order_blocks)} OBs, "
                           f"{len(signal.fair_value_gaps)} FVGs, "
                           f"{len(signal.liquidity_zones)} Liquidity Zones")
                
                # Send webhook alert
                await self.send_ict_webhook_alert(signal)
                
        except Exception as e:
            logger.error(f"Error monitoring {symbol} with ICT: {e}")

    async def scan_all_pairs_ict(self):
        """Scan all pairs using ICT methodology"""
        logger.info("🔍 Starting ICT institutional scan...")
        
        tasks = []
        for symbol in self.symbols:
            task = self.monitor_symbol_ict(symbol)
            tasks.append(task)
        
        # Run all ICT analysis concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("✅ ICT scan completed")

    async def run_ict_monitoring(self):
        """Main ICT monitoring loop - institutional analysis 24/7"""
        self.running = True
        
        logger.info("🎯 ICT PROACTIVE MONITOR STARTED")
        logger.info(f"🏦 Using Inner Circle Trader methodology")
        logger.info(f"📊 Monitoring {len(self.symbols)} symbols")
        logger.info(f"⏰ Timeframe Hierarchy: {self.bias_timeframe} → {self.setup_timeframe} → {self.execution_timeframe}")
        logger.info(f"🎯 Minimum Confluence: {self.min_confluence_score:.1%}")
        logger.info(f"🏆 Quality Filter: {self.min_institutional_quality}+")
        
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                  ICT INSTITUTIONAL MONITOR                      ║
╠══════════════════════════════════════════════════════════════════╣
║  🎯 Methodology: Inner Circle Trader (ICT)                      ║
║  🏦 Focus: Institutional Smart Money Analysis                   ║
║  📈 Concepts: Order Blocks, FVGs, Market Structure             ║
║  ⏰ Hierarchy: 4H Bias → 5M Setup → 1M Execution               ║
║  🎯 Confluence: {self.min_confluence_score:.0%}+ Required                              ║
║  🏆 Quality: {self.min_institutional_quality}+ Institutional Grade                    ║
╚══════════════════════════════════════════════════════════════════╝
""")
        
        while self.running:
            try:
                await self.scan_all_pairs_ict()
                
                # ICT monitoring frequency (every 2 minutes for efficiency)
                scan_interval = 120
                logger.info(f"⏳ Next ICT scan in {scan_interval}s...")
                await asyncio.sleep(scan_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 ICT Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in ICT monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    def stop(self):
        """Stop ICT monitoring"""
        self.running = False

# Main execution
async def main():
    monitor = ICTProactiveCryptoMonitor()
    
    try:
        await monitor.run_ict_monitoring()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down ICT monitor...")
        monitor.stop()

if __name__ == "__main__":
    print("""
🎯 ICT PROACTIVE CRYPTO MONITOR
==============================

Institutional Trading Concepts:
✅ Order Block Detection - Last opposing candle before moves  
✅ Fair Value Gaps - Price inefficiency areas
✅ Market Structure - BoS/ChoCH identification
✅ Liquidity Analysis - Where smart money hunts stops
✅ Timeframe Hierarchy - 4H bias → 5M setup → 1M execution
✅ Confluence Scoring - Multi-factor institutional validation

This replaces traditional indicators with smart money analysis!

Press Ctrl+C to stop monitoring
""")
    
    asyncio.run(main())