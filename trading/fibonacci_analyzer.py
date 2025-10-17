#!/usr/bin/env python3
"""
ICT Fibonacci Confluence Analysis System
========================================

Advanced Fibonacci analysis following ICT methodology for institutional
trading confluence. Focuses on the critical 79% Fibonacci level and
other key institutional retracement levels for optimal entry points.

Key ICT Fibonacci Concepts:
- 79% Fibonacci Level: Primary institutional retracement target
- Optimal Trade Entry (OTE): 62%-79% retracement zone for entries
- Fibonacci Extensions: Target levels for institutional profit taking
- Premium vs Discount Arrays: Market structure context for Fibonacci
- Confluence Zones: Where Fibonacci aligns with Order Blocks/FVGs

ICT Fibonacci Levels (in priority order):
1. 79% (0.79) - Primary institutional retracement
2. 70.5% (0.705) - Secondary institutional level  
3. 62% (0.618) - Golden ratio retracement
4. 50% (0.5) - Equilibrium level
5. 38.2% (0.382) - Shallow retracement
6. 23.6% (0.236) - Minor retracement

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

class FibonacciType(Enum):
    """Types of Fibonacci analysis in ICT methodology."""
    RETRACEMENT = "RETRACEMENT"           # Pullback measurement
    EXTENSION = "EXTENSION"               # Projection measurement
    EXPANSION = "EXPANSION"               # Full move projection
    TIME_FIBONACCI = "TIME_FIBONACCI"     # Time-based Fibonacci

class FibonacciLevel(Enum):
    """ICT Fibonacci levels in order of importance."""
    LEVEL_79 = 0.79          # Primary ICT level
    LEVEL_705 = 0.705        # Secondary ICT level
    LEVEL_618 = 0.618        # Golden ratio
    LEVEL_50 = 0.5           # Equilibrium
    LEVEL_382 = 0.382        # Shallow retracement
    LEVEL_236 = 0.236        # Minor retracement
    LEVEL_127 = 1.27         # Extension level
    LEVEL_162 = 1.618        # Golden extension
    LEVEL_200 = 2.0          # Double extension
    LEVEL_272 = 2.718        # Institutional extension

class MarketArray(Enum):
    """Market array context for Fibonacci analysis."""
    PREMIUM = "PREMIUM"       # Above 50% (institutional selling zone)
    DISCOUNT = "DISCOUNT"     # Below 50% (institutional buying zone)
    EQUILIBRIUM = "EQUILIBRIUM"  # At or near 50%

class FibonacciQuality(Enum):
    """Quality classification of Fibonacci setups."""
    PREMIUM = "PREMIUM"       # Perfect ICT setup with multiple confluences
    HIGH = "HIGH"            # Strong setup with good confluence
    MEDIUM = "MEDIUM"        # Decent setup with some confluence
    LOW = "LOW"              # Weak setup with minimal confluence
    INVALID = "INVALID"      # Poor setup not worth trading

@dataclass
class FibonacciRetracement:
    """ICT Fibonacci retracement analysis."""
    # Measurement points
    swing_high: float
    swing_low: float
    current_price: float
    retracement_percentage: float
    
    # Key levels
    level_79: float          # Primary ICT level
    level_705: float         # Secondary ICT level
    level_618: float         # Golden ratio
    level_50: float          # Equilibrium
    level_382: float         # Shallow level
    level_236: float         # Minor level
    
    # ICT context
    market_array: MarketArray
    ote_zone_high: float     # Optimal Trade Entry high (79%)
    ote_zone_low: float      # Optimal Trade Entry low (62%)
    is_in_ote: bool         # Is current price in OTE zone?
    
    # Confluence analysis
    order_block_confluence: List[str] = field(default_factory=list)
    fvg_confluence: List[str] = field(default_factory=list)
    liquidity_confluence: List[str] = field(default_factory=list)
    
    # Quality metrics
    setup_quality: FibonacciQuality = FibonacciQuality.MEDIUM
    confluence_score: float = 0.0
    institutional_probability: float = 0.0

@dataclass
class FibonacciExtension:
    """ICT Fibonacci extension for target analysis."""
    # Base measurement
    base_swing_low: float
    base_swing_high: float
    retracement_level: float
    
    # Extension targets
    level_127: float         # 127% extension
    level_162: float         # Golden extension (161.8%)
    level_200: float         # 200% extension
    level_272: float         # Institutional extension (271.8%)
    
    # ICT target context
    primary_target: float    # Most likely institutional target
    secondary_target: float  # Secondary institutional target
    final_target: float      # Final institutional target
    
    # Confluence
    target_confluences: Dict[float, List[str]] = field(default_factory=dict)

@dataclass
class FibonacciZone:
    """Complete Fibonacci analysis zone."""
    zone_id: str
    zone_type: FibonacciType
    formation_timestamp: datetime
    timeframe: str
    
    # Price structure
    zone_high: float
    zone_low: float
    zone_mid: float
    fibonacci_level: float   # Which Fib level (0.79, 0.618, etc.)
    
    # ICT analysis
    retracement: Optional[FibonacciRetracement]
    extension: Optional[FibonacciExtension]
    market_context: MarketArray
    
    # Confluence factors
    order_block_alignment: bool = False
    fvg_alignment: bool = False
    liquidity_alignment: bool = False
    structure_alignment: bool = False
    
    # Quality and scoring
    quality: FibonacciQuality = FibonacciQuality.MEDIUM
    confluence_score: float = 0.0
    institutional_interest: float = 0.0
    
    # State tracking
    is_active: bool = True
    times_tested: int = 0
    last_test_timestamp: Optional[datetime] = None
    
    # Metadata
    notes: Optional[str] = None
    invalidation_level: Optional[float] = None

class ICTFibonacciAnalyzer:
    """
    ICT Fibonacci Analysis Engine for institutional trading confluence.
    
    Implements advanced Fibonacci analysis following ICT methodology,
    focusing on the 79% level and Optimal Trade Entry zones for
    high-probability institutional setups.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize ICT Fibonacci analyzer."""
        self.config = self._load_default_config()
        if config:
            self.config.update(config)
        
        # ICT Fibonacci levels (in priority order)
        self.ict_levels = [
            FibonacciLevel.LEVEL_79,    # Primary ICT level
            FibonacciLevel.LEVEL_705,   # Secondary ICT level
            FibonacciLevel.LEVEL_618,   # Golden ratio
            FibonacciLevel.LEVEL_50,    # Equilibrium
            FibonacciLevel.LEVEL_382,   # Shallow retracement
            FibonacciLevel.LEVEL_236    # Minor retracement
        ]
        
        # Extension levels for targets
        self.extension_levels = [
            FibonacciLevel.LEVEL_127,   # 127% extension
            FibonacciLevel.LEVEL_162,   # Golden extension
            FibonacciLevel.LEVEL_200,   # 200% extension
            FibonacciLevel.LEVEL_272    # Institutional extension
        ]
        
        # Analysis cache
        self.fibonacci_cache: Dict[str, List[FibonacciZone]] = {}
        
        logger.info("ICT Fibonacci Analyzer initialized with institutional methodology")
    
    def _load_default_config(self) -> Dict:
        """Load default ICT Fibonacci configuration."""
        return {
            # Level priorities and tolerances
            'primary_level_79': True,           # Enable 79% level analysis
            'secondary_level_705': True,        # Enable 70.5% level analysis
            'golden_ratio_618': True,           # Enable 61.8% analysis
            'equilibrium_50': True,             # Enable 50% analysis
            'level_tolerance': 0.005,           # 0.5% tolerance for level touches
            
            # OTE (Optimal Trade Entry) zone settings
            'ote_zone_enabled': True,           # Enable OTE zone analysis
            'ote_high_level': 0.79,            # OTE zone high (79%)
            'ote_low_level': 0.618,            # OTE zone low (61.8%)
            'ote_confluence_bonus': 0.2,        # 20% bonus for OTE entries
            
            # Premium/Discount array analysis
            'premium_discount_analysis': True,   # Enable P/D array analysis
            'premium_threshold': 0.62,          # Above 62% = premium
            'discount_threshold': 0.38,         # Below 38% = discount
            
            # Confluence requirements
            'min_confluence_score': 0.6,        # 60% minimum confluence
            'order_block_confluence_weight': 0.3, # 30% weight for OB confluence
            'fvg_confluence_weight': 0.25,      # 25% weight for FVG confluence
            'liquidity_confluence_weight': 0.25, # 25% weight for liquidity
            'structure_confluence_weight': 0.2,  # 20% weight for structure
            
            # Swing identification
            'min_swing_size': 0.02,            # 2% minimum swing size
            'swing_lookback_periods': 20,       # Periods to look back for swings
            'swing_confirmation_periods': 3,    # Confirmation periods for swing
            
            # Extension analysis
            'enable_extensions': True,          # Enable extension analysis
            'primary_extension_127': True,      # Use 127% as primary target
            'golden_extension_162': True,       # Use 161.8% as secondary target
            'institutional_extension_272': True, # Use 271.8% for final targets
            
            # Quality classification
            'premium_confluence_threshold': 0.8,  # 80% for premium quality
            'high_confluence_threshold': 0.7,     # 70% for high quality
            'medium_confluence_threshold': 0.5,   # 50% for medium quality
            
            # Time-based analysis
            'enable_time_fibonacci': False,     # Disable time Fib for now
            'time_confluence_weight': 0.1,      # 10% weight for time confluence
        }
    
    def analyze_fibonacci_confluence(self, df: pd.DataFrame, symbol: str, timeframe: str,
                                   order_blocks: Optional[List] = None,
                                   fair_value_gaps: Optional[List] = None,
                                   liquidity_zones: Optional[List] = None) -> List[FibonacciZone]:
        """
        Analyze Fibonacci confluence with ICT methodology.
        
        Args:
            df: OHLCV DataFrame
            symbol: Trading symbol
            timeframe: Chart timeframe
            order_blocks: List of Order Block zones for confluence
            fair_value_gaps: List of FVG zones for confluence
            liquidity_zones: List of liquidity zones for confluence
            
        Returns:
            List of FibonacciZone objects with confluence analysis
        """
        try:
            logger.debug(f"Analyzing Fibonacci confluence for {symbol} {timeframe}")
            
            if df.empty or len(df) < 50:
                logger.warning(f"Insufficient data for Fibonacci analysis: {len(df)} candles")
                return []
            
            fibonacci_zones = []
            
            # Identify significant swings for Fibonacci analysis
            swings = self._identify_significant_swings(df)
            
            if len(swings) < 2:
                logger.debug("Insufficient swings for Fibonacci analysis")
                return []
            
            # Analyze each swing for Fibonacci opportunities
            for i in range(len(swings) - 1):
                swing_low = swings[i]
                swing_high = swings[i + 1]
                
                # Create retracement analysis
                retracement = self._create_fibonacci_retracement(
                    df, swing_low, swing_high, symbol, timeframe
                )
                
                if retracement:
                    # Create Fibonacci zones for key levels
                    fib_zones = self._create_fibonacci_zones_from_retracement(
                        retracement, symbol, timeframe, df
                    )
                    
                    # Add confluence analysis
                    self._add_confluence_analysis(
                        fib_zones, order_blocks, fair_value_gaps, liquidity_zones
                    )
                    
                    fibonacci_zones.extend(fib_zones)
                
                # Create extension analysis if we have a retracement
                if len(swings) > i + 2:
                    next_swing = swings[i + 2]
                    extension = self._create_fibonacci_extension(
                        swing_low, swing_high, next_swing, symbol, timeframe
                    )
                    
                    if extension:
                        ext_zones = self._create_extension_zones(
                            extension, symbol, timeframe, df
                        )
                        fibonacci_zones.extend(ext_zones)
            
            # Filter and rank zones by quality
            quality_zones = self._filter_and_rank_fibonacci_zones(fibonacci_zones)
            
            # Cache results
            cache_key = f"{symbol}_{timeframe}"
            self.fibonacci_cache[cache_key] = quality_zones
            
            logger.debug(f"Created {len(quality_zones)} quality Fibonacci zones")
            return quality_zones
            
        except Exception as e:
            logger.error(f"Fibonacci confluence analysis failed: {e}")
            return []
    
    def _identify_significant_swings(self, df: pd.DataFrame) -> List[Dict]:
        """Identify significant swing highs and lows for Fibonacci analysis."""
        try:
            swings = []
            highs = df['high'].values
            lows = df['low'].values
            timestamps = pd.to_datetime(df.index).to_pydatetime()
            
            min_swing_points = int(self.config['swing_confirmation_periods'])
            min_swing_size = self.config['min_swing_size']
            
            # Find swing highs
            for i in range(min_swing_points, len(highs) - min_swing_points):
                is_swing_high = True
                current_high = highs[i]
                
                # Check if it's higher than surrounding candles
                for j in range(1, min_swing_points + 1):
                    if (current_high <= highs[i-j] or current_high <= highs[i+j]):
                        is_swing_high = False
                        break
                
                if is_swing_high:
                    # Check if swing is significant enough
                    nearby_low = min(lows[max(0, i-10):min(len(lows), i+10)])
                    if (current_high - nearby_low) / nearby_low >= min_swing_size:
                        swings.append({
                            'type': 'HIGH',
                            'price': current_high,
                            'index': i,
                            'timestamp': timestamps[i]
                        })
            
            # Find swing lows
            for i in range(min_swing_points, len(lows) - min_swing_points):
                is_swing_low = True
                current_low = lows[i]
                
                # Check if it's lower than surrounding candles
                for j in range(1, min_swing_points + 1):
                    if (current_low >= lows[i-j] or current_low >= lows[i+j]):
                        is_swing_low = False
                        break
                
                if is_swing_low:
                    # Check if swing is significant enough
                    nearby_high = max(highs[max(0, i-10):min(len(highs), i+10)])
                    if (nearby_high - current_low) / current_low >= min_swing_size:
                        swings.append({
                            'type': 'LOW',
                            'price': current_low,
                            'index': i,
                            'timestamp': timestamps[i]
                        })
            
            # Sort swings by timestamp
            swings.sort(key=lambda x: x['timestamp'])
            
            logger.debug(f"Identified {len(swings)} significant swings")
            return swings
            
        except Exception as e:
            logger.error(f"Swing identification failed: {e}")
            return []
    
    def _create_fibonacci_retracement(self, df: pd.DataFrame, swing_low: Dict, 
                                    swing_high: Dict, symbol: str, timeframe: str) -> Optional[FibonacciRetracement]:
        """Create Fibonacci retracement analysis from swing points."""
        try:
            high_price = swing_high['price']
            low_price = swing_low['price']
            current_price = df['close'].iloc[-1]
            
            # Calculate retracement levels
            price_range = high_price - low_price
            
            if price_range <= 0:
                return None
            
            # Calculate key Fibonacci levels
            level_79 = high_price - (price_range * 0.79)
            level_705 = high_price - (price_range * 0.705)
            level_618 = high_price - (price_range * 0.618)
            level_50 = high_price - (price_range * 0.5)
            level_382 = high_price - (price_range * 0.382)
            level_236 = high_price - (price_range * 0.236)
            
            # Calculate current retracement percentage
            if current_price <= high_price:
                retracement_pct = (high_price - current_price) / price_range
            else:
                retracement_pct = 0.0  # Extension territory
            
            # Determine market array context
            if retracement_pct < 0.38:
                market_array = MarketArray.PREMIUM
            elif retracement_pct > 0.62:
                market_array = MarketArray.DISCOUNT
            else:
                market_array = MarketArray.EQUILIBRIUM
            
            # OTE zone analysis
            ote_high = level_79
            ote_low = level_618
            is_in_ote = ote_low <= current_price <= ote_high
            
            retracement = FibonacciRetracement(
                swing_high=high_price,
                swing_low=low_price,
                current_price=current_price,
                retracement_percentage=retracement_pct,
                level_79=level_79,
                level_705=level_705,
                level_618=level_618,
                level_50=level_50,
                level_382=level_382,
                level_236=level_236,
                market_array=market_array,
                ote_zone_high=ote_high,
                ote_zone_low=ote_low,
                is_in_ote=is_in_ote,
                confluence_score=0.5,  # Base score, will be updated
                institutional_probability=0.6 if is_in_ote else 0.4
            )
            
            return retracement
            
        except Exception as e:
            logger.error(f"Fibonacci retracement creation failed: {e}")
            return None
    
    def _create_fibonacci_zones_from_retracement(self, retracement: FibonacciRetracement,
                                               symbol: str, timeframe: str, df: pd.DataFrame) -> List[FibonacciZone]:
        """Create Fibonacci zones from retracement analysis."""
        try:
            zones = []
            current_time = datetime.now()
            
            # Create zones for key ICT levels
            ict_levels = [
                ('79%', retracement.level_79, FibonacciLevel.LEVEL_79),
                ('70.5%', retracement.level_705, FibonacciLevel.LEVEL_705),
                ('61.8%', retracement.level_618, FibonacciLevel.LEVEL_618),
                ('50%', retracement.level_50, FibonacciLevel.LEVEL_50),
                ('38.2%', retracement.level_382, FibonacciLevel.LEVEL_382),
                ('23.6%', retracement.level_236, FibonacciLevel.LEVEL_236)
            ]
            
            for level_name, level_price, fib_level in ict_levels:
                # Create tolerance zone around level
                tolerance = level_price * self.config['level_tolerance']
                
                zone = FibonacciZone(
                    zone_id=f"FIB_{symbol}_{timeframe}_{level_name}_{len(zones)}",
                    zone_type=FibonacciType.RETRACEMENT,
                    formation_timestamp=current_time,
                    timeframe=timeframe,
                    zone_high=level_price + tolerance,
                    zone_low=level_price - tolerance,
                    zone_mid=level_price,
                    fibonacci_level=fib_level.value,
                    retracement=retracement,
                    extension=None,
                    market_context=retracement.market_array,
                    confluence_score=0.4,  # Base score
                    institutional_interest=self._calculate_level_institutional_interest(fib_level, retracement)
                )
                
                # Set quality based on ICT level importance
                if fib_level == FibonacciLevel.LEVEL_79:
                    zone.quality = FibonacciQuality.PREMIUM
                    zone.confluence_score = 0.7
                elif fib_level in [FibonacciLevel.LEVEL_705, FibonacciLevel.LEVEL_618]:
                    zone.quality = FibonacciQuality.HIGH
                    zone.confluence_score = 0.6
                elif fib_level == FibonacciLevel.LEVEL_50:
                    zone.quality = FibonacciQuality.MEDIUM
                    zone.confluence_score = 0.5
                else:
                    zone.quality = FibonacciQuality.LOW
                    zone.confluence_score = 0.4
                
                zones.append(zone)
            
            return zones
            
        except Exception as e:
            logger.error(f"Fibonacci zone creation failed: {e}")
            return []
    
    def _create_fibonacci_extension(self, swing_low: Dict, swing_high: Dict, 
                                  retracement_point: Dict, symbol: str, timeframe: str) -> Optional[FibonacciExtension]:
        """Create Fibonacci extension analysis for targets."""
        try:
            base_low = swing_low['price']
            base_high = swing_high['price']
            retracement_level = retracement_point['price']
            
            # Calculate base range
            base_range = base_high - base_low
            
            if base_range <= 0:
                return None
            
            # Calculate extension levels from retracement point
            if swing_low['timestamp'] < swing_high['timestamp']:
                # Bullish extension (up from retracement)
                level_127 = retracement_level + (base_range * 1.27)
                level_162 = retracement_level + (base_range * 1.618)
                level_200 = retracement_level + (base_range * 2.0)
                level_272 = retracement_level + (base_range * 2.718)
            else:
                # Bearish extension (down from retracement)
                level_127 = retracement_level - (base_range * 1.27)
                level_162 = retracement_level - (base_range * 1.618)
                level_200 = retracement_level - (base_range * 2.0)
                level_272 = retracement_level - (base_range * 2.718)
            
            extension = FibonacciExtension(
                base_swing_low=base_low,
                base_swing_high=base_high,
                retracement_level=retracement_level,
                level_127=level_127,
                level_162=level_162,
                level_200=level_200,
                level_272=level_272,
                primary_target=level_127,      # ICT prefers 127% for primary target
                secondary_target=level_162,    # Golden extension for secondary
                final_target=level_272         # Institutional final target
            )
            
            return extension
            
        except Exception as e:
            logger.error(f"Fibonacci extension creation failed: {e}")
            return None
    
    def _create_extension_zones(self, extension: FibonacciExtension, symbol: str, 
                              timeframe: str, df: pd.DataFrame) -> List[FibonacciZone]:
        """Create zones for Fibonacci extension levels."""
        try:
            zones = []
            current_time = datetime.now()
            
            # Create zones for extension targets
            extension_levels = [
                ('127%', extension.level_127, 'PRIMARY'),
                ('161.8%', extension.level_162, 'SECONDARY'),
                ('200%', extension.level_200, 'INTERMEDIATE'),
                ('271.8%', extension.level_272, 'FINAL')
            ]
            
            for level_name, level_price, target_type in extension_levels:
                tolerance = level_price * self.config['level_tolerance']
                
                zone = FibonacciZone(
                    zone_id=f"FIB_EXT_{symbol}_{timeframe}_{level_name}_{len(zones)}",
                    zone_type=FibonacciType.EXTENSION,
                    formation_timestamp=current_time,
                    timeframe=timeframe,
                    zone_high=level_price + tolerance,
                    zone_low=level_price - tolerance,
                    zone_mid=level_price,
                    fibonacci_level=float(level_name.replace('%', '')) / 100,
                    retracement=None,
                    extension=extension,
                    market_context=MarketArray.EQUILIBRIUM,  # Extensions are neutral
                    confluence_score=0.5,
                    institutional_interest=0.8 if target_type == 'PRIMARY' else 0.6,
                    notes=f"Extension target: {target_type}"
                )
                
                # Quality based on target importance
                if target_type == 'PRIMARY':
                    zone.quality = FibonacciQuality.HIGH
                elif target_type == 'SECONDARY':
                    zone.quality = FibonacciQuality.MEDIUM
                else:
                    zone.quality = FibonacciQuality.LOW
                
                zones.append(zone)
            
            return zones
            
        except Exception as e:
            logger.error(f"Extension zone creation failed: {e}")
            return []
    
    def _calculate_level_institutional_interest(self, fib_level: FibonacciLevel, 
                                               retracement: FibonacciRetracement) -> float:
        """Calculate institutional interest level for specific Fibonacci level."""
        try:
            # ICT level hierarchy scoring
            level_scores = {
                FibonacciLevel.LEVEL_79: 0.9,    # Highest ICT priority
                FibonacciLevel.LEVEL_705: 0.8,   # Secondary ICT level
                FibonacciLevel.LEVEL_618: 0.7,   # Golden ratio
                FibonacciLevel.LEVEL_50: 0.6,    # Equilibrium
                FibonacciLevel.LEVEL_382: 0.4,   # Shallow level
                FibonacciLevel.LEVEL_236: 0.3    # Minor level
            }
            
            base_score = level_scores.get(fib_level, 0.5)
            
            # Bonus for OTE zone
            if retracement.is_in_ote and fib_level in [FibonacciLevel.LEVEL_79, FibonacciLevel.LEVEL_618]:
                base_score += 0.1
            
            # Bonus for discount array (institutional buying zone)
            if retracement.market_array == MarketArray.DISCOUNT:
                base_score += 0.1
            
            return min(1.0, base_score)
            
        except Exception as e:
            logger.error(f"Institutional interest calculation failed: {e}")
            return 0.5
    
    def _add_confluence_analysis(self, fib_zones: List[FibonacciZone],
                               order_blocks: Optional[List],
                               fair_value_gaps: Optional[List],
                               liquidity_zones: Optional[List]) -> None:
        """Add confluence analysis to Fibonacci zones."""
        try:
            for zone in fib_zones:
                confluence_factors = []
                confluence_score = zone.confluence_score  # Base score
                
                # Order Block confluence
                if order_blocks:
                    ob_confluence = self._check_order_block_confluence(zone, order_blocks)
                    if ob_confluence:
                        zone.order_block_alignment = True
                        confluence_factors.extend(ob_confluence)
                        confluence_score += self.config['order_block_confluence_weight']
                
                # Fair Value Gap confluence
                if fair_value_gaps:
                    fvg_confluence = self._check_fvg_confluence(zone, fair_value_gaps)
                    if fvg_confluence:
                        zone.fvg_alignment = True
                        confluence_factors.extend(fvg_confluence)
                        confluence_score += self.config['fvg_confluence_weight']
                
                # Liquidity confluence
                if liquidity_zones:
                    liq_confluence = self._check_liquidity_confluence(zone, liquidity_zones)
                    if liq_confluence:
                        zone.liquidity_alignment = True
                        confluence_factors.extend(liq_confluence)
                        confluence_score += self.config['liquidity_confluence_weight']
                
                # Update zone with confluence
                zone.confluence_score = min(1.0, confluence_score)
                
                # Update quality based on confluence
                if zone.confluence_score >= self.config['premium_confluence_threshold']:
                    zone.quality = FibonacciQuality.PREMIUM
                elif zone.confluence_score >= self.config['high_confluence_threshold']:
                    zone.quality = FibonacciQuality.HIGH
                elif zone.confluence_score >= self.config['medium_confluence_threshold']:
                    zone.quality = FibonacciQuality.MEDIUM
                else:
                    zone.quality = FibonacciQuality.LOW
                
                # Update institutional interest
                zone.institutional_interest = min(1.0, zone.institutional_interest + (zone.confluence_score * 0.2))
                
        except Exception as e:
            logger.error(f"Confluence analysis failed: {e}")
    
    def _check_order_block_confluence(self, fib_zone: FibonacciZone, order_blocks: List) -> List[str]:
        """Check for Order Block confluence with Fibonacci level."""
        try:
            confluences = []
            tolerance = self.config['level_tolerance']
            
            for ob in order_blocks:
                # Check if Order Block overlaps with Fibonacci zone
                ob_high = getattr(ob, 'zone_high', getattr(ob, 'high', 0))
                ob_low = getattr(ob, 'zone_low', getattr(ob, 'low', 0))
                
                # Check overlap
                if (ob_low <= fib_zone.zone_high and ob_high >= fib_zone.zone_low):
                    ob_quality = getattr(ob, 'quality', 'MEDIUM')
                    confluences.append(f"Order Block {ob_quality} confluence")
                
                # Check for nearby Order Blocks (within tolerance)
                ob_mid = (ob_high + ob_low) / 2
                fib_distance = abs(ob_mid - fib_zone.zone_mid) / fib_zone.zone_mid
                
                if fib_distance <= tolerance * 2:  # Double tolerance for nearby
                    confluences.append(f"Nearby Order Block at {fib_distance:.1%}")
            
            return confluences
            
        except Exception as e:
            logger.error(f"Order Block confluence check failed: {e}")
            return []
    
    def _check_fvg_confluence(self, fib_zone: FibonacciZone, fair_value_gaps: List) -> List[str]:
        """Check for Fair Value Gap confluence with Fibonacci level."""
        try:
            confluences = []
            tolerance = self.config['level_tolerance']
            
            for fvg in fair_value_gaps:
                # Check if FVG overlaps with Fibonacci zone
                fvg_high = getattr(fvg, 'gap_high', getattr(fvg, 'high', 0))
                fvg_low = getattr(fvg, 'gap_low', getattr(fvg, 'low', 0))
                
                # Check overlap
                if (fvg_low <= fib_zone.zone_high and fvg_high >= fib_zone.zone_low):
                    fvg_quality = getattr(fvg, 'quality', 'MEDIUM')
                    confluences.append(f"Fair Value Gap {fvg_quality} confluence")
                
                # Check for nearby FVGs
                fvg_mid = (fvg_high + fvg_low) / 2
                fib_distance = abs(fvg_mid - fib_zone.zone_mid) / fib_zone.zone_mid
                
                if fib_distance <= tolerance * 2:
                    confluences.append(f"Nearby Fair Value Gap at {fib_distance:.1%}")
            
            return confluences
            
        except Exception as e:
            logger.error(f"Fair Value Gap confluence check failed: {e}")
            return []
    
    def _check_liquidity_confluence(self, fib_zone: FibonacciZone, liquidity_zones: List) -> List[str]:
        """Check for liquidity zone confluence with Fibonacci level."""
        try:
            confluences = []
            tolerance = self.config['level_tolerance']
            
            for liq_zone in liquidity_zones:
                # Check if liquidity zone overlaps with Fibonacci zone
                liq_level = getattr(liq_zone, 'exact_level', getattr(liq_zone, 'level', 0))
                
                # Check proximity
                fib_distance = abs(liq_level - fib_zone.zone_mid) / fib_zone.zone_mid
                
                if fib_distance <= tolerance:
                    liq_type = getattr(liq_zone, 'zone_type', 'UNKNOWN')
                    confluences.append(f"Liquidity {liq_type} confluence")
                elif fib_distance <= tolerance * 3:
                    confluences.append(f"Nearby liquidity at {fib_distance:.1%}")
            
            return confluences
            
        except Exception as e:
            logger.error(f"Liquidity confluence check failed: {e}")
            return []
    
    def _filter_and_rank_fibonacci_zones(self, zones: List[FibonacciZone]) -> List[FibonacciZone]:
        """Filter and rank Fibonacci zones by quality and confluence."""
        try:
            # Filter out low quality zones
            quality_zones = [
                zone for zone in zones
                if zone.confluence_score >= self.config['min_confluence_score']
                and zone.quality != FibonacciQuality.INVALID
            ]
            
            # Sort by confluence score and ICT level priority
            def zone_priority(zone):
                priority_scores = {
                    0.79: 10,    # 79% level - highest priority
                    0.705: 9,    # 70.5% level
                    0.618: 8,    # 61.8% level
                    0.5: 7,      # 50% level
                    0.382: 6,    # 38.2% level
                    0.236: 5,    # 23.6% level
                }
                
                level_priority = priority_scores.get(zone.fibonacci_level, 1)
                return (zone.confluence_score * 10) + level_priority
            
            quality_zones.sort(key=zone_priority, reverse=True)
            
            return quality_zones[:20]  # Return top 20 zones
            
        except Exception as e:
            logger.error(f"Zone filtering and ranking failed: {e}")
            return zones
    
    def get_optimal_trade_entry_analysis(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """Get Optimal Trade Entry (OTE) analysis for current market conditions."""
        try:
            cache_key = f"{symbol}_{timeframe}"
            
            if cache_key not in self.fibonacci_cache:
                return None
            
            zones = self.fibonacci_cache[cache_key]
            
            # Find zones in OTE range (62% - 79%)
            ote_zones = []
            for zone in zones:
                if zone.retracement and zone.retracement.is_in_ote:
                    ote_zones.append(zone)
            
            if not ote_zones:
                return None
            
            # Get best OTE zone
            best_ote = max(ote_zones, key=lambda x: x.confluence_score)
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'is_in_ote': True,
                'ote_zone_high': best_ote.retracement.ote_zone_high,
                'ote_zone_low': best_ote.retracement.ote_zone_low,
                'current_price': best_ote.retracement.current_price,
                'retracement_percentage': best_ote.retracement.retracement_percentage,
                'market_array': best_ote.retracement.market_array.value,
                'confluence_score': best_ote.confluence_score,
                'quality': best_ote.quality.value,
                'institutional_interest': best_ote.institutional_interest,
                'order_block_confluence': best_ote.order_block_alignment,
                'fvg_confluence': best_ote.fvg_alignment,
                'liquidity_confluence': best_ote.liquidity_alignment,
                'entry_recommendation': self._generate_ote_entry_recommendation(best_ote)
            }
            
        except Exception as e:
            logger.error(f"OTE analysis failed: {e}")
            return None
    
    def _generate_ote_entry_recommendation(self, ote_zone: FibonacciZone) -> str:
        """Generate entry recommendation for OTE zone."""
        try:
            if not ote_zone.retracement:
                return "NO_RECOMMENDATION"
            
            retracement = ote_zone.retracement
            
            # Bullish setup recommendations
            if retracement.market_array == MarketArray.DISCOUNT:
                if ote_zone.confluence_score >= 0.8:
                    return "STRONG_BUY_SETUP"
                elif ote_zone.confluence_score >= 0.6:
                    return "MODERATE_BUY_SETUP"
                else:
                    return "WEAK_BUY_SETUP"
            
            # Bearish setup recommendations  
            elif retracement.market_array == MarketArray.PREMIUM:
                if ote_zone.confluence_score >= 0.8:
                    return "STRONG_SELL_SETUP"
                elif ote_zone.confluence_score >= 0.6:
                    return "MODERATE_SELL_SETUP"
                else:
                    return "WEAK_SELL_SETUP"
            
            # Equilibrium
            else:
                return "NEUTRAL_WAIT_FOR_DIRECTION"
                
        except Exception as e:
            logger.error(f"OTE recommendation generation failed: {e}")
            return "NO_RECOMMENDATION"
    
    def get_fibonacci_summary(self, symbol: str, timeframe: str) -> Dict:
        """Get summary of Fibonacci analysis for symbol/timeframe."""
        try:
            cache_key = f"{symbol}_{timeframe}"
            
            if cache_key not in self.fibonacci_cache:
                return {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'total_zones': 0,
                    'premium_zones': 0,
                    'ote_zones': 0,
                    'confluence_zones': 0,
                    'analysis_available': False
                }
            
            zones = self.fibonacci_cache[cache_key]
            
            premium_zones = len([z for z in zones if z.quality == FibonacciQuality.PREMIUM])
            ote_zones = len([z for z in zones if z.retracement and z.retracement.is_in_ote])
            confluence_zones = len([z for z in zones if z.confluence_score >= 0.7])
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'total_zones': len(zones),
                'premium_zones': premium_zones,
                'high_quality_zones': len([z for z in zones if z.quality == FibonacciQuality.HIGH]),
                'ote_zones': ote_zones,
                'confluence_zones': confluence_zones,
                'avg_confluence_score': np.mean([z.confluence_score for z in zones]) if zones else 0,
                'analysis_available': True,
                'last_analysis': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Fibonacci summary generation failed: {e}")
            return {'error': str(e)}


if __name__ == "__main__":
    # Example usage and testing
    import logging
    logging.basicConfig(level=logging.INFO)
    
    def test_fibonacci_analyzer():
        """Test the ICT Fibonacci analyzer."""
        print("📐 Testing ICT Fibonacci Analyzer...")
        
        # Create sample data with clear swings
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=200, freq='1H')
        
        # Generate price data with clear swing patterns
        base_price = 50000
        prices = [base_price]
        
        # Create uptrend with retracements
        for i in range(199):
            if i < 50:  # Uptrend
                change = np.random.normal(0.001, 0.005)
            elif i < 80:  # Retracement
                change = np.random.normal(-0.002, 0.005)
            elif i < 150:  # Continuation
                change = np.random.normal(0.0015, 0.005)
            else:  # Final retracement
                change = np.random.normal(-0.001, 0.005)
            
            price = prices[-1] * (1 + change)
            prices.append(price)
        
        # Create OHLCV DataFrame
        df = pd.DataFrame({
            'open': prices[:-1],
            'high': [p * (1 + abs(np.random.normal(0, 0.002))) for p in prices[:-1]],
            'low': [p * (1 - abs(np.random.normal(0, 0.002))) for p in prices[:-1]],
            'close': prices[1:],
            'volume': np.random.default_rng(42).uniform(100, 1000, 199)
        }, index=dates[1:])
        
        # Initialize analyzer
        analyzer = ICTFibonacciAnalyzer()
        
        # Analyze Fibonacci confluence
        fib_zones = analyzer.analyze_fibonacci_confluence(df, "BTC/USDT", "1h")
        
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                   FIBONACCI ANALYSIS RESULTS                    ║
╠══════════════════════════════════════════════════════════════════╣
║  Total Fibonacci Zones:  {len(fib_zones):>6}                    ║
║  Current Price:         ${df['close'].iloc[-1]:>10,.2f}         ║
╚══════════════════════════════════════════════════════════════════╝
""")
        
        # Show top Fibonacci zones
        print("\n📐 Top Fibonacci Zones:")
        for i, zone in enumerate(fib_zones[:10]):
            level_pct = zone.fibonacci_level * 100
            print("   {i+1}. {level_pct:>5.1f}% Level: ${zone.zone_mid:>10,.2f} - {zone.quality.value} ({zone.confluence_score:.1%})")
        
        # Get OTE analysis
        ote_analysis = analyzer.get_optimal_trade_entry_analysis("BTC/USDT", "1h")
        if ote_analysis:
            print("""
📐 Optimal Trade Entry (OTE) Analysis:
   In OTE Zone:        {ote_analysis['is_in_ote']}
   OTE High:          ${ote_analysis['ote_zone_high']:,.2f}
   OTE Low:           ${ote_analysis['ote_zone_low']:,.2f}
   Retracement:       {ote_analysis['retracement_percentage']:.1%}
   Market Array:      {ote_analysis['market_array']}
   Confluence:        {ote_analysis['confluence_score']:.1%}
   Recommendation:    {ote_analysis['entry_recommendation']}
""")
        
        # Get summary
        summary = analyzer.get_fibonacci_summary("BTC/USDT", "1h")
        print("""
📊 Fibonacci Summary:
   Premium Zones:      {summary['premium_zones']}
   High Quality:       {summary['high_quality_zones']}
   OTE Zones:          {summary['ote_zones']}
   Confluence Zones:   {summary['confluence_zones']}
   Avg Confluence:     {summary['avg_confluence_score']:.1%}
""")
        
        print("\n✅ ICT Fibonacci analyzer test completed!")
    
    # Run the test
    test_fibonacci_analyzer()