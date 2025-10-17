#!/usr/bin/env python3
"""
ICT Timeframe Hierarchy Manager
==============================

Implements proper ICT timeframe structure for crypto trading:
- 4H: Higher timeframe bias and market direction
- 5M: Setup identification and order block selection  
- 1M: Precise entry timing and execution

This replaces the traditional multi-timeframe confusion with
a clear institutional trading hierarchy.

ICT Principle: "Trade WITH the higher timeframe bias, 
               find setups on the intermediate timeframe,
               execute on the lower timeframe."

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor

from trading.ict_analyzer import ICTAnalyzer, TrendDirection, ICTSignal
from src.utils.data_fetcher import DataFetcher
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class TimeframeRole(Enum):
    """Timeframe role in ICT hierarchy."""
    BIAS = "BIAS"           # 4H - Market direction and bias
    SETUP = "SETUP"         # 5M - Order blocks and setups
    EXECUTION = "EXECUTION"  # 1M - Precise entry timing

@dataclass
class TimeframeAnalysis:
    """Analysis result for a specific timeframe."""
    timeframe: str
    role: TimeframeRole
    symbol: str
    timestamp: datetime
    
    # ICT Analysis components
    ict_analysis: Dict
    trend_direction: TrendDirection
    trend_strength: float
    
    # Key levels and zones
    key_levels: List[float]
    order_blocks: List
    liquidity_zones: List
    
    # Signal information
    signals: List[ICTSignal]
    signal_count: int
    highest_confidence: float
    
    # Confluence scoring
    confluence_score: float
    alignment_with_htf: bool

@dataclass
class HierarchyAnalysis:
    """Complete multi-timeframe hierarchy analysis."""
    symbol: str
    timestamp: datetime
    
    # Individual timeframe analyses
    bias_analysis: TimeframeAnalysis      # 4H analysis
    setup_analysis: TimeframeAnalysis     # 5M analysis  
    execution_analysis: TimeframeAnalysis # 1M analysis
    
    # Cross-timeframe confluence
    timeframe_alignment: bool
    confluence_score: float
    
    # Final trading decision
    trading_bias: TrendDirection
    setup_quality: str              # 'HIGH', 'MEDIUM', 'LOW', 'NONE'
    execution_signals: List[ICTSignal]
    
    # Risk management
    overall_confidence: float
    recommended_position_size: float
    
    # Next analysis timing
    next_bias_update: datetime      # When to update 4H bias
    next_setup_update: datetime     # When to update 5M setups
    continuous_execution: bool      # Whether to continuously monitor 1M


class ICTTimeframeHierarchy:
    """
    Manages ICT timeframe hierarchy for institutional trading approach.
    
    This class coordinates analysis across multiple timeframes following
    ICT methodology to eliminate confusion and provide clear trade direction.
    """
    
    def __init__(self, config_path: str = "project/configuration/"):
        """Initialize timeframe hierarchy manager."""
        self.config_path = config_path
        self.config_loader = ConfigLoader(config_path)
        self.data_fetcher = DataFetcher(config_path)
        
        # Initialize ICT analyzers for each timeframe
        self.ict_analyzer = ICTAnalyzer(self._load_ict_config())
        
        # Load hierarchy configuration
        self.hierarchy_config = self._load_hierarchy_config()
        
        # Analysis cache
        self.bias_cache = {}        # 4H bias cache (longer TTL)
        self.setup_cache = {}       # 5M setup cache (medium TTL)
        self.execution_cache = {}   # 1M execution cache (short TTL)
        
        # Update intervals (in minutes)
        self.bias_update_interval = 240     # 4 hours
        self.setup_update_interval = 30     # 30 minutes
        self.execution_update_interval = 5  # 5 minutes
        
        # Thread pool for parallel analysis
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        logger.info("ICT Timeframe Hierarchy Manager initialized")
    
    def _load_ict_config(self) -> Dict:
        """Load ICT analyzer configuration."""
        try:
            return self.config_loader.get_config("ict_analysis")
        except Exception as e:
            logger.warning(f"Failed to load ICT config: {e}")
            return {}
    
    def _load_hierarchy_config(self) -> Dict:
        """Load timeframe hierarchy configuration."""
        try:
            config = self.config_loader.get_config("timeframe_hierarchy")
        except Exception as e:
            logger.warning(f"Failed to load hierarchy config: {e}")
            config = {}
        
        # Default configuration
        defaults = {
            # Timeframe mappings
            'bias_timeframe': '4H',
            'setup_timeframe': '5T',
            'execution_timeframe': '1T',
            
            # Data requirements
            'bias_data_periods': 200,       # 200 x 4H = ~33 days
            'setup_data_periods': 500,      # 500 x 5M = ~41 hours
            'execution_data_periods': 100,  # 100 x 1M = ~1.7 hours
            
            # Cache TTL (time to live in minutes)
            'bias_cache_ttl': 240,          # 4 hours
            'setup_cache_ttl': 30,          # 30 minutes
            'execution_cache_ttl': 5,       # 5 minutes
            
            # Confluence requirements
            'min_timeframe_alignment': 0.7,  # 70% alignment required
            'bias_weight': 0.5,             # 50% weight to bias timeframe
            'setup_weight': 0.3,            # 30% weight to setup timeframe
            'execution_weight': 0.2,        # 20% weight to execution timeframe
            
            # Signal filtering
            'min_confluence_score': 0.6,    # Minimum confluence for signals
            'require_bias_alignment': True, # Must align with 4H bias
            'max_signals_per_symbol': 3,    # Maximum concurrent signals
            
            # Risk management
            'confluence_position_scaling': True, # Scale position by confluence
            'max_position_size': 0.05,      # 5% max position size
            'min_position_size': 0.01,      # 1% min position size
        }
        
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
        
        return config
    
    async def analyze_symbol_hierarchy(self, symbol: str) -> HierarchyAnalysis:
        """
        Perform complete ICT hierarchy analysis for a symbol.
        
        Args:
            symbol: Trading pair to analyze
            
        Returns:
            Complete hierarchy analysis with signals
        """
        try:
            logger.info(f"Starting ICT hierarchy analysis for {symbol}")
            
            # Check cache first
            cached_analysis = self._get_cached_hierarchy(symbol)
            if cached_analysis:
                return cached_analysis
            
            # Fetch data for all timeframes concurrently
            data_tasks = [
                self._fetch_timeframe_data(symbol, self.hierarchy_config['bias_timeframe'], 
                                         self.hierarchy_config['bias_data_periods']),
                self._fetch_timeframe_data(symbol, self.hierarchy_config['setup_timeframe'],
                                         self.hierarchy_config['setup_data_periods']),
                self._fetch_timeframe_data(symbol, self.hierarchy_config['execution_timeframe'],
                                         self.hierarchy_config['execution_data_periods'])
            ]
            
            bias_data, setup_data, execution_data = await asyncio.gather(*data_tasks)
            
            # Perform ICT analysis on each timeframe concurrently
            analysis_tasks = [
                self._analyze_bias_timeframe(symbol, bias_data),
                self._analyze_setup_timeframe(symbol, setup_data),
                self._analyze_execution_timeframe(symbol, execution_data)
            ]
            
            bias_analysis, setup_analysis, execution_analysis = await asyncio.gather(*analysis_tasks)
            
            # Calculate cross-timeframe confluence
            confluence_data = self._calculate_timeframe_confluence(
                bias_analysis, setup_analysis, execution_analysis
            )
            
            # Generate final trading decisions
            trading_decisions = self._generate_trading_decisions(
                bias_analysis, setup_analysis, execution_analysis, confluence_data
            )
            
            # Create complete hierarchy analysis
            hierarchy_analysis = HierarchyAnalysis(
                symbol=symbol,
                timestamp=datetime.now(),
                bias_analysis=bias_analysis,
                setup_analysis=setup_analysis,
                execution_analysis=execution_analysis,
                timeframe_alignment=confluence_data['alignment'],
                confluence_score=confluence_data['score'],
                trading_bias=trading_decisions['bias'],
                setup_quality=trading_decisions['setup_quality'],
                execution_signals=trading_decisions['signals'],
                overall_confidence=trading_decisions['confidence'],
                recommended_position_size=trading_decisions['position_size'],
                next_bias_update=datetime.now() + timedelta(minutes=self.bias_update_interval),
                next_setup_update=datetime.now() + timedelta(minutes=self.setup_update_interval),
                continuous_execution=True
            )
            
            # Cache the analysis
            self._cache_hierarchy_analysis(symbol, hierarchy_analysis)
            
            logger.info(f"Hierarchy analysis completed for {symbol}: "
                       f"{len(trading_decisions['signals'])} signals, "
                       f"{confluence_data['score']:.2f} confluence")
            
            return hierarchy_analysis
            
        except Exception as e:
            logger.error(f"Hierarchy analysis failed for {symbol}: {e}")
            return self._get_empty_hierarchy_analysis(symbol)
    
    async def _fetch_timeframe_data(self, symbol: str, timeframe: str, periods: int) -> pd.DataFrame:
        """Fetch OHLCV data for specific timeframe."""
        try:
            # Convert timeframe format if needed
            tf_mapping = {
                '4H': '4h',
                '5T': '5m', 
                '1T': '1m'
            }
            api_timeframe = tf_mapping.get(timeframe, timeframe)
            
            # Fetch data
            data = await self.data_fetcher.fetch_ohlcv_async(
                symbol=symbol,
                timeframe=api_timeframe,
                limit=periods
            )
            
            if data is None or data.empty:
                raise ValueError(f"No data received for {symbol} {timeframe}")
            
            logger.debug(f"Fetched {len(data)} periods for {symbol} {timeframe}")
            return data
            
        except Exception as e:
            logger.error(f"Data fetch failed for {symbol} {timeframe}: {e}")
            # Return empty DataFrame with proper structure
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    
    async def _analyze_bias_timeframe(self, symbol: str, data: pd.DataFrame) -> TimeframeAnalysis:
        """
        Analyze 4H bias timeframe for market direction.
        
        ICT Principle: 4H timeframe provides overall market bias.
        All lower timeframe trades must align with this bias.
        """
        try:
            if data.empty:
                return self._get_empty_timeframe_analysis(symbol, '4H', TimeframeRole.BIAS)
            
            # Run ICT analysis on 4H data
            ict_result = self.ict_analyzer.analyze_market_structure(
                data, symbol, '4H'
            )
            
            # Extract key information for bias determination
            trend_direction = ict_result['htf_bias']['trend_direction']
            trend_strength = ict_result['htf_bias']['trend_strength']
            
            # Key levels from 4H perspective
            key_levels = self._extract_key_levels(ict_result, 'bias')
            
            # Calculate bias confluence score
            confluence_score = self._calculate_bias_confluence(ict_result)
            
            bias_analysis = TimeframeAnalysis(
                timeframe='4H',
                role=TimeframeRole.BIAS,
                symbol=symbol,
                timestamp=datetime.now(),
                ict_analysis=ict_result,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                key_levels=key_levels,
                order_blocks=ict_result['order_blocks'],
                liquidity_zones=ict_result['liquidity_zones'],
                signals=ict_result['ict_signals'],
                signal_count=len(ict_result['ict_signals']),
                highest_confidence=max([s.confidence for s in ict_result['ict_signals']], default=0),
                confluence_score=confluence_score,
                alignment_with_htf=True  # 4H is the HTF
            )
            
            logger.debug(f"4H Bias Analysis: {trend_direction.value} trend, "
                        f"{trend_strength:.2f} strength")
            
            return bias_analysis
            
        except Exception as e:
            logger.error(f"4H bias analysis failed for {symbol}: {e}")
            return self._get_empty_timeframe_analysis(symbol, '4H', TimeframeRole.BIAS)
    
    async def _analyze_setup_timeframe(self, symbol: str, data: pd.DataFrame) -> TimeframeAnalysis:
        """
        Analyze 5M setup timeframe for order blocks and entry setups.
        
        ICT Principle: 5M timeframe identifies specific order blocks
        and setup patterns for trade execution.
        """
        try:
            if data.empty:
                return self._get_empty_timeframe_analysis(symbol, '5M', TimeframeRole.SETUP)
            
            # Run ICT analysis on 5M data
            ict_result = self.ict_analyzer.analyze_market_structure(
                data, symbol, '5M'
            )
            
            # Focus on order blocks and setups
            trend_direction = ict_result['htf_bias']['trend_direction']
            trend_strength = ict_result['htf_bias']['trend_strength']
            
            # Key setup levels
            key_levels = self._extract_key_levels(ict_result, 'setup')
            
            # Calculate setup quality confluence
            confluence_score = self._calculate_setup_confluence(ict_result)
            
            setup_analysis = TimeframeAnalysis(
                timeframe='5M',
                role=TimeframeRole.SETUP,
                symbol=symbol,
                timestamp=datetime.now(),
                ict_analysis=ict_result,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                key_levels=key_levels,
                order_blocks=ict_result['order_blocks'],
                liquidity_zones=ict_result['liquidity_zones'],
                signals=ict_result['ict_signals'],
                signal_count=len(ict_result['ict_signals']),
                highest_confidence=max([s.confidence for s in ict_result['ict_signals']], default=0),
                confluence_score=confluence_score,
                alignment_with_htf=False  # Will be calculated later
            )
            
            logger.debug(f"5M Setup Analysis: {len(ict_result['order_blocks'])} order blocks, "
                        f"{len(ict_result['ict_signals'])} signals")
            
            return setup_analysis
            
        except Exception as e:
            logger.error(f"5M setup analysis failed for {symbol}: {e}")
            return self._get_empty_timeframe_analysis(symbol, '5M', TimeframeRole.SETUP)
    
    async def _analyze_execution_timeframe(self, symbol: str, data: pd.DataFrame) -> TimeframeAnalysis:
        """
        Analyze 1M execution timeframe for precise entry timing.
        
        ICT Principle: 1M timeframe provides precise entry and exit timing
        based on higher timeframe setups.
        """
        try:
            if data.empty:
                return self._get_empty_timeframe_analysis(symbol, '1M', TimeframeRole.EXECUTION)
            
            # Run ICT analysis on 1M data (focused on timing)
            ict_result = self.ict_analyzer.analyze_market_structure(
                data, symbol, '1M'
            )
            
            # Focus on execution timing
            trend_direction = ict_result['htf_bias']['trend_direction']
            trend_strength = ict_result['htf_bias']['trend_strength']
            
            # Execution-focused levels
            key_levels = self._extract_key_levels(ict_result, 'execution')
            
            # Calculate execution timing score
            confluence_score = self._calculate_execution_confluence(ict_result)
            
            execution_analysis = TimeframeAnalysis(
                timeframe='1M',
                role=TimeframeRole.EXECUTION,
                symbol=symbol,
                timestamp=datetime.now(),
                ict_analysis=ict_result,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                key_levels=key_levels,
                order_blocks=ict_result['order_blocks'],
                liquidity_zones=ict_result['liquidity_zones'],
                signals=ict_result['ict_signals'],
                signal_count=len(ict_result['ict_signals']),
                highest_confidence=max([s.confidence for s in ict_result['ict_signals']], default=0),
                confluence_score=confluence_score,
                alignment_with_htf=False  # Will be calculated later
            )
            
            logger.debug(f"1M Execution Analysis: {confluence_score:.2f} execution score")
            
            return execution_analysis
            
        except Exception as e:
            logger.error(f"1M execution analysis failed for {symbol}: {e}")
            return self._get_empty_timeframe_analysis(symbol, '1M', TimeframeRole.EXECUTION)
    
    def _calculate_timeframe_confluence(self, bias_analysis: TimeframeAnalysis,
                                      setup_analysis: TimeframeAnalysis,
                                      execution_analysis: TimeframeAnalysis) -> Dict:
        """Calculate confluence across all timeframes."""
        try:
            # Trend direction alignment
            bias_direction = bias_analysis.trend_direction
            setup_direction = setup_analysis.trend_direction
            execution_direction = execution_analysis.trend_direction
            
            # Check alignment
            directions_aligned = (
                bias_direction == setup_direction == execution_direction and
                bias_direction != TrendDirection.CONSOLIDATION
            )
            
            # Calculate weighted confluence score
            bias_weight = self.hierarchy_config['bias_weight']
            setup_weight = self.hierarchy_config['setup_weight']
            execution_weight = self.hierarchy_config['execution_weight']
            
            confluence_score = (
                bias_analysis.confluence_score * bias_weight +
                setup_analysis.confluence_score * setup_weight +
                execution_analysis.confluence_score * execution_weight
            )
            
            # Trend strength alignment bonus
            avg_trend_strength = (
                bias_analysis.trend_strength +
                setup_analysis.trend_strength +
                execution_analysis.trend_strength
            ) / 3
            
            if directions_aligned and avg_trend_strength > 0.7:
                confluence_score *= 1.2  # 20% bonus for strong alignment
            
            # Check minimum alignment threshold
            alignment_meets_threshold = confluence_score >= self.hierarchy_config['min_timeframe_alignment']
            
            return {
                'alignment': directions_aligned and alignment_meets_threshold,
                'score': min(1.0, confluence_score),
                'direction_alignment': directions_aligned,
                'strength_alignment': avg_trend_strength,
                'bias_direction': bias_direction,
                'setup_direction': setup_direction,
                'execution_direction': execution_direction
            }
            
        except Exception as e:
            logger.error(f"Confluence calculation failed: {e}")
            return {
                'alignment': False,
                'score': 0.0,
                'direction_alignment': False,
                'strength_alignment': 0.0,
                'bias_direction': TrendDirection.CONSOLIDATION,
                'setup_direction': TrendDirection.CONSOLIDATION,
                'execution_direction': TrendDirection.CONSOLIDATION
            }
    
    def _generate_trading_decisions(self, bias_analysis: TimeframeAnalysis,
                                  setup_analysis: TimeframeAnalysis,
                                  execution_analysis: TimeframeAnalysis,
                                  confluence_data: Dict) -> Dict:
        """Generate final trading decisions based on hierarchy analysis."""
        try:
            # Overall trading bias from 4H
            trading_bias = bias_analysis.trend_direction
            
            # Setup quality assessment
            setup_quality = self._assess_setup_quality(setup_analysis, confluence_data)
            
            # Filter and combine signals
            execution_signals = self._filter_execution_signals(
                bias_analysis, setup_analysis, execution_analysis, confluence_data
            )
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(
                bias_analysis, setup_analysis, execution_analysis, confluence_data
            )
            
            # Calculate recommended position size
            position_size = self._calculate_position_size(
                confluence_data['score'], overall_confidence
            )
            
            return {
                'bias': trading_bias,
                'setup_quality': setup_quality,
                'signals': execution_signals,
                'confidence': overall_confidence,
                'position_size': position_size
            }
            
        except Exception as e:
            logger.error(f"Trading decision generation failed: {e}")
            return {
                'bias': TrendDirection.CONSOLIDATION,
                'setup_quality': 'NONE',
                'signals': [],
                'confidence': 0.0,
                'position_size': 0.0
            }
    
    def _assess_setup_quality(self, setup_analysis: TimeframeAnalysis, 
                            confluence_data: Dict) -> str:
        """Assess the quality of trading setups."""
        try:
            # Base quality on confluence score and signal count
            score = confluence_data['score']
            signal_count = setup_analysis.signal_count
            highest_confidence = setup_analysis.highest_confidence
            
            if score >= 0.8 and signal_count >= 2 and highest_confidence >= 0.8:
                return 'HIGH'
            elif score >= 0.6 and signal_count >= 1 and highest_confidence >= 0.6:
                return 'MEDIUM'
            elif score >= 0.4 and signal_count >= 1:
                return 'LOW'
            else:
                return 'NONE'
                
        except Exception as e:
            logger.error(f"Setup quality assessment failed: {e}")
            return 'NONE'
    
    def _filter_execution_signals(self, bias_analysis: TimeframeAnalysis,
                                setup_analysis: TimeframeAnalysis,
                                execution_analysis: TimeframeAnalysis,
                                confluence_data: Dict) -> List[ICTSignal]:
        """Filter and rank signals for execution."""
        try:
            all_signals = []
            
            # Collect signals from all timeframes
            all_signals.extend(setup_analysis.signals)
            all_signals.extend(execution_analysis.signals)
            
            # Filter based on confluence requirements
            filtered_signals = []
            
            for signal in all_signals:
                # Must align with 4H bias if required
                if self.hierarchy_config['require_bias_alignment']:
                    if not self._signal_aligns_with_bias(signal, bias_analysis.trend_direction):
                        continue
                
                # Must meet minimum confluence score
                if signal.confidence < self.hierarchy_config['min_confluence_score']:
                    continue
                
                # Add to filtered list
                filtered_signals.append(signal)
            
            # Sort by confidence and limit count
            filtered_signals.sort(key=lambda x: x.confidence, reverse=True)
            max_signals = self.hierarchy_config['max_signals_per_symbol']
            
            return filtered_signals[:max_signals]
            
        except Exception as e:
            logger.error(f"Signal filtering failed: {e}")
            return []
    
    def _signal_aligns_with_bias(self, signal: ICTSignal, bias_direction: TrendDirection) -> bool:
        """Check if signal aligns with higher timeframe bias."""
        if bias_direction == TrendDirection.BULLISH:
            return signal.direction == 'LONG'
        elif bias_direction == TrendDirection.BEARISH:
            return signal.direction == 'SHORT'
        else:
            return False  # Don't trade in consolidation
    
    def _calculate_overall_confidence(self, bias_analysis: TimeframeAnalysis,
                                    setup_analysis: TimeframeAnalysis,
                                    execution_analysis: TimeframeAnalysis,
                                    confluence_data: Dict) -> float:
        """Calculate overall confidence score."""
        try:
            # Weighted combination of timeframe confidences
            bias_weight = self.hierarchy_config['bias_weight']
            setup_weight = self.hierarchy_config['setup_weight']
            execution_weight = self.hierarchy_config['execution_weight']
            
            overall_confidence = (
                bias_analysis.highest_confidence * bias_weight +
                setup_analysis.highest_confidence * setup_weight +
                execution_analysis.highest_confidence * execution_weight
            )
            
            # Confluence bonus
            confluence_bonus = confluence_data['score'] * 0.2
            
            return min(1.0, overall_confidence + confluence_bonus)
            
        except Exception as e:
            logger.error(f"Overall confidence calculation failed: {e}")
            return 0.0
    
    def _calculate_position_size(self, confluence_score: float, confidence: float) -> float:
        """Calculate recommended position size based on confluence."""
        try:
            if not self.hierarchy_config['confluence_position_scaling']:
                return self.hierarchy_config['min_position_size']
            
            # Scale position by confluence and confidence
            base_size = self.hierarchy_config['min_position_size']
            max_size = self.hierarchy_config['max_position_size']
            
            # Combined scaling factor
            scaling_factor = (confluence_score + confidence) / 2
            
            position_size = base_size + (max_size - base_size) * scaling_factor
            
            return min(max_size, max(base_size, position_size))
            
        except Exception as e:
            logger.error(f"Position size calculation failed: {e}")
            return self.hierarchy_config['min_position_size']
    
    # Helper methods for level extraction and scoring
    
    def _extract_key_levels(self, ict_result: Dict, analysis_type: str) -> List[float]:
        """Extract key levels based on analysis type."""
        try:
            levels = []
            
            if analysis_type == 'bias':
                # 4H key levels - major support/resistance
                levels.extend(ict_result['htf_bias'].get('key_levels', []))
                
            elif analysis_type == 'setup':
                # 5M setup levels - order blocks and liquidity
                for ob in ict_result['order_blocks']:
                    levels.extend([ob.high, ob.low])
                for lz in ict_result['liquidity_zones']:
                    levels.append(lz.level)
                    
            elif analysis_type == 'execution':
                # 1M execution levels - precise entry/exit
                for fvg in ict_result['fair_value_gaps']:
                    levels.extend([fvg.gap_high, fvg.gap_low])
            
            return sorted(list(set(levels)))  # Remove duplicates and sort
            
        except Exception as e:
            logger.error(f"Key level extraction failed: {e}")
            return []
    
    def _calculate_bias_confluence(self, ict_result: Dict) -> float:
        """Calculate confluence score for bias timeframe."""
        try:
            # Base score from trend strength
            base_score = ict_result['htf_bias']['trend_strength']
            
            # Bonus for clear market structure
            structure_bonus = 0.1 if ict_result['market_summary']['market_structure'] != 'UNKNOWN' else 0
            
            # Bonus for multiple confirmations
            signal_bonus = min(0.2, len(ict_result['ict_signals']) * 0.05)
            
            return min(1.0, base_score + structure_bonus + signal_bonus)
            
        except Exception as e:
            logger.error(f"Bias confluence calculation failed: {e}")
            return 0.5
    
    def _calculate_setup_confluence(self, ict_result: Dict) -> float:
        """Calculate confluence score for setup timeframe."""
        try:
            # Base score from order block quality
            ob_score = min(1.0, len(ict_result['order_blocks']) * 0.2)
            
            # FVG alignment bonus
            fvg_bonus = min(0.2, len(ict_result['fair_value_gaps']) * 0.05)
            
            # Signal confidence bonus
            signal_confidences = [s.confidence for s in ict_result['ict_signals']]
            signal_bonus = max(signal_confidences, default=0) * 0.3
            
            return min(1.0, ob_score + fvg_bonus + signal_bonus)
            
        except Exception as e:
            logger.error(f"Setup confluence calculation failed: {e}")
            return 0.5
    
    def _calculate_execution_confluence(self, ict_result: Dict) -> float:
        """Calculate confluence score for execution timeframe."""
        try:
            # Base score from timing precision
            timing_score = 0.6  # Base timing score
            
            # Recent structure break bonus
            recent_breaks = len([
                sb for sb in ict_result['structure_analysis']['structure_breaks']
                if (datetime.now() - sb.timestamp).total_seconds() < 3600  # Last hour
            ])
            break_bonus = min(0.3, recent_breaks * 0.1)
            
            # Liquidity sweep bonus
            liquidity_bonus = min(0.1, len(ict_result['liquidity_zones']) * 0.02)
            
            return min(1.0, timing_score + break_bonus + liquidity_bonus)
            
        except Exception as e:
            logger.error(f"Execution confluence calculation failed: {e}")
            return 0.5
    
    # Cache management methods
    
    def _get_cached_hierarchy(self, symbol: str) -> Optional[HierarchyAnalysis]:
        """Get cached hierarchy analysis if still valid."""
        try:
            cache_key = f"{symbol}_hierarchy"
            
            # Check if we have cached analysis
            if cache_key in self.setup_cache:
                cached_analysis, cache_time = self.setup_cache[cache_key]
                
                # Check if cache is still valid
                if (datetime.now() - cache_time).total_seconds() < self.setup_update_interval * 60:
                    logger.debug(f"Using cached hierarchy analysis for {symbol}")
                    return cached_analysis
            
            return None
            
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
            return None
    
    def _cache_hierarchy_analysis(self, symbol: str, analysis: HierarchyAnalysis) -> None:
        """Cache hierarchy analysis with timestamp."""
        try:
            cache_key = f"{symbol}_hierarchy"
            self.setup_cache[cache_key] = (analysis, datetime.now())
            
            # Clean old cache entries
            self._clean_cache()
            
        except Exception as e:
            logger.error(f"Cache storage failed: {e}")
    
    def _clean_cache(self) -> None:
        """Clean expired cache entries."""
        try:
            current_time = datetime.now()
            expired_keys = []
            
            for cache_dict, ttl_minutes in [
                (self.bias_cache, self.hierarchy_config['bias_cache_ttl']),
                (self.setup_cache, self.hierarchy_config['setup_cache_ttl']),
                (self.execution_cache, self.hierarchy_config['execution_cache_ttl'])
            ]:
                for key, (data, cache_time) in cache_dict.items():
                    if (current_time - cache_time).total_seconds() > ttl_minutes * 60:
                        expired_keys.append((cache_dict, key))
            
            for cache_dict, key in expired_keys:
                del cache_dict[key]
                
        except Exception as e:
            logger.error(f"Cache cleaning failed: {e}")
    
    # Empty analysis generators
    
    def _get_empty_timeframe_analysis(self, symbol: str, timeframe: str, 
                                    role: TimeframeRole) -> TimeframeAnalysis:
        """Get empty timeframe analysis on error."""
        return TimeframeAnalysis(
            timeframe=timeframe,
            role=role,
            symbol=symbol,
            timestamp=datetime.now(),
            ict_analysis={},
            trend_direction=TrendDirection.CONSOLIDATION,
            trend_strength=0.0,
            key_levels=[],
            order_blocks=[],
            liquidity_zones=[],
            signals=[],
            signal_count=0,
            highest_confidence=0.0,
            confluence_score=0.0,
            alignment_with_htf=False
        )
    
    def _get_empty_hierarchy_analysis(self, symbol: str) -> HierarchyAnalysis:
        """Get empty hierarchy analysis on error."""
        empty_bias = self._get_empty_timeframe_analysis(symbol, '4H', TimeframeRole.BIAS)
        empty_setup = self._get_empty_timeframe_analysis(symbol, '5M', TimeframeRole.SETUP)
        empty_execution = self._get_empty_timeframe_analysis(symbol, '1M', TimeframeRole.EXECUTION)
        
        return HierarchyAnalysis(
            symbol=symbol,
            timestamp=datetime.now(),
            bias_analysis=empty_bias,
            setup_analysis=empty_setup,
            execution_analysis=empty_execution,
            timeframe_alignment=False,
            confluence_score=0.0,
            trading_bias=TrendDirection.CONSOLIDATION,
            setup_quality='NONE',
            execution_signals=[],
            overall_confidence=0.0,
            recommended_position_size=0.0,
            next_bias_update=datetime.now() + timedelta(hours=4),
            next_setup_update=datetime.now() + timedelta(minutes=30),
            continuous_execution=False
        )
    
    async def get_trading_summary(self, symbol: str) -> Dict:
        """Get quick trading summary for a symbol."""
        try:
            analysis = await self.analyze_symbol_hierarchy(symbol)
            
            return {
                'symbol': symbol,
                'timestamp': analysis.timestamp,
                'trading_bias': analysis.trading_bias.value,
                'setup_quality': analysis.setup_quality,
                'signal_count': len(analysis.execution_signals),
                'highest_confidence': analysis.overall_confidence,
                'timeframe_alignment': analysis.timeframe_alignment,
                'confluence_score': analysis.confluence_score,
                'recommended_position_size': analysis.recommended_position_size,
                'next_update': analysis.next_setup_update,
                'trading_recommendation': self._get_trading_recommendation(analysis)
            }
            
        except Exception as e:
            logger.error(f"Trading summary failed for {symbol}: {e}")
            return {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'trading_bias': 'CONSOLIDATION',
                'setup_quality': 'NONE',
                'signal_count': 0,
                'highest_confidence': 0.0,
                'timeframe_alignment': False,
                'confluence_score': 0.0,
                'recommended_position_size': 0.0,
                'next_update': datetime.now(),
                'trading_recommendation': 'NO_TRADE'
            }
    
    def _get_trading_recommendation(self, analysis: HierarchyAnalysis) -> str:
        """Get overall trading recommendation."""
        if analysis.setup_quality == 'HIGH' and analysis.timeframe_alignment:
            return 'STRONG_BUY' if analysis.trading_bias == TrendDirection.BULLISH else 'STRONG_SELL'
        elif analysis.setup_quality == 'MEDIUM' and analysis.confluence_score > 0.6:
            return 'MODERATE_BUY' if analysis.trading_bias == TrendDirection.BULLISH else 'MODERATE_SELL'
        elif analysis.setup_quality == 'LOW':
            return 'WEAK_SIGNAL'
        else:
            return 'NO_TRADE'


if __name__ == "__main__":
    # Example usage and testing
    import asyncio
    logging.basicConfig(level=logging.INFO)
    
    async def test_hierarchy():
        """Test the ICT hierarchy system."""
        print("🔬 Testing ICT Timeframe Hierarchy System...")
        
        # Initialize hierarchy manager
        hierarchy = ICTTimeframeHierarchy()
        
        # Test with BTC/USDT
        print("📊 Analyzing BTC/USDT hierarchy...")
        analysis = await hierarchy.analyze_symbol_hierarchy("BTC/USDT")
        
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                  ICT HIERARCHY ANALYSIS RESULTS                 ║
╠══════════════════════════════════════════════════════════════════╣
║  Symbol: {analysis.symbol:<20} Time: {analysis.timestamp.strftime('%H:%M:%S')}            ║
║                                                                  ║
║  📈 Trading Bias (4H): {analysis.trading_bias.value:<15}                      ║
║  🎯 Setup Quality:     {analysis.setup_quality:<15}                      ║
║  🔥 Signal Count:      {len(analysis.execution_signals):<15}                      ║
║  📊 Confluence:        {analysis.confluence_score:.2f}                                ║
║  ⚡ Timeframe Align:   {'✅' if analysis.timeframe_alignment else '❌'}                                 ║
║                                                                  ║
║  💡 Overall Confidence: {analysis.overall_confidence:.1%}                            ║
║  💰 Position Size:      {analysis.recommended_position_size:.1%}                            ║
╚══════════════════════════════════════════════════════════════════╝
""")
        
        # Show individual timeframe results
        print("🕐 Individual Timeframe Analysis:")
        print(f"  4H Bias:      {analysis.bias_analysis.trend_direction.value} ({analysis.bias_analysis.trend_strength:.2f})")
        print(f"  5M Setup:     {len(analysis.setup_analysis.order_blocks)} OBs, {analysis.setup_analysis.signal_count} signals")
        print(f"  1M Execution: {analysis.execution_analysis.confluence_score:.2f} timing score")
        
        if analysis.execution_signals:
            print(f"\n📡 Execution Signals:")
            for i, signal in enumerate(analysis.execution_signals[:3], 1):
                print(f"  {i}. {signal.direction} - {signal.confidence:.1%} confidence")
                print(f"     Entry: ${signal.entry_price:.2f}, R:R = {signal.risk_reward_ratio:.1f}")
        
        # Get trading summary
        summary = await hierarchy.get_trading_summary("BTC/USDT")
        print(f"\n🎯 Trading Recommendation: {summary['trading_recommendation']}")
        
        print("✅ ICT Hierarchy test completed!")
    
    # Run the test
    asyncio.run(test_hierarchy())