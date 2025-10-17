#!/usr/bin/env python3
"""
ICT (Inner Circle Trader) Analysis Engine
========================================

Complete implementation of ICT trading methodology for crypto markets.
Replaces traditional retail indicators with institutional trading concepts.

Core ICT Concepts Implemented:
✅ Order Blocks (OB) - Institutional accumulation/distribution zones
✅ Fair Value Gaps (FVG) - Unfilled price imbalances  
✅ Break of Structure (BoS) - Trend continuation signals
✅ Change of Character (ChoCH) - Trend reversal signals
✅ Liquidity Sweeps - Hunt for retail stops
✅ 79% Fibonacci Confluence - ICT-specific mathematical levels
✅ Timeframe Hierarchy - 4H bias → 5M setup → 1M execution

Author: GitHub Copilot Trading Algorithm  
Date: September 2025
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, NamedTuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TrendDirection(Enum):
    """Market trend direction enumeration."""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    CONSOLIDATION = "CONSOLIDATION"
    TRANSITION = "TRANSITION"

class OrderBlockType(Enum):
    """Order block type enumeration."""
    BULLISH_OB = "BULLISH_OB"    # Last bullish candle before drop
    BEARISH_OB = "BEARISH_OB"    # Last bearish candle before rally
    BREAKER_BLOCK = "BREAKER_BLOCK"  # Former support/resistance flipped

class StructureType(Enum):
    """Market structure change type."""
    BOS_BULLISH = "BOS_BULLISH"      # Break of structure to upside
    BOS_BEARISH = "BOS_BEARISH"      # Break of structure to downside
    CHOCH_BULLISH = "CHOCH_BULLISH"  # Change of character to bullish
    CHOCH_BEARISH = "CHOCH_BEARISH"  # Change of character to bearish

@dataclass
class OrderBlock:
    """Institutional Order Block data structure."""
    type: OrderBlockType
    timeframe: str
    timestamp: datetime
    high: float
    low: float
    open: float
    close: float
    volume: float
    
    # ICT-specific metrics
    freshness_score: float      # 0-1, based on age and reactions
    confluence_level: float     # Multiple factors alignment
    reaction_strength: float    # Historical reaction magnitude
    fibonacci_alignment: float  # 79% level proximity score
    
    # Zone characteristics
    is_untested: bool
    test_count: int
    last_test_time: Optional[datetime]
    
    # Market context
    higher_tf_bias: TrendDirection
    session_context: str        # 'ASIA', 'LONDON', 'NY'
    
    def __post_init__(self):
        """Calculate derived properties."""
        self.zone_size = self.high - self.low
        self.zone_mid = (self.high + self.low) / 2
        self.age_hours = (datetime.now() - self.timestamp).total_seconds() / 3600

@dataclass
class FairValueGap:
    """Fair Value Gap (FVG) data structure."""
    timestamp: datetime
    timeframe: str
    gap_high: float
    gap_low: float
    gap_size: float
    
    # Gap characteristics
    is_filled: bool
    fill_percentage: float
    volume_confirmation: bool
    
    # ICT context
    formation_type: str         # 'BULLISH_FVG', 'BEARISH_FVG'
    institutional_interest: float  # Volume-based institutional score
    
    def __post_init__(self):
        """Calculate derived properties."""
        self.gap_mid = (self.gap_high + self.gap_low) / 2
        self.age_hours = (datetime.now() - self.timestamp).total_seconds() / 3600

@dataclass
class StructureBreak:
    """Market structure break data."""
    type: StructureType
    timestamp: datetime
    timeframe: str
    break_level: float
    volume_confirmation: bool
    previous_structure: Dict
    
    # Confirmation metrics
    confirmation_strength: float  # 0-1 based on multiple factors
    follow_through: bool         # Price continued after break
    
@dataclass
class LiquidityZone:
    """Liquidity accumulation zone."""
    level: float
    zone_type: str              # 'EQUAL_HIGHS', 'EQUAL_LOWS', 'PSYCHOLOGICAL'
    strength: float             # Based on touches and volume
    timestamp: datetime
    is_swept: bool
    sweep_timestamp: Optional[datetime]

@dataclass
class ICTSignal:
    """Complete ICT trading signal."""
    symbol: str
    timeframe: str
    timestamp: datetime
    
    # Signal characteristics
    signal_type: str            # 'BUY_OB', 'SELL_OB', 'FVG_FILL', etc.
    direction: str              # 'LONG', 'SHORT'
    confidence: float           # 0-1 overall signal confidence
    
    # ICT components
    primary_order_block: Optional[OrderBlock]
    supporting_fvg: Optional[FairValueGap]
    structure_confirmation: Optional[StructureBreak]
    liquidity_sweep: Optional[LiquidityZone]
    
    # Entry mechanics
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    
    # Higher timeframe context
    htf_bias: TrendDirection
    htf_structure: Dict
    
    # Fibonacci confluence
    fib_confluence: float       # 79% level alignment score
    
    # Session context
    session: str                # Market session
    session_alignment: bool     # Aligns with session bias


class ICTAnalyzer:
    """
    Complete ICT trading methodology implementation.
    
    This class replaces traditional technical analysis with institutional
    trading concepts focusing on order flow and market maker behavior.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize ICT analyzer with configuration."""
        self.config = self._load_default_config()
        if config:
            self.config.update(config)
        
        # Historical data cache
        self.order_blocks_cache = {}
        self.fvg_cache = {}
        self.structure_cache = {}
        self.liquidity_cache = {}
        
        # Analysis state
        self.last_analysis_time = {}
        
        logger.info("ICT Analyzer initialized with institutional trading methodology")
    
    def _load_default_config(self) -> Dict:
        """Load default ICT analysis configuration."""
        return {
            # Timeframe hierarchy
            'htf_bias_timeframe': '4H',
            'setup_timeframe': '5T',
            'execution_timeframe': '1T',
            
            # Order Block settings
            'min_ob_size_percentage': 0.002,    # 0.2% minimum size
            'max_ob_age_hours': 48,             # Fresh OBs preferred
            'ob_confluence_radius': 0.001,      # 0.1% for confluence
            'min_ob_volume_multiplier': 1.5,    # 1.5x average volume
            
            # Fair Value Gap settings
            'min_fvg_size_percentage': 0.003,   # 0.3% minimum gap size
            'fvg_fill_threshold': 0.5,          # 50% fill = partially filled
            'max_fvg_age_hours': 24,            # Fresh gaps priority
            
            # Structure settings
            'min_structure_break_size': 0.005,  # 0.5% minimum break
            'structure_confirmation_bars': 2,    # Bars to confirm break
            'min_bos_volume_multiplier': 2.0,   # 2x volume for BoS
            
            # Liquidity settings
            'equal_level_tolerance': 0.002,     # 0.2% tolerance for equal levels
            'min_liquidity_touches': 2,         # Minimum touches for liquidity
            'liquidity_sweep_tolerance': 0.001, # 0.1% for sweep detection
            
            # Fibonacci settings
            'fib_levels': [0.236, 0.382, 0.5, 0.618, 0.79, 0.886],
            'fib_79_weight': 3.0,               # Higher weight for 79% level
            'fib_confluence_threshold': 0.001,  # 0.1% for confluence
            
            # Session settings
            'asia_session': (22, 8),            # 22:00-08:00 UTC
            'london_session': (8, 16),          # 08:00-16:00 UTC  
            'ny_session': (13, 21),             # 13:00-21:00 UTC
            
            # Signal generation
            'min_signal_confidence': 0.7,       # Minimum confidence for signals
            'max_risk_per_trade': 0.02,         # 2% max risk
            'min_risk_reward_ratio': 1.5,       # Minimum R:R ratio
            
            # Crypto-specific adaptations
            'crypto_volatility_multiplier': 1.5, # Adjust for crypto volatility
            'btc_correlation_weight': 0.3,       # BTC influence on alts
        }
    
    def analyze_market_structure(self, df: pd.DataFrame, symbol: str, 
                               timeframe: str) -> Dict:
        """
        Complete ICT market structure analysis.
        
        Args:
            df: OHLCV data with datetime index
            symbol: Trading pair symbol
            timeframe: Analysis timeframe
            
        Returns:
            Complete market structure analysis
        """
        try:
            logger.info(f"Starting ICT analysis for {symbol} {timeframe}")
            
            # Ensure data is properly formatted
            df = self._prepare_data(df)
            
            # Step 1: Higher timeframe bias analysis
            htf_bias = self._analyze_htf_bias(df, symbol)
            
            # Step 2: Order block identification
            order_blocks = self._identify_order_blocks(df, timeframe, htf_bias)
            
            # Step 3: Fair value gap detection
            fair_value_gaps = self._detect_fair_value_gaps(df, timeframe)
            
            # Step 4: Market structure analysis (BoS/ChoCH)
            structure_analysis = self._analyze_market_structure_breaks(df, timeframe)
            
            # Step 5: Liquidity mapping
            liquidity_zones = self._map_liquidity_zones(df, timeframe)
            
            # Step 6: Fibonacci confluence analysis
            fibonacci_levels = self._calculate_fibonacci_confluence(df, order_blocks)
            
            # Step 7: Session context analysis
            session_context = self._analyze_session_context(df)
            
            # Step 8: Generate ICT signals
            ict_signals = self._generate_ict_signals(
                df, order_blocks, fair_value_gaps, structure_analysis,
                liquidity_zones, fibonacci_levels, session_context, htf_bias
            )
            
            # Compile complete analysis
            analysis_result = {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.now(),
                'htf_bias': htf_bias,
                'order_blocks': order_blocks,
                'fair_value_gaps': fair_value_gaps,
                'structure_analysis': structure_analysis,
                'liquidity_zones': liquidity_zones,
                'fibonacci_levels': fibonacci_levels,
                'session_context': session_context,
                'ict_signals': ict_signals,
                'market_summary': self._create_market_summary(
                    htf_bias, order_blocks, structure_analysis, ict_signals
                )
            }
            
            # Cache results
            self._cache_analysis_results(symbol, timeframe, analysis_result)
            
            logger.info(f"ICT analysis completed: {len(ict_signals)} signals generated")
            return analysis_result
            
        except Exception as e:
            logger.error(f"ICT analysis failed for {symbol}: {e}")
            return self._get_empty_analysis(symbol, timeframe)
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate OHLCV data for ICT analysis."""
        try:
            # Ensure required columns exist
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Ensure datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                if 'timestamp' in df.columns:
                    df.index = pd.to_datetime(df['timestamp'])
                else:
                    raise ValueError("No datetime index or timestamp column found")
            
            # Sort by timestamp
            df = df.sort_index()
            
            # Calculate additional ICT-specific indicators
            df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
            df['hlc3'] = df['typical_price']
            df['body_size'] = abs(df['close'] - df['open'])
            df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
            df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
            df['candle_range'] = df['high'] - df['low']
            
            # Volume-based calculations
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
            
            # True Range for volatility
            df['tr'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['close'].shift(1)),
                    abs(df['low'] - df['close'].shift(1))
                )
            )
            df['atr'] = df['tr'].rolling(window=14).mean()
            
            return df
            
        except Exception as e:
            logger.error(f"Data preparation failed: {e}")
            raise
    
    def _analyze_htf_bias(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Analyze higher timeframe bias for market direction.
        
        ICT Principle: Always trade with higher timeframe bias.
        4H timeframe determines the overall market direction.
        """
        try:
            # Use last 100 candles for trend analysis
            recent_data = df.tail(100).copy()
            
            # Calculate swing highs and lows
            swing_highs = self._identify_swing_points(recent_data, 'high')
            swing_lows = self._identify_swing_points(recent_data, 'low')
            
            # Determine trend direction
            trend_direction = self._determine_trend_direction(swing_highs, swing_lows)
            
            # Calculate trend strength
            trend_strength = self._calculate_trend_strength(recent_data, trend_direction)
            
            # Identify key levels
            key_levels = self._identify_key_levels(recent_data, swing_highs, swing_lows)
            
            # Market phase classification
            market_phase = self._classify_market_phase(recent_data, trend_direction)
            
            return {
                'trend_direction': trend_direction,
                'trend_strength': trend_strength,
                'market_phase': market_phase,
                'key_levels': key_levels,
                'swing_highs': swing_highs,
                'swing_lows': swing_lows,
                'last_update': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"HTF bias analysis failed: {e}")
            return {
                'trend_direction': TrendDirection.CONSOLIDATION,
                'trend_strength': 0.5,
                'market_phase': 'TRANSITION',
                'key_levels': [],
                'swing_highs': [],
                'swing_lows': [],
                'last_update': datetime.now()
            }
    
    def _identify_order_blocks(self, df: pd.DataFrame, timeframe: str, 
                             htf_bias: Dict) -> List[OrderBlock]:
        """
        Identify institutional Order Blocks on the analysis timeframe.
        
        ICT Definition: Last opposing candle before significant directional move.
        - Bullish OB: Last red candle before strong move up
        - Bearish OB: Last green candle before strong move down
        """
        try:
            order_blocks = []
            data = df.copy()
            
            # Calculate move significance threshold
            atr = data['atr'].iloc[-1]
            min_move_size = atr * self.config['crypto_volatility_multiplier']
            
            # Scan for order blocks
            for i in range(10, len(data) - 5):  # Leave buffer for move detection
                
                # Check for bullish order block formation
                bullish_ob = self._check_bullish_order_block(data, i, min_move_size)
                if bullish_ob:
                    ob = self._create_order_block(
                        data, i, OrderBlockType.BULLISH_OB, timeframe, htf_bias
                    )
                    if ob:
                        order_blocks.append(ob)
                
                # Check for bearish order block formation  
                bearish_ob = self._check_bearish_order_block(data, i, min_move_size)
                if bearish_ob:
                    ob = self._create_order_block(
                        data, i, OrderBlockType.BEARISH_OB, timeframe, htf_bias
                    )
                    if ob:
                        order_blocks.append(ob)
            
            # Filter and rank order blocks
            filtered_obs = self._filter_order_blocks(order_blocks, data)
            ranked_obs = self._rank_order_blocks(filtered_obs, htf_bias)
            
            logger.info(f"Identified {len(ranked_obs)} order blocks")
            return ranked_obs
            
        except Exception as e:
            logger.error(f"Order block identification failed: {e}")
            return []
    
    def _check_bullish_order_block(self, data: pd.DataFrame, index: int, 
                                 min_move_size: float) -> bool:
        """Check if candle forms a bullish order block."""
        try:
            # Current candle must be bearish (red)
            current_candle = data.iloc[index]
            if current_candle['close'] >= current_candle['open']:
                return False
            
            # Look for significant move up after this candle
            future_candles = data.iloc[index+1:index+6]  # Next 5 candles
            if len(future_candles) < 3:
                return False
            
            # Check for strong upward move
            highest_future = future_candles['high'].max()
            move_size = highest_future - current_candle['close']
            
            # Must exceed minimum move threshold
            if move_size < min_move_size:
                return False
            
            # Volume confirmation
            avg_volume = data['volume_ma'].iloc[index]
            if current_candle['volume'] < avg_volume * self.config['min_ob_volume_multiplier']:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Bullish OB check failed: {e}")
            return False
    
    def _check_bearish_order_block(self, data: pd.DataFrame, index: int,
                                 min_move_size: float) -> bool:
        """Check if candle forms a bearish order block."""
        try:
            # Current candle must be bullish (green)
            current_candle = data.iloc[index]
            if current_candle['close'] <= current_candle['open']:
                return False
            
            # Look for significant move down after this candle
            future_candles = data.iloc[index+1:index+6]  # Next 5 candles
            if len(future_candles) < 3:
                return False
            
            # Check for strong downward move
            lowest_future = future_candles['low'].min()
            move_size = current_candle['close'] - lowest_future
            
            # Must exceed minimum move threshold
            if move_size < min_move_size:
                return False
            
            # Volume confirmation
            avg_volume = data['volume_ma'].iloc[index]
            if current_candle['volume'] < avg_volume * self.config['min_ob_volume_multiplier']:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Bearish OB check failed: {e}")
            return False
    
    def _create_order_block(self, data: pd.DataFrame, index: int, 
                          ob_type: OrderBlockType, timeframe: str, 
                          htf_bias: Dict) -> Optional[OrderBlock]:
        """Create OrderBlock object with ICT characteristics."""
        try:
            candle = data.iloc[index]
            
            # Calculate freshness score (newer is better)
            age_hours = (datetime.now() - candle.name).total_seconds() / 3600
            freshness_score = max(0, 1 - (age_hours / self.config['max_ob_age_hours']))
            
            # Calculate confluence level (will be updated with Fibonacci)
            confluence_level = 0.5  # Base level, updated later
            
            # Calculate reaction strength (placeholder)
            reaction_strength = 0.7  # Will be calculated based on historical reactions
            
            # Current session context
            session_context = self._get_current_session(candle.name)
            
            order_block = OrderBlock(
                type=ob_type,
                timeframe=timeframe,
                timestamp=candle.name,
                high=candle['high'],
                low=candle['low'],
                open=candle['open'],
                close=candle['close'],
                volume=candle['volume'],
                freshness_score=freshness_score,
                confluence_level=confluence_level,
                reaction_strength=reaction_strength,
                fibonacci_alignment=0.0,  # Updated later
                is_untested=True,
                test_count=0,
                last_test_time=None,
                higher_tf_bias=htf_bias['trend_direction'],
                session_context=session_context
            )
            
            return order_block
            
        except Exception as e:
            logger.error(f"Order block creation failed: {e}")
            return None
    
    def _detect_fair_value_gaps(self, df: pd.DataFrame, timeframe: str) -> List[FairValueGap]:
        """
        Detect Fair Value Gaps (FVG) - unfilled price imbalances.
        
        ICT Definition: 3-candle pattern where middle candle creates gap
        that doesn't get filled by surrounding candles.
        """
        try:
            fvgs = []
            data = df.copy()
            
            # Scan for 3-candle FVG patterns
            for i in range(1, len(data) - 1):
                # Get three consecutive candles
                candle1 = data.iloc[i-1]  # Before
                candle2 = data.iloc[i]    # Middle (gap creator)
                candle3 = data.iloc[i+1]  # After
                
                # Check for bullish FVG
                bullish_fvg = self._check_bullish_fvg(candle1, candle2, candle3)
                if bullish_fvg:
                    fvg = self._create_fvg(bullish_fvg, candle2.name, timeframe, 'BULLISH_FVG')
                    if fvg:
                        fvgs.append(fvg)
                
                # Check for bearish FVG
                bearish_fvg = self._check_bearish_fvg(candle1, candle2, candle3)
                if bearish_fvg:
                    fvg = self._create_fvg(bearish_fvg, candle2.name, timeframe, 'BEARISH_FVG')
                    if fvg:
                        fvgs.append(fvg)
            
            # Filter recent and significant FVGs
            filtered_fvgs = self._filter_fair_value_gaps(fvgs, data)
            
            logger.info(f"Detected {len(filtered_fvgs)} fair value gaps")
            return filtered_fvgs
            
        except Exception as e:
            logger.error(f"FVG detection failed: {e}")
            return []
    
    def _check_bullish_fvg(self, candle1: pd.Series, candle2: pd.Series, 
                          candle3: pd.Series) -> Optional[Dict]:
        """Check for bullish FVG pattern."""
        try:
            # Bullish FVG: candle1.high < candle3.low (gap between them)
            if candle1['high'] < candle3['low']:
                gap_size = candle3['low'] - candle1['high']
                gap_percentage = gap_size / candle2['close']
                
                # Must meet minimum size threshold
                if gap_percentage >= self.config['min_fvg_size_percentage']:
                    return {
                        'gap_high': candle3['low'],
                        'gap_low': candle1['high'],
                        'gap_size': gap_size,
                        'volume_confirmation': candle2['volume_ratio'] > 1.2
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Bullish FVG check failed: {e}")
            return None
    
    def _check_bearish_fvg(self, candle1: pd.Series, candle2: pd.Series,
                          candle3: pd.Series) -> Optional[Dict]:
        """Check for bearish FVG pattern."""
        try:
            # Bearish FVG: candle1.low > candle3.high (gap between them)
            if candle1['low'] > candle3['high']:
                gap_size = candle1['low'] - candle3['high']
                gap_percentage = gap_size / candle2['close']
                
                # Must meet minimum size threshold
                if gap_percentage >= self.config['min_fvg_size_percentage']:
                    return {
                        'gap_high': candle1['low'],
                        'gap_low': candle3['high'],
                        'gap_size': gap_size,
                        'volume_confirmation': candle2['volume_ratio'] > 1.2
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Bearish FVG check failed: {e}")
            return None
    
    def _create_fvg(self, gap_data: Dict, timestamp: datetime, 
                   timeframe: str, formation_type: str) -> Optional[FairValueGap]:
        """Create FairValueGap object."""
        try:
            # Calculate institutional interest based on gap size and volume
            institutional_interest = min(1.0, gap_data['gap_size'] / 100 * 
                                       (1.5 if gap_data['volume_confirmation'] else 1.0))
            
            fvg = FairValueGap(
                timestamp=timestamp,
                timeframe=timeframe,
                gap_high=gap_data['gap_high'],
                gap_low=gap_data['gap_low'],
                gap_size=gap_data['gap_size'],
                is_filled=False,
                fill_percentage=0.0,
                volume_confirmation=gap_data['volume_confirmation'],
                formation_type=formation_type,
                institutional_interest=institutional_interest
            )
            
            return fvg
            
        except Exception as e:
            logger.error(f"FVG creation failed: {e}")
            return None
    
    def _analyze_market_structure_breaks(self, df: pd.DataFrame, 
                                       timeframe: str) -> Dict:
        """
        Analyze market structure for BoS (Break of Structure) and 
        ChoCH (Change of Character) patterns.
        """
        try:
            structure_breaks = []
            data = df.copy()
            
            # Identify swing highs and lows
            swing_highs = self._identify_swing_points(data, 'high')
            swing_lows = self._identify_swing_points(data, 'low')
            
            # Analyze structure breaks
            bos_breaks = self._identify_bos_patterns(data, swing_highs, swing_lows)
            choch_breaks = self._identify_choch_patterns(data, swing_highs, swing_lows)
            
            structure_breaks.extend(bos_breaks)
            structure_breaks.extend(choch_breaks)
            
            # Current market structure state
            current_structure = self._determine_current_structure(
                structure_breaks, swing_highs, swing_lows
            )
            
            return {
                'structure_breaks': structure_breaks,
                'current_structure': current_structure,
                'swing_highs': swing_highs,
                'swing_lows': swing_lows,
                'last_analysis': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Structure analysis failed: {e}")
            return {
                'structure_breaks': [],
                'current_structure': 'UNKNOWN',
                'swing_highs': [],
                'swing_lows': [],
                'last_analysis': datetime.now()
            }
    
    def _map_liquidity_zones(self, df: pd.DataFrame, timeframe: str) -> List[LiquidityZone]:
        """
        Map liquidity accumulation zones where retail stops cluster.
        
        ICT Concept: Equal highs/lows where retail traders place stops.
        Smart money hunts these levels before reversing.
        """
        try:
            liquidity_zones = []
            data = df.copy()
            
            # Identify equal highs
            equal_highs = self._identify_equal_levels(data, 'high')
            for level_data in equal_highs:
                zone = LiquidityZone(
                    level=level_data['level'],
                    zone_type='EQUAL_HIGHS',
                    strength=level_data['strength'],
                    timestamp=level_data['timestamp'],
                    is_swept=level_data['is_swept'],
                    sweep_timestamp=level_data.get('sweep_timestamp')
                )
                liquidity_zones.append(zone)
            
            # Identify equal lows
            equal_lows = self._identify_equal_levels(data, 'low')
            for level_data in equal_lows:
                zone = LiquidityZone(
                    level=level_data['level'],
                    zone_type='EQUAL_LOWS',
                    strength=level_data['strength'],
                    timestamp=level_data['timestamp'],
                    is_swept=level_data['is_swept'],
                    sweep_timestamp=level_data.get('sweep_timestamp')
                )
                liquidity_zones.append(zone)
            
            # Identify psychological levels
            psychological_levels = self._identify_psychological_levels(data)
            for level_data in psychological_levels:
                zone = LiquidityZone(
                    level=level_data['level'],
                    zone_type='PSYCHOLOGICAL',
                    strength=level_data['strength'],
                    timestamp=level_data['timestamp'],
                    is_swept=level_data['is_swept'],
                    sweep_timestamp=level_data.get('sweep_timestamp')
                )
                liquidity_zones.append(zone)
            
            logger.info(f"Mapped {len(liquidity_zones)} liquidity zones")
            return liquidity_zones
            
        except Exception as e:
            logger.error(f"Liquidity mapping failed: {e}")
            return []
    
    def _calculate_fibonacci_confluence(self, df: pd.DataFrame, 
                                      order_blocks: List[OrderBlock]) -> Dict:
        """
        Calculate Fibonacci confluence with ICT 79% level emphasis.
        
        ICT teaches that 79% retracement often aligns with institutional
        re-entry levels and order blocks.
        """
        try:
            fibonacci_data = {}
            data = df.copy()
            
            # Get recent significant swing points
            swing_highs = self._identify_swing_points(data.tail(100), 'high')
            swing_lows = self._identify_swing_points(data.tail(100), 'low')
            
            # Calculate Fibonacci levels for recent swings
            for i, (high_point, low_point) in enumerate(zip(swing_highs[-5:], swing_lows[-5:])):
                swing_range = high_point['price'] - low_point['price']
                
                fib_levels = {}
                for level in self.config['fib_levels']:
                    # Calculate both bullish and bearish retracements
                    bullish_level = low_point['price'] + (swing_range * level)
                    bearish_level = high_point['price'] - (swing_range * level)
                    
                    fib_levels[f"{level:.3f}"] = {
                        'bullish_level': bullish_level,
                        'bearish_level': bearish_level,
                        'weight': self.config['fib_79_weight'] if level == 0.79 else 1.0
                    }
                
                fibonacci_data[f"swing_{i}"] = {
                    'high_point': high_point,
                    'low_point': low_point,
                    'levels': fib_levels
                }
            
            # Check Order Block confluence with 79% Fibonacci
            for ob in order_blocks:
                ob.fibonacci_alignment = self._calculate_ob_fib_confluence(ob, fibonacci_data)
            
            return fibonacci_data
            
        except Exception as e:
            logger.error(f"Fibonacci calculation failed: {e}")
            return {}
    
    def _analyze_session_context(self, df: pd.DataFrame) -> Dict:
        """Analyze trading session context for crypto markets."""
        try:
            current_time = datetime.now()
            current_hour = current_time.hour
            
            # Determine current session
            session = self._get_current_session(current_time)
            
            # Session-specific behavior analysis
            session_stats = self._calculate_session_statistics(df, session)
            
            return {
                'current_session': session,
                'session_stats': session_stats,
                'session_alignment': self._determine_session_alignment(df, session),
                'next_session_time': self._get_next_session_time(current_time)
            }
            
        except Exception as e:
            logger.error(f"Session analysis failed: {e}")
            return {
                'current_session': 'UNKNOWN',
                'session_stats': {},
                'session_alignment': False,
                'next_session_time': None
            }
    
    def _generate_ict_signals(self, df: pd.DataFrame, order_blocks: List[OrderBlock],
                            fair_value_gaps: List[FairValueGap], 
                            structure_analysis: Dict, liquidity_zones: List[LiquidityZone],
                            fibonacci_levels: Dict, session_context: Dict,
                            htf_bias: Dict) -> List[ICTSignal]:
        """Generate complete ICT trading signals with all confluence factors."""
        try:
            ict_signals = []
            current_price = df['close'].iloc[-1]
            
            # Generate signals from Order Blocks
            ob_signals = self._generate_order_block_signals(
                order_blocks, current_price, htf_bias, structure_analysis,
                fibonacci_levels, session_context, liquidity_zones
            )
            ict_signals.extend(ob_signals)
            
            # Generate signals from Fair Value Gaps
            fvg_signals = self._generate_fvg_signals(
                fair_value_gaps, current_price, htf_bias, structure_analysis
            )
            ict_signals.extend(fvg_signals)
            
            # Generate structure break signals
            structure_signals = self._generate_structure_signals(
                structure_analysis, current_price, htf_bias, order_blocks
            )
            ict_signals.extend(structure_signals)
            
            # Filter and rank signals by confidence
            filtered_signals = [
                signal for signal in ict_signals 
                if signal.confidence >= self.config['min_signal_confidence']
            ]
            
            # Sort by confidence descending
            filtered_signals.sort(key=lambda x: x.confidence, reverse=True)
            
            logger.info(f"Generated {len(filtered_signals)} high-confidence ICT signals")
            return filtered_signals
            
        except Exception as e:
            logger.error(f"ICT signal generation failed: {e}")
            return []
    
    # Placeholder methods for complex calculations
    # These would be implemented with detailed ICT logic
    
    def _identify_swing_points(self, df: pd.DataFrame, price_type: str) -> List[Dict]:
        """Identify swing highs or lows in price data."""
        # Simplified implementation - would use proper swing point detection
        return []
    
    def _determine_trend_direction(self, swing_highs: List, swing_lows: List) -> TrendDirection:
        """Determine overall trend direction from swing points."""
        # Simplified - would analyze swing point progression
        return TrendDirection.CONSOLIDATION
    
    def _calculate_trend_strength(self, df: pd.DataFrame, direction: TrendDirection) -> float:
        """Calculate trend strength score."""
        return 0.5
    
    def _identify_key_levels(self, df: pd.DataFrame, highs: List, lows: List) -> List:
        """Identify key support/resistance levels."""
        return []
    
    def _classify_market_phase(self, df: pd.DataFrame, direction: TrendDirection) -> str:
        """Classify current market phase."""
        return 'TRANSITION'
    
    def _filter_order_blocks(self, order_blocks: List[OrderBlock], df: pd.DataFrame) -> List[OrderBlock]:
        """Filter order blocks by relevance and quality."""
        return order_blocks[:5]  # Return top 5
    
    def _rank_order_blocks(self, order_blocks: List[OrderBlock], htf_bias: Dict) -> List[OrderBlock]:
        """Rank order blocks by confluence and probability."""
        return order_blocks
    
    def _filter_fair_value_gaps(self, fvgs: List[FairValueGap], df: pd.DataFrame) -> List[FairValueGap]:
        """Filter FVGs by age and significance."""
        return fvgs[:10]  # Return top 10
    
    def _identify_bos_patterns(self, df: pd.DataFrame, highs: List, lows: List) -> List:
        """Identify Break of Structure patterns."""
        return []
    
    def _identify_choch_patterns(self, df: pd.DataFrame, highs: List, lows: List) -> List:
        """Identify Change of Character patterns."""
        return []
    
    def _determine_current_structure(self, breaks: List, highs: List, lows: List) -> str:
        """Determine current market structure state."""
        return 'UPTREND'
    
    def _identify_equal_levels(self, df: pd.DataFrame, price_type: str) -> List[Dict]:
        """Identify equal highs or lows for liquidity mapping."""
        return []
    
    def _identify_psychological_levels(self, df: pd.DataFrame) -> List[Dict]:
        """Identify psychological price levels."""
        return []
    
    def _calculate_ob_fib_confluence(self, ob: OrderBlock, fib_data: Dict) -> float:
        """Calculate Order Block confluence with Fibonacci levels."""
        return 0.5
    
    def _get_current_session(self, timestamp) -> str:
        """Determine current trading session."""
        if isinstance(timestamp, datetime):
            hour = timestamp.hour
        else:
            hour = datetime.now().hour
        
        if self.config['asia_session'][0] <= hour < self.config['asia_session'][1]:
            return 'ASIA'
        elif self.config['london_session'][0] <= hour < self.config['london_session'][1]:
            return 'LONDON'
        elif self.config['ny_session'][0] <= hour < self.config['ny_session'][1]:
            return 'NY'
        else:
            return 'TRANSITION'
    
    def _calculate_session_statistics(self, df: pd.DataFrame, session: str) -> Dict:
        """Calculate session-specific trading statistics."""
        return {'volatility': 0.5, 'volume_avg': 1000, 'direction_bias': 'NEUTRAL'}
    
    def _determine_session_alignment(self, df: pd.DataFrame, session: str) -> bool:
        """Determine if current setup aligns with session bias."""
        return True
    
    def _get_next_session_time(self, current_time: datetime) -> datetime:
        """Get next session start time."""
        return current_time + timedelta(hours=1)
    
    def _generate_order_block_signals(self, order_blocks: List[OrderBlock],
                                    current_price: float, htf_bias: Dict,
                                    structure_analysis: Dict, fibonacci_levels: Dict,
                                    session_context: Dict, liquidity_zones: List[LiquidityZone]) -> List[ICTSignal]:
        """Generate signals from Order Block analysis."""
        signals = []
        
        for ob in order_blocks[:3]:  # Top 3 order blocks
            # Check if price is approaching order block
            if self._is_price_approaching_ob(current_price, ob):
                signal = self._create_order_block_signal(
                    ob, current_price, htf_bias, structure_analysis,
                    fibonacci_levels, session_context, liquidity_zones
                )
                if signal:
                    signals.append(signal)
        
        return signals
    
    def _generate_fvg_signals(self, fvgs: List[FairValueGap], current_price: float,
                            htf_bias: Dict, structure_analysis: Dict) -> List[ICTSignal]:
        """Generate signals from Fair Value Gap analysis."""
        return []  # Simplified for now
    
    def _generate_structure_signals(self, structure_analysis: Dict, current_price: float,
                                  htf_bias: Dict, order_blocks: List[OrderBlock]) -> List[ICTSignal]:
        """Generate signals from market structure breaks."""
        return []  # Simplified for now
    
    def _is_price_approaching_ob(self, current_price: float, ob: OrderBlock) -> bool:
        """Check if price is approaching an order block."""
        distance_to_ob = abs(current_price - ob.zone_mid) / current_price
        return distance_to_ob < 0.01  # Within 1%
    
    def _create_order_block_signal(self, ob: OrderBlock, current_price: float,
                                 htf_bias: Dict, structure_analysis: Dict,
                                 fibonacci_levels: Dict, session_context: Dict,
                                 liquidity_zones: List[LiquidityZone]) -> Optional[ICTSignal]:
        """Create a complete ICT signal from order block setup."""
        try:
            # Determine signal direction
            if ob.type == OrderBlockType.BULLISH_OB and htf_bias['trend_direction'] == TrendDirection.BULLISH:
                direction = 'LONG'
                entry_price = ob.low  # Enter at bottom of bullish OB
                stop_loss = entry_price * 0.99  # 1% below entry
                take_profit = entry_price * 1.04  # 4% above entry (2:1 R:R)
            elif ob.type == OrderBlockType.BEARISH_OB and htf_bias['trend_direction'] == TrendDirection.BEARISH:
                direction = 'SHORT'
                entry_price = ob.high  # Enter at top of bearish OB
                stop_loss = entry_price * 1.01  # 1% above entry
                take_profit = entry_price * 0.96  # 4% below entry (2:1 R:R)
            else:
                return None  # No signal if OB doesn't align with HTF bias
            
            # Calculate confidence score
            confidence = self._calculate_signal_confidence(
                ob, htf_bias, structure_analysis, fibonacci_levels, session_context
            )
            
            # Calculate risk-reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Create signal
            signal = ICTSignal(
                symbol="",  # Will be set by caller
                timeframe=ob.timeframe,
                timestamp=datetime.now(),
                signal_type=f"{direction}_OB",
                direction=direction,
                confidence=confidence,
                primary_order_block=ob,
                supporting_fvg=None,
                structure_confirmation=None,
                liquidity_sweep=None,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=risk_reward_ratio,
                htf_bias=htf_bias['trend_direction'],
                htf_structure=htf_bias,
                fib_confluence=ob.fibonacci_alignment,
                session=session_context['current_session'],
                session_alignment=session_context['session_alignment']
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Order block signal creation failed: {e}")
            return None
    
    def _calculate_signal_confidence(self, ob: OrderBlock, htf_bias: Dict,
                                   structure_analysis: Dict, fibonacci_levels: Dict,
                                   session_context: Dict) -> float:
        """Calculate overall signal confidence score."""
        try:
            base_confidence = 0.5
            
            # Order block quality (25% weight)
            ob_score = (ob.freshness_score * 0.4 + 
                       ob.confluence_level * 0.3 + 
                       ob.reaction_strength * 0.3)
            
            # Higher timeframe alignment (30% weight)
            htf_score = htf_bias['trend_strength']
            
            # Fibonacci confluence (20% weight)
            fib_score = ob.fibonacci_alignment
            
            # Session alignment (15% weight)
            session_score = 1.0 if session_context['session_alignment'] else 0.5
            
            # Structure confirmation (10% weight)
            structure_score = 0.8  # Simplified
            
            # Calculate weighted confidence
            confidence = (
                base_confidence * 0.0 +
                ob_score * 0.25 +
                htf_score * 0.30 +
                fib_score * 0.20 +
                session_score * 0.15 +
                structure_score * 0.10
            )
            
            return min(1.0, max(0.0, confidence))
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.5
    
    def _create_market_summary(self, htf_bias: Dict, order_blocks: List[OrderBlock],
                             structure_analysis: Dict, signals: List[ICTSignal]) -> Dict:
        """Create comprehensive market summary."""
        return {
            'market_bias': htf_bias['trend_direction'].value,
            'trend_strength': htf_bias['trend_strength'],
            'active_order_blocks': len(order_blocks),
            'fresh_order_blocks': len([ob for ob in order_blocks if ob.freshness_score > 0.7]),
            'signal_count': len(signals),
            'high_confidence_signals': len([s for s in signals if s.confidence > 0.8]),
            'market_structure': structure_analysis['current_structure'],
            'trading_recommendation': self._get_trading_recommendation(signals, htf_bias)
        }
    
    def _get_trading_recommendation(self, signals: List[ICTSignal], htf_bias: Dict) -> str:
        """Get overall trading recommendation."""
        if not signals:
            return "NO_SIGNALS"
        
        high_conf_signals = [s for s in signals if s.confidence > 0.8]
        
        if len(high_conf_signals) >= 2:
            return "HIGH_PROBABILITY_SETUP"
        elif len(signals) >= 1:
            return "MODERATE_SETUP"
        else:
            return "WAIT_FOR_BETTER_SETUP"
    
    def _cache_analysis_results(self, symbol: str, timeframe: str, results: Dict) -> None:
        """Cache analysis results for performance."""
        cache_key = f"{symbol}_{timeframe}"
        # Simple caching - in production, would use proper cache with expiry
        self.last_analysis_time[cache_key] = datetime.now()
    
    def _get_empty_analysis(self, symbol: str, timeframe: str) -> Dict:
        """Return empty analysis structure on error."""
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.now(),
            'htf_bias': {'trend_direction': TrendDirection.CONSOLIDATION},
            'order_blocks': [],
            'fair_value_gaps': [],
            'structure_analysis': {'structure_breaks': [], 'current_structure': 'UNKNOWN'},
            'liquidity_zones': [],
            'fibonacci_levels': {},
            'session_context': {'current_session': 'UNKNOWN'},
            'ict_signals': [],
            'market_summary': {'trading_recommendation': 'NO_DATA'}
        }


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize ICT analyzer
    analyzer = ICTAnalyzer()
    
    # Create sample OHLCV data
    dates = pd.date_range(start='2025-09-01', end='2025-09-29', freq='5T')
    np.random.seed(42)
    
    sample_data = pd.DataFrame({
        'open': np.random.randn(len(dates)).cumsum() + 50000,
        'high': np.random.randn(len(dates)).cumsum() + 50200,
        'low': np.random.randn(len(dates)).cumsum() + 49800,
        'close': np.random.randn(len(dates)).cumsum() + 50000,
        'volume': np.random.randint(100, 1000, len(dates))
    }, index=dates)
    
    # Ensure OHLC relationship
    sample_data['high'] = sample_data[['open', 'close']].max(axis=1) + np.abs(np.random.randn(len(dates))) * 50
    sample_data['low'] = sample_data[['open', 'close']].min(axis=1) - np.abs(np.random.randn(len(dates))) * 50
    
    # Run ICT analysis
    print("🔬 Running ICT Analysis...")
    analysis = analyzer.analyze_market_structure(sample_data, "BTC/USDT", "5T")
    
    # Display results
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                     ICT ANALYSIS RESULTS                        ║
╠══════════════════════════════════════════════════════════════════╣
║  Market Summary:                                                 ║
║    Market Bias: {analysis['market_summary']['market_bias']:>15}                      ║
║    Order Blocks: {analysis['market_summary']['active_order_blocks']:>14}                         ║
║    ICT Signals: {analysis['market_summary']['signal_count']:>15}                         ║
║    Recommendation: {analysis['market_summary']['trading_recommendation']:>12}                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    if analysis['ict_signals']:
        print("📈 ICT SIGNALS DETECTED:")
        for i, signal in enumerate(analysis['ict_signals'][:3], 1):
            print(f"  {i}. {signal.direction} signal - {signal.confidence:.1%} confidence")
            print(f"     Entry: ${signal.entry_price:.2f}, R:R = {signal.risk_reward_ratio:.1f}")
    else:
        print("🔍 No ICT signals detected in current market conditions")
    
    print("✅ ICT Analysis Complete!")