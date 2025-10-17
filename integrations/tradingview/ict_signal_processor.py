#!/usr/bin/env python3
"""
ICT-Enhanced Signal Processing Engine
====================================

Complete replacement of traditional retail-focused signal processing with
institutional ICT methodology. Processes TradingView alerts through the lens
of Order Blocks, Fair Value Gaps, Market Structure, and Liquidity concepts.

Key Improvements over Traditional System:
- Order Block confluence analysis vs RSI/MACD signals
- Fair Value Gap validation vs moving average crossovers
- Market structure confirmation vs generic trend following
- Liquidity hunt detection vs basic support/resistance
- ICT risk management vs percentage-based stops

Signal Flow:
1. Alert Reception → 2. ICT Analysis → 3. Order Block Validation → 
4. FVG Confluence → 5. Market Structure Check → 6. Liquidity Analysis →
7. ICT Signal Generation → 8. Institutional Risk Management → 9. Execution Ready

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

import logging
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

# Import ICT components
from trading.ict_analyzer import ICTAnalyzer, TrendDirection, ICTSignal
from trading.ict_hierarchy import ICTTimeframeHierarchy, HierarchyAnalysis
from trading.order_block_detector import EnhancedOrderBlockDetector, OrderBlockZone, OrderBlockState
from trading.fvg_detector import FVGDetector, FVGZone, FVGState, FVGType

# Import traditional components for compatibility
from integrations.tradingview.webhook_server import WebhookAlert
from utils.config_loader import ConfigLoader
from utils.crypto_pairs import CryptoPairs
from utils.risk_management import RiskManager
from src.utils.data_fetcher import DataFetcher

logger = logging.getLogger(__name__)

@dataclass
class ICTProcessedSignal:
    """Enhanced signal structure with ICT analysis."""
    # Original alert data
    original_alert: WebhookAlert
    
    # ICT Analysis components
    hierarchy_analysis: Optional[HierarchyAnalysis]
    primary_order_block: Optional[OrderBlockZone]
    supporting_fvgs: List[FVGZone]
    market_structure: Dict
    liquidity_analysis: Dict
    
    # Signal classification
    signal_type: str            # 'ICT_OB_LONG', 'ICT_FVG_SHORT', etc.
    ict_setup_type: str         # 'ORDER_BLOCK', 'FVG_FILL', 'STRUCTURE_BREAK'
    confidence_breakdown: Dict   # Detailed confidence factors
    
    # Enhanced signal data
    symbol: str
    direction: str              # 'LONG', 'SHORT'
    entry_strategy: str         # 'MARKET', 'LIMIT_OB', 'LIMIT_FVG'
    
    # ICT-specific entry/exit levels
    ict_entry_price: float
    ict_stop_loss: float       # Based on structure, not percentages
    ict_take_profit: float     # Based on next liquidity level
    invalidation_level: float  # Level that invalidates ICT setup
    
    # Risk management (ICT-based)
    institutional_risk: float   # Risk based on market structure
    position_size: float
    max_drawdown_allowed: float
    
    # Confluence scoring
    overall_confluence: float   # 0-1 total confluence score
    htf_alignment_score: float  # Higher timeframe alignment
    order_block_score: float    # Order block quality
    fvg_score: float           # Fair value gap confluence  
    structure_score: float      # Market structure strength
    liquidity_score: float     # Liquidity hunt probability
    
    # Timing and execution
    optimal_entry_window: Tuple[datetime, datetime]
    execution_urgency: str      # 'IMMEDIATE', 'WITHIN_HOUR', 'PATIENT'
    
    # Validation status
    validation_status: str      # 'APPROVED', 'REJECTED', 'PENDING'
    rejection_reason: Optional[str] = None
    
    # Metadata
    processing_timestamp: datetime = None
    ict_session: str = ""
    metadata: Optional[Dict] = None
    
    def __post_init__(self):
        if self.processing_timestamp is None:
            self.processing_timestamp = datetime.now()

class ICTSignalProcessor:
    """
    Advanced ICT-based signal processor for institutional trading approach.
    
    This processor completely replaces traditional retail indicators with
    ICT concepts, providing signals based on actual market maker behavior
    rather than lagging technical analysis.
    """
    
    def __init__(self, config_path: str = "project/configuration/"):
        """Initialize ICT signal processor."""
        self.config_path = config_path
        self.config_loader = ConfigLoader(config_path)
        
        # Initialize ICT components
        self.ict_analyzer = ICTAnalyzer()
        self.ict_hierarchy = ICTTimeframeHierarchy(config_path)
        self.enhanced_order_block_detector = EnhancedOrderBlockDetector()
        self.fvg_detector = FVGDetector()
        
        # Traditional components for compatibility
        self.crypto_pairs = CryptoPairs(config_path)
        self.risk_manager = RiskManager(config_path)
        self.data_fetcher = DataFetcher()
        
        # Load ICT signal processing configuration
        self.ict_config = self._load_ict_config()
        
        # Signal handlers
        self.signal_handlers: List[Callable[[ICTProcessedSignal], None]] = []
        
        # Processing statistics
        self.stats = {
            'total_alerts': 0,
            'ict_signals_generated': 0,
            'signals_by_type': {},
            'avg_confluence_score': 0.0,
            'htf_alignment_rate': 0.0,
            'order_block_signals': 0,
            'fvg_signals': 0,
            'structure_signals': 0,
            'rejected_signals': 0,
            'last_reset': datetime.now()
        }
        
        # Data cache for performance
        self.market_data_cache = {}
        self.analysis_cache = {}
        
        logger.info("ICT Signal Processor initialized - Traditional indicators replaced with institutional methodology")
    
    def _load_ict_config(self) -> Dict:
        """Load ICT signal processing configuration."""
        try:
            config = self.config_loader.get_config("ict_signal_processing")
        except Exception as e:
            logger.warning(f"Failed to load ICT config: {e}")
            config = {}
        
        # Default ICT configuration
        defaults = {
            # Confluence requirements
            'min_overall_confluence': 0.7,        # 70% minimum confluence
            'min_htf_alignment': 0.6,             # 60% HTF alignment required
            'min_order_block_score': 0.5,         # 50% OB quality minimum
            'require_fresh_order_blocks': True,    # Only trade fresh OBs
            'require_fvg_confirmation': False,     # FVG confirmation optional
            
            # Signal type weights
            'order_block_signal_weight': 0.4,     # 40% weight to OB signals
            'fvg_signal_weight': 0.25,            # 25% weight to FVG signals
            'structure_signal_weight': 0.2,       # 20% weight to structure
            'liquidity_signal_weight': 0.15,      # 15% weight to liquidity
            
            # Entry strategy preferences
            'prefer_limit_orders': True,           # Use limit orders at OB/FVG levels
            'market_entry_confluence_threshold': 0.85, # 85% confluence for market orders
            'entry_window_minutes': 30,           # 30 minute optimal entry window
            
            # Risk management (ICT-based)
            'use_structure_stops': True,           # Stops based on structure breaks
            'max_stop_loss_atr': 2.0,             # Max 2x ATR for stop loss
            'min_risk_reward_ratio': 1.5,         # Minimum 1.5:1 R:R
            'position_size_by_confluence': True,   # Scale size by confluence
            'max_position_size': 0.05,            # 5% max position size
            'min_position_size': 0.01,            # 1% min position size
            
            # Timing and session preferences
            'prefer_london_ny_sessions': True,     # Higher weight for major sessions
            'avoid_asia_session_entries': False,   # Allow Asia session trades
            'weekend_signal_reduction': 0.8,       # 20% reduction in weekend signals
            
            # Quality filters
            'premium_order_blocks_only': False,    # Allow medium quality OBs
            'fresh_fvg_priority': True,            # Prioritize unfilled FVGs
            'multiple_confluence_bonus': 0.1,      # 10% bonus for multiple factors
            
            # Alert processing
            'require_tradingview_confluence': False, # Don't require TV signal confluence
            'override_retail_signals': True,       # Override TV retail signals with ICT
            'signal_timeout_minutes': 15,          # 15 minute signal validity
            'max_concurrent_ict_signals': 5,       # Max 5 concurrent ICT signals
        }
        
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
        
        return config
    
    def add_signal_handler(self, handler: Callable[[ICTProcessedSignal], None]) -> None:
        """Add handler for processed ICT signals."""
        self.signal_handlers.append(handler)
        logger.info(f"Added ICT signal handler: {handler.__name__}")
    
    async def process_alert_with_ict(self, alert: WebhookAlert) -> Optional[ICTProcessedSignal]:
        """
        Process TradingView alert through complete ICT analysis.
        
        This is the main entry point that replaces traditional signal processing
        with institutional trading methodology.
        
        Args:
            alert: Raw webhook alert from TradingView
            
        Returns:
            ICTProcessedSignal if valid, None if rejected
        """
        self.stats['total_alerts'] += 1
        
        try:
            logger.info(f"Processing alert with ICT methodology: {alert.action} {alert.symbol}")
            
            # Step 1: Basic alert validation (still needed)
            if not self._validate_basic_alert(alert):
                return None
            
            # Step 2: Fetch market data for ICT analysis
            market_data = await self._fetch_market_data_for_ict(alert.symbol)
            if not market_data:
                logger.warning(f"Failed to fetch market data for {alert.symbol}")
                return self._reject_signal("Market data unavailable")
            
            # Step 3: Perform complete ICT hierarchy analysis
            hierarchy_analysis = await self.ict_hierarchy.analyze_symbol_hierarchy(alert.symbol)
            
            # Step 4: Detect Order Blocks on current timeframes
            order_blocks = await self._detect_current_order_blocks(alert.symbol, market_data)
            
            # Step 5: Detect Fair Value Gaps
            fair_value_gaps = await self._detect_current_fvgs(alert.symbol, market_data)
            
            # Step 6: Analyze market structure
            market_structure = await self._analyze_market_structure(alert.symbol, market_data, hierarchy_analysis)
            
            # Step 7: Perform liquidity analysis
            liquidity_analysis = await self._analyze_liquidity_zones(alert.symbol, market_data)
            
            # Step 8: Generate ICT signal from analysis
            ict_signal = await self._generate_ict_signal(
                alert, hierarchy_analysis, order_blocks, fair_value_gaps,
                market_structure, liquidity_analysis, market_data
            )
            
            if not ict_signal:
                return self._reject_signal("No valid ICT setup found")
            
            # Step 9: Validate ICT signal confluence
            if not self._validate_ict_confluence(ict_signal):
                return self._reject_signal(f"Insufficient confluence: {ict_signal.overall_confluence:.2f}")
            
            # Step 10: Calculate ICT-based risk management
            self._calculate_ict_risk_management(ict_signal, market_data)
            
            # Step 11: Set execution timing and strategy
            self._set_execution_strategy(ict_signal)
            
            # Update statistics
            self.stats['ict_signals_generated'] += 1
            self._update_signal_stats(ict_signal)
            
            # Dispatch to handlers
            await self._dispatch_ict_signal(ict_signal)
            
            logger.info(f"ICT signal generated: {ict_signal.signal_type} with {ict_signal.overall_confluence:.2f} confluence")
            return ict_signal
            
        except Exception as e:
            logger.error(f"ICT signal processing failed: {e}")
            return self._reject_signal(f"Processing error: {e}")
    
    def _validate_basic_alert(self, alert: WebhookAlert) -> bool:
        """Basic alert validation (required fields, supported symbol, etc)."""
        try:
            # Check required fields
            if not alert.symbol or not alert.action or not alert.price:
                logger.warning("Alert missing required fields")
                return False
            
            # Validate symbol support
            if not self.crypto_pairs.is_pair_supported(alert.symbol):
                logger.warning(f"Unsupported symbol: {alert.symbol}")
                return False
            
            # Validate price
            if alert.price <= 0:
                logger.warning("Invalid price in alert")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Basic alert validation failed: {e}")
            return False
    
    async def _fetch_market_data_for_ict(self, symbol: str) -> Optional[Dict]:
        """Fetch comprehensive market data needed for ICT analysis."""
        try:
            # Check cache first
            cache_key = f"{symbol}_market_data"
            if cache_key in self.market_data_cache:
                cached_data, cache_time = self.market_data_cache[cache_key]
                if (datetime.now() - cache_time).total_seconds() < 300:  # 5 minute cache
                    return cached_data
            
            # Fetch multiple timeframes for ICT analysis
            timeframes = ['1m', '5m', '1h', '4h']
            market_data = {}
            
            for tf in timeframes:
                try:
                    # Determine appropriate limit for each timeframe
                    limits = {'1m': 100, '5m': 300, '1h': 200, '4h': 100}
                    limit = limits.get(tf, 100)
                    
                    data = await self.data_fetcher.fetch_ohlcv_async(
                        symbol=symbol.replace('/', ''),  # Remove slash for API
                        timeframe=tf,
                        limit=limit
                    )
                    
                    if data is not None and not data.empty:
                        market_data[tf] = data
                    else:
                        logger.warning(f"No data received for {symbol} {tf}")
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch {tf} data for {symbol}: {e}")
                    continue
            
            if not market_data:
                logger.error(f"No market data available for {symbol}")
                return None
            
            # Cache the data
            self.market_data_cache[cache_key] = (market_data, datetime.now())
            
            logger.debug(f"Fetched market data for {symbol}: {list(market_data.keys())} timeframes")
            return market_data
            
        except Exception as e:
            logger.error(f"Market data fetch failed for {symbol}: {e}")
            return None
    
    async def _detect_current_order_blocks(self, symbol: str, market_data: Dict) -> List[OrderBlockZone]:
        """Detect current Order Blocks across relevant timeframes."""
        try:
            all_order_blocks = []
            
            # Detect OBs on 5M and 1H timeframes (most relevant for entries)
            for tf in ['5m', '1h']:
                if tf in market_data:
                    eobs = self.enhanced_order_block_detector.detect_enhanced_order_blocks(
                        market_data[tf], symbol, tf
                    )
                    all_order_blocks.extend(eobs)
            
            # Filter for only fresh and tested Order Blocks
            if self.ict_config['require_fresh_order_blocks']:
                filtered_obs = [
                    ob for ob in all_order_blocks 
                    if ob.state in [OrderBlockState.FRESH, OrderBlockState.TESTED]
                ]
            else:
                filtered_obs = all_order_blocks
            
            # Sort by quality and relevance
            filtered_obs.sort(key=lambda x: x.strength_score, reverse=True)
            
            logger.debug(f"Detected {len(filtered_obs)} relevant Order Blocks for {symbol}")
            return filtered_obs[:10]  # Top 10 Order Blocks
            
        except Exception as e:
            logger.error(f"Order Block detection failed for {symbol}: {e}")
            return []
    
    async def _detect_current_fvgs(self, symbol: str, market_data: Dict) -> List[FVGZone]:
        """Detect current Fair Value Gaps across relevant timeframes."""
        try:
            all_fvgs = []
            
            # Detect FVGs on 1M and 5M timeframes (most relevant for entries)
            for tf in ['1m', '5m']:
                if tf in market_data:
                    fvgs = self.fvg_detector.detect_fair_value_gaps(
                        market_data[tf], symbol, tf
                    )
                    all_fvgs.extend(fvgs)
            
            # Filter for fresh and partially filled FVGs
            if self.ict_config['fresh_fvg_priority']:
                filtered_fvgs = [
                    fvg for fvg in all_fvgs 
                    if fvg.state in [FVGState.FRESH, FVGState.PARTIALLY_FILLED]
                ]
            else:
                filtered_fvgs = all_fvgs
            
            # Sort by quality and relevance
            filtered_fvgs.sort(key=lambda x: x.strength_score, reverse=True)
            
            logger.debug(f"Detected {len(filtered_fvgs)} relevant Fair Value Gaps for {symbol}")
            return filtered_fvgs[:15]  # Top 15 FVGs
            
        except Exception as e:
            logger.error(f"Fair Value Gap detection failed for {symbol}: {e}")
            return []
    
    async def _analyze_market_structure(self, symbol: str, market_data: Dict, 
                                      hierarchy_analysis: HierarchyAnalysis) -> Dict:
        """Analyze current market structure for ICT signals."""
        try:
            structure_analysis = {
                'current_trend': hierarchy_analysis.trading_bias,
                'trend_strength': hierarchy_analysis.overall_confidence,
                'htf_alignment': hierarchy_analysis.timeframe_alignment,
                'recent_breaks': [],
                'key_levels': [],
                'structure_score': 0.0
            }
            
            # Analyze structure breaks on multiple timeframes
            for tf in ['5m', '1h']:
                if tf in market_data:
                    # Use ICT analyzer for structure analysis
                    tf_analysis = self.ict_analyzer.analyze_market_structure(
                        market_data[tf], symbol, tf
                    )
                    
                    # Extract recent structure breaks
                    recent_breaks = [
                        sb for sb in tf_analysis['structure_analysis']['structure_breaks']
                        if (datetime.now() - sb.timestamp).total_seconds() < 3600  # Last hour
                    ]
                    structure_analysis['recent_breaks'].extend(recent_breaks)
                    
                    # Extract key levels
                    if 'key_levels' in tf_analysis['htf_bias']:
                        structure_analysis['key_levels'].extend(tf_analysis['htf_bias']['key_levels'])
            
            # Calculate structure score
            structure_score = 0.5  # Base score
            
            # Bonus for clear trend direction
            if hierarchy_analysis.trading_bias != TrendDirection.CONSOLIDATION:
                structure_score += 0.2
            
            # Bonus for timeframe alignment
            if hierarchy_analysis.timeframe_alignment:
                structure_score += 0.2
            
            # Bonus for recent structure breaks
            if len(structure_analysis['recent_breaks']) > 0:
                structure_score += 0.1
            
            structure_analysis['structure_score'] = min(1.0, structure_score)
            
            return structure_analysis
            
        except Exception as e:
            logger.error(f"Market structure analysis failed for {symbol}: {e}")
            return {
                'current_trend': TrendDirection.CONSOLIDATION,
                'trend_strength': 0.0,
                'htf_alignment': False,
                'recent_breaks': [],
                'key_levels': [],
                'structure_score': 0.0
            }
    
    async def _analyze_liquidity_zones(self, symbol: str, market_data: Dict) -> Dict:
        """Analyze liquidity zones for hunt patterns."""
        try:
            liquidity_analysis = {
                'equal_highs': [],
                'equal_lows': [],
                'psychological_levels': [],
                'recent_sweeps': [],
                'liquidity_score': 0.0
            }
            
            # Analyze liquidity on 5M and 1H timeframes
            for tf in ['5m', '1h']:
                if tf in market_data:
                    # Use ICT analyzer for liquidity analysis
                    tf_analysis = self.ict_analyzer.analyze_market_structure(
                        market_data[tf], symbol, tf
                    )
                    
                    # Extract liquidity zones
                    liquidity_zones = tf_analysis.get('liquidity_zones', [])
                    
                    for zone in liquidity_zones:
                        if zone.zone_type == 'EQUAL_HIGHS':
                            liquidity_analysis['equal_highs'].append(zone)
                        elif zone.zone_type == 'EQUAL_LOWS':
                            liquidity_analysis['equal_lows'].append(zone)
                        elif zone.zone_type == 'PSYCHOLOGICAL':
                            liquidity_analysis['psychological_levels'].append(zone)
                        
                        # Check for recent sweeps
                        if zone.is_swept and zone.sweep_timestamp:
                            if (datetime.now() - zone.sweep_timestamp).total_seconds() < 1800:  # 30 minutes
                                liquidity_analysis['recent_sweeps'].append(zone)
            
            # Calculate liquidity score
            liquidity_score = 0.3  # Base score
            
            # Bonus for identified liquidity zones
            total_zones = (len(liquidity_analysis['equal_highs']) + 
                          len(liquidity_analysis['equal_lows']) +
                          len(liquidity_analysis['psychological_levels']))
            
            if total_zones > 0:
                liquidity_score += min(0.3, total_zones * 0.05)
            
            # Bonus for recent sweeps (indicates active liquidity hunting)
            if len(liquidity_analysis['recent_sweeps']) > 0:
                liquidity_score += 0.2
            
            liquidity_analysis['liquidity_score'] = min(1.0, liquidity_score)
            
            return liquidity_analysis
            
        except Exception as e:
            logger.error(f"Liquidity analysis failed for {symbol}: {e}")
            return {
                'equal_highs': [],
                'equal_lows': [],
                'psychological_levels': [],
                'recent_sweeps': [],
                'liquidity_score': 0.0
            }
    
    async def _generate_ict_signal(self, alert: WebhookAlert, hierarchy_analysis: HierarchyAnalysis,
                                 order_blocks: List[OrderBlockZone], fair_value_gaps: List[FVGZone],
                                 market_structure: Dict, liquidity_analysis: Dict,
                                 market_data: Dict) -> Optional[ICTProcessedSignal]:
        """Generate ICT signal from complete analysis."""
        try:
            # Determine primary ICT setup type
            setup_type, primary_ob, supporting_fvgs = self._identify_primary_ict_setup(
                order_blocks, fair_value_gaps, market_structure, hierarchy_analysis
            )
            
            if not setup_type:
                logger.debug("No valid ICT setup identified")
                return None
            
            # Determine signal direction based on ICT analysis
            signal_direction = self._determine_ict_signal_direction(
                setup_type, primary_ob, supporting_fvgs, hierarchy_analysis, market_structure
            )
            
            if not signal_direction:
                logger.debug("Could not determine clear signal direction")
                return None
            
            # Calculate confluence scores
            confluence_breakdown = self._calculate_confluence_breakdown(
                hierarchy_analysis, primary_ob, supporting_fvgs, market_structure, liquidity_analysis
            )
            
            # Calculate ICT entry, stop, and target levels
            entry_levels = self._calculate_ict_entry_levels(
                setup_type, primary_ob, supporting_fvgs, signal_direction, market_data
            )
            
            if not entry_levels:
                logger.debug("Could not calculate valid ICT entry levels")
                return None
            
            # Create ICT processed signal
            ict_signal = ICTProcessedSignal(
                original_alert=alert,
                hierarchy_analysis=hierarchy_analysis,
                primary_order_block=primary_ob,
                supporting_fvgs=supporting_fvgs,
                market_structure=market_structure,
                liquidity_analysis=liquidity_analysis,
                
                signal_type=f"ICT_{setup_type}_{signal_direction}",
                ict_setup_type=setup_type,
                confidence_breakdown=confluence_breakdown,
                
                symbol=alert.symbol,
                direction=signal_direction,
                entry_strategy=self._determine_entry_strategy(setup_type, confluence_breakdown['overall']),
                
                ict_entry_price=entry_levels['entry'],
                ict_stop_loss=entry_levels['stop_loss'],
                ict_take_profit=entry_levels['take_profit'],
                invalidation_level=entry_levels['invalidation'],
                
                institutional_risk=0.0,  # Will be calculated
                position_size=0.0,       # Will be calculated
                max_drawdown_allowed=0.0, # Will be calculated
                
                overall_confluence=confluence_breakdown['overall'],
                htf_alignment_score=confluence_breakdown['htf_alignment'],
                order_block_score=confluence_breakdown['order_block'],
                fvg_score=confluence_breakdown['fvg'],
                structure_score=confluence_breakdown['structure'],
                liquidity_score=confluence_breakdown['liquidity'],
                
                optimal_entry_window=(datetime.now(), datetime.now() + timedelta(minutes=30)),
                execution_urgency=self._determine_execution_urgency(confluence_breakdown['overall']),
                
                validation_status='APPROVED',
                ict_session=self._get_current_ict_session(),
                metadata={
                    'alert_confidence': alert.confidence,
                    'setup_quality': setup_type,
                    'primary_ob_quality': primary_ob.quality.value if primary_ob else 'NONE',
                    'fvg_count': len(supporting_fvgs)
                }
            )
            
            return ict_signal
            
        except Exception as e:
            logger.error(f"ICT signal generation failed: {e}")
            return None
    
    def _identify_primary_ict_setup(self, order_blocks: List[OrderBlockZone], 
                                   fair_value_gaps: List[FVGZone],
                                   market_structure: Dict, 
                                   hierarchy_analysis: HierarchyAnalysis) -> Tuple[Optional[str], Optional[OrderBlockZone], List[FVGZone]]:
        """Identify the primary ICT setup type."""
        try:
            # Priority 1: Fresh Order Block with high quality
            premium_obs = [ob for ob in order_blocks if ob.quality.value == 'PREMIUM' and ob.state == OrderBlockState.FRESH]
            if premium_obs:
                return 'ORDER_BLOCK', premium_obs[0], []
            
            # Priority 2: High quality Order Block with FVG confluence
            high_obs = [ob for ob in order_blocks if ob.quality.value in ['HIGH', 'PREMIUM']]
            if high_obs:
                # Check for nearby FVGs that could provide confluence
                primary_ob = high_obs[0]
                supporting_fvgs = [
                    fvg for fvg in fair_value_gaps
                    if abs(fvg.gap_mid - primary_ob.zone_mid) / primary_ob.zone_mid < 0.02  # Within 2%
                ]
                
                if supporting_fvgs:
                    return 'ORDER_BLOCK_FVG', primary_ob, supporting_fvgs
                else:
                    return 'ORDER_BLOCK', primary_ob, []
            
            # Priority 3: Fresh FVG with good quality
            fresh_fvgs = [fvg for fvg in fair_value_gaps if fvg.state == FVGState.FRESH and fvg.quality.value in ['HIGH', 'PREMIUM']]
            if fresh_fvgs:
                return 'FVG_FILL', None, fresh_fvgs[:1]
            
            # Priority 4: Market structure break continuation
            if len(market_structure.get('recent_breaks', [])) > 0:
                # Look for any supporting Order Blocks or FVGs
                if order_blocks:
                    return 'STRUCTURE_BREAK', order_blocks[0], fair_value_gaps[:2]
                elif fair_value_gaps:
                    return 'STRUCTURE_BREAK', None, fair_value_gaps[:2]
            
            # No clear setup identified
            return None, None, []
            
        except Exception as e:
            logger.error(f"ICT setup identification failed: {e}")
            return None, None, []
    
    def _determine_ict_signal_direction(self, setup_type: str, primary_ob: Optional[OrderBlockZone],
                                      supporting_fvgs: List[FVGZone], 
                                      hierarchy_analysis: HierarchyAnalysis,
                                      market_structure: Dict) -> Optional[str]:
        """Determine signal direction based on ICT analysis."""
        try:
            # Primary rule: Must align with higher timeframe bias
            htf_bias = hierarchy_analysis.trading_bias
            
            if htf_bias == TrendDirection.CONSOLIDATION:
                logger.debug("HTF in consolidation - no clear direction")
                return None
            
            # Direction based on setup type
            if setup_type == 'ORDER_BLOCK' and primary_ob:
                if primary_ob.ob_type == 'BULLISH_OB' and htf_bias == TrendDirection.BULLISH:
                    return 'LONG'
                elif primary_ob.ob_type == 'BEARISH_OB' and htf_bias == TrendDirection.BEARISH:
                    return 'SHORT'
            
            elif setup_type == 'ORDER_BLOCK_FVG' and primary_ob:
                # Order Block direction takes priority
                if primary_ob.ob_type == 'BULLISH_OB' and htf_bias == TrendDirection.BULLISH:
                    return 'LONG'
                elif primary_ob.ob_type == 'BEARISH_OB' and htf_bias == TrendDirection.BEARISH:
                    return 'SHORT'
            
            elif setup_type == 'FVG_FILL' and supporting_fvgs:
                # FVG direction with HTF alignment
                primary_fvg = supporting_fvgs[0]
                if primary_fvg.fvg_type == FVGType.BULLISH_FVG and htf_bias == TrendDirection.BULLISH:
                    return 'LONG'
                elif primary_fvg.fvg_type == FVGType.BEARISH_FVG and htf_bias == TrendDirection.BEARISH:
                    return 'SHORT'
            
            elif setup_type == 'STRUCTURE_BREAK':
                # Follow HTF bias for structure breaks
                if htf_bias == TrendDirection.BULLISH:
                    return 'LONG'
                elif htf_bias == TrendDirection.BEARISH:
                    return 'SHORT'
            
            logger.debug(f"Could not determine direction for setup: {setup_type}")
            return None
            
        except Exception as e:
            logger.error(f"Signal direction determination failed: {e}")
            return None
    
    def _calculate_confluence_breakdown(self, hierarchy_analysis: HierarchyAnalysis,
                                      primary_ob: Optional[OrderBlockZone],
                                      supporting_fvgs: List[FVGZone],
                                      market_structure: Dict,
                                      liquidity_analysis: Dict) -> Dict:
        """Calculate detailed confluence breakdown."""
        try:
            # Higher timeframe alignment score
            htf_score = 0.0
            if hierarchy_analysis.timeframe_alignment:
                htf_score = hierarchy_analysis.confluence_score
            
            # Order Block score
            ob_score = 0.0
            if primary_ob:
                ob_score = primary_ob.strength_score
            
            # Fair Value Gap score
            fvg_score = 0.0
            if supporting_fvgs:
                fvg_score = np.mean([fvg.strength_score for fvg in supporting_fvgs])
            
            # Market structure score
            structure_score = market_structure.get('structure_score', 0.0)
            
            # Liquidity score
            liquidity_score = liquidity_analysis.get('liquidity_score', 0.0)
            
            # Calculate weighted overall confluence
            weights = {
                'htf': self.ict_config['order_block_signal_weight'],
                'ob': self.ict_config['order_block_signal_weight'],
                'fvg': self.ict_config['fvg_signal_weight'],
                'structure': self.ict_config['structure_signal_weight'],
                'liquidity': self.ict_config['liquidity_signal_weight']
            }
            
            overall_confluence = (
                htf_score * weights['htf'] +
                ob_score * weights['ob'] +
                fvg_score * weights['fvg'] +
                structure_score * weights['structure'] +
                liquidity_score * weights['liquidity']
            )
            
            # Multiple confluence bonus
            active_factors = sum([
                1 if htf_score > 0.5 else 0,
                1 if ob_score > 0.5 else 0,
                1 if fvg_score > 0.5 else 0,
                1 if structure_score > 0.5 else 0,
                1 if liquidity_score > 0.5 else 0
            ])
            
            if active_factors >= 3:
                overall_confluence += self.ict_config['multiple_confluence_bonus']
            
            overall_confluence = min(1.0, overall_confluence)
            
            return {
                'overall': overall_confluence,
                'htf_alignment': htf_score,
                'order_block': ob_score,
                'fvg': fvg_score,
                'structure': structure_score,
                'liquidity': liquidity_score,
                'active_factors': active_factors
            }
            
        except Exception as e:
            logger.error(f"Confluence calculation failed: {e}")
            return {
                'overall': 0.0,
                'htf_alignment': 0.0,
                'order_block': 0.0,
                'fvg': 0.0,
                'structure': 0.0,
                'liquidity': 0.0,
                'active_factors': 0
            }
    
    def _calculate_ict_entry_levels(self, setup_type: str, primary_ob: Optional[OrderBlockZone],
                                  supporting_fvgs: List[FVGZone], signal_direction: str,
                                  market_data: Dict) -> Optional[Dict]:
        """Calculate ICT-based entry, stop loss, and take profit levels."""
        try:
            current_price = market_data['5m']['close'].iloc[-1] if '5m' in market_data else market_data['1m']['close'].iloc[-1]
            atr = market_data['5m']['atr'].iloc[-1] if 'atr' in market_data.get('5m', {}).columns else current_price * 0.02
            
            entry_levels = {}
            
            if setup_type in ['ORDER_BLOCK', 'ORDER_BLOCK_FVG'] and primary_ob:
                # Entry at optimal Order Block level
                entry_levels['entry'] = primary_ob.optimal_entry
                
                if signal_direction == 'LONG':
                    # Stop below Order Block
                    entry_levels['stop_loss'] = primary_ob.zone_low * 0.995  # 0.5% below OB low
                    # Target at next resistance or 2:1 R:R
                    risk = entry_levels['entry'] - entry_levels['stop_loss']
                    entry_levels['take_profit'] = entry_levels['entry'] + (risk * 2)
                    # Invalidation if OB is broken significantly
                    entry_levels['invalidation'] = primary_ob.zone_low * 0.99
                    
                else:  # SHORT
                    # Stop above Order Block
                    entry_levels['stop_loss'] = primary_ob.zone_high * 1.005  # 0.5% above OB high
                    # Target at next support or 2:1 R:R
                    risk = entry_levels['stop_loss'] - entry_levels['entry']
                    entry_levels['take_profit'] = entry_levels['entry'] - (risk * 2)
                    # Invalidation if OB is broken significantly
                    entry_levels['invalidation'] = primary_ob.zone_high * 1.01
                    
            elif setup_type == 'FVG_FILL' and supporting_fvgs:
                primary_fvg = supporting_fvgs[0]
                
                if signal_direction == 'LONG':
                    # Enter at FVG low (expect bounce)
                    entry_levels['entry'] = primary_fvg.gap_low
                    # Stop below FVG
                    entry_levels['stop_loss'] = primary_fvg.gap_low * 0.995
                    # Target above FVG or next resistance
                    risk = entry_levels['entry'] - entry_levels['stop_loss']
                    entry_levels['take_profit'] = primary_fvg.gap_high + risk
                    # Invalidation if FVG is completely filled
                    entry_levels['invalidation'] = primary_fvg.gap_low * 0.995
                    
                else:  # SHORT
                    # Enter at FVG high (expect rejection)
                    entry_levels['entry'] = primary_fvg.gap_high
                    # Stop above FVG
                    entry_levels['stop_loss'] = primary_fvg.gap_high * 1.005
                    # Target below FVG or next support
                    risk = entry_levels['stop_loss'] - entry_levels['entry']
                    entry_levels['take_profit'] = primary_fvg.gap_low - risk
                    # Invalidation if FVG is completely filled
                    entry_levels['invalidation'] = primary_fvg.gap_high * 1.005
                    
            else:
                # Default structure-based levels
                entry_levels['entry'] = current_price
                
                if signal_direction == 'LONG':
                    entry_levels['stop_loss'] = current_price - (atr * 1.5)
                    entry_levels['take_profit'] = current_price + (atr * 3)
                    entry_levels['invalidation'] = current_price - (atr * 2)
                else:
                    entry_levels['stop_loss'] = current_price + (atr * 1.5)
                    entry_levels['take_profit'] = current_price - (atr * 3)
                    entry_levels['invalidation'] = current_price + (atr * 2)
            
            # Validate levels make sense
            if signal_direction == 'LONG':
                if (entry_levels['entry'] >= entry_levels['stop_loss'] and 
                    entry_levels['take_profit'] > entry_levels['entry']):
                    return entry_levels
            else:
                if (entry_levels['entry'] <= entry_levels['stop_loss'] and 
                    entry_levels['take_profit'] < entry_levels['entry']):
                    return entry_levels
            
            logger.warning("Calculated ICT levels failed validation")
            return None
            
        except Exception as e:
            logger.error(f"ICT level calculation failed: {e}")
            return None
    
    def _validate_ict_confluence(self, ict_signal: ICTProcessedSignal) -> bool:
        """Validate ICT signal confluence requirements."""
        try:
            # Overall confluence check
            if ict_signal.overall_confluence < self.ict_config['min_overall_confluence']:
                logger.debug(f"Overall confluence too low: {ict_signal.overall_confluence:.2f}")
                return False
            
            # Higher timeframe alignment check
            if ict_signal.htf_alignment_score < self.ict_config['min_htf_alignment']:
                logger.debug(f"HTF alignment too low: {ict_signal.htf_alignment_score:.2f}")
                return False
            
            # Order Block quality check (if OB-based signal)
            if (ict_signal.primary_order_block and 
                ict_signal.order_block_score < self.ict_config['min_order_block_score']):
                logger.debug(f"Order Block score too low: {ict_signal.order_block_score:.2f}")
                return False
            
            # Risk/reward validation
            entry = ict_signal.ict_entry_price
            stop = ict_signal.ict_stop_loss
            target = ict_signal.ict_take_profit
            
            if ict_signal.direction == 'LONG':
                risk = entry - stop
                reward = target - entry
            else:
                risk = stop - entry
                reward = entry - target
            
            if risk <= 0 or reward <= 0:
                logger.debug("Invalid risk/reward calculation")
                return False
            
            risk_reward_ratio = reward / risk
            if risk_reward_ratio < self.ict_config['min_risk_reward_ratio']:
                logger.debug(f"Risk/reward ratio too low: {risk_reward_ratio:.2f}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"ICT confluence validation failed: {e}")
            return False
    
    def _calculate_ict_risk_management(self, ict_signal: ICTProcessedSignal, market_data: Dict) -> None:
        """Calculate ICT-based risk management parameters."""
        try:
            # Calculate institutional risk based on market structure
            base_risk = 0.02  # 2% base risk
            
            # Adjust risk based on confluence
            confluence_multiplier = 0.5 + (ict_signal.overall_confluence * 0.5)  # 0.5 to 1.0
            adjusted_risk = base_risk * confluence_multiplier
            
            # Position size based on risk and confluence
            if self.ict_config['position_size_by_confluence']:
                size_multiplier = 0.5 + (ict_signal.overall_confluence * 0.5)
                base_position_size = self.ict_config['min_position_size']
                max_position_size = self.ict_config['max_position_size']
                
                position_size = base_position_size + (max_position_size - base_position_size) * size_multiplier
            else:
                position_size = self.ict_config['min_position_size']
            
            # Max drawdown based on setup quality
            setup_quality_multiplier = {
                'ORDER_BLOCK': 1.0,
                'ORDER_BLOCK_FVG': 1.2,
                'FVG_FILL': 0.8,
                'STRUCTURE_BREAK': 0.9
            }
            
            multiplier = setup_quality_multiplier.get(ict_signal.ict_setup_type, 1.0)
            max_drawdown = adjusted_risk * multiplier
            
            # Update signal with risk parameters
            ict_signal.institutional_risk = adjusted_risk
            ict_signal.position_size = position_size
            ict_signal.max_drawdown_allowed = max_drawdown
            
        except Exception as e:
            logger.error(f"ICT risk management calculation failed: {e}")
    
    def _set_execution_strategy(self, ict_signal: ICTProcessedSignal) -> None:
        """Set execution strategy and timing for ICT signal."""
        try:
            # Determine entry strategy based on confluence and setup
            if ict_signal.overall_confluence >= self.ict_config['market_entry_confluence_threshold']:
                ict_signal.entry_strategy = 'MARKET'
                ict_signal.execution_urgency = 'IMMEDIATE'
            elif ict_signal.primary_order_block or ict_signal.supporting_fvgs:
                ict_signal.entry_strategy = 'LIMIT_OB' if ict_signal.primary_order_block else 'LIMIT_FVG'
                ict_signal.execution_urgency = 'WITHIN_HOUR'
            else:
                ict_signal.entry_strategy = 'MARKET'
                ict_signal.execution_urgency = 'PATIENT'
            
            # Set optimal entry window
            window_minutes = self.ict_config['entry_window_minutes']
            ict_signal.optimal_entry_window = (
                datetime.now(),
                datetime.now() + timedelta(minutes=window_minutes)
            )
            
        except Exception as e:
            logger.error(f"Execution strategy setting failed: {e}")
    
    def _determine_entry_strategy(self, setup_type: str, confluence: float) -> str:
        """Determine optimal entry strategy."""
        if confluence >= 0.85:
            return 'MARKET'
        elif setup_type in ['ORDER_BLOCK', 'ORDER_BLOCK_FVG']:
            return 'LIMIT_OB'
        elif setup_type == 'FVG_FILL':
            return 'LIMIT_FVG'
        else:
            return 'MARKET'
    
    def _determine_execution_urgency(self, confluence: float) -> str:
        """Determine execution urgency based on confluence."""
        if confluence >= 0.85:
            return 'IMMEDIATE'
        elif confluence >= 0.7:
            return 'WITHIN_HOUR'
        else:
            return 'PATIENT'
    
    def _get_current_ict_session(self) -> str:
        """Get current ICT session context."""
        current_hour = datetime.now().hour
        
        if 8 <= current_hour <= 16:
            return 'LONDON'
        elif 13 <= current_hour <= 21:
            return 'NY'
        elif 22 <= current_hour or current_hour <= 8:
            return 'ASIA'
        else:
            return 'TRANSITION'
    
    def _reject_signal(self, reason: str) -> None:
        """Record signal rejection."""
        self.stats['rejected_signals'] += 1
        logger.debug(f"ICT signal rejected: {reason}")
        return None
    
    def _update_signal_stats(self, ict_signal: ICTProcessedSignal) -> None:
        """Update signal generation statistics."""
        try:
            signal_type = ict_signal.signal_type
            
            if signal_type not in self.stats['signals_by_type']:
                self.stats['signals_by_type'][signal_type] = 0
            self.stats['signals_by_type'][signal_type] += 1
            
            # Update average confluence score
            total_signals = self.stats['ict_signals_generated']
            current_avg = self.stats['avg_confluence_score']
            new_avg = (current_avg * (total_signals - 1) + ict_signal.overall_confluence) / total_signals
            self.stats['avg_confluence_score'] = new_avg
            
            # Update HTF alignment rate
            if ict_signal.htf_alignment_score > 0.6:
                htf_aligned = 1
            else:
                htf_aligned = 0
            
            current_htf_rate = self.stats['htf_alignment_rate']
            new_htf_rate = (current_htf_rate * (total_signals - 1) + htf_aligned) / total_signals
            self.stats['htf_alignment_rate'] = new_htf_rate
            
            # Count by setup type
            if 'ORDER_BLOCK' in ict_signal.ict_setup_type:
                self.stats['order_block_signals'] += 1
            elif 'FVG' in ict_signal.ict_setup_type:
                self.stats['fvg_signals'] += 1
            elif 'STRUCTURE' in ict_signal.ict_setup_type:
                self.stats['structure_signals'] += 1
                
        except Exception as e:
            logger.error(f"Statistics update failed: {e}")
    
    async def _dispatch_ict_signal(self, ict_signal: ICTProcessedSignal) -> None:
        """Dispatch ICT signal to registered handlers."""
        for handler in self.signal_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(ict_signal)
                else:
                    handler(ict_signal)
            except Exception as e:
                logger.error(f"Error in ICT signal handler {handler.__name__}: {e}")
    
    def get_ict_statistics(self) -> Dict[str, any]:
        """Get ICT signal processing statistics."""
        uptime = datetime.now() - self.stats['last_reset']
        
        total_processed = self.stats['total_alerts']
        ict_generated = self.stats['ict_signals_generated']
        
        return {
            'total_alerts_processed': total_processed,
            'ict_signals_generated': ict_generated,
            'ict_conversion_rate': ict_generated / max(1, total_processed) * 100,
            'rejected_signals': self.stats['rejected_signals'],
            'avg_confluence_score': self.stats['avg_confluence_score'],
            'htf_alignment_rate': self.stats['htf_alignment_rate'] * 100,
            'signals_by_type': self.stats['signals_by_type'],
            'order_block_signals': self.stats['order_block_signals'],
            'fvg_signals': self.stats['fvg_signals'],
            'structure_signals': self.stats['structure_signals'],
            'uptime_hours': uptime.total_seconds() / 3600
        }
    
    def reset_statistics(self) -> None:
        """Reset ICT processing statistics."""
        self.stats = {
            'total_alerts': 0,
            'ict_signals_generated': 0,
            'signals_by_type': {},
            'avg_confluence_score': 0.0,
            'htf_alignment_rate': 0.0,
            'order_block_signals': 0,
            'fvg_signals': 0,
            'structure_signals': 0,
            'rejected_signals': 0,
            'last_reset': datetime.now()
        }
        logger.info("ICT processing statistics reset")


if __name__ == "__main__":
    # Example usage and testing
    import asyncio
    logging.basicConfig(level=logging.INFO)
    
    async def test_ict_signal_handler(signal: ICTProcessedSignal):
        """Test ICT signal handler."""
        print("📡 ICT Signal Received:")
        print("   Type: {signal.signal_type}")
        print("   Direction: {signal.direction}")
        print("   Setup: {signal.ict_setup_type}")
        print("   Confluence: {signal.overall_confluence:.1%}")
        print("   Entry: ${signal.ict_entry_price:.2f}")
        print("   Stop: ${signal.ict_stop_loss:.2f}")
        print("   Target: ${signal.ict_take_profit:.2f}")
        print("   Urgency: {signal.execution_urgency}")
        print("─" * 50)
    
    async def test_ict_processor():
        """Test ICT signal processor."""
        print("🔬 Testing ICT Signal Processor...")
        
        # Initialize processor
        processor = ICTSignalProcessor()
        processor.add_signal_handler(test_ict_signal_handler)
        
        # Create test alert
        test_alert = WebhookAlert(
            timestamp=datetime.now(),
            symbol="BTC/USDT",
            action="BUY",
            price=50000.0,
            market_phase="MARKUP",
            confidence=0.8,
            stop_loss=49000.0,
            take_profit=52000.0,
            source_ip="127.0.0.1",
            signature_valid=True
        )
        
        print("Processing test alert: {test_alert.action} {test_alert.symbol}")
        
        # Process alert with ICT methodology
        ict_result = await processor.process_alert_with_ict(test_alert)
        
        if ict_result:
            print("✅ ICT Signal Generated: {ict_result.validation_status}")
        else:
            print("❌ No ICT signal generated")
        
        # Print statistics
        stats = processor.get_ict_statistics()
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                   ICT PROCESSOR STATISTICS                      ║
╠══════════════════════════════════════════════════════════════════╣
║  Alerts Processed:     {stats['total_alerts_processed']:>6}                           ║
║  ICT Signals:          {stats['ict_signals_generated']:>6}                           ║
║  Conversion Rate:      {stats['ict_conversion_rate']:>6.1f}%                          ║
║  Avg Confluence:      {stats['avg_confluence_score']:>6.1%}                          ║
║  HTF Alignment:       {stats['htf_alignment_rate']:>6.1f}%                          ║
║                                                                  ║
║  Order Block Signals:  {stats['order_block_signals']:>6}                           ║
║  FVG Signals:          {stats['fvg_signals']:>6}                           ║
║  Structure Signals:    {stats['structure_signals']:>6}                           ║
║  Rejected Signals:     {stats['rejected_signals']:>6}                           ║
╚══════════════════════════════════════════════════════════════════╝
""")
        
        print("✅ ICT Signal Processor test completed!")
    
    # Run the test
    asyncio.run(test_ict_processor())