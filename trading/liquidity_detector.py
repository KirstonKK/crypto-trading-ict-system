#!/usr/bin/env python3
"""
ICT Liquidity Mapping System
============================

Advanced liquidity detection system following ICT methodology for identifying
where institutional smart money hunts retail trader stop losses and entries.

Key Liquidity Concepts:
- Equal Highs/Lows: Areas where retail traders typically place stops
- Psychological Levels: Round numbers that attract retail orders  
- Liquidity Sweeps: When price briefly breaks levels to grab liquidity
- Relative Equal Highs/Lows: Multiple price points at similar levels
- Stop Hunt Patterns: Institutional manipulation to trigger retail stops

Detection Patterns:
1. Equal High/Low Formation → 2. Liquidity Pool Identification →
3. Sweep Detection → 4. Post-Sweep Reaction → 5. Liquidity Status Tracking

Author: GitHub Copilot Trading Algorithm  
Date: September 2025
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)

class LiquidityType(Enum):
    """Types of liquidity zones in ICT methodology."""
    EQUAL_HIGHS = "EQUAL_HIGHS"
    EQUAL_LOWS = "EQUAL_LOWS"
    RELATIVE_EQUAL_HIGHS = "RELATIVE_EQUAL_HIGHS"
    RELATIVE_EQUAL_LOWS = "RELATIVE_EQUAL_LOWS"
    PSYCHOLOGICAL_LEVEL = "PSYCHOLOGICAL_LEVEL"
    WEEKLY_HIGH = "WEEKLY_HIGH"
    WEEKLY_LOW = "WEEKLY_LOW"
    DAILY_HIGH = "DAILY_HIGH"
    DAILY_LOW = "DAILY_LOW"
    SESSION_HIGH = "SESSION_HIGH"
    SESSION_LOW = "SESSION_LOW"
    BUY_SIDE_LIQUIDITY = "BUY_SIDE_LIQUIDITY"    # Above current price
    SELL_SIDE_LIQUIDITY = "SELL_SIDE_LIQUIDITY"   # Below current price

class LiquidityState(Enum):
    """State of liquidity zones."""
    UNTESTED = "UNTESTED"           # Fresh liquidity, not yet swept
    PARTIAL_SWEEP = "PARTIAL_SWEEP" # Partially taken out
    SWEPT = "SWEPT"                 # Fully swept/taken
    DEFENDED = "DEFENDED"           # Price approached but rejected
    EXPIRED = "EXPIRED"             # Too old to be relevant

class LiquidityQuality(Enum):
    """Quality classification of liquidity zones."""
    PREMIUM = "PREMIUM"     # Multiple touches, high volume, institutional interest
    HIGH = "HIGH"           # Clear formation, good volume
    MEDIUM = "MEDIUM"       # Decent formation, average volume
    LOW = "LOW"             # Weak formation, low volume
    INVALID = "INVALID"     # Too messy or unreliable

class SweepPattern(Enum):
    """Types of liquidity sweep patterns."""
    CLEAN_SWEEP = "CLEAN_SWEEP"         # Price cleanly takes out level
    WICK_SWEEP = "WICK_SWEEP"           # Only wicks sweep the level
    GRADUAL_SWEEP = "GRADUAL_SWEEP"     # Slow grinding through level
    EXPLOSIVE_SWEEP = "EXPLOSIVE_SWEEP"  # Fast violent sweep
    FAKE_SWEEP = "FAKE_SWEEP"           # Sweep that immediately fails

@dataclass
class LiquidityTouch:
    """Individual touch/test of a liquidity level."""
    timestamp: datetime
    price: float
    volume: float
    touch_type: str        # 'APPROACH', 'TOUCH', 'PENETRATION', 'SWEEP'
    rejection_strength: float  # 0.0 to 1.0
    distance_to_level: float   # How close price got to level
    follow_through: bool       # Did price continue past level?

@dataclass
class LiquidityZone:
    """ICT Liquidity Zone representation."""
    # Zone identification
    zone_id: str
    zone_type: LiquidityType
    formation_timestamp: datetime
    timeframe: str
    
    # Price levels
    exact_level: float          # Exact liquidity level
    zone_high: float           # High of liquidity zone
    zone_low: float            # Low of liquidity zone
    zone_mid: float            # Midpoint of zone
    tolerance: float           # Acceptable distance for sweep detection
    
    # Formation details
    formation_candles: List[Dict]  # Candles that formed the level
    touch_count: int               # Number of times level was tested
    formation_volume: float        # Volume during formation
    formation_strength: float     # 0.0 to 1.0 strength score
    
    # Liquidity pool analysis
    estimated_stops: float         # Estimated stop losses above/below
    institutional_interest: float  # 0.0 to 1.0 institutional activity
    retail_concentration: float    # 0.0 to 1.0 retail trader concentration
    liquidity_depth: float        # Amount of liquidity available
    
    # State tracking
    state: LiquidityState
    quality: LiquidityQuality
    times_tested: int
    last_test_timestamp: Optional[datetime] = None
    last_test_reaction: Optional[float] = None
    
    # Sweep analysis
    is_swept: bool = False
    sweep_timestamp: Optional[datetime] = None
    sweep_pattern: Optional[SweepPattern] = None
    sweep_volume: Optional[float] = None
    post_sweep_reaction: Optional[float] = None
    
    # Historical tracking
    all_touches: List[LiquidityTouch] = field(default_factory=list)
    daily_tests: Dict[str, int] = field(default_factory=dict)
    
    # ICT context
    market_session: str = ""       # 'ASIA', 'LONDON', 'NY'
    weekly_bias: str = ""          # Weekly trend context
    pd_array_context: str = ""     # Premium/Discount context
    
    # Quality metrics
    accuracy_score: float = 0.0    # How accurately level was respected
    reliability_score: float = 0.0 # Historical reliability
    strength_score: float = 0.0    # Overall strength rating
    
    # Metadata
    notes: Optional[str] = None
    invalidation_level: Optional[float] = None
    next_liquidity_target: Optional[float] = None
    
    def __post_init__(self):
        """Calculate derived values after initialization."""
        if self.zone_mid == 0:
            self.zone_mid = (self.zone_high + self.zone_low) / 2
        
        if self.tolerance == 0:
            # Default tolerance based on zone size
            zone_size = abs(self.zone_high - self.zone_low)
            self.tolerance = max(zone_size * 0.1, self.exact_level * 0.001)  # 10% of zone or 0.1%

@dataclass
class LiquidityMap:
    """Complete liquidity map for a symbol/timeframe."""
    symbol: str
    timeframe: str
    analysis_timestamp: datetime
    
    # Current liquidity zones
    buy_side_liquidity: List[LiquidityZone]    # Above current price
    sell_side_liquidity: List[LiquidityZone]   # Below current price
    psychological_levels: List[LiquidityZone]  # Round number levels
    session_extremes: List[LiquidityZone]      # Session highs/lows
    
    # Sweep analysis
    recent_sweeps: List[LiquidityZone]         # Recently swept zones
    pending_sweeps: List[LiquidityZone]        # Likely next targets
    
    # Market context
    current_price: float
    primary_trend: str                         # 'BULLISH', 'BEARISH', 'CONSOLIDATION'
    liquidity_bias: str                        # 'BUY_SIDE', 'SELL_SIDE', 'NEUTRAL'
    next_target: Optional[LiquidityZone] = None
    
    # Statistics
    total_zones: int = 0
    untested_zones: int = 0
    recently_swept: int = 0
    
    def __post_init__(self):
        """Calculate statistics after initialization."""
        all_zones = (self.buy_side_liquidity + self.sell_side_liquidity + 
                    self.psychological_levels + self.session_extremes)
        
        self.total_zones = len(all_zones)
        self.untested_zones = len([z for z in all_zones if z.state == LiquidityState.UNTESTED])
        
        # Count recently swept (last 24 hours)
        recent_threshold = datetime.now() - timedelta(hours=24)
        self.recently_swept = len([
            z for z in all_zones 
            if z.is_swept and z.sweep_timestamp and z.sweep_timestamp > recent_threshold
        ])

class LiquidityDetector:
    """
    ICT Liquidity Detection and Mapping System.
    
    Identifies where institutional smart money is likely to hunt retail
    stop losses and liquidity pools. Essential for understanding market
    maker behavior and institutional manipulation patterns.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize liquidity detector with ICT parameters."""
        self.config = self._load_default_config()
        if config:
            self.config.update(config)
        
        # Detection parameters
        self.equal_level_tolerance = self.config['equal_level_tolerance']
        self.min_touches_for_liquidity = self.config['min_touches_for_liquidity']
        self.sweep_confirmation_pips = self.config['sweep_confirmation_pips']
        self.max_age_hours = self.config['max_age_hours']
        
        # Quality thresholds
        self.premium_volume_threshold = self.config['premium_volume_threshold']
        self.high_quality_touches = self.config['high_quality_touches']
        self.medium_quality_touches = self.config['medium_quality_touches']
        
        # Psychological level settings
        self.psychological_levels = self.config['psychological_levels']
        self.round_number_precision = self.config['round_number_precision']
        
        # Tracking
        self.detected_zones: Dict[str, List[LiquidityZone]] = {}
        self.sweep_history: List[LiquidityZone] = []
        
        logger.info("ICT Liquidity Detector initialized with institutional parameters")
    
    def _load_default_config(self) -> Dict:
        """Load default ICT liquidity detection configuration."""
        return {
            # Detection sensitivity
            'equal_level_tolerance': 0.002,      # 0.2% tolerance for equal levels
            'min_touches_for_liquidity': 2,      # Minimum touches to form liquidity
            'sweep_confirmation_pips': 5,        # Pips beyond level for sweep confirmation
            'max_age_hours': 168,               # 1 week maximum age for liquidity zones
            
            # Quality classification
            'premium_volume_threshold': 1.5,     # 1.5x average volume for premium
            'high_quality_touches': 3,           # 3+ touches for high quality
            'medium_quality_touches': 2,         # 2+ touches for medium quality
            'min_formation_strength': 0.4,       # Minimum formation strength
            
            # Psychological levels
            'psychological_levels': True,        # Enable psychological level detection
            'round_number_precision': [100, 50, 10, 5, 1],  # Round number levels
            'session_extreme_tracking': True,    # Track session highs/lows
            
            # Sweep detection
            'wick_sweep_minimum': 0.5,          # Minimum wick size for sweep
            'sweep_reaction_threshold': 0.003,   # 0.3% reaction for valid sweep
            'false_sweep_reentry_time': 300,     # 5 minutes for false sweep detection
            
            # Volume analysis
            'volume_confirmation': True,         # Require volume confirmation
            'institutional_volume_multiplier': 2.0,  # 2x volume for institutional interest
            'retail_volume_threshold': 0.8,      # Below average volume = retail
            
            # Timeframe preferences
            'primary_timeframes': ['1h', '4h'],  # Primary timeframes for liquidity
            'execution_timeframes': ['1m', '5m'], # Execution timeframes
            'confirmation_timeframes': ['15m', '1h'], # Confirmation timeframes
        }
    
    def detect_liquidity_zones(self, df: pd.DataFrame, symbol: str, timeframe: str) -> LiquidityMap:
        """
        Detect all liquidity zones on given market data.
        
        Args:
            df: OHLCV DataFrame with price data
            symbol: Trading symbol
            timeframe: Chart timeframe
            
        Returns:
            LiquidityMap: Complete liquidity analysis
        """
        try:
            logger.debug(f"Detecting liquidity zones for {symbol} {timeframe}")
            
            if df.empty or len(df) < 20:
                logger.warning(f"Insufficient data for liquidity detection: {len(df)} candles")
                return self._create_empty_liquidity_map(symbol, timeframe, df['close'].iloc[-1] if not df.empty else 0)
            
            current_price = df['close'].iloc[-1]
            
            # Detect different types of liquidity zones
            equal_highs = self._detect_equal_highs(df, symbol, timeframe)
            equal_lows = self._detect_equal_lows(df, symbol, timeframe)
            psychological_levels = self._detect_psychological_levels(df, symbol, timeframe, current_price)
            session_extremes = self._detect_session_extremes(df, symbol, timeframe)
            
            # Classify zones by position relative to current price
            buy_side_liquidity = []
            sell_side_liquidity = []
            
            all_zones = equal_highs + equal_lows + session_extremes
            
            for zone in all_zones:
                if zone.exact_level > current_price:
                    buy_side_liquidity.append(zone)
                else:
                    sell_side_liquidity.append(zone)
            
            # Update zone states and sweep analysis
            self._update_zone_states(all_zones + psychological_levels, df)
            self._analyze_recent_sweeps(all_zones + psychological_levels, df)
            
            # Determine market bias and next targets
            liquidity_bias = self._determine_liquidity_bias(buy_side_liquidity, sell_side_liquidity, current_price)
            next_target = self._identify_next_liquidity_target(buy_side_liquidity + sell_side_liquidity, current_price)
            
            # Create liquidity map
            liquidity_map = LiquidityMap(
                symbol=symbol,
                timeframe=timeframe,
                analysis_timestamp=datetime.now(),
                buy_side_liquidity=sorted(buy_side_liquidity, key=lambda x: x.exact_level),
                sell_side_liquidity=sorted(sell_side_liquidity, key=lambda x: x.exact_level, reverse=True),
                psychological_levels=psychological_levels,
                session_extremes=session_extremes,
                recent_sweeps=[z for z in all_zones if z.is_swept and self._is_recent_sweep(z)],
                pending_sweeps=self._identify_pending_sweeps(all_zones + psychological_levels),
                current_price=current_price,
                primary_trend=self._determine_primary_trend(df),
                liquidity_bias=liquidity_bias,
                next_target=next_target
            )
            
            # Cache results
            cache_key = f"{symbol}_{timeframe}"
            self.detected_zones[cache_key] = all_zones + psychological_levels
            
            logger.debug(f"Detected {liquidity_map.total_zones} liquidity zones for {symbol}")
            return liquidity_map
            
        except Exception as e:
            logger.error(f"Liquidity zone detection failed for {symbol} {timeframe}: {e}")
            return self._create_empty_liquidity_map(symbol, timeframe, current_price if 'current_price' in locals() else 0)
    
    def _detect_equal_highs(self, df: pd.DataFrame, symbol: str, timeframe: str) -> List[LiquidityZone]:
        """Detect equal highs (resistance levels where retail stops cluster)."""
        try:
            equal_highs = []
            highs = df['high'].values
            volumes = df['volume'].values if 'volume' in df.columns else np.ones(len(df))
            timestamps = pd.to_datetime(df.index).to_pydatetime()
            
            # Find local peaks
            peaks = self._find_local_peaks(highs, prominence=0.002)  # 0.2% prominence
            
            if len(peaks) < 2:
                return equal_highs
            
            # Group peaks by similar price levels
            peak_groups = self._group_similar_levels(
                [(i, highs[i]) for i in peaks], 
                self.equal_level_tolerance
            )
            
            for group in peak_groups:
                if len(group) >= self.min_touches_for_liquidity:
                    # Create liquidity zone for equal highs
                    indices, prices = zip(*group)
                    
                    zone = LiquidityZone(
                        zone_id=f"EH_{symbol}_{timeframe}_{len(equal_highs)}",
                        zone_type=LiquidityType.EQUAL_HIGHS,
                        formation_timestamp=timestamps[indices[0]],
                        timeframe=timeframe,
                        exact_level=np.mean(prices),
                        zone_high=max(prices),
                        zone_low=min(prices),
                        zone_mid=np.mean(prices),
                        tolerance=self.equal_level_tolerance * np.mean(prices),
                        formation_candles=[{
                            'timestamp': timestamps[i],
                            'high': highs[i],
                            'low': df['low'].iloc[i],
                            'volume': volumes[i]
                        } for i in indices],
                        touch_count=len(group),
                        formation_volume=np.mean([volumes[i] for i in indices]),
                        formation_strength=self._calculate_formation_strength(group, volumes, indices),
                        estimated_stops=self._estimate_stop_concentration(prices, 'above'),
                        institutional_interest=self._calculate_institutional_interest(volumes, indices),
                        retail_concentration=self._calculate_retail_concentration(group),
                        liquidity_depth=self._calculate_liquidity_depth(group, volumes, indices),
                        state=LiquidityState.UNTESTED,
                        quality=self._classify_zone_quality(len(group), volumes, indices),
                        times_tested=len(group) - 1,  # Formation doesn't count as test
                        market_session=self._get_market_session(timestamps[indices[0]]),
                        accuracy_score=0.8,  # Default, will be updated with testing
                        reliability_score=0.7,  # Default, will be updated
                        strength_score=self._calculate_formation_strength(group, volumes, indices)
                    )
                    
                    equal_highs.append(zone)
            
            logger.debug(f"Detected {len(equal_highs)} equal high zones")
            return equal_highs
            
        except Exception as e:
            logger.error(f"Equal highs detection failed: {e}")
            return []
    
    def _detect_equal_lows(self, df: pd.DataFrame, symbol: str, timeframe: str) -> List[LiquidityZone]:
        """Detect equal lows (support levels where retail stops cluster)."""
        try:
            equal_lows = []
            lows = df['low'].values
            volumes = df['volume'].values if 'volume' in df.columns else np.ones(len(df))
            timestamps = pd.to_datetime(df.index).to_pydatetime()
            
            # Find local troughs
            troughs = self._find_local_troughs(lows, prominence=0.002)  # 0.2% prominence
            
            if len(troughs) < 2:
                return equal_lows
            
            # Group troughs by similar price levels
            trough_groups = self._group_similar_levels(
                [(i, lows[i]) for i in troughs], 
                self.equal_level_tolerance
            )
            
            for group in trough_groups:
                if len(group) >= self.min_touches_for_liquidity:
                    # Create liquidity zone for equal lows
                    indices, prices = zip(*group)
                    
                    zone = LiquidityZone(
                        zone_id=f"EL_{symbol}_{timeframe}_{len(equal_lows)}",
                        zone_type=LiquidityType.EQUAL_LOWS,
                        formation_timestamp=timestamps[indices[0]],
                        timeframe=timeframe,
                        exact_level=np.mean(prices),
                        zone_high=max(prices),
                        zone_low=min(prices),
                        zone_mid=np.mean(prices),
                        tolerance=self.equal_level_tolerance * np.mean(prices),
                        formation_candles=[{
                            'timestamp': timestamps[i],
                            'high': df['high'].iloc[i],
                            'low': lows[i],
                            'volume': volumes[i]
                        } for i in indices],
                        touch_count=len(group),
                        formation_volume=np.mean([volumes[i] for i in indices]),
                        formation_strength=self._calculate_formation_strength(group, volumes, indices),
                        estimated_stops=self._estimate_stop_concentration(prices, 'below'),
                        institutional_interest=self._calculate_institutional_interest(volumes, indices),
                        retail_concentration=self._calculate_retail_concentration(group),
                        liquidity_depth=self._calculate_liquidity_depth(group, volumes, indices),
                        state=LiquidityState.UNTESTED,
                        quality=self._classify_zone_quality(len(group), volumes, indices),
                        times_tested=len(group) - 1,
                        market_session=self._get_market_session(timestamps[indices[0]]),
                        accuracy_score=0.8,
                        reliability_score=0.7,
                        strength_score=self._calculate_formation_strength(group, volumes, indices)
                    )
                    
                    equal_lows.append(zone)
            
            logger.debug(f"Detected {len(equal_lows)} equal low zones")
            return equal_lows
            
        except Exception as e:
            logger.error(f"Equal lows detection failed: {e}")
            return []
    
    def _detect_psychological_levels(self, df: pd.DataFrame, symbol: str, timeframe: str, current_price: float) -> List[LiquidityZone]:
        """Detect psychological levels (round numbers that attract retail orders)."""
        try:
            if not self.config['psychological_levels']:
                return []
            
            psychological_zones = []
            
            # Generate round number levels around current price
            for precision in self.round_number_precision:
                # Find round levels above and below current price
                current_rounded = round(current_price / precision) * precision
                
                for offset in [-2, -1, 0, 1, 2]:  # Check levels around current price
                    level = current_rounded + (offset * precision)
                    
                    if level <= 0:
                        continue
                    
                    # Check if this level has been significant in the data
                    significance = self._check_psychological_level_significance(df, level)
                    
                    if significance > 0.3:  # 30% significance threshold
                        zone = LiquidityZone(
                            zone_id=f"PSY_{symbol}_{timeframe}_{level}",
                            zone_type=LiquidityType.PSYCHOLOGICAL_LEVEL,
                            formation_timestamp=datetime.now() - timedelta(days=30),  # Historical
                            timeframe=timeframe,
                            exact_level=level,
                            zone_high=level * 1.001,  # 0.1% tolerance
                            zone_low=level * 0.999,
                            zone_mid=level,
                            tolerance=level * 0.002,  # 0.2% tolerance
                            formation_candles=[],  # Psychological levels don't have formation candles
                            touch_count=0,  # Will be calculated
                            formation_volume=0,
                            formation_strength=significance,
                            estimated_stops=self._estimate_psychological_stops(level, current_price),
                            institutional_interest=0.3,  # Moderate institutional interest
                            retail_concentration=0.8,    # High retail concentration
                            liquidity_depth=significance * 1000,  # Arbitrary depth based on significance
                            state=LiquidityState.UNTESTED,
                            quality=self._classify_psychological_quality(significance),
                            times_tested=0,
                            market_session='ANY',
                            accuracy_score=0.6,  # Psychological levels are less accurate
                            reliability_score=significance,
                            strength_score=significance
                        )
                        
                        psychological_zones.append(zone)
            
            # Sort by distance from current price and keep closest ones
            psychological_zones.sort(key=lambda x: abs(x.exact_level - current_price))
            
            logger.debug(f"Detected {len(psychological_zones)} psychological levels")
            return psychological_zones[:10]  # Keep top 10 closest levels
            
        except Exception as e:
            logger.error(f"Psychological levels detection failed: {e}")
            return []
    
    def _detect_session_extremes(self, df: pd.DataFrame, symbol: str, timeframe: str) -> List[LiquidityZone]:
        """Detect session high/low levels that often act as liquidity zones."""
        try:
            if not self.config['session_extreme_tracking']:
                return []
            
            session_zones = []
            
            # Group data by trading sessions (simplified)
            # In real implementation, you'd use proper session times
            session_size = 24 if timeframe in ['1h', '4h'] else 480  # Hours or minutes
            
            for i in range(0, len(df), session_size):
                session_data = df.iloc[i:i+session_size]
                
                if len(session_data) < 10:  # Skip small sessions
                    continue
                
                session_high = session_data['high'].max()
                session_low = session_data['low'].min()
                session_volume = session_data['volume'].mean() if 'volume' in session_data.columns else 100
                
                # Create session high zone
                high_zone = LiquidityZone(
                    zone_id=f"SH_{symbol}_{timeframe}_{i}",
                    zone_type=LiquidityType.SESSION_HIGH,
                    formation_timestamp=pd.to_datetime(session_data.index[0]).to_pydatetime(),
                    timeframe=timeframe,
                    exact_level=session_high,
                    zone_high=session_high * 1.001,
                    zone_low=session_high * 0.999,
                    zone_mid=session_high,
                    tolerance=session_high * 0.002,
                    formation_candles=[],
                    touch_count=1,
                    formation_volume=session_volume,
                    formation_strength=0.6,
                    estimated_stops=session_high * 0.02,  # 2% of level
                    institutional_interest=0.4,
                    retail_concentration=0.6,
                    liquidity_depth=session_volume * 10,
                    state=LiquidityState.UNTESTED,
                    quality=LiquidityQuality.MEDIUM,
                    times_tested=0,
                    market_session=self._get_market_session(pd.to_datetime(session_data.index[0]).to_pydatetime()),
                    accuracy_score=0.7,
                    reliability_score=0.6,
                    strength_score=0.6
                )
                
                # Create session low zone
                low_zone = LiquidityZone(
                    zone_id=f"SL_{symbol}_{timeframe}_{i}",
                    zone_type=LiquidityType.SESSION_LOW,
                    formation_timestamp=pd.to_datetime(session_data.index[0]).to_pydatetime(),
                    timeframe=timeframe,
                    exact_level=session_low,
                    zone_high=session_low * 1.001,
                    zone_low=session_low * 0.999,
                    zone_mid=session_low,
                    tolerance=session_low * 0.002,
                    formation_candles=[],
                    touch_count=1,
                    formation_volume=session_volume,
                    formation_strength=0.6,
                    estimated_stops=session_low * 0.02,
                    institutional_interest=0.4,
                    retail_concentration=0.6,
                    liquidity_depth=session_volume * 10,
                    state=LiquidityState.UNTESTED,
                    quality=LiquidityQuality.MEDIUM,
                    times_tested=0,
                    market_session=self._get_market_session(pd.to_datetime(session_data.index[0]).to_pydatetime()),
                    accuracy_score=0.7,
                    reliability_score=0.6,
                    strength_score=0.6
                )
                
                session_zones.extend([high_zone, low_zone])
            
            # Keep only recent session extremes
            recent_threshold = datetime.now() - timedelta(days=7)
            recent_zones = [z for z in session_zones if z.formation_timestamp > recent_threshold]
            
            logger.debug(f"Detected {len(recent_zones)} session extreme zones")
            return recent_zones
            
        except Exception as e:
            logger.error(f"Session extremes detection failed: {e}")
            return []
    
    def _find_local_peaks(self, data: np.ndarray, prominence: float = 0.002) -> List[int]:
        """Find local peaks in price data."""
        try:
            peaks = []
            
            for i in range(1, len(data) - 1):
                if data[i] > data[i-1] and data[i] > data[i+1]:
                    # Check prominence
                    if data[i] / max(data[i-1], data[i+1]) - 1 >= prominence:
                        peaks.append(i)
            
            return peaks
            
        except Exception as e:
            logger.error(f"Peak finding failed: {e}")
            return []
    
    def _find_local_troughs(self, data: np.ndarray, prominence: float = 0.002) -> List[int]:
        """Find local troughs in price data."""
        try:
            troughs = []
            
            for i in range(1, len(data) - 1):
                if data[i] < data[i-1] and data[i] < data[i+1]:
                    # Check prominence
                    if 1 - data[i] / min(data[i-1], data[i+1]) >= prominence:
                        troughs.append(i)
            
            return troughs
            
        except Exception as e:
            logger.error(f"Trough finding failed: {e}")
            return []
    
    def _group_similar_levels(self, points: List[Tuple[int, float]], tolerance: float) -> List[List[Tuple[int, float]]]:
        """Group points with similar price levels."""
        try:
            if not points:
                return []
            
            # Sort by price
            points.sort(key=lambda x: x[1])
            
            groups = []
            current_group = [points[0]]
            
            for i in range(1, len(points)):
                current_price = points[i][1]
                group_price = current_group[0][1]
                
                # Check if within tolerance
                if abs(current_price - group_price) / group_price <= tolerance:
                    current_group.append(points[i])
                else:
                    groups.append(current_group)
                    current_group = [points[i]]
            
            # Add the last group
            if current_group:
                groups.append(current_group)
            
            return groups
            
        except Exception as e:
            logger.error(f"Level grouping failed: {e}")
            return []
    
    def _calculate_formation_strength(self, group: List[Tuple[int, float]], volumes: np.ndarray, indices: List[int]) -> float:
        """Calculate the strength of liquidity zone formation."""
        try:
            # Base strength from number of touches
            touch_strength = min(len(group) / 5.0, 1.0)  # Max strength at 5 touches
            
            # Volume strength
            group_volume = np.mean([volumes[i] for i in indices])
            avg_volume = np.mean(volumes)
            volume_strength = min(group_volume / avg_volume / 2.0, 1.0)  # Max at 2x average
            
            # Price consistency strength
            prices = [price for _, price in group]
            price_std = np.std(prices) / np.mean(prices)
            consistency_strength = max(0, 1.0 - price_std * 100)  # Lower std = higher strength
            
            # Combined strength
            overall_strength = (touch_strength * 0.4 + volume_strength * 0.3 + consistency_strength * 0.3)
            
            return min(1.0, max(0.0, overall_strength))
            
        except Exception as e:
            logger.error(f"Formation strength calculation failed: {e}")
            return 0.5
    
    def _calculate_institutional_interest(self, volumes: np.ndarray, indices: List[int]) -> float:
        """Calculate institutional interest based on volume patterns."""
        try:
            if len(indices) == 0:
                return 0.0
            
            group_volume = np.mean([volumes[i] for i in indices])
            avg_volume = np.mean(volumes)
            
            # Institutional interest increases with volume
            volume_ratio = group_volume / avg_volume
            
            if volume_ratio > self.institutional_volume_multiplier:
                return min(1.0, volume_ratio / 3.0)  # Max at 3x average
            else:
                return max(0.1, volume_ratio / 2.0)
            
        except Exception as e:
            logger.error(f"Institutional interest calculation failed: {e}")
            return 0.3
    
    def _calculate_retail_concentration(self, group: List[Tuple[int, float]]) -> float:
        """Calculate retail trader concentration at this level."""
        try:
            # More touches generally indicate higher retail concentration
            touch_count = len(group)
            
            if touch_count >= 4:
                return 0.9  # High retail concentration
            elif touch_count == 3:
                return 0.7  # Medium-high
            elif touch_count == 2:
                return 0.5  # Medium
            else:
                return 0.3  # Low
            
        except Exception as e:
            logger.error(f"Retail concentration calculation failed: {e}")
            return 0.5
    
    def _calculate_liquidity_depth(self, group: List[Tuple[int, float]], volumes: np.ndarray, indices: List[int]) -> float:
        """Calculate estimated liquidity depth at this level."""
        try:
            # Liquidity depth based on touches and volume
            touch_multiplier = len(group)
            avg_volume = np.mean([volumes[i] for i in indices])
            
            # Estimated depth in volume units
            depth = touch_multiplier * avg_volume * 10  # Arbitrary scaling
            
            return depth
            
        except Exception as e:
            logger.error(f"Liquidity depth calculation failed: {e}")
            return 1000.0
    
    def _estimate_stop_concentration(self, prices: List[float], direction: str) -> float:
        """Estimate stop loss concentration above/below levels."""
        try:
            avg_price = np.mean(prices)
            
            # Estimate stops as percentage of price level
            if direction == 'above':
                # Buy stops above resistance
                return avg_price * 0.01  # 1% above level
            else:
                # Sell stops below support  
                return avg_price * 0.01  # 1% below level
            
        except Exception as e:
            logger.error(f"Stop concentration estimation failed: {e}")
            return 0.0
    
    def _classify_zone_quality(self, touch_count: int, volumes: np.ndarray, indices: List[int]) -> LiquidityQuality:
        """Classify the quality of a liquidity zone."""
        try:
            # Volume analysis
            group_volume = np.mean([volumes[i] for i in indices]) if indices else 0
            avg_volume = np.mean(volumes)
            volume_ratio = group_volume / avg_volume if avg_volume > 0 else 1
            
            # Quality classification
            if touch_count >= 4 and volume_ratio >= self.premium_volume_threshold:
                return LiquidityQuality.PREMIUM
            elif touch_count >= self.high_quality_touches and volume_ratio >= 1.2:
                return LiquidityQuality.HIGH
            elif touch_count >= self.medium_quality_touches:
                return LiquidityQuality.MEDIUM
            elif touch_count >= 1:
                return LiquidityQuality.LOW
            else:
                return LiquidityQuality.INVALID
                
        except Exception as e:
            logger.error(f"Zone quality classification failed: {e}")
            return LiquidityQuality.LOW
    
    def _check_psychological_level_significance(self, df: pd.DataFrame, level: float) -> float:
        """Check how significant a psychological level has been historically."""
        try:
            tolerance = level * 0.002  # 0.2% tolerance
            
            # Count how many times price touched this level
            touches = 0
            reactions = 0
            
            for i, row in df.iterrows():
                high = row['high']
                low = row['low']
                close = row['close']
                prev_close = df['close'].iloc[max(0, df.index.get_loc(i) - 1)]
                
                # Check if candle touched the level
                if low <= level <= high:
                    touches += 1
                    
                    # Check for reaction (reversal after touch)
                    if abs(close - level) > abs(prev_close - level):
                        reactions += 1
            
            if touches == 0:
                return 0.0
            
            # Significance based on touches and reaction rate
            reaction_rate = reactions / touches
            touch_significance = min(touches / 10.0, 1.0)  # Max significance at 10 touches
            
            return (touch_significance * 0.7 + reaction_rate * 0.3)
            
        except Exception as e:
            logger.error(f"Psychological level significance check failed: {e}")
            return 0.0
    
    def _estimate_psychological_stops(self, level: float, current_price: float) -> float:
        """Estimate stop concentration at psychological levels."""
        try:
            # Round numbers attract more retail stops
            distance_factor = abs(level - current_price) / current_price
            
            # Closer levels have more stops
            if distance_factor < 0.05:  # Within 5%
                return level * 0.02  # 2% of level value
            elif distance_factor < 0.1:  # Within 10%
                return level * 0.015  # 1.5% of level value
            else:
                return level * 0.01  # 1% of level value
                
        except Exception as e:
            logger.error(f"Psychological stops estimation failed: {e}")
            return level * 0.01
    
    def _classify_psychological_quality(self, significance: float) -> LiquidityQuality:
        """Classify psychological level quality based on significance."""
        if significance >= 0.8:
            return LiquidityQuality.PREMIUM
        elif significance >= 0.6:
            return LiquidityQuality.HIGH
        elif significance >= 0.4:
            return LiquidityQuality.MEDIUM
        elif significance >= 0.2:
            return LiquidityQuality.LOW
        else:
            return LiquidityQuality.INVALID
    
    def _get_market_session(self, timestamp: datetime) -> str:
        """Determine market session for timestamp."""
        hour = timestamp.hour
        
        if 8 <= hour <= 16:
            return 'LONDON'
        elif 13 <= hour <= 21:
            return 'NY'
        elif 22 <= hour or hour <= 7:
            return 'ASIA'
        else:
            return 'TRANSITION'
    
    def _update_zone_states(self, zones: List[LiquidityZone], df: pd.DataFrame) -> None:
        """Update the state of all liquidity zones based on recent price action."""
        try:
            for zone in zones:
                self._update_single_zone_state(zone, df)
                
        except Exception as e:
            logger.error(f"Zone state update failed: {e}")
    
    def _update_single_zone_state(self, zone: LiquidityZone, df: pd.DataFrame) -> None:
        """Update state of a single liquidity zone."""
        try:
            current_price = df['close'].iloc[-1]
            
            # Check for sweeps in recent data
            recent_data = df.tail(50)  # Last 50 candles
            
            for i, row in recent_data.iterrows():
                high = row['high']
                low = row['low']
                close = row['close']
                timestamp = pd.to_datetime(i).to_pydatetime()
                
                # Check if zone was swept
                if zone.zone_type in [LiquidityType.EQUAL_HIGHS, LiquidityType.SESSION_HIGH]:
                    # Buy side liquidity sweep (price above level)
                    if high > zone.exact_level + zone.tolerance:
                        if not zone.is_swept:
                            zone.is_swept = True
                            zone.sweep_timestamp = timestamp
                            zone.state = LiquidityState.SWEPT
                            zone.sweep_pattern = self._classify_sweep_pattern(row, zone)
                            zone.sweep_volume = row.get('volume', 0)
                            
                            # Check post-sweep reaction
                            if i < len(df) - 1:
                                next_close = df['close'].iloc[df.index.get_loc(i) + 1]
                                zone.post_sweep_reaction = abs(next_close - close) / close
                
                elif zone.zone_type in [LiquidityType.EQUAL_LOWS, LiquidityType.SESSION_LOW]:
                    # Sell side liquidity sweep (price below level)
                    if low < zone.exact_level - zone.tolerance:
                        if not zone.is_swept:
                            zone.is_swept = True
                            zone.sweep_timestamp = timestamp
                            zone.state = LiquidityState.SWEPT
                            zone.sweep_pattern = self._classify_sweep_pattern(row, zone)
                            zone.sweep_volume = row.get('volume', 0)
                            
                            # Check post-sweep reaction
                            if i < len(df) - 1:
                                next_close = df['close'].iloc[df.index.get_loc(i) + 1]
                                zone.post_sweep_reaction = abs(next_close - close) / close
                
                # Check for approaches and tests
                zone_distance = abs(close - zone.exact_level) / zone.exact_level
                if zone_distance < 0.005:  # Within 0.5%
                    zone.last_test_timestamp = timestamp
                    zone.times_tested += 1
                    
                    # Record the touch
                    touch = LiquidityTouch(
                        timestamp=timestamp,
                        price=close,
                        volume=row.get('volume', 0),
                        touch_type='APPROACH',
                        rejection_strength=0.5,  # Default
                        distance_to_level=zone_distance,
                        follow_through=False
                    )
                    zone.all_touches.append(touch)
            
            # Update zone state based on age
            age_hours = (datetime.now() - zone.formation_timestamp).total_seconds() / 3600
            if age_hours > self.max_age_hours and not zone.is_swept:
                zone.state = LiquidityState.EXPIRED
                
        except Exception as e:
            logger.error(f"Single zone state update failed: {e}")
    
    def _classify_sweep_pattern(self, candle_row: pd.Series, zone: LiquidityZone) -> SweepPattern:
        """Classify the type of sweep pattern."""
        try:
            high = candle_row['high']
            low = candle_row['low']
            open_price = candle_row['open']
            close = candle_row['close']
            
            body_size = abs(close - open_price)
            total_range = high - low
            
            if total_range == 0:
                return SweepPattern.CLEAN_SWEEP
            
            body_ratio = body_size / total_range
            
            # Classify based on candle characteristics
            if body_ratio > 0.7:
                return SweepPattern.CLEAN_SWEEP
            elif body_ratio < 0.3:
                return SweepPattern.WICK_SWEEP
            else:
                # Check volume for explosive moves
                volume = candle_row.get('volume', 0)
                if volume > 0:  # High volume threshold would be better
                    return SweepPattern.EXPLOSIVE_SWEEP
                else:
                    return SweepPattern.GRADUAL_SWEEP
                    
        except Exception as e:
            logger.error(f"Sweep pattern classification failed: {e}")
            return SweepPattern.CLEAN_SWEEP
    
    def _analyze_recent_sweeps(self, zones: List[LiquidityZone], df: pd.DataFrame) -> None:
        """Analyze recent sweeps for patterns and reactions."""
        try:
            recent_threshold = datetime.now() - timedelta(hours=24)
            
            for zone in zones:
                if zone.is_swept and zone.sweep_timestamp and zone.sweep_timestamp > recent_threshold:
                    # Analyze post-sweep price action
                    self._analyze_post_sweep_reaction(zone, df)
                    
        except Exception as e:
            logger.error(f"Recent sweep analysis failed: {e}")
    
    def _analyze_post_sweep_reaction(self, zone: LiquidityZone, df: pd.DataFrame) -> None:
        """Analyze price reaction after a liquidity sweep."""
        try:
            if not zone.sweep_timestamp:
                return
            
            # Find candles after the sweep
            sweep_time = zone.sweep_timestamp
            post_sweep_data = df[pd.to_datetime(df.index) > sweep_time].head(10)
            
            if len(post_sweep_data) < 2:
                return
            
            # Calculate reaction strength
            sweep_price = zone.exact_level
            max_reaction = 0
            
            for _, row in post_sweep_data.iterrows():
                if zone.zone_type in [LiquidityType.EQUAL_HIGHS, LiquidityType.SESSION_HIGH]:
                    # For highs, look for downward reaction
                    reaction = (sweep_price - row['low']) / sweep_price
                else:
                    # For lows, look for upward reaction
                    reaction = (row['high'] - sweep_price) / sweep_price
                
                max_reaction = max(max_reaction, reaction)
            
            zone.post_sweep_reaction = max_reaction
            
            # Classify sweep validity based on reaction
            if max_reaction > self.sweep_reaction_threshold:
                # Good reaction indicates valid sweep
                pass
            else:
                # Poor reaction might indicate false sweep
                zone.sweep_pattern = SweepPattern.FAKE_SWEEP
                
        except Exception as e:
            logger.error(f"Post-sweep reaction analysis failed: {e}")
    
    def _determine_liquidity_bias(self, buy_side: List[LiquidityZone], sell_side: List[LiquidityZone], current_price: float) -> str:
        """Determine overall liquidity bias for the market."""
        try:
            # Count untested zones
            untested_buy_side = len([z for z in buy_side if z.state == LiquidityState.UNTESTED])
            untested_sell_side = len([z for z in sell_side if z.state == LiquidityState.UNTESTED])
            
            # Consider distance to zones
            closest_buy_distance = min([abs(z.exact_level - current_price) / current_price for z in buy_side], default=1.0)
            closest_sell_distance = min([abs(z.exact_level - current_price) / current_price for z in sell_side], default=1.0)
            
            # Bias determination
            if untested_buy_side > untested_sell_side * 1.5:
                return 'BUY_SIDE'
            elif untested_sell_side > untested_buy_side * 1.5:
                return 'SELL_SIDE'
            elif closest_buy_distance < closest_sell_distance * 0.7:
                return 'BUY_SIDE'
            elif closest_sell_distance < closest_buy_distance * 0.7:
                return 'SELL_SIDE'
            else:
                return 'NEUTRAL'
                
        except Exception as e:
            logger.error(f"Liquidity bias determination failed: {e}")
            return 'NEUTRAL'
    
    def _identify_next_liquidity_target(self, all_zones: List[LiquidityZone], current_price: float) -> Optional[LiquidityZone]:
        """Identify the most likely next liquidity target."""
        try:
            # Filter untested zones
            untested_zones = [z for z in all_zones if z.state == LiquidityState.UNTESTED]
            
            if not untested_zones:
                return None
            
            # Score zones by likelihood of being targeted
            scored_zones = []
            
            for zone in untested_zones:
                distance = abs(zone.exact_level - current_price) / current_price
                quality_score = {'PREMIUM': 1.0, 'HIGH': 0.8, 'MEDIUM': 0.6, 'LOW': 0.4, 'INVALID': 0.0}[zone.quality.value]
                
                # Closer zones with higher quality are more likely targets
                score = quality_score / (1 + distance * 10)  # Distance penalty
                
                scored_zones.append((score, zone))
            
            # Return highest scoring zone
            scored_zones.sort(key=lambda x: x[0], reverse=True)
            return scored_zones[0][1] if scored_zones else None
            
        except Exception as e:
            logger.error(f"Next target identification failed: {e}")
            return None
    
    def _identify_pending_sweeps(self, zones: List[LiquidityZone]) -> List[LiquidityZone]:
        """Identify zones likely to be swept soon."""
        try:
            pending = []
            
            for zone in zones:
                if zone.state == LiquidityState.UNTESTED:
                    # Check if zone has been tested recently
                    if zone.last_test_timestamp:
                        time_since_test = (datetime.now() - zone.last_test_timestamp).total_seconds() / 3600
                        
                        if time_since_test < 24:  # Tested within 24 hours
                            pending.append(zone)
                    
                    # High quality zones are more likely to be swept
                    if zone.quality in [LiquidityQuality.PREMIUM, LiquidityQuality.HIGH]:
                        pending.append(zone)
            
            return list(set(pending))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Pending sweeps identification failed: {e}")
            return []
    
    def _determine_primary_trend(self, df: pd.DataFrame) -> str:
        """Determine primary trend from price data."""
        try:
            if len(df) < 20:
                return 'CONSOLIDATION'
            
            # Simple trend determination using recent highs and lows
            recent_data = df.tail(20)
            
            first_half = recent_data.head(10)
            second_half = recent_data.tail(10)
            
            first_avg = (first_half['high'].mean() + first_half['low'].mean()) / 2
            second_avg = (second_half['high'].mean() + second_half['low'].mean()) / 2
            
            change = (second_avg - first_avg) / first_avg
            
            if change > 0.02:  # 2% increase
                return 'BULLISH'
            elif change < -0.02:  # 2% decrease
                return 'BEARISH'
            else:
                return 'CONSOLIDATION'
                
        except Exception as e:
            logger.error(f"Primary trend determination failed: {e}")
            return 'CONSOLIDATION'
    
    def _is_recent_sweep(self, zone: LiquidityZone) -> bool:
        """Check if zone was swept recently."""
        if not zone.is_swept or not zone.sweep_timestamp:
            return False
        
        time_since_sweep = (datetime.now() - zone.sweep_timestamp).total_seconds() / 3600
        return time_since_sweep <= 24  # Within 24 hours
    
    def _create_empty_liquidity_map(self, symbol: str, timeframe: str, current_price: float) -> LiquidityMap:
        """Create empty liquidity map for error cases."""
        return LiquidityMap(
            symbol=symbol,
            timeframe=timeframe,
            analysis_timestamp=datetime.now(),
            buy_side_liquidity=[],
            sell_side_liquidity=[],
            psychological_levels=[],
            session_extremes=[],
            recent_sweeps=[],
            pending_sweeps=[],
            current_price=current_price,
            primary_trend='CONSOLIDATION',
            liquidity_bias='NEUTRAL'
        )
    
    def get_liquidity_summary(self, symbol: str, timeframe: str) -> Dict:
        """Get summary of current liquidity situation."""
        try:
            cache_key = f"{symbol}_{timeframe}"
            
            if cache_key not in self.detected_zones:
                return {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'total_zones': 0,
                    'buy_side_zones': 0,
                    'sell_side_zones': 0,
                    'recent_sweeps': 0,
                    'next_target': None,
                    'liquidity_bias': 'UNKNOWN'
                }
            
            zones = self.detected_zones[cache_key]
            
            # Count zones by type and state
            total_zones = len(zones)
            buy_side = len([z for z in zones if z.exact_level > zones[0].zone_mid])  # Approximate
            sell_side = total_zones - buy_side
            recent_sweeps = len([z for z in zones if self._is_recent_sweep(z)])
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'total_zones': total_zones,
                'buy_side_zones': buy_side,
                'sell_side_zones': sell_side,
                'recent_sweeps': recent_sweeps,
                'untested_zones': len([z for z in zones if z.state == LiquidityState.UNTESTED]),
                'premium_zones': len([z for z in zones if z.quality == LiquidityQuality.PREMIUM]),
                'last_analysis': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Liquidity summary generation failed: {e}")
            return {'error': str(e)}


if __name__ == "__main__":
    # Example usage and testing
    import logging
    logging.basicConfig(level=logging.INFO)
    
    def test_liquidity_detector():
        """Test the liquidity detector with sample data."""
        print("🎯 Testing ICT Liquidity Detector...")
        
        # Create sample data
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=1000, freq='1H')
        
        # Generate sample OHLCV data with some patterns
        price = 50000
        prices = [price]
        
        for i in range(999):
            change = np.random.normal(0, 0.02)  # 2% volatility
            price = price * (1 + change)
            prices.append(price)
        
        # Create DataFrame
        df = pd.DataFrame({
            'open': prices[:-1],
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices[:-1]],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices[:-1]],
            'close': prices[1:],
            'volume': np.random.default_rng(42).uniform(100, 1000, 999)
        }, index=dates[1:])
        
        # Initialize detector
        detector = LiquidityDetector()
        
        # Detect liquidity zones
        liquidity_map = detector.detect_liquidity_zones(df, "BTC/USDT", "1h")
        
        # Print results
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                   LIQUIDITY MAP ANALYSIS                        ║
╠══════════════════════════════════════════════════════════════════╣
║  Symbol:               {liquidity_map.symbol:<20}                ║
║  Timeframe:           {liquidity_map.timeframe:<20}                ║
║  Current Price:       ${liquidity_map.current_price:>10,.2f}     ║
║  Primary Trend:       {liquidity_map.primary_trend:<20}           ║
║  Liquidity Bias:      {liquidity_map.liquidity_bias:<20}          ║
║                                                                  ║
║  Total Zones:         {liquidity_map.total_zones:>6}            ║
║  Buy Side Liquidity:  {len(liquidity_map.buy_side_liquidity):>6}            ║
║  Sell Side Liquidity: {len(liquidity_map.sell_side_liquidity):>6}            ║
║  Psychological:       {len(liquidity_map.psychological_levels):>6}            ║
║  Session Extremes:    {len(liquidity_map.session_extremes):>6}            ║
║                                                                  ║
║  Untested Zones:      {liquidity_map.untested_zones:>6}            ║
║  Recent Sweeps:       {liquidity_map.recently_swept:>6}            ║
║  Pending Sweeps:      {len(liquidity_map.pending_sweeps):>6}            ║
╚══════════════════════════════════════════════════════════════════╝
""")
        
        # Show top liquidity zones
        print("\n🎯 Top Buy Side Liquidity Zones:")
        for i, zone in enumerate(liquidity_map.buy_side_liquidity[:5]):
            print("   {i+1}. ${zone.exact_level:>10,.2f} ({zone.zone_type.value}) - {zone.quality.value} - {zone.state.value}")
        
        print("\n🎯 Top Sell Side Liquidity Zones:")
        for i, zone in enumerate(liquidity_map.sell_side_liquidity[:5]):
            print("   {i+1}. ${zone.exact_level:>10,.2f} ({zone.zone_type.value}) - {zone.quality.value} - {zone.state.value}")
        
        if liquidity_map.next_target:
            print("\n🎯 Next Liquidity Target: ${liquidity_map.next_target.exact_level:,.2f} ({liquidity_map.next_target.zone_type.value})")
        
        # Get summary
        summary = detector.get_liquidity_summary("BTC/USDT", "1h")
        print("\n📊 Liquidity Summary: {summary}")
        
        print("\n✅ Liquidity detector test completed!")
    
    # Run the test
    test_liquidity_detector()