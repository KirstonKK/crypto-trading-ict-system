#!/usr/bin/env python3
"""
ICT Fair Value Gap (FVG) Detection System
========================================

Implements precise Fair Value Gap identification following ICT methodology.
Fair Value Gaps represent inefficiencies in price delivery where institutional
algorithms haven't filled all available liquidity, creating trading opportunities.

ICT Fair Value Gap Rules:
1. Three-candle pattern with unfilled gap in middle candle
2. Candle 1 and Candle 3 must not overlap in specific ranges
3. Volume confirmation on gap creation candle (middle candle)
4. Gap must be significant relative to average true range
5. Fresh gaps (unfilled) have highest priority for reversals

Types of FVGs:
- Bullish FVG: Gap below current price (potential support)
- Bearish FVG: Gap above current price (potential resistance)
- Breaker FVG: Former FVG that becomes opposite after break

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

logger = logging.getLogger(__name__)

class FVGType(Enum):
    """Fair Value Gap type classification."""
    BULLISH_FVG = "BULLISH_FVG"      # Gap below price (support)
    BEARISH_FVG = "BEARISH_FVG"      # Gap above price (resistance) 
    BREAKER_FVG = "BREAKER_FVG"      # Broken FVG that flipped polarity

class FVGState(Enum):
    """Fair Value Gap current state."""
    FRESH = "FRESH"                  # Never touched by price
    PARTIALLY_FILLED = "PARTIALLY_FILLED"  # Price touched but didn't fill completely
    FILLED = "FILLED"                # Completely filled by price
    BREAKER = "BREAKER"              # Broken and now acts as opposite

class FVGQuality(Enum):
    """Fair Value Gap quality classification."""
    PREMIUM = "PREMIUM"              # Perfect formation with all confirmations
    HIGH = "HIGH"                    # Strong formation with most confirmations
    MEDIUM = "MEDIUM"                # Good formation with some confirmations
    LOW = "LOW"                      # Weak formation, few confirmations
    INVALID = "INVALID"              # Doesn't meet minimum criteria

@dataclass
class FVGCandles:
    """Three candles that form a Fair Value Gap."""
    # Before candle (candle 1)
    before_timestamp: datetime
    before_open: float
    before_high: float
    before_low: float
    before_close: float
    before_volume: float
    
    # Gap creation candle (candle 2 - middle)
    gap_timestamp: datetime
    gap_open: float
    gap_high: float
    gap_low: float
    gap_close: float
    gap_volume: float
    
    # After candle (candle 3)
    after_timestamp: datetime
    after_open: float
    after_high: float
    after_low: float
    after_close: float
    after_volume: float
    
    # Optional fields with defaults
    gap_volume_ratio: float = 0.0
    
    # Pattern characteristics
    gap_direction: str = field(init=False)
    gap_efficiency: float = field(init=False)
    institutional_signature: bool = field(init=False)
    
    def __post_init__(self):
        """Calculate derived FVG pattern properties."""
        # Determine gap direction
        if self.gap_close > self.gap_open:
            self.gap_direction = "BULLISH"
        else:
            self.gap_direction = "BEARISH"
        
        # Calculate gap efficiency (how clean the gap formation is)
        gap_body = abs(self.gap_close - self.gap_open)
        gap_range = self.gap_high - self.gap_low
        self.gap_efficiency = gap_body / gap_range if gap_range > 0 else 0
        
        # Institutional signature (high volume on gap candle)
        self.institutional_signature = self.gap_volume_ratio >= 2.0

@dataclass
class FVGZone:
    """Complete Fair Value Gap zone definition."""
    # Core identification
    fvg_candles: FVGCandles
    fvg_type: FVGType
    timeframe: str
    creation_time: datetime
    
    # Gap zone boundaries
    gap_high: float
    gap_low: float
    gap_mid: float
    gap_size: float
    gap_percentage: float           # Size relative to price
    
    # Fill tracking
    fill_percentage: float = 0.0    # How much has been filled (0-100%)
    fill_high: float = 0.0          # Highest price that entered gap
    fill_low: float = 0.0           # Lowest price that entered gap
    first_touch_time: Optional[datetime] = None
    
    # Quality metrics
    quality: FVGQuality = FVGQuality.MEDIUM
    strength_score: float = 0.5
    confluence_factors: List[str] = field(default_factory=list)
    
    # State management
    state: FVGState = FVGState.FRESH
    invalidation_price: Optional[float] = None
    
    # Context and confluence
    higher_tf_alignment: bool = False
    session_context: str = ""
    fibonacci_confluence: float = 0.0
    order_block_confluence: bool = False
    
    # Trading parameters
    optimal_entry: float = 0.0
    suggested_stop_loss: float = 0.0
    suggested_take_profit: float = 0.0
    risk_reward_ratio: float = 0.0

class FVGDetector:
    """
    Advanced Fair Value Gap detection system following ICT methodology.
    
    This detector identifies high-probability FVGs by analyzing:
    1. Three-candle gap patterns
    2. Volume signatures during gap creation
    3. Gap size and significance  
    4. Market context and confluence
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize Fair Value Gap detector."""
        self.config = self._load_default_config()
        if config:
            self.config.update(config)
        
        # Detection statistics
        self.detection_stats = {
            'total_scanned': 0,
            'fvgs_found': 0,
            'bullish_fvgs': 0,
            'bearish_fvgs': 0,
            'quality_distribution': {q.value: 0 for q in FVGQuality},
            'fill_rate': 0.0,
            'last_scan_time': None
        }
        
        logger.info("Fair Value Gap Detector initialized with ICT methodology")
    
    def _load_default_config(self) -> Dict:
        """Load default FVG detection configuration."""
        return {
            # Gap size requirements
            'min_gap_percentage': 0.1,        # 0.1% minimum gap size
            'max_gap_percentage': 2.0,        # 2.0% maximum gap size (too big = manipulation)
            'min_gap_atr_ratio': 0.3,         # Gap must be 30% of ATR minimum
            'max_gap_atr_ratio': 3.0,         # Gap must be less than 3x ATR
            
            # Volume requirements
            'min_volume_ratio': 1.2,          # 1.2x average volume minimum
            'institutional_volume_ratio': 2.5, # 2.5x = institutional signature
            'volume_lookback_periods': 20,     # Periods for volume average
            
            # Pattern validation
            'require_volume_confirmation': True, # Must have volume confirmation
            'min_gap_efficiency': 0.3,        # Minimum gap formation efficiency
            'allow_minor_overlap': True,       # Allow small overlaps in formation
            'overlap_tolerance': 0.05,         # 5% overlap tolerance
            
            # Quality factors
            'fresh_fvg_bonus': 0.4,           # Bonus for unfilled FVGs
            'institutional_volume_bonus': 0.3, # Bonus for high volume
            'session_alignment_bonus': 0.1,    # Bonus for session alignment
            'confluence_bonus': 0.2,          # Bonus for multiple confluences
            
            # Fill tracking
            'partial_fill_threshold': 0.5,    # 50% = partially filled
            'complete_fill_threshold': 0.95,  # 95% = completely filled
            'breaker_threshold': 1.05,        # 105% = becomes breaker
            
            # Age and expiry
            'max_fvg_age_hours': 48,          # 48 hours max relevance
            'optimal_fvg_age_hours': 12,      # 12 hours optimal window
            'fresh_priority_hours': 6,        # First 6 hours = highest priority
            
            # Risk management
            'default_stop_loss_ratio': 0.015, # 1.5% stop loss beyond gap
            'default_take_profit_ratio': 0.03, # 3% take profit (2:1 R:R)
            'max_risk_per_fvg': 0.02,         # 2% max risk per FVG trade
            
            # Crypto-specific adaptations
            'crypto_volatility_multiplier': 1.3, # Adjust for crypto volatility
            'weekend_gap_adjustment': 0.8,    # Reduce weekend gap significance
        }
    
    def detect_fair_value_gaps(self, df: pd.DataFrame, symbol: str, 
                             timeframe: str = "5T") -> List[FVGZone]:
        """
        Detect Fair Value Gaps in price data following ICT methodology.
        
        Args:
            df: OHLCV DataFrame with datetime index
            symbol: Trading pair symbol  
            timeframe: Analysis timeframe
            
        Returns:
            List of detected Fair Value Gap zones
        """
        try:
            logger.info(f"Starting Fair Value Gap detection for {symbol} {timeframe}")
            
            # Prepare data for analysis
            df = self._prepare_data(df)
            
            if len(df) < 30:
                logger.warning(f"Insufficient data for FVG detection: {len(df)} candles")
                return []
            
            # Scan for three-candle FVG patterns
            potential_fvgs = self._scan_for_fvg_patterns(df, symbol, timeframe)
            
            # Validate FVG formations
            validated_fvgs = self._validate_fvg_patterns(potential_fvgs, df)
            
            # Classify FVG quality
            classified_fvgs = self._classify_fvg_quality(validated_fvgs, df)
            
            # Calculate confluence factors
            enhanced_fvgs = self._calculate_fvg_confluence(classified_fvgs, df)
            
            # Update FVG states and fill levels
            current_fvgs = self._update_fvg_states(enhanced_fvgs, df)
            
            # Filter by relevance and quality
            final_fvgs = self._filter_fair_value_gaps(current_fvgs)
            
            # Update detection statistics
            self._update_detection_stats(final_fvgs)
            
            logger.info(f"FVG detection completed: {len(final_fvgs)} high-quality FVGs found")
            return final_fvgs
            
        except Exception as e:
            logger.error(f"Fair Value Gap detection failed for {symbol}: {e}")
            return []
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare OHLCV data for FVG analysis."""
        try:
            # Create a copy to avoid modifying original data
            data = df.copy()
            
            # Ensure proper datetime index
            if not isinstance(data.index, pd.DatetimeIndex):
                if 'timestamp' in data.columns:
                    data.index = pd.to_datetime(data['timestamp'])
                else:
                    data.index = pd.to_datetime(data.index)
            
            # Calculate volume indicators
            volume_periods = self.config['volume_lookback_periods']
            data['volume_ma'] = data['volume'].rolling(window=volume_periods).mean()
            data['volume_ratio'] = data['volume'] / data['volume_ma']
            
            # Calculate ATR for gap size validation
            data['tr'] = np.maximum(
                data['high'] - data['low'],
                np.maximum(
                    abs(data['high'] - data['close'].shift(1)),
                    abs(data['low'] - data['close'].shift(1))
                )
            )
            data['atr'] = data['tr'].rolling(window=14).mean()
            
            # Calculate typical price for gap measurements
            data['typical_price'] = (data['high'] + data['low'] + data['close']) / 3
            
            # Candle characteristics
            data['body_size'] = abs(data['close'] - data['open'])
            data['candle_range'] = data['high'] - data['low']
            data['is_bullish'] = data['close'] > data['open']
            
            return data
            
        except Exception as e:
            logger.error(f"FVG data preparation failed: {e}")
            raise
    
    def _scan_for_fvg_patterns(self, df: pd.DataFrame, symbol: str, 
                             timeframe: str) -> List[FVGZone]:
        """Scan for three-candle Fair Value Gap patterns."""
        try:
            potential_fvgs = []
            
            # Need at least 3 candles for pattern
            for i in range(1, len(df) - 1):
                # Get three consecutive candles
                candle1 = df.iloc[i-1]  # Before candle
                candle2 = df.iloc[i]    # Gap creation candle (middle)
                candle3 = df.iloc[i+1]  # After candle
                
                # Check for bullish FVG pattern
                bullish_fvg = self._check_bullish_fvg_pattern(candle1, candle2, candle3)
                if bullish_fvg:
                    fvg_zone = self._create_fvg_zone(
                        candle1, candle2, candle3, FVGType.BULLISH_FVG, 
                        bullish_fvg, symbol, timeframe
                    )
                    if fvg_zone:
                        potential_fvgs.append(fvg_zone)
                
                # Check for bearish FVG pattern
                bearish_fvg = self._check_bearish_fvg_pattern(candle1, candle2, candle3)
                if bearish_fvg:
                    fvg_zone = self._create_fvg_zone(
                        candle1, candle2, candle3, FVGType.BEARISH_FVG,
                        bearish_fvg, symbol, timeframe
                    )
                    if fvg_zone:
                        potential_fvgs.append(fvg_zone)
            
            logger.debug(f"Found {len(potential_fvgs)} potential Fair Value Gaps")
            return potential_fvgs
            
        except Exception as e:
            logger.error(f"FVG pattern scanning failed: {e}")
            return []
    
    def _check_bullish_fvg_pattern(self, candle1: pd.Series, candle2: pd.Series, 
                                 candle3: pd.Series) -> Optional[Dict]:
        """
        Check for bullish Fair Value Gap pattern.
        
        Bullish FVG Rules:
        1. candle1.high < candle3.low (clear gap between them)
        2. candle2 is the gap creation candle (usually bullish)
        3. Gap size meets minimum requirements
        4. Volume confirmation on candle2
        """
        try:
            # Rule 1: Check for clear gap
            if candle1['high'] >= candle3['low']:
                # Check for minor overlap if allowed
                if self.config['allow_minor_overlap']:
                    overlap = candle1['high'] - candle3['low']
                    overlap_percentage = overlap / candle1['high']
                    if overlap_percentage > self.config['overlap_tolerance']:
                        return None
                else:
                    return None
            
            # Calculate gap characteristics
            gap_high = candle3['low']
            gap_low = candle1['high']
            gap_size = gap_high - gap_low
            gap_percentage = gap_size / candle2['close']
            
            # Rule 2: Gap size validation
            if gap_percentage < self.config['min_gap_percentage'] / 100:
                return None
            if gap_percentage > self.config['max_gap_percentage'] / 100:
                return None
            
            # Rule 3: ATR ratio validation (if ATR available)
            if 'atr' in candle2 and not pd.isna(candle2['atr']):
                atr_ratio = gap_size / candle2['atr']
                if (atr_ratio < self.config['min_gap_atr_ratio'] or 
                    atr_ratio > self.config['max_gap_atr_ratio']):
                    return None
            
            # Rule 4: Volume confirmation
            if self.config['require_volume_confirmation']:
                volume_ratio = candle2.get('volume_ratio', 1.0)
                if volume_ratio < self.config['min_volume_ratio']:
                    return None
            
            return {
                'gap_high': gap_high,
                'gap_low': gap_low,
                'gap_size': gap_size,
                'gap_percentage': gap_percentage,
                'volume_ratio': candle2.get('volume_ratio', 1.0),
                'gap_efficiency': self._calculate_gap_efficiency(candle1, candle2, candle3),
                'institutional_signature': candle2.get('volume_ratio', 1.0) >= self.config['institutional_volume_ratio']
            }
            
        except Exception as e:
            logger.error(f"Bullish FVG pattern check failed: {e}")
            return None
    
    def _check_bearish_fvg_pattern(self, candle1: pd.Series, candle2: pd.Series,
                                 candle3: pd.Series) -> Optional[Dict]:
        """
        Check for bearish Fair Value Gap pattern.
        
        Bearish FVG Rules:
        1. candle1.low > candle3.high (clear gap between them)
        2. candle2 is the gap creation candle (usually bearish)
        3. Gap size meets minimum requirements
        4. Volume confirmation on candle2
        """
        try:
            # Rule 1: Check for clear gap
            if candle1['low'] <= candle3['high']:
                # Check for minor overlap if allowed
                if self.config['allow_minor_overlap']:
                    overlap = candle3['high'] - candle1['low']
                    overlap_percentage = overlap / candle1['low']
                    if overlap_percentage > self.config['overlap_tolerance']:
                        return None
                else:
                    return None
            
            # Calculate gap characteristics
            gap_high = candle1['low']
            gap_low = candle3['high']
            gap_size = gap_high - gap_low
            gap_percentage = gap_size / candle2['close']
            
            # Rule 2: Gap size validation
            if gap_percentage < self.config['min_gap_percentage'] / 100:
                return None
            if gap_percentage > self.config['max_gap_percentage'] / 100:
                return None
            
            # Rule 3: ATR ratio validation (if ATR available)
            if 'atr' in candle2 and not pd.isna(candle2['atr']):
                atr_ratio = gap_size / candle2['atr']
                if (atr_ratio < self.config['min_gap_atr_ratio'] or 
                    atr_ratio > self.config['max_gap_atr_ratio']):
                    return None
            
            # Rule 4: Volume confirmation
            if self.config['require_volume_confirmation']:
                volume_ratio = candle2.get('volume_ratio', 1.0)
                if volume_ratio < self.config['min_volume_ratio']:
                    return None
            
            return {
                'gap_high': gap_high,
                'gap_low': gap_low,
                'gap_size': gap_size,
                'gap_percentage': gap_percentage,
                'volume_ratio': candle2.get('volume_ratio', 1.0),
                'gap_efficiency': self._calculate_gap_efficiency(candle1, candle2, candle3),
                'institutional_signature': candle2.get('volume_ratio', 1.0) >= self.config['institutional_volume_ratio']
            }
            
        except Exception as e:
            logger.error(f"Bearish FVG pattern check failed: {e}")
            return None
    
    def _calculate_gap_efficiency(self, candle1: pd.Series, candle2: pd.Series, 
                                candle3: pd.Series) -> float:
        """Calculate how efficiently the gap was created."""
        try:
            # Gap efficiency = how clean and directional the gap formation is
            
            # Middle candle body efficiency
            candle2_body = abs(candle2['close'] - candle2['open'])
            candle2_range = candle2['high'] - candle2['low']
            body_efficiency = candle2_body / candle2_range if candle2_range > 0 else 0
            
            # Directional consistency
            if candle2['close'] > candle2['open']:  # Bullish gap candle
                directional_score = 1.0 if candle2['close'] > candle1['close'] else 0.5
            else:  # Bearish gap candle
                directional_score = 1.0 if candle2['close'] < candle1['close'] else 0.5
            
            # Overall efficiency
            efficiency = (body_efficiency + directional_score) / 2
            return min(1.0, efficiency)
            
        except Exception as e:
            logger.error(f"Gap efficiency calculation failed: {e}")
            return 0.5
    
    def _create_fvg_zone(self, candle1: pd.Series, candle2: pd.Series, candle3: pd.Series,
                        fvg_type: FVGType, gap_data: Dict, symbol: str, timeframe: str) -> Optional[FVGZone]:
        """Create complete Fair Value Gap zone from pattern data."""
        try:
            # Create FVG candles object
            fvg_candles = FVGCandles(
                before_timestamp=candle1.name,
                before_open=candle1['open'],
                before_high=candle1['high'],
                before_low=candle1['low'],
                before_close=candle1['close'],
                before_volume=candle1['volume'],
                gap_timestamp=candle2.name,
                gap_open=candle2['open'],
                gap_high=candle2['high'],
                gap_low=candle2['low'],
                gap_close=candle2['close'],
                gap_volume=candle2['volume'],
                gap_volume_ratio=gap_data['volume_ratio'],
                after_timestamp=candle3.name,
                after_open=candle3['open'],
                after_high=candle3['high'],
                after_low=candle3['low'],
                after_close=candle3['close'],
                after_volume=candle3['volume']
            )
            
            # Calculate optimal entry and risk levels
            gap_mid = (gap_data['gap_high'] + gap_data['gap_low']) / 2
            
            if fvg_type == FVGType.BULLISH_FVG:
                # For bullish FVG, enter on gap low, target above gap
                optimal_entry = gap_data['gap_low']
                stop_loss = optimal_entry * (1 - self.config['default_stop_loss_ratio'])
                take_profit = optimal_entry * (1 + self.config['default_take_profit_ratio'])
            else:  # BEARISH_FVG
                # For bearish FVG, enter on gap high, target below gap
                optimal_entry = gap_data['gap_high']
                stop_loss = optimal_entry * (1 + self.config['default_stop_loss_ratio'])
                take_profit = optimal_entry * (1 - self.config['default_take_profit_ratio'])
            
            # Calculate risk/reward ratio
            risk = abs(optimal_entry - stop_loss)
            reward = abs(take_profit - optimal_entry)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Create FVG zone
            fvg_zone = FVGZone(
                fvg_candles=fvg_candles,
                fvg_type=fvg_type,
                timeframe=timeframe,
                creation_time=candle2.name,
                gap_high=gap_data['gap_high'],
                gap_low=gap_data['gap_low'],
                gap_mid=gap_mid,
                gap_size=gap_data['gap_size'],
                gap_percentage=gap_data['gap_percentage'],
                quality=FVGQuality.MEDIUM,  # Will be updated in classification
                strength_score=0.5,  # Will be calculated
                state=FVGState.FRESH,
                optimal_entry=optimal_entry,
                suggested_stop_loss=stop_loss,
                suggested_take_profit=take_profit,
                risk_reward_ratio=risk_reward_ratio
            )
            
            return fvg_zone
            
        except Exception as e:
            logger.error(f"FVG zone creation failed: {e}")
            return None
    
    def _validate_fvg_patterns(self, potential_fvgs: List[FVGZone], 
                             df: pd.DataFrame) -> List[FVGZone]:
        """Validate potential FVG patterns against additional criteria."""
        try:
            validated_fvgs = []
            
            for fvg in potential_fvgs:
                # Age validation
                age_hours = (datetime.now() - fvg.creation_time).total_seconds() / 3600
                if age_hours > self.config['max_fvg_age_hours']:
                    continue
                
                # Gap efficiency validation
                gap_efficiency = fvg.fvg_candles.gap_efficiency
                if gap_efficiency < self.config['min_gap_efficiency']:
                    continue
                
                # Risk/reward validation
                if fvg.risk_reward_ratio < 1.0:  # Minimum 1:1 R:R
                    continue
                
                # Size validation relative to price
                if (fvg.gap_percentage < self.config['min_gap_percentage'] / 100 or
                    fvg.gap_percentage > self.config['max_gap_percentage'] / 100):
                    continue
                
                validated_fvgs.append(fvg)
            
            logger.debug(f"Validated {len(validated_fvgs)} Fair Value Gaps")
            return validated_fvgs
            
        except Exception as e:
            logger.error(f"FVG validation failed: {e}")
            return potential_fvgs
    
    def _classify_fvg_quality(self, validated_fvgs: List[FVGZone], 
                            df: pd.DataFrame) -> List[FVGZone]:
        """Classify Fair Value Gap quality based on multiple factors."""
        try:
            for fvg in validated_fvgs:
                quality_score = 0.0
                confluence_factors = []
                
                # Base score from gap size (larger gaps = higher institutional interest)
                gap_score = min(1.0, fvg.gap_percentage * 100)  # Convert to percentage points
                quality_score += gap_score * 0.3
                
                # Volume factor
                if fvg.fvg_candles.institutional_signature:
                    quality_score += self.config['institutional_volume_bonus']
                    confluence_factors.append("Institutional Volume")
                elif fvg.fvg_candles.gap_volume_ratio >= self.config['min_volume_ratio']:
                    quality_score += 0.1
                    confluence_factors.append("Above Average Volume")
                
                # Gap efficiency
                efficiency_score = fvg.fvg_candles.gap_efficiency * 0.2
                quality_score += efficiency_score
                if fvg.fvg_candles.gap_efficiency > 0.7:
                    confluence_factors.append("Clean Gap Formation")
                
                # Freshness bonus
                if fvg.state == FVGState.FRESH:
                    quality_score += self.config['fresh_fvg_bonus']
                    confluence_factors.append("Untested FVG")
                
                # Time factor (fresher = better)
                age_hours = (datetime.now() - fvg.creation_time).total_seconds() / 3600
                if age_hours <= self.config['fresh_priority_hours']:
                    quality_score += 0.2
                    confluence_factors.append("Very Fresh (<6h)")
                elif age_hours <= self.config['optimal_fvg_age_hours']:
                    quality_score += 0.1
                    confluence_factors.append("Fresh (<12h)")
                
                # Risk/reward factor
                if fvg.risk_reward_ratio >= 2.0:
                    quality_score += 0.15
                    confluence_factors.append("Excellent R:R (2:1+)")
                elif fvg.risk_reward_ratio >= 1.5:
                    quality_score += 0.1
                    confluence_factors.append("Good R:R (1.5:1+)")
                
                # Gap direction alignment with momentum
                gap_direction = fvg.fvg_candles.gap_direction
                if fvg.fvg_type == FVGType.BULLISH_FVG and gap_direction == "BULLISH":
                    quality_score += 0.1
                    confluence_factors.append("Direction Alignment")
                elif fvg.fvg_type == FVGType.BEARISH_FVG and gap_direction == "BEARISH":
                    quality_score += 0.1
                    confluence_factors.append("Direction Alignment")
                
                # Normalize quality score
                normalized_score = min(1.0, quality_score)
                
                # Classify quality
                if normalized_score >= 0.8:
                    quality = FVGQuality.PREMIUM
                elif normalized_score >= 0.6:
                    quality = FVGQuality.HIGH
                elif normalized_score >= 0.4:
                    quality = FVGQuality.MEDIUM
                elif normalized_score >= 0.2:
                    quality = FVGQuality.LOW
                else:
                    quality = FVGQuality.INVALID
                
                # Update FVG with quality assessment
                fvg.quality = quality
                fvg.strength_score = normalized_score
                fvg.confluence_factors = confluence_factors
            
            logger.debug(f"FVG quality classification completed")
            return validated_fvgs
            
        except Exception as e:
            logger.error(f"FVG quality classification failed: {e}")
            return validated_fvgs
    
    def _calculate_fvg_confluence(self, classified_fvgs: List[FVGZone], 
                                df: pd.DataFrame) -> List[FVGZone]:
        """Calculate additional confluence factors for FVGs."""
        try:
            for fvg in classified_fvgs:
                # Session alignment (simplified)
                current_hour = datetime.now().hour
                if 8 <= current_hour <= 16:  # London session
                    fvg.session_context = "LONDON"
                    if "Session Alignment" not in fvg.confluence_factors:
                        fvg.confluence_factors.append("London Session")
                        fvg.strength_score += self.config['session_alignment_bonus']
                elif 13 <= current_hour <= 21:  # NY session
                    fvg.session_context = "NY"
                    if "Session Alignment" not in fvg.confluence_factors:
                        fvg.confluence_factors.append("NY Session")
                        fvg.strength_score += self.config['session_alignment_bonus']
                else:
                    fvg.session_context = "ASIA"
                
                # Weekend gap adjustment (crypto trades 24/7 but has quieter periods)
                if fvg.creation_time.weekday() >= 5:  # Saturday/Sunday
                    fvg.strength_score *= self.config['weekend_gap_adjustment']
                
                # Multiple confluence bonus
                if len(fvg.confluence_factors) >= 3:
                    fvg.strength_score += self.config['confluence_bonus']
                    if "Multiple Confluences" not in fvg.confluence_factors:
                        fvg.confluence_factors.append("Multiple Confluences")
                
                # Ensure score doesn't exceed 1.0
                fvg.strength_score = min(1.0, fvg.strength_score)
            
            return classified_fvgs
            
        except Exception as e:
            logger.error(f"FVG confluence calculation failed: {e}")
            return classified_fvgs
    
    def _update_fvg_states(self, enhanced_fvgs: List[FVGZone], 
                         df: pd.DataFrame) -> List[FVGZone]:
        """Update FVG states based on current price action."""
        try:
            current_price = df['close'].iloc[-1]
            
            for fvg in enhanced_fvgs:
                # Check if FVG has been touched or filled
                if fvg.fvg_type == FVGType.BULLISH_FVG:
                    # Bullish FVG - check if price came down to fill gap
                    if current_price <= fvg.gap_high:
                        if fvg.state == FVGState.FRESH:
                            fvg.first_touch_time = datetime.now()
                        
                        # Calculate fill percentage
                        if current_price <= fvg.gap_low:
                            # Completely filled
                            fvg.fill_percentage = 100.0
                            fvg.state = FVGState.FILLED
                        else:
                            # Partially filled
                            fill_amount = fvg.gap_high - current_price
                            fvg.fill_percentage = (fill_amount / fvg.gap_size) * 100
                            
                            if fvg.fill_percentage >= self.config['complete_fill_threshold'] * 100:
                                fvg.state = FVGState.FILLED
                            elif fvg.fill_percentage >= self.config['partial_fill_threshold'] * 100:
                                fvg.state = FVGState.PARTIALLY_FILLED
                        
                        # Track fill levels
                        fvg.fill_low = min(fvg.fill_low or current_price, current_price)
                        
                else:  # BEARISH_FVG
                    # Bearish FVG - check if price came up to fill gap
                    if current_price >= fvg.gap_low:
                        if fvg.state == FVGState.FRESH:
                            fvg.first_touch_time = datetime.now()
                        
                        # Calculate fill percentage
                        if current_price >= fvg.gap_high:
                            # Completely filled
                            fvg.fill_percentage = 100.0
                            fvg.state = FVGState.FILLED
                        else:
                            # Partially filled
                            fill_amount = current_price - fvg.gap_low
                            fvg.fill_percentage = (fill_amount / fvg.gap_size) * 100
                            
                            if fvg.fill_percentage >= self.config['complete_fill_threshold'] * 100:
                                fvg.state = FVGState.FILLED
                            elif fvg.fill_percentage >= self.config['partial_fill_threshold'] * 100:
                                fvg.state = FVGState.PARTIALLY_FILLED
                        
                        # Track fill levels
                        fvg.fill_high = max(fvg.fill_high or current_price, current_price)
                
                # Check for breaker transformation
                if fvg.state == FVGState.FILLED:
                    # If FVG is completely filled and price moves significantly beyond,
                    # it may become a breaker (flipped polarity)
                    if fvg.fvg_type == FVGType.BULLISH_FVG:
                        if current_price < fvg.gap_low * (1 - self.config['breaker_threshold'] / 100):
                            fvg.state = FVGState.BREAKER
                            fvg.fvg_type = FVGType.BREAKER_FVG
                    else:  # BEARISH_FVG
                        if current_price > fvg.gap_high * (1 + self.config['breaker_threshold'] / 100):
                            fvg.state = FVGState.BREAKER
                            fvg.fvg_type = FVGType.BREAKER_FVG
            
            return enhanced_fvgs
            
        except Exception as e:
            logger.error(f"FVG state update failed: {e}")
            return enhanced_fvgs
    
    def _filter_fair_value_gaps(self, current_fvgs: List[FVGZone]) -> List[FVGZone]:
        """Filter FVGs by quality and relevance."""
        try:
            filtered_fvgs = []
            
            for fvg in current_fvgs:
                # Filter out invalid quality FVGs
                if fvg.quality == FVGQuality.INVALID:
                    continue
                
                # Prioritize fresh and partially filled FVGs
                if fvg.state in [FVGState.FRESH, FVGState.PARTIALLY_FILLED]:
                    filtered_fvgs.append(fvg)
                # Include high-quality filled FVGs that might become breakers
                elif fvg.state == FVGState.FILLED and fvg.quality in [FVGQuality.PREMIUM, FVGQuality.HIGH]:
                    filtered_fvgs.append(fvg)
                # Include breaker FVGs
                elif fvg.state == FVGState.BREAKER:
                    filtered_fvgs.append(fvg)
            
            # Sort by quality and freshness
            filtered_fvgs.sort(key=lambda x: (
                x.quality.value,
                x.state == FVGState.FRESH,
                x.strength_score
            ), reverse=True)
            
            # Limit to prevent overload
            max_fvgs = 15
            return filtered_fvgs[:max_fvgs]
            
        except Exception as e:
            logger.error(f"FVG filtering failed: {e}")
            return current_fvgs
    
    def _update_detection_stats(self, final_fvgs: List[FVGZone]) -> None:
        """Update detection statistics."""
        try:
            self.detection_stats['total_scanned'] += 1
            self.detection_stats['fvgs_found'] = len(final_fvgs)
            self.detection_stats['last_scan_time'] = datetime.now()
            
            # Count by type
            self.detection_stats['bullish_fvgs'] = len([
                fvg for fvg in final_fvgs if fvg.fvg_type == FVGType.BULLISH_FVG
            ])
            self.detection_stats['bearish_fvgs'] = len([
                fvg for fvg in final_fvgs if fvg.fvg_type == FVGType.BEARISH_FVG
            ])
            
            # Quality distribution
            for quality in FVGQuality:
                self.detection_stats['quality_distribution'][quality.value] = len([
                    fvg for fvg in final_fvgs if fvg.quality == quality
                ])
            
            # Fill rate calculation
            filled_fvgs = len([fvg for fvg in final_fvgs if fvg.state == FVGState.FILLED])
            total_fvgs = len(final_fvgs)
            self.detection_stats['fill_rate'] = filled_fvgs / max(1, total_fvgs)
            
        except Exception as e:
            logger.error(f"Statistics update failed: {e}")
    
    def get_fvg_summary(self, fair_value_gaps: List[FVGZone]) -> Dict:
        """Get summary of detected Fair Value Gaps."""
        try:
            if not fair_value_gaps:
                return {
                    'total_count': 0,
                    'bullish_count': 0,
                    'bearish_count': 0,
                    'fresh_count': 0,
                    'quality_breakdown': {},
                    'avg_strength': 0.0,
                    'recommendation': 'NO_FVGS'
                }
            
            # Basic counts
            total_count = len(fair_value_gaps)
            bullish_count = len([fvg for fvg in fair_value_gaps if fvg.fvg_type == FVGType.BULLISH_FVG])
            bearish_count = len([fvg for fvg in fair_value_gaps if fvg.fvg_type == FVGType.BEARISH_FVG])
            fresh_count = len([fvg for fvg in fair_value_gaps if fvg.state == FVGState.FRESH])
            
            # Quality breakdown
            quality_breakdown = {}
            for quality in FVGQuality:
                quality_breakdown[quality.value] = len([
                    fvg for fvg in fair_value_gaps if fvg.quality == quality
                ])
            
            # Average strength
            avg_strength = np.mean([fvg.strength_score for fvg in fair_value_gaps])
            
            # Trading recommendation
            premium_count = quality_breakdown.get('PREMIUM', 0)
            high_count = quality_breakdown.get('HIGH', 0)
            
            if premium_count >= 2 and fresh_count >= 1:
                recommendation = 'MULTIPLE_PREMIUM_FVGS'
            elif premium_count >= 1 or (high_count >= 2 and fresh_count >= 1):
                recommendation = 'HIGH_QUALITY_SETUP'
            elif fresh_count >= 3:
                recommendation = 'MULTIPLE_FRESH_FVGS'
            elif bullish_count > 0 and bearish_count > 0:
                recommendation = 'MIXED_DIRECTION_FVGS'
            elif total_count >= 3:
                recommendation = 'MULTIPLE_OPPORTUNITIES'
            else:
                recommendation = 'MONITOR_FILLS'
            
            return {
                'total_count': total_count,
                'bullish_count': bullish_count,
                'bearish_count': bearish_count,
                'fresh_count': fresh_count,
                'quality_breakdown': quality_breakdown,
                'avg_strength': avg_strength,
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.error(f"FVG summary failed: {e}")
            return {'total_count': 0, 'recommendation': 'ERROR'}


if __name__ == "__main__":
    # Example usage and testing
    import asyncio
    logging.basicConfig(level=logging.INFO)
    
    def test_fvg_detection():
        """Test Fair Value Gap detection system."""
        print("🔬 Testing Fair Value Gap Detection System...")
        
        # Create sample OHLCV data with FVG patterns
        dates = pd.date_range(start='2025-09-25', end='2025-09-29', freq='5T')
        np.random.seed(42)
        
        # Generate realistic price data with embedded FVG patterns
        base_price = 50000
        price_data = []
        current_price = base_price
        
        for i in range(len(dates)):
            # Create some FVG patterns every 150 candles
            if i % 150 == 0 and i > 0:
                # Create bullish FVG: bearish candle, gap up candle, bullish continuation
                
                # Candle 1 (before): Bearish
                open1 = current_price
                close1 = current_price - 100
                high1 = open1 + 20
                low1 = close1 - 30
                vol1 = np.random.default_rng(42).integers(800, 1200)
                
                price_data.append({
                    'open': open1, 'high': high1, 'low': low1, 'close': close1, 'volume': vol1
                })
                
                if i + 1 < len(dates):
                    # Candle 2 (gap): Strong bullish with gap
                    open2 = close1 + 150  # Gap up
                    close2 = open2 + 200  # Strong bullish
                    high2 = close2 + 50
                    low2 = open2 - 20
                    vol2 = np.random.default_rng(42).integers(2000, 4000)  # High volume
                    
                    price_data.append({
                        'open': open2, 'high': high2, 'low': low2, 'close': close2, 'volume': vol2
                    })
                    current_price = close2
                    
                    if i + 2 < len(dates):
                        # Candle 3 (after): Continuation
                        open3 = close2
                        close3 = open3 + 100
                        high3 = close3 + 30
                        low3 = open3 - 10
                        vol3 = np.random.default_rng(42).integers(1200, 1800)
                        
                        price_data.append({
                            'open': open3, 'high': high3, 'low': low3, 'close': close3, 'volume': vol3
                        })
                        current_price = close3
                        
                        # Skip next 2 iterations since we added them manually
                        continue
            
            # Regular price movement
            change = np.random.randn() * 30
            current_price += change
            
            open_price = current_price
            close_price = current_price + np.random.randn() * 50
            high_price = max(open_price, close_price) + abs(np.random.randn()) * 25
            low_price = min(open_price, close_price) - abs(np.random.randn()) * 25
            volume = np.random.default_rng(42).integers(600, 1400)
            
            price_data.append({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
        
        # Ensure we have the right number of records
        if len(price_data) > len(dates):
            price_data = price_data[:len(dates)]
        elif len(price_data) < len(dates):
            # Pad with last values if needed
            while len(price_data) < len(dates):
                price_data.append(price_data[-1].copy())
        
        # Create DataFrame
        sample_data = pd.DataFrame(price_data, index=dates[:len(price_data)])
        
        # Initialize detector
        detector = FVGDetector()
        
        # Detect Fair Value Gaps
        fair_value_gaps = detector.detect_fair_value_gaps(sample_data, "BTC/USDT", "5T")
        
        # Get summary
        summary = detector.get_fvg_summary(fair_value_gaps)
        
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                 FAIR VALUE GAP DETECTION RESULTS                ║
╠══════════════════════════════════════════════════════════════════╣
║  📊 Detection Summary:                                           ║
║     Total FVGs:         {summary['total_count']:>6}                           ║
║     Bullish FVGs:       {summary['bullish_count']:>6}                           ║
║     Bearish FVGs:       {summary['bearish_count']:>6}                           ║
║     Fresh FVGs:         {summary['fresh_count']:>6}                           ║
║     Average Strength:   {summary['avg_strength']:>6.2f}                           ║
║                                                                  ║
║  🏆 Quality Breakdown:                                           ║
║     Premium: {summary['quality_breakdown'].get('PREMIUM', 0):>3}   High: {summary['quality_breakdown'].get('HIGH', 0):>3}   Medium: {summary['quality_breakdown'].get('MEDIUM', 0):>3}        ║
║                                                                  ║
║  🎯 Recommendation: {summary['recommendation']:<20}             ║
╚══════════════════════════════════════════════════════════════════╝
""")
        
        if fair_value_gaps:
            print("🎯 TOP FAIR VALUE GAPS:")
            for i, fvg in enumerate(fair_value_gaps[:3], 1):
                fvg_direction = "BULLISH" if fvg.fvg_type == FVGType.BULLISH_FVG else "BEARISH"
                print("  {i}. {fvg_direction} FVG - {fvg.quality.value} quality ({fvg.strength_score:.2f})")
                print("     Gap: ${fvg.gap_low:.2f} - ${fvg.gap_high:.2f} ({fvg.gap_percentage*100:.3f}%)")
                print("     State: {fvg.state.value}, Fill: {fvg.fill_percentage:.1f}%")
                print("     Entry: ${fvg.optimal_entry:.2f}, R:R = {fvg.risk_reward_ratio:.1f}")
                print("     Confluence: {', '.join(fvg.confluence_factors[:2])}")
                print()
        
        print("✅ Fair Value Gap Detection test completed!")
    
    # Run the test
    test_fvg_detection()