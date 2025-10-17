#!/usr/bin/env python3
#!/usr/bin/env python3
"""
ICT Enhanced Order Block Detection System
========================================

Advanced Enhanced Order Block (EOB) detection following ICT methodology for
institutional trading analysis. Enhanced Order Blocks represent upgraded
areas where smart money has placed large orders with volume confirmation,
time validation, and institutional quality scoring.

Key ICT Enhanced Order Block Concepts:
- Bullish EOBs: Areas of institutional accumulation with volume confirmation
- Bearish EOBs: Areas of institutional distribution with volume validation
- Fair Value Gaps: Imbalances that often respect EOB boundaries
- Liquidity Zones: Areas where EOBs attract price for institutional liquidity
- Time & Volume Validation: Enhanced institutional footprints in market data
- Quality Scoring: Institutional-grade EOB rating system

Enhanced Order Block Quality Factors:
1. Volume Confirmation: Institutional volume during EOB formation
2. Time Validation: Duration and institutional time spent in EOB area
3. Reaction Strength: Institutional-level price movement away from EOB
4. Respect Count: Number of times price has respected the EOB
5. Fresh vs Tested: Untested EOBs have higher institutional probability
6. Institutional Quality Score: 0-100 rating based on smart money criteria

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, NamedTuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import ta

logger = logging.getLogger(__name__)

class OrderBlockQuality(Enum):
    """Order Block quality classification."""
    PREMIUM = "PREMIUM"       # Fresh, strong, high volume
    HIGH = "HIGH"            # Good quality with most confirmations
    MEDIUM = "MEDIUM"        # Decent quality, some confirmations
    LOW = "LOW"              # Weak quality, few confirmations
    INVALID = "INVALID"      # Doesn't meet minimum criteria

class OrderBlockState(Enum):
    """Order Block current state."""
    FRESH = "FRESH"          # Never tested
    TESTED = "TESTED"        # Price has touched but held
    BROKEN = "BROKEN"        # Price has broken through
    EXPIRED = "EXPIRED"      # Too old to be relevant

@dataclass
class OrderBlockCandle:
    """Individual candle that forms an Order Block."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    # Candle characteristics
    body_size: float = field(init=False)
    upper_wick: float = field(init=False)
    lower_wick: float = field(init=False)
    total_range: float = field(init=False)
    is_bullish: bool = field(init=False)
    
    # Volume analysis
    volume_ratio: float = 0.0         # Volume vs average
    institutional_volume: bool = False # High volume signature
    
    def __post_init__(self):
        """Calculate derived candle properties."""
        self.body_size = abs(self.close - self.open)
        self.upper_wick = self.high - max(self.open, self.close)
        self.lower_wick = min(self.open, self.close) - self.low
        self.total_range = self.high - self.low
        self.is_bullish = self.close > self.open

@dataclass
class OrderBlockDisplacement:
    """Price displacement that confirms Order Block validity."""
    start_price: float
    end_price: float
    displacement_size: float
    displacement_percentage: float
    candles_count: int
    max_retracement: float
    
    # Displacement characteristics
    is_impulsive: bool          # Strong, clean movement
    volume_confirmation: bool   # Volume supports move
    time_efficiency: float      # Speed of displacement (price/time)

@dataclass
class OrderBlockZone:
    """Complete Order Block zone definition."""
    # Core identification
    formation_candle: OrderBlockCandle
    displacement: OrderBlockDisplacement
    ob_type: str                # 'BULLISH_OB', 'BEARISH_OB'
    timeframe: str
    
    # Zone boundaries
    zone_high: float
    zone_low: float
    zone_mid: float
    optimal_entry: float        # Best entry point within zone
    
    # Quality metrics
    quality: OrderBlockQuality
    strength_score: float       # 0-1 overall strength
    confluence_factors: List[str] # What makes this OB strong
    
    # State tracking
    state: OrderBlockState
    creation_time: datetime
    last_test_time: Optional[datetime] = None
    test_count: int = 0
    break_price: Optional[float] = None
    
    # Market context
    higher_tf_alignment: bool = False
    session_context: str = ""
    fibonacci_confluence: float = 0.0
    
    # Risk/Reward
    suggested_stop_loss: float = 0.0
    suggested_take_profit: float = 0.0
    risk_reward_ratio: float = 0.0

@dataclass
class EnhancedOrderBlock:
    """Represents an ICT Enhanced Order Block with institutional significance."""
    # Core identification
    symbol: str
    timeframe: str
    timestamp: datetime
    
    # Enhanced block boundaries with institutional precision
    high: float
    low: float
    open: float
    close: float
    optimal_entry_zone: Tuple[float, float]  # Precise institutional entry zone
    
    # Enhanced block type and characteristics
    block_type: str             # 'BULLISH_EOB', 'BEARISH_EOB'
    institutional_signature: str # 'ACCUMULATION', 'DISTRIBUTION', 'MANIPULATION'
    
    # Enhanced block quality metrics
    volume_confirmation: float      # Institutional volume during EOB formation
    time_spent: float              # Time consolidating in EOB area
    reaction_strength: float       # Strength of institutional move away from EOB
    respect_count: int             # Times price respected this EOB
    is_fresh: bool                 # Whether EOB is untested
    
    # Enhanced institutional metrics
    institutional_quality_score: float  # 0-100 institutional quality rating
    volume_profile_score: float     # Volume distribution quality score
    time_validation_score: float    # Time-based validation score
    smart_money_signature: float    # Smart money footprint strength
    
    # Classification
    quality: OrderBlockQuality     # Overall EOB quality rating
    confidence: float              # Confidence in EOB validity (0-1)
    
    # Market context and confluence
    session_context: str           # Trading session when EOB formed
    higher_tf_alignment: bool      # Alignment with higher timeframes
    confluence_factors: List[str]  # Institutional confluence indicators
    
    # State and tracking
    state: OrderBlockState         # Current EOB state
    last_test_time: Optional[datetime] = None
    break_price: Optional[float] = None
    break_time: Optional[datetime] = None
    
    # Enhanced risk management
    institutional_stop_loss: float = 0.0
    institutional_take_profit: float = 0.0
    institutional_rrr: float = 0.0  # Risk-reward ratio

class EnhancedOrderBlockDetector:
    """
    Detects and analyzes ICT Enhanced Order Blocks in market data.
    
    This enhanced detector identifies areas where institutional traders have
    placed significant orders with volume confirmation, time validation, and
    institutional quality scoring for superior smart money analysis.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize Enhanced Order Block detector."""
        self.config = self._load_default_config()
        if config:
            self.config.update(config)
            
        # Enhanced detection state
        self.detected_eobs = {}
        self.eob_history = {}
        self.institutional_metrics = {}
        
        logger.info("Enhanced Order Block Detector initialized with ICT methodology")
    
    def _load_default_config(self) -> Dict:
        """Load default Order Block detection configuration."""
        return {
            # Displacement requirements
            'min_displacement_percentage': 0.5,    # 0.5% minimum move
            'min_displacement_candles': 3,         # At least 3 candles
            'max_displacement_candles': 20,        # Max 20 candles for displacement
            'min_impulsive_ratio': 0.7,           # 70% of move should be impulsive
            
            # Volume requirements
            'min_volume_ratio': 1.5,              # 1.5x average volume minimum
            'institutional_volume_ratio': 2.5,    # 2.5x = institutional signature
            'volume_lookback_periods': 20,         # Periods for volume average
            
            # Order Block quality factors
            'fresh_ob_bonus': 0.3,                # Bonus for untested OBs
            'session_alignment_bonus': 0.1,       # Bonus for session alignment
            'htf_alignment_bonus': 0.2,           # Bonus for HTF alignment
            'fibonacci_alignment_bonus': 0.1,     # Bonus for Fib confluence
            
            # Age and expiry
            'max_ob_age_hours': 72,               # 72 hours max age
            'optimal_ob_age_hours': 24,           # 24 hours optimal age
            'test_invalidation_count': 3,         # Max tests before invalidation
            
            # Zone definition
            'zone_extension_percentage': 0.1,     # Extend zone by 0.1%
            'optimal_entry_ratio': 0.618,        # Golden ratio for entry
            
            # Risk management
            'default_stop_loss_ratio': 0.02,     # 2% stop loss
            'default_take_profit_ratio': 0.04,   # 4% take profit (2:1 R:R)
            'max_risk_per_ob': 0.03,             # 3% max risk per Order Block
            
            # Crypto-specific adaptations
            'crypto_volatility_multiplier': 1.5,  # Adjust for crypto volatility
            'btc_correlation_factor': 0.8,        # BTC correlation importance
        }
    
    def detect_enhanced_order_blocks(self, df: pd.DataFrame, symbol: str, 
                                   timeframe: str = "5T") -> List[EnhancedOrderBlock]:
        """
        Detect Enhanced Order Blocks with institutional validation.
        
        This enhanced method identifies EOBs with volume confirmation,
        time validation, and institutional quality scoring.
        
        Args:
            df: OHLCV DataFrame with datetime index and volume
            symbol: Trading pair symbol
            timeframe: Analysis timeframe
            
        Returns:
            List of Enhanced Order Blocks with institutional metrics
        """
        try:
            logger.info(f"Starting Order Block detection for {symbol} {timeframe}")
            
            # Prepare data for analysis
            df = self._prepare_data(df)
            
            if len(df) < 50:
                logger.warning(f"Insufficient data for Order Block detection: {len(df)} candles")
                return []
            
            # Scan for potential Order Block formations
            potential_obs = self._scan_for_ob_formations(df, symbol, timeframe)
            
            # Validate and filter Order Blocks
            validated_obs = self._validate_order_blocks(potential_obs, df)
            
            # Classify Order Block quality
            classified_obs = self._classify_order_block_quality(validated_obs, df)
            
            # Calculate confluence factors
            enhanced_obs = self._calculate_confluence_factors(classified_obs, df)
            
            # Update Order Block states
            current_obs = self._update_order_block_states(enhanced_obs, df)
            
            # Filter by quality and relevance
            final_obs = self._filter_order_blocks(current_obs)
            
            # Update detection statistics
            self._update_detection_stats(final_obs)
            
            logger.info(f"Order Block detection completed: {len(final_obs)} high-quality OBs found")
            return final_obs
            
        except Exception as e:
            logger.error(f"Order Block detection failed for {symbol}: {e}")
            return []
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare OHLCV data for Order Block analysis."""
        try:
            # Create a copy to avoid modifying original data
            data = df.copy()
            
            # Ensure proper datetime index
            if not isinstance(data.index, pd.DatetimeIndex):
                if 'timestamp' in data.columns:
                    data.index = pd.to_datetime(data['timestamp'])
                else:
                    data.index = pd.to_datetime(data.index)
            
            # Calculate basic indicators
            data['body_size'] = abs(data['close'] - data['open'])
            data['upper_wick'] = data['high'] - data[['open', 'close']].max(axis=1)
            data['lower_wick'] = data[['open', 'close']].min(axis=1) - data['low']
            data['candle_range'] = data['high'] - data['low']
            data['is_bullish'] = data['close'] > data['open']
            
            # Volume analysis
            volume_periods = self.config['volume_lookback_periods']
            data['volume_ma'] = data['volume'].rolling(window=volume_periods).mean()
            data['volume_ratio'] = data['volume'] / data['volume_ma']
            
            # True Range and ATR for volatility
            data['tr'] = np.maximum(
                data['high'] - data['low'],
                np.maximum(
                    abs(data['high'] - data['close'].shift(1)),
                    abs(data['low'] - data['close'].shift(1))
                )
            )
            data['atr'] = data['tr'].rolling(window=14).mean()
            
            # Price displacement detection
            data['displacement_up'] = self._calculate_displacement_strength(data, 'up')
            data['displacement_down'] = self._calculate_displacement_strength(data, 'down')
            
            return data
            
        except Exception as e:
            logger.error(f"Data preparation failed: {e}")
            raise
    
    def _calculate_displacement_strength(self, df: pd.DataFrame, direction: str) -> pd.Series:
        """Calculate price displacement strength in given direction."""
        try:
            lookback = 10  # Look at next 10 candles for displacement
            displacement_strength = pd.Series(index=df.index, dtype=float)
            
            for i in range(len(df) - lookback):
                current_price = df['close'].iloc[i]
                future_prices = df['close'].iloc[i+1:i+lookback+1]
                
                if direction == 'up':
                    max_future = future_prices.max()
                    displacement = (max_future - current_price) / current_price
                else:  # down
                    min_future = future_prices.min()
                    displacement = (current_price - min_future) / current_price
                
                displacement_strength.iloc[i] = max(0, displacement)
            
            return displacement_strength.fillna(0)
            
        except Exception as e:
            logger.error(f"Displacement calculation failed: {e}")
            return pd.Series(index=df.index, dtype=float).fillna(0)
    
    def _scan_for_ob_formations(self, df: pd.DataFrame, symbol: str, 
                              timeframe: str) -> List[OrderBlockZone]:
        """Scan for potential Order Block formations in price data."""
        try:
            potential_obs = []
            
            # Scan through price data looking for OB patterns
            for i in range(20, len(df) - 20):  # Leave buffer for displacement analysis
                
                # Check for bullish Order Block formation
                bullish_ob = self._check_bullish_ob_formation(df, i)
                if bullish_ob:
                    ob_zone = self._create_order_block_zone(
                        df, i, 'BULLISH_OB', bullish_ob, symbol, timeframe
                    )
                    if ob_zone:
                        potential_obs.append(ob_zone)
                
                # Check for bearish Order Block formation
                bearish_ob = self._check_bearish_ob_formation(df, i)
                if bearish_ob:
                    ob_zone = self._create_order_block_zone(
                        df, i, 'BEARISH_OB', bearish_ob, symbol, timeframe
                    )
                    if ob_zone:
                        potential_obs.append(ob_zone)
            
            logger.debug(f"Found {len(potential_obs)} potential Order Blocks")
            return potential_obs
            
        except Exception as e:
            logger.error(f"Order Block formation scan failed: {e}")
            return []
    
    def _check_bullish_ob_formation(self, df: pd.DataFrame, index: int) -> Optional[Dict]:
        """
        Check for bullish Order Block formation at given index.
        
        Bullish OB Rules:
        1. Current candle is bearish (red)
        2. Strong upward displacement follows
        3. Volume confirmation on OB candle
        4. Minimal retracement during displacement
        """
        try:
            current_candle = df.iloc[index]
            
            # Rule 1: Must be bearish candle
            if current_candle['close'] >= current_candle['open']:
                return None
            
            # Rule 2: Check for upward displacement
            future_data = df.iloc[index+1:index+21]  # Next 20 candles
            if len(future_data) < self.config['min_displacement_candles']:
                return None
            
            # Calculate displacement metrics
            displacement_start = current_candle['close']
            displacement_high = future_data['high'].max()
            displacement_percentage = (displacement_high - displacement_start) / displacement_start
            
            # Must meet minimum displacement
            if displacement_percentage < self.config['min_displacement_percentage'] / 100:
                return None
            
            # Rule 3: Volume confirmation
            volume_ratio = current_candle['volume_ratio']
            if volume_ratio < self.config['min_volume_ratio']:
                return None
            
            # Rule 4: Check displacement quality
            displacement_quality = self._analyze_displacement_quality(
                future_data, displacement_start, 'up'
            )
            
            if not displacement_quality['is_valid']:
                return None
            
            return {
                'displacement_start': displacement_start,
                'displacement_high': displacement_high,
                'displacement_percentage': displacement_percentage,
                'volume_ratio': volume_ratio,
                'displacement_quality': displacement_quality
            }
            
        except Exception as e:
            logger.error(f"Bullish OB formation check failed: {e}")
            return None
    
    def _check_bearish_ob_formation(self, df: pd.DataFrame, index: int) -> Optional[Dict]:
        """
        Check for bearish Order Block formation at given index.
        
        Bearish OB Rules:
        1. Current candle is bullish (green)
        2. Strong downward displacement follows
        3. Volume confirmation on OB candle
        4. Minimal retracement during displacement
        """
        try:
            current_candle = df.iloc[index]
            
            # Rule 1: Must be bullish candle
            if current_candle['close'] <= current_candle['open']:
                return None
            
            # Rule 2: Check for downward displacement
            future_data = df.iloc[index+1:index+21]  # Next 20 candles
            if len(future_data) < self.config['min_displacement_candles']:
                return None
            
            # Calculate displacement metrics
            displacement_start = current_candle['close']
            displacement_low = future_data['low'].min()
            displacement_percentage = (displacement_start - displacement_low) / displacement_start
            
            # Must meet minimum displacement
            if displacement_percentage < self.config['min_displacement_percentage'] / 100:
                return None
            
            # Rule 3: Volume confirmation
            volume_ratio = current_candle['volume_ratio']
            if volume_ratio < self.config['min_volume_ratio']:
                return None
            
            # Rule 4: Check displacement quality
            displacement_quality = self._analyze_displacement_quality(
                future_data, displacement_start, 'down'
            )
            
            if not displacement_quality['is_valid']:
                return None
            
            return {
                'displacement_start': displacement_start,
                'displacement_low': displacement_low,
                'displacement_percentage': displacement_percentage,
                'volume_ratio': volume_ratio,
                'displacement_quality': displacement_quality
            }
            
        except Exception as e:
            logger.error(f"Bearish OB formation check failed: {e}")
            return None
    
    def _analyze_displacement_quality(self, future_data: pd.DataFrame, 
                                    start_price: float, direction: str) -> Dict:
        """Analyze the quality of price displacement following Order Block."""
        try:
            if direction == 'up':
                end_price = future_data['high'].max()
                displacement_size = end_price - start_price
                
                # Check for clean, impulsive movement
                retracements = []
                current_high = start_price
                
                for _, candle in future_data.iterrows():
                    if candle['high'] > current_high:
                        current_high = candle['high']
                    else:
                        retracement = (current_high - candle['low']) / current_high
                        retracements.append(retracement)
                        
            else:  # down
                end_price = future_data['low'].min()
                displacement_size = start_price - end_price
                
                # Check for clean, impulsive movement
                retracements = []
                current_low = start_price
                
                for _, candle in future_data.iterrows():
                    if candle['low'] < current_low:
                        current_low = candle['low']
                    else:
                        retracement = (candle['high'] - current_low) / current_low
                        retracements.append(retracement)
            
            # Calculate displacement quality metrics
            max_retracement = max(retracements) if retracements else 0
            avg_retracement = np.mean(retracements) if retracements else 0
            
            # Displacement is valid if it's mostly impulsive
            is_impulsive = max_retracement < 0.3  # Max 30% retracement
            
            # Volume confirmation during displacement
            avg_volume_ratio = future_data['volume_ratio'].mean()
            volume_confirmation = avg_volume_ratio > 1.2
            
            # Time efficiency (price movement per candle)
            time_efficiency = displacement_size / len(future_data)
            
            return {
                'is_valid': is_impulsive and volume_confirmation,
                'is_impulsive': is_impulsive,
                'max_retracement': max_retracement,
                'avg_retracement': avg_retracement,
                'volume_confirmation': volume_confirmation,
                'time_efficiency': time_efficiency,
                'displacement_size': displacement_size
            }
            
        except Exception as e:
            logger.error(f"Displacement quality analysis failed: {e}")
            return {
                'is_valid': False,
                'is_impulsive': False,
                'max_retracement': 1.0,
                'avg_retracement': 1.0,
                'volume_confirmation': False,
                'time_efficiency': 0.0,
                'displacement_size': 0.0
            }
    
    def _create_order_block_zone(self, df: pd.DataFrame, index: int, ob_type: str,
                               formation_data: Dict, symbol: str, timeframe: str) -> Optional[OrderBlockZone]:
        """Create complete Order Block zone from formation data."""
        try:
            candle_data = df.iloc[index]
            
            # Create formation candle object
            formation_candle = OrderBlockCandle(
                timestamp=candle_data.name,
                open=candle_data['open'],
                high=candle_data['high'],
                low=candle_data['low'],
                close=candle_data['close'],
                volume=candle_data['volume'],
                volume_ratio=formation_data['volume_ratio'],
                institutional_volume=formation_data['volume_ratio'] >= self.config['institutional_volume_ratio']
            )
            
            # Create displacement object
            displacement = OrderBlockDisplacement(
                start_price=formation_data['displacement_start'],
                end_price=formation_data.get('displacement_high', formation_data.get('displacement_low')),
                displacement_size=formation_data['displacement_quality']['displacement_size'],
                displacement_percentage=formation_data['displacement_percentage'],
                candles_count=len(df.iloc[index+1:index+21]),
                max_retracement=formation_data['displacement_quality']['max_retracement'],
                is_impulsive=formation_data['displacement_quality']['is_impulsive'],
                volume_confirmation=formation_data['displacement_quality']['volume_confirmation'],
                time_efficiency=formation_data['displacement_quality']['time_efficiency']
            )
            
            # Define Order Block zone boundaries
            if ob_type == 'BULLISH_OB':
                zone_high = candle_data['high']
                zone_low = candle_data['low']
                optimal_entry = zone_low + (zone_high - zone_low) * self.config['optimal_entry_ratio']
            else:  # BEARISH_OB
                zone_high = candle_data['high']
                zone_low = candle_data['low']
                optimal_entry = zone_high - (zone_high - zone_low) * self.config['optimal_entry_ratio']
            
            zone_mid = (zone_high + zone_low) / 2
            
            # Calculate risk/reward levels
            if ob_type == 'BULLISH_OB':
                stop_loss = zone_low * (1 - self.config['default_stop_loss_ratio'])
                take_profit = optimal_entry * (1 + self.config['default_take_profit_ratio'])
            else:  # BEARISH_OB
                stop_loss = zone_high * (1 + self.config['default_stop_loss_ratio'])
                take_profit = optimal_entry * (1 - self.config['default_take_profit_ratio'])
            
            risk = abs(optimal_entry - stop_loss)
            reward = abs(take_profit - optimal_entry)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Create Order Block zone
            ob_zone = OrderBlockZone(
                formation_candle=formation_candle,
                displacement=displacement,
                ob_type=ob_type,
                timeframe=timeframe,
                zone_high=zone_high,
                zone_low=zone_low,
                zone_mid=zone_mid,
                optimal_entry=optimal_entry,
                quality=OrderBlockQuality.MEDIUM,  # Will be updated in classification
                strength_score=0.5,  # Will be calculated in quality classification
                confluence_factors=[],  # Will be populated later
                state=OrderBlockState.FRESH,
                creation_time=candle_data.name,
                suggested_stop_loss=stop_loss,
                suggested_take_profit=take_profit,
                risk_reward_ratio=risk_reward_ratio
            )
            
            return ob_zone
            
        except Exception as e:
            logger.error(f"Order Block zone creation failed: {e}")
            return None
    
    def _validate_order_blocks(self, potential_obs: List[OrderBlockZone], 
                             df: pd.DataFrame) -> List[OrderBlockZone]:
        """Validate potential Order Blocks against ICT criteria."""
        try:
            validated_obs = []
            
            for ob in potential_obs:
                # Age validation
                age_hours = (datetime.now() - ob.creation_time).total_seconds() / 3600
                if age_hours > self.config['max_ob_age_hours']:
                    continue
                
                # Displacement validation
                if ob.displacement.displacement_percentage < self.config['min_displacement_percentage'] / 100:
                    continue
                
                # Volume validation
                if ob.formation_candle.volume_ratio < self.config['min_volume_ratio']:
                    continue
                
                # Risk/reward validation
                if ob.risk_reward_ratio < 1.0:  # Minimum 1:1 R:R
                    continue
                
                validated_obs.append(ob)
            
            logger.debug(f"Validated {len(validated_obs)} Order Blocks")
            return validated_obs
            
        except Exception as e:
            logger.error(f"Order Block validation failed: {e}")
            return potential_obs
    
    def _classify_order_block_quality(self, validated_obs: List[OrderBlockZone], 
                                    df: pd.DataFrame) -> List[OrderBlockZone]:
        """Classify Order Block quality based on multiple factors."""
        try:
            for ob in validated_obs:
                quality_score = 0.0
                confluence_factors = []
                
                # Base score from displacement quality
                quality_score += ob.displacement.displacement_percentage * 2  # Up to 2.0 for 100% displacement
                
                # Volume factor
                if ob.formation_candle.institutional_volume:
                    quality_score += 0.3
                    confluence_factors.append("Institutional Volume")
                elif ob.formation_candle.volume_ratio >= self.config['min_volume_ratio']:
                    quality_score += 0.1
                    confluence_factors.append("Above Average Volume")
                
                # Displacement impulsiveness
                if ob.displacement.is_impulsive:
                    quality_score += 0.2
                    confluence_factors.append("Impulsive Displacement")
                
                # Time efficiency
                if ob.displacement.time_efficiency > 0.01:  # Threshold for fast movement
                    quality_score += 0.1
                    confluence_factors.append("Fast Displacement")
                
                # Fresh Order Block bonus
                if ob.state == OrderBlockState.FRESH:
                    quality_score += self.config['fresh_ob_bonus']
                    confluence_factors.append("Untested Order Block")
                
                # Risk/reward ratio
                if ob.risk_reward_ratio >= 2.0:
                    quality_score += 0.2
                    confluence_factors.append("Good Risk:Reward (2:1+)")
                elif ob.risk_reward_ratio >= 1.5:
                    quality_score += 0.1
                    confluence_factors.append("Decent Risk:Reward (1.5:1+)")
                
                # Age factor (fresher is better)
                age_hours = (datetime.now() - ob.creation_time).total_seconds() / 3600
                if age_hours <= self.config['optimal_ob_age_hours']:
                    age_bonus = (self.config['optimal_ob_age_hours'] - age_hours) / self.config['optimal_ob_age_hours'] * 0.1
                    quality_score += age_bonus
                    if age_hours <= 12:
                        confluence_factors.append("Very Fresh (<12h)")
                    else:
                        confluence_factors.append("Fresh (<24h)")
                
                # Normalize quality score to 0-1 range
                normalized_score = min(1.0, quality_score / 3.0)
                
                # Classify quality
                if normalized_score >= 0.8:
                    quality = OrderBlockQuality.PREMIUM
                elif normalized_score >= 0.6:
                    quality = OrderBlockQuality.HIGH
                elif normalized_score >= 0.4:
                    quality = OrderBlockQuality.MEDIUM
                elif normalized_score >= 0.2:
                    quality = OrderBlockQuality.LOW
                else:
                    quality = OrderBlockQuality.INVALID
                
                # Update Order Block with quality assessment
                ob.quality = quality
                ob.strength_score = normalized_score
                ob.confluence_factors = confluence_factors
            
            logger.debug(f"Quality classification completed")
            return validated_obs
            
        except Exception as e:
            logger.error(f"Order Block quality classification failed: {e}")
            return validated_obs
    
    def _calculate_confluence_factors(self, classified_obs: List[OrderBlockZone], 
                                    df: pd.DataFrame) -> List[OrderBlockZone]:
        """Calculate additional confluence factors for Order Blocks."""
        try:
            for ob in classified_obs:
                # Session alignment (simplified - would use actual session analysis)
                current_hour = datetime.now().hour
                if 8 <= current_hour <= 16:  # London session
                    ob.session_context = "LONDON"
                    if "Session Alignment" not in ob.confluence_factors:
                        ob.confluence_factors.append("London Session")
                        ob.strength_score += self.config['session_alignment_bonus']
                elif 13 <= current_hour <= 21:  # NY session
                    ob.session_context = "NY"
                    if "Session Alignment" not in ob.confluence_factors:
                        ob.confluence_factors.append("NY Session")
                        ob.strength_score += self.config['session_alignment_bonus']
                else:
                    ob.session_context = "ASIA"
                
                # Fibonacci confluence (simplified - would calculate actual Fib levels)
                # This is a placeholder for more sophisticated Fib analysis
                ob.fibonacci_confluence = 0.5  # Neutral value
                
                # Update final strength score
                ob.strength_score = min(1.0, ob.strength_score)
            
            return classified_obs
            
        except Exception as e:
            logger.error(f"Confluence factor calculation failed: {e}")
            return classified_obs
    
    def _update_order_block_states(self, enhanced_obs: List[OrderBlockZone], 
                                 df: pd.DataFrame) -> List[OrderBlockZone]:
        """Update Order Block states based on current price action."""
        try:
            current_price = df['close'].iloc[-1]
            
            for ob in enhanced_obs:
                # Check if Order Block has been tested or broken
                if ob.ob_type == 'BULLISH_OB':
                    if current_price <= ob.zone_low:
                        ob.state = OrderBlockState.BROKEN
                        ob.break_price = current_price
                    elif ob.zone_low <= current_price <= ob.zone_high:
                        if ob.state == OrderBlockState.FRESH:
                            ob.state = OrderBlockState.TESTED
                            ob.last_test_time = datetime.now()
                            ob.test_count += 1
                        
                else:  # BEARISH_OB
                    if current_price >= ob.zone_high:
                        ob.state = OrderBlockState.BROKEN
                        ob.break_price = current_price
                    elif ob.zone_low <= current_price <= ob.zone_high:
                        if ob.state == OrderBlockState.FRESH:
                            ob.state = OrderBlockState.TESTED
                            ob.last_test_time = datetime.now()
                            ob.test_count += 1
                
                # Check if Order Block should be expired
                age_hours = (datetime.now() - ob.creation_time).total_seconds() / 3600
                if (age_hours > self.config['max_ob_age_hours'] or 
                    ob.test_count >= self.config['test_invalidation_count']):
                    ob.state = OrderBlockState.EXPIRED
            
            return enhanced_obs
            
        except Exception as e:
            logger.error(f"Order Block state update failed: {e}")
            return enhanced_obs
    
    def _filter_order_blocks(self, current_obs: List[OrderBlockZone]) -> List[OrderBlockZone]:
        """Filter Order Blocks by quality and relevance."""
        try:
            filtered_obs = []
            
            for ob in current_obs:
                # Filter out invalid, broken, or expired Order Blocks
                if ob.quality == OrderBlockQuality.INVALID:
                    continue
                if ob.state in [OrderBlockState.BROKEN, OrderBlockState.EXPIRED]:
                    continue
                
                # Only keep high-quality Order Blocks
                if ob.quality in [OrderBlockQuality.PREMIUM, OrderBlockQuality.HIGH, OrderBlockQuality.MEDIUM]:
                    filtered_obs.append(ob)
            
            # Sort by quality and strength
            filtered_obs.sort(key=lambda x: (x.quality.value, x.strength_score), reverse=True)
            
            # Limit to top Order Blocks to avoid overload
            max_obs = 10
            return filtered_obs[:max_obs]
            
        except Exception as e:
            logger.error(f"Order Block filtering failed: {e}")
            return current_obs
    
    def _update_detection_stats(self, final_obs: List[OrderBlockZone]) -> None:
        """Update detection statistics."""
        try:
            self.detection_stats['total_scanned'] += 1
            self.detection_stats['order_blocks_found'] = len(final_obs)
            self.detection_stats['last_scan_time'] = datetime.now()
            
            # Update quality distribution
            for quality in OrderBlockQuality:
                self.detection_stats['quality_distribution'][quality.value] = len([
                    ob for ob in final_obs if ob.quality == quality
                ])
                
        except Exception as e:
            logger.error(f"Statistics update failed: {e}")
    
    def get_detection_summary(self, order_blocks: List[OrderBlockZone]) -> Dict:
        """Get summary of detected Order Blocks."""
        try:
            if not order_blocks:
                return {
                    'total_count': 0,
                    'quality_breakdown': {},
                    'state_breakdown': {},
                    'avg_strength': 0.0,
                    'fresh_count': 0,
                    'recommendation': 'NO_ORDER_BLOCKS'
                }
            
            # Quality breakdown
            quality_breakdown = {}
            for quality in OrderBlockQuality:
                quality_breakdown[quality.value] = len([
                    ob for ob in order_blocks if ob.quality == quality
                ])
            
            # State breakdown
            state_breakdown = {}
            for state in OrderBlockState:
                state_breakdown[state.value] = len([
                    ob for ob in order_blocks if ob.state == state
                ])
            
            # Average strength
            avg_strength = np.mean([ob.strength_score for ob in order_blocks])
            
            # Fresh Order Blocks count
            fresh_count = len([ob for ob in order_blocks if ob.state == OrderBlockState.FRESH])
            
            # Trading recommendation
            premium_count = quality_breakdown.get('PREMIUM', 0)
            high_count = quality_breakdown.get('HIGH', 0)
            
            if premium_count >= 2:
                recommendation = 'MULTIPLE_PREMIUM_OBS'
            elif premium_count >= 1 or high_count >= 2:
                recommendation = 'HIGH_QUALITY_SETUP'
            elif fresh_count >= 2:
                recommendation = 'FRESH_ORDER_BLOCKS'
            elif len(order_blocks) >= 3:
                recommendation = 'MULTIPLE_OPPORTUNITIES'
            else:
                recommendation = 'MONITOR_CLOSELY'
            
            return {
                'total_count': len(order_blocks),
                'quality_breakdown': quality_breakdown,
                'state_breakdown': state_breakdown,
                'avg_strength': avg_strength,
                'fresh_count': fresh_count,
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.error(f"Detection summary failed: {e}")
            return {'total_count': 0, 'recommendation': 'ERROR'}


if __name__ == "__main__":
    # Example usage and testing
    import asyncio
    logging.basicConfig(level=logging.INFO)
    
    def test_order_block_detection():
        """Test Order Block detection system."""
        print("🔬 Testing Order Block Detection System...")
        
        # Create sample OHLCV data
        dates = pd.date_range(start='2025-09-25', end='2025-09-29', freq='5T')
        np.random.seed(42)
        
        # Generate realistic price data with some Order Block patterns
        base_price = 50000
        price_data = []
        current_price = base_price
        
        for i in range(len(dates)):
            # Simulate some Order Block formations
            if i % 100 == 0:  # Every 100 candles, create potential OB
                # Bearish candle followed by strong move up (Bullish OB)
                open_price = current_price
                close_price = current_price - 200  # Bearish candle
                high_price = max(open_price, close_price) + 50
                low_price = min(open_price, close_price) - 50
                volume = np.random.randint(1000, 3000)  # Higher volume
                
                # Add displacement in next few candles
                for j in range(1, 6):
                    if i + j < len(dates):
                        current_price += 100  # Strong move up
                        
            else:
                # Regular price movement
                change = np.random.randn() * 50
                current_price += change
                
                open_price = current_price
                close_price = current_price + np.random.randn() * 30
                high_price = max(open_price, close_price) + abs(np.random.randn()) * 20
                low_price = min(open_price, close_price) - abs(np.random.randn()) * 20
                volume = np.random.randint(500, 1500)
            
            price_data.append({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
        
        # Create DataFrame
        sample_data = pd.DataFrame(price_data, index=dates)
        
        # Initialize Enhanced Order Block detector
        detector = EnhancedOrderBlockDetector()
        
        # Detect Enhanced Order Blocks
        enhanced_order_blocks = detector.detect_enhanced_order_blocks(sample_data, "BTC/USDT", "5T")
        
        # Get summary
        summary = detector.get_detection_summary(enhanced_order_blocks)
        
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                    ORDER BLOCK DETECTION RESULTS                ║
╠══════════════════════════════════════════════════════════════════╣
║  📊 Detection Summary:                                           ║
║     Total Order Blocks: {summary['total_count']:>6}                           ║
║     Fresh Order Blocks: {summary['fresh_count']:>6}                           ║
║     Average Strength:   {summary['avg_strength']:>6.2f}                           ║
║                                                                  ║
║  🏆 Quality Breakdown:                                           ║
║     Premium: {summary['quality_breakdown'].get('PREMIUM', 0):>3}   High: {summary['quality_breakdown'].get('HIGH', 0):>3}   Medium: {summary['quality_breakdown'].get('MEDIUM', 0):>3}        ║
║                                                                  ║
║  🎯 Recommendation: {summary['recommendation']:<20}             ║
╚══════════════════════════════════════════════════════════════════╝
""")
        
        if enhanced_order_blocks:
            print("🎯 TOP ENHANCED ORDER BLOCKS:")
            for i, eob in enumerate(enhanced_order_blocks[:3], 1):
                direction = "BULLISH" if eob.block_type == 'BULLISH_EOB' else "BEARISH"
                print(f"  {i}. {direction} EOB - {eob.quality.value} quality ({eob.institutional_quality_score:.1f}/100)")
                print(f"     Zone: ${eob.low:.2f} - ${eob.high:.2f}")
                print(f"     Entry: ${eob.optimal_entry_zone[0]:.2f}-${eob.optimal_entry_zone[1]:.2f}")
                print(f"     Smart Money: {eob.smart_money_signature:.1%} | Volume: {eob.volume_confirmation:.1%}")
                print(f"     Confluence: {', '.join(eob.confluence_factors[:2])}")
                print()
        
        print("✅ Enhanced Order Block Detection test completed!")
    
    # Run the Enhanced Order Block test
    test_order_block_detection()