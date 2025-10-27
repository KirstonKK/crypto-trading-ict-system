"""
ICT Strategy Simulation Engine for Backtesting
==============================================

This module integrates the ICT Enhanced Monitor signal generation logic
into the backtesting framework for comprehensive strategy validation.

Features:
- ICT Smart Money Concept analysis
- Multi-timeframe confluence analysis (4H direction, 15m/5m execution)
- Market regime detection and adaptation
- Supply/demand zone identification
- Liquidity level analysis and sweeps
- Fair Value Gap detection
- Order block analysis
- Session-based timing optimization
- Enhanced risk management (1% fixed risk, dynamic RR tiers)

Technical Framework:
- Market structure shift detection
- Premium/discount zone analysis
- Volume imbalance identification
- Session multiplier calculations
- Directional bias filtering

Author: GitHub Copilot Trading Algorithm  
Date: October 2025
"""

import logging
import os
import sys
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import time

# Add path for imports
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(project_root)

# Add utils directory to path for direct imports
utils_path = os.path.join(project_root, 'utils')
sys.path.append(utils_path)

# Setup logger first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _try_import(module_name: str):
    """Try multiple import paths for a module and return the module or None."""
    try:
        return __import__(module_name, fromlist=['*'])
    except ImportError:
        return None

# Robust import logic: try both package-style (utils.<module>) and flat module name
CryptoPairs = None
RiskManager = None
VolatilityAnalyzer = None
CorrelationAnalyzer = None
SignalQualityAnalyzer = None
MeanReversionAnalyzer = None

_cmod = _try_import('crypto_pairs') or _try_import('utils.crypto_pairs') or _try_import('src.utils.crypto_pairs')
if _cmod:
    CryptoPairs = getattr(_cmod, 'CryptoPairs', None)

_rmod = _try_import('risk_management') or _try_import('utils.risk_management') or _try_import('src.utils.risk_management')
if _rmod:
    RiskManager = getattr(_rmod, 'RiskManager', None)

_vmod = _try_import('volatility_indicators') or _try_import('utils.volatility_indicators') or _try_import('src.utils.volatility_indicators')
if _vmod:
    VolatilityAnalyzer = getattr(_vmod, 'VolatilityAnalyzer', None)

_cormod = _try_import('correlation_matrix') or _try_import('utils.correlation_matrix') or _try_import('src.utils.correlation_matrix')
if _cormod:
    CorrelationAnalyzer = getattr(_cormod, 'CorrelationAnalyzer', None)

_sqmod = _try_import('signal_quality') or _try_import('utils.signal_quality') or _try_import('src.utils.signal_quality')
if _sqmod:
    SignalQualityAnalyzer = getattr(_sqmod, 'SignalQualityAnalyzer', None)

_mrmod = _try_import('mean_reversion') or _try_import('utils.mean_reversion') or _try_import('src.utils.mean_reversion')
if _mrmod:
    MeanReversionAnalyzer = getattr(_mrmod, 'MeanReversionAnalyzer', None)

if not any([CryptoPairs, RiskManager, VolatilityAnalyzer, CorrelationAnalyzer, SignalQualityAnalyzer, MeanReversionAnalyzer]):
    logger.warning('Could not import any utility modules from expected paths; proceeding with None defaults')

@dataclass
class ICTTradingSignal:
    """Enhanced ICT trading signal with confluence analysis."""
    timestamp: pd.Timestamp
    symbol: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0.0 to 1.0
    ict_confidence: float  # Base ICT confluence score
    ml_boost: float  # ML enhancement (if available)
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    risk_amount: float
    risk_reward_ratio: int  # Discrete tier: 3, 5, 8
    market_regime: str  # 'trending', 'sideways'
    timeframe: str  # '4h', '15m', '5m'
    confluence_factors: List[str]
    confluence_score: float
    session_multiplier: float
    directional_bias: Dict
    dynamic_rr_calculation: Dict
    indicators: Dict[str, float]
    reasoning: str

@dataclass 
class MultiTimeframeData:
    """Container for multi-timeframe OHLCV data."""
    tf_4h: pd.DataFrame
    tf_15m: pd.DataFrame
    tf_5m: pd.DataFrame
    current_index_4h: int
    current_index_15m: int
    current_index_5m: int

class ICTStrategyEngine:
    """
    Enhanced ICT Strategy Engine with multi-timeframe analysis.
    
    Implements the full ICT methodology:
    - 4H timeframe for directional bias and market structure
    - 15m timeframe for setup identification and confluence
    - 5m timeframe for precise entry timing
    - Smart Money Concept integration
    - Supply/demand zone analysis
    - Liquidity sweep detection
    """
    
    def __init__(self, config_path: str = "config/"):
        """Initialize ICT strategy engine with quant enhancements."""
        # Try to load utilities if available
        if CryptoPairs:
            self.crypto_pairs = CryptoPairs(config_path)
        if RiskManager:
            self.risk_manager = RiskManager(config_path)
        
        # Initialize quant trading analyzers
        self.use_quant_enhancements = True  # Toggle for A/B testing
        if VolatilityAnalyzer and self.use_quant_enhancements:
            self.volatility_analyzer = VolatilityAnalyzer()
            self.correlation_analyzer = CorrelationAnalyzer()
            self.signal_quality_analyzer = SignalQualityAnalyzer()
            self.mean_reversion_analyzer = MeanReversionAnalyzer()
            logger.info("✅ Quant enhancements ENABLED")
        else:
            self.volatility_analyzer = None
            self.correlation_analyzer = None
            self.signal_quality_analyzer = None
            self.mean_reversion_analyzer = None
            logger.info("⚠️  Quant enhancements DISABLED (baseline mode)")
        
        # Active positions tracking for correlation analysis
        self.active_positions = []
        
        # ICT Strategy Parameters
        self.ict_params = {
            # Market Structure
            'trend_threshold': 2.0,  # % change to identify trends
            'structure_shift_threshold': 1.5,  # % for structure shifts
            'liquidity_volume_threshold': 1000000000,  # High volume threshold
            
            # Confluence Requirements
            'min_confluence_trending': 0.18,  # Min confluence in trending markets
            'min_confluence_sideways': 0.15,  # Min confluence in sideways markets
            'base_signal_probability': 0.035,  # 3.5% base signal chance
            
            # Risk Management
            'fixed_risk_percentage': 0.01,  # 1% fixed risk per trade
            'max_positions': 3,  # Maximum concurrent positions
            'base_stop_multiplier': 0.008,  # Base stop loss %
            'confidence_stop_range': 0.007,  # Additional stop based on confidence
            
            # Multi-timeframe Settings
            'direction_timeframe': '4h',  # Primary direction analysis
            'setup_timeframe': '15m',  # Setup identification
            'entry_timeframe': '5m',  # Precise entry timing
            
            # Session Multipliers
            'session_multipliers': {
                'asia': 0.8,     # 23:00-08:00 GMT
                'london': 1.2,   # 08:00-16:00 GMT  
                'ny': 1.3,       # 13:00-21:00 GMT
                'overlap': 1.8   # 13:00-16:00 GMT (London/NY)
            }
        }
        
        # Market regime tracking
        self.current_market_regime = 'sideways'
        self.supply_demand_zones = {}
        self.liquidity_levels = {}
        
        # Trading sessions (GMT hours)
        self.trading_sessions = {
            'asia': {'start': 23, 'end': 8, 'name': 'Asia'},
            'london': {'start': 8, 'end': 16, 'name': 'London'},
            'ny': {'start': 13, 'end': 21, 'name': 'New York'}
        }
        
        logger.info("ICT Strategy Engine initialized with multi-timeframe analysis")
    
    def _get_nearest_index(self, index: pd.DatetimeIndex, timestamp: pd.Timestamp) -> int:
        """
        Get nearest index position for a timestamp in a pandas-version-agnostic way.
        
        This replaces index.get_loc(timestamp, method='nearest') which is not
        supported in older pandas versions.
        
        Args:
            index: DatetimeIndex to search in
            timestamp: Target timestamp to find
            
        Returns:
            Integer index position of nearest timestamp
        """
        try:
            # Try exact match first
            return index.get_loc(timestamp)
        except KeyError:
            # Find nearest using get_indexer with nearest method
            indexer = index.get_indexer([timestamp], method='nearest')
            return indexer[0] if len(indexer) > 0 else 0
        except TypeError:
            # Fallback: manual search for nearest
            if len(index) == 0:
                return 0
            time_diffs = abs(index - timestamp)
            return time_diffs.argmin()
    
    def prepare_multitimeframe_data(self, df_1h: pd.DataFrame) -> MultiTimeframeData:
        """
        Convert 1H data to multi-timeframe structure for ICT analysis.
        
        Args:
            df_1h: Base 1H OHLCV DataFrame
            
        Returns:
            MultiTimeframeData with 4H, 15m, 5m resampled data
        """
        # Resample to 4H for directional bias
        tf_4h = df_1h.resample('4H').agg({
            'open': 'first',
            'high': 'max', 
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        # Create 15m data (interpolate from 1H)
        tf_15m = df_1h.resample('15T').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min', 
            'close': 'last',
            'volume': 'sum'
        }).interpolate().dropna()
        
        # Create 5m data (interpolate from 1H)
        tf_5m = df_1h.resample('5T').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last', 
            'volume': 'sum'
        }).interpolate().dropna()
        
        return MultiTimeframeData(
            tf_4h=tf_4h,
            tf_15m=tf_15m,
            tf_5m=tf_5m,
            current_index_4h=0,
            current_index_15m=0,
            current_index_5m=0
        )
    
    def detect_market_regime(self, mtf_data: MultiTimeframeData, current_time: pd.Timestamp) -> str:
        """
        Detect market regime using 4H timeframe analysis.
        
        Args:
            mtf_data: Multi-timeframe data
            current_time: Current timestamp
            
        Returns:
            Market regime: 'trending' or 'sideways'
        """
        tf_4h = mtf_data.tf_4h
        
        # Find current 4H index using pandas-agnostic helper
        try:
            current_4h_idx = self._get_nearest_index(tf_4h.index, current_time)
        except (KeyError, IndexError):
            return 'sideways'
        
        if current_4h_idx < 10:  # Need sufficient history
            return 'sideways'
        
        # Analyze last 10 4H candles for trend detection
        recent_data = tf_4h.iloc[current_4h_idx-10:current_4h_idx+1]
        
        # Calculate price momentum and trend strength
        price_changes = recent_data['close'].pct_change().dropna()
        avg_change = price_changes.mean() * 100
        trend_strength = abs(avg_change)
        
        # Calculate trending ratio (% of moves in same direction)
        positive_moves = (price_changes > 0).sum()
        negative_moves = (price_changes < 0).sum()
        total_moves = len(price_changes)
        
        if total_moves > 0:
            directional_ratio = max(positive_moves, negative_moves) / total_moves
        else:
            directional_ratio = 0.5
        
        # Determine regime
        if trend_strength > self.ict_params['trend_threshold'] and directional_ratio >= 0.6:
            regime = 'trending'
        else:
            regime = 'sideways'
        
        logger.debug(f"Market Regime: {regime} (strength: {trend_strength:.2f}%, ratio: {directional_ratio:.2f})")
        return regime
    
    def analyze_supply_demand_zones(self, mtf_data: MultiTimeframeData, current_time: pd.Timestamp) -> Dict:
        """Analyze supply and demand zones using multi-timeframe confluence."""
        tf_4h = mtf_data.tf_4h
        # tf_15m not used, removed to fix linting issue
        
        try:
            current_4h_idx = self._get_nearest_index(tf_4h.index, current_time)
            current_price = tf_4h.iloc[current_4h_idx]['close']
        except (KeyError, IndexError):
            return {'score': 0, 'factors': []}
        
        confluence_score = 0
        factors = []
        
        if current_4h_idx < 20:
            return {'score': confluence_score, 'factors': factors}
        
        # Look for recent swing highs/lows as supply/demand zones
        recent_4h = tf_4h.iloc[current_4h_idx-20:current_4h_idx+1]
        highs = recent_4h['high']
        lows = recent_4h['low']
        
        # Identify key levels
        recent_high = highs.max()
        recent_low = lows.min()
        
        # Distance to key levels
        distance_to_high = abs(current_price - recent_high) / current_price
        distance_to_low = abs(current_price - recent_low) / current_price
        
        # Supply zone confluence (near recent highs)
        if distance_to_high < 0.02:  # Within 2% of recent high
            confluence_score += 0.15
            factors.append("Near Supply Zone (Recent High)")
        
        # Demand zone confluence (near recent lows)
        if distance_to_low < 0.02:  # Within 2% of recent low
            confluence_score += 0.15
            factors.append("Near Demand Zone (Recent Low)")
        
        # Volume analysis for zone strength
        if current_4h_idx > 0:
            recent_volume = tf_4h.iloc[current_4h_idx]['volume']
            avg_volume = tf_4h.iloc[current_4h_idx-10:current_4h_idx]['volume'].mean()
            
            if recent_volume > avg_volume * 1.5:
                confluence_score += 0.08
                factors.append("High Volume Zone Confirmation")
        
        return {'score': confluence_score, 'factors': factors}
    
    def analyze_liquidity_levels(self, mtf_data: MultiTimeframeData, current_time: pd.Timestamp) -> Dict:
        """Analyze liquidity levels and potential sweep opportunities."""
        tf_4h = mtf_data.tf_4h
        
        try:
            current_4h_idx = self._get_nearest_index(tf_4h.index, current_time)
            current_price = tf_4h.iloc[current_4h_idx]['close']
        except (KeyError, IndexError):
            return {'score': 0, 'factors': []}
        
        confluence_score = 0
        factors = []
        
        if current_4h_idx < 15:
            return {'score': confluence_score, 'factors': factors}
        
        # Analyze recent price action for liquidity sweeps
        recent_data = tf_4h.iloc[current_4h_idx-15:current_4h_idx+1]
        
        # Look for equal highs/lows (liquidity pools)
        highs = recent_data['high']
        lows = recent_data['low']
        
        # Find potential liquidity levels
        recent_high = highs.rolling(window=5).max().iloc[-1]
        recent_low = lows.rolling(window=5).min().iloc[-1]
        
        # Check for liquidity sweep setups
        price_near_high = abs(current_price - recent_high) / current_price < 0.015
        price_near_low = abs(current_price - recent_low) / current_price < 0.015
        
        if price_near_high:
            confluence_score += 0.12
            factors.append("Buy-side Liquidity Sweep Setup")
        
        if price_near_low:
            confluence_score += 0.12
            factors.append("Sell-side Liquidity Sweep Setup")
        
        # Volume confirmation for liquidity levels
        current_volume = tf_4h.iloc[current_4h_idx]['volume']
        avg_volume = recent_data['volume'].mean()
        
        if current_volume > avg_volume * 1.3:
            confluence_score += 0.06
            factors.append("Volume Spike at Liquidity Level")
        
        return {'score': confluence_score, 'factors': factors}
    
    def get_session_multiplier(self, current_time: pd.Timestamp) -> float:
        """Calculate session-based multiplier for signal probability."""
        # Convert to GMT hour
        current_hour = current_time.hour
        
        # Check for session overlaps first (highest priority)
        if 13 <= current_hour < 16:  # London/NY overlap
            return self.ict_params['session_multipliers']['overlap']
        elif 13 <= current_hour < 21:  # NY session
            return self.ict_params['session_multipliers']['ny']
        elif 8 <= current_hour < 16:  # London session
            return self.ict_params['session_multipliers']['london']
        elif current_hour >= 23 or current_hour < 8:  # Asia session
            return self.ict_params['session_multipliers']['asia']
        else:  # Off-hours
            return 0.6
    
    def calculate_directional_bias(self, mtf_data: MultiTimeframeData, current_time: pd.Timestamp) -> Dict:
        """Calculate directional bias using 4H timeframe."""
        tf_4h = mtf_data.tf_4h
        
        try:
            current_4h_idx = self._get_nearest_index(tf_4h.index, current_time)
        except (KeyError, IndexError):
            return {'direction': 'NEUTRAL', 'strength': 0.5}
        
        if current_4h_idx < 5:
            return {'direction': 'NEUTRAL', 'strength': 0.5}
        
        # Analyze last 5 4H candles for directional bias
        recent_closes = tf_4h.iloc[current_4h_idx-5:current_4h_idx+1]['close']
        price_changes = recent_closes.pct_change().dropna()
        
        avg_change = price_changes.mean() * 100
        
        if avg_change > 1.5:
            return {'direction': 'BULLISH', 'strength': min(avg_change / 5.0, 1.0)}
        elif avg_change < -1.5:
            return {'direction': 'BEARISH', 'strength': min(abs(avg_change) / 5.0, 1.0)}
        else:
            return {'direction': 'NEUTRAL', 'strength': 0.5}
    
    def generate_ict_signal(self, symbol: str, mtf_data: MultiTimeframeData, current_time: pd.Timestamp, account_balance: float = 10000) -> Optional[ICTTradingSignal]:
        """
        Generate ICT trading signal using multi-timeframe confluence analysis.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            mtf_data: Multi-timeframe OHLCV data
            current_time: Current timestamp for analysis
            account_balance: Current account balance for 1% risk calculation (default: 10000 for backtesting)
            
        Returns:
            ICTTradingSignal or None if no signal generated
        """
        # Step 1: Market regime detection (4H timeframe)
        market_regime = self.detect_market_regime(mtf_data, current_time)
        
        # Step 2: Directional bias (4H timeframe)
        directional_bias = self.calculate_directional_bias(mtf_data, current_time)
        
        # Step 3: Session multiplier
        session_multiplier = self.get_session_multiplier(current_time)
        
        # Step 4: Base signal probability calculation
        base_prob = self.ict_params['base_signal_probability']
        regime_multiplier = 1.2 if market_regime == 'trending' else 0.9
        
        adjusted_prob = base_prob * session_multiplier * regime_multiplier
        
        # Step 5: Probabilistic signal generation
        rng = np.random.default_rng(int(time.time() * 1000000) % 2**32)
        signal_chance = rng.random()
        
        if signal_chance >= adjusted_prob:
            return None  # No signal generated
        
        # Step 6: Get current price data
        try:
            tf_15m = mtf_data.tf_15m
            current_15m_idx = self._get_nearest_index(tf_15m.index, current_time)
            current_price_data = tf_15m.iloc[current_15m_idx]
            entry_price = current_price_data['close']
        except (KeyError, IndexError):
            return None
        
        # Step 7: ICT Confluence Analysis
        confluence_score = 0.05  # Base confluence
        confluence_factors = []
        
        # Apply directional bias filter
        if not self._passes_directional_filter(directional_bias, rng):
            return None
        
        # Supply/Demand Zone Analysis
        supply_demand = self.analyze_supply_demand_zones(mtf_data, current_time)
        confluence_score += supply_demand['score']
        confluence_factors.extend(supply_demand['factors'])
        
        # Liquidity Level Analysis
        liquidity = self.analyze_liquidity_levels(mtf_data, current_time)
        confluence_score += liquidity['score']
        confluence_factors.extend(liquidity['factors'])
        
        # Fair Value Gap Analysis
        fvg_analysis = self._analyze_fair_value_gaps(mtf_data, current_time, rng)
        confluence_score += fvg_analysis['score']
        confluence_factors.extend(fvg_analysis['factors'])
        
        # Order Block Analysis
        ob_analysis = self._analyze_order_blocks(mtf_data, current_time, rng)
        confluence_score += ob_analysis['score']
        confluence_factors.extend(ob_analysis['factors'])
        
        # Market Structure Analysis
        structure_analysis = self._analyze_market_structure(mtf_data, current_time, market_regime, rng)
        confluence_score += structure_analysis['score']
        confluence_factors.extend(structure_analysis['factors'])
        
        # Premium/Discount Analysis
        premium_discount = self._analyze_premium_discount(mtf_data, current_time)
        confluence_score += premium_discount['score']
        confluence_factors.extend(premium_discount['factors'])
        
        # Step 8: Confluence threshold check
        min_confluence = (self.ict_params['min_confluence_trending'] if market_regime == 'trending' 
                         else self.ict_params['min_confluence_sideways'])
        
        if confluence_score < min_confluence:
            return None
        
        # Step 9: Action determination
        action = self._determine_ict_action(confluence_factors, directional_bias, market_regime)
        
        # Step 10: Calculate confidence and position sizing
        ict_confidence = min(0.35 + (confluence_score * 0.55), 0.90)
        ml_boost = 0  # No ML model in backtest for now
        final_confidence = min(ict_confidence + ml_boost, 0.95)
        
        # Step 11: Risk management and position sizing
        fixed_risk_percentage = self.ict_params['fixed_risk_percentage']  # 0.01 = 1%
        portfolio_balance = account_balance  # Use actual account balance (live) or default (backtest)
        risk_amount = portfolio_balance * fixed_risk_percentage  # 1% of current balance
        
        logger.debug(f"💰 Risk Calculation: Balance=${portfolio_balance:.2f} × {fixed_risk_percentage*100}% = ${risk_amount:.2f} per trade")
        
        # =================================================================
        # STEP 1: Calculate ATR-based stop loss first
        # =================================================================
        if self.volatility_analyzer:
            atr_analysis = self.volatility_analyzer.get_atr_analysis(
                mtf_data.tf_15m.loc[:current_time],
                entry_price
            )
            stop_loss = self.volatility_analyzer.calculate_dynamic_stop_loss(
                entry_price=entry_price,
                atr=atr_analysis['atr'],
                direction=action,
                volatility_regime=atr_analysis['regime']
            )
            logger.debug(f"📊 ATR Stop: ${stop_loss:.2f} | Regime: {atr_analysis['regime']} | Multiplier: {atr_analysis['stop_multiplier']}")
        else:
            # Fallback to percentage-based stop
            stop_multiplier = (self.ict_params['base_stop_multiplier'] + 
                              (final_confidence * self.ict_params['confidence_stop_range']))
            if action == 'BUY':
                stop_loss = entry_price * (1 - stop_multiplier)
            else:
                stop_loss = entry_price * (1 + stop_multiplier)
        
        # =================================================================
        # STEP 2: Calculate SMART take profit based on actual price levels
        # =================================================================
        smart_tp_data = self._calculate_smart_take_profit(
            entry_price=entry_price,
            stop_loss=stop_loss,
            action=action,
            mtf_data=mtf_data,
            current_time=current_time,
            min_rr=2.0  # Minimum 1:2 R:R
        )
        
        take_profit = smart_tp_data['take_profit']
        actual_rr_ratio = smart_tp_data['rr_ratio']
        target_type = smart_tp_data['target_type']
        
        logger.debug(f"🎯 Smart TP: ${take_profit:.2f} | Actual R:R: 1:{actual_rr_ratio:.2f} | Target: {target_type}")
        
        # =================================================================
        # OLD METHOD (kept for reference, not used)
        # =================================================================
        # rr_data = self._calculate_dynamic_rr(final_confidence, market_regime, confluence_score)
        # rr_target = rr_data['rr_target']  # This was fixed tiers: 3, 5, 8
        
        # Stop loss and take profit calculation
        # stop_multiplier = (self.ict_params['base_stop_multiplier'] + 
        #                   (final_confidence * self.ict_params['confidence_stop_range']))
        # tp_multiplier = stop_multiplier * rr_target
        
        # =================================================================
        # QUANT ENHANCEMENTS: Mean Reversion, Signal Quality
        # =================================================================
        position_size_multiplier = 1.0
        if self.mean_reversion_analyzer:
            mr_analysis = self.mean_reversion_analyzer.analyze_price_extension(
                mtf_data.tf_15m.loc[:current_time],
                action
            )
            # Only use multiplier if explicitly enabled in config
            use_mr_multiplier = self.ict_params.get('quant_enhancements', {}).get('mean_reversion', {}).get('use_position_multiplier', False)
            if use_mr_multiplier:
                position_size_multiplier = mr_analysis['position_multiplier']
                logger.debug(f"📉 Mean Reversion: {mr_analysis['condition']} | Size adjust: {position_size_multiplier}x")
            else:
                logger.debug(f"📉 Mean Reversion: {mr_analysis['condition']} | Size adjust: DISABLED - pure 1 percent risk")
        
        # Position size calculation - STRICT 1% RISK
        stop_distance = abs(entry_price - stop_loss)
        base_position_size = risk_amount / stop_distance if stop_distance > 0 else 0
        position_size = base_position_size * position_size_multiplier
        
        # Step 12: Timeframe selection for execution
        execution_timeframe = self._select_execution_timeframe(confluence_score)
        
        # Create preliminary signal for quality check
        preliminary_signal = {
            'timestamp': current_time,
            'symbol': symbol,
            'action': action,
            'confidence': final_confidence,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'timeframe': execution_timeframe
        }
        
        # 3. Signal Quality Check (Time-decay + Expectancy)
        if self.signal_quality_analyzer:
            quality = self.signal_quality_analyzer.analyze_signal_quality(preliminary_signal, current_time)
            if not quality['should_take_signal']:
                logger.info(f"❌ Signal REJECTED: {quality['rejection_reason']}")
                return None
            # Time-decay multiplier: DISABLED for pure 1% risk
            use_time_decay_multiplier = self.ict_params.get('quant_enhancements', {}).get('signal_quality', {}).get('use_position_multiplier', False)
            if use_time_decay_multiplier:
                position_size *= quality['position_size_multiplier']
                logger.debug(f"✅ Signal Quality: {quality['time_decay']['freshness']} | Size adjust: {quality['position_size_multiplier']:.2f}x")
            else:
                logger.debug(f"✅ Signal Quality: {quality['time_decay']['freshness']} | Expectancy: {quality['expectancy']['expectancy_ratio']:.2f}R | Size adjust: DISABLED")
        
        # 4. Correlation Check (Portfolio Heat)
        if self.correlation_analyzer:
            allowed, reason, projected_heat = self.correlation_analyzer.check_new_position_allowed(
                symbol,
                risk_amount / portfolio_balance,  # Risk as fraction
                self.active_positions
            )
            if not allowed:
                logger.info(f"🔥 Portfolio Heat BLOCKED: {reason}")
                return None
            logger.debug(f"🌡️  Portfolio Heat: {projected_heat:.4f} (limit: {self.correlation_analyzer.max_portfolio_heat})")
        
        # =================================================================
        # END QUANT ENHANCEMENTS
        # =================================================================
        
        # Create ICT trading signal
        signal = ICTTradingSignal(
            timestamp=current_time,
            symbol=symbol,
            action=action,
            confidence=final_confidence,
            ict_confidence=ict_confidence,
            ml_boost=ml_boost,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            risk_amount=risk_amount,
            risk_reward_ratio=int(actual_rr_ratio),  # Use actual calculated R:R
            market_regime=market_regime,
            timeframe=execution_timeframe,
            confluence_factors=confluence_factors,
            confluence_score=confluence_score,
            session_multiplier=session_multiplier,
            directional_bias=directional_bias,
            dynamic_rr_calculation={'actual_rr': actual_rr_ratio, 'target_type': target_type},
            indicators={
                'entry_price': entry_price,
                'confluence_score': confluence_score,
                'session_multiplier': session_multiplier,
                'regime': market_regime,
                'target_type': target_type,
                'actual_rr': actual_rr_ratio
            },
            reasoning="; ".join(confluence_factors[:3])  # Top 3 factors
        )
        
        logger.info(f"ICT Signal: {symbol} {action} @ ${entry_price:.4f} | Confluence: {confluence_score:.3f} | RR: 1:{actual_rr_ratio:.1f} ({target_type})")
        return signal
    
    def _passes_directional_filter(self, directional_bias: Dict, rng: np.random.Generator) -> bool:
        """Filter signals based on directional bias."""
        if directional_bias['direction'] == 'NEUTRAL':
            return True
        
        # Reduce counter-trend signals in strong directional markets
        if directional_bias['strength'] > 0.7:
            return rng.random() < 0.3  # 30% pass rate
        elif directional_bias['strength'] > 0.5:
            return rng.random() < 0.6  # 60% pass rate
        
        return True
    
    def _analyze_fair_value_gaps(self, mtf_data: MultiTimeframeData, current_time: pd.Timestamp, rng: np.random.Generator) -> Dict:
        """Analyze Fair Value Gaps using 15m timeframe."""
        tf_15m = mtf_data.tf_15m
        
        try:
            current_idx = self._get_nearest_index(tf_15m.index, current_time)
        except (KeyError, IndexError):
            return {'score': 0, 'factors': []}
        
        if current_idx < 5:
            return {'score': 0, 'factors': []}
        
        confluence_score = 0
        factors = []
        
        # Calculate recent volatility for FVG analysis
        recent_data = tf_15m.iloc[current_idx-5:current_idx+1]
        price_changes = recent_data['close'].pct_change().abs()
        avg_change = price_changes.mean() * 100
        
        # FVG analysis based on volatility
        if avg_change > 1.5:  # High volatility = guaranteed FVG
            fvg_strength = min(avg_change / 5.0, 1.0)
            confluence_score += 0.20 + (fvg_strength * 0.10)
            factors.append(f"FVG High Volatility ({avg_change:.1f}%)")
        elif avg_change > 0.5:  # Moderate volatility = probabilistic FVG
            fvg_chance = 0.40 + (avg_change * 0.05)
            if rng.random() < min(fvg_chance, 0.80):
                confluence_score += 0.15
                factors.append("FVG Moderate")
        
        return {'score': confluence_score, 'factors': factors}
    
    def _analyze_order_blocks(self, mtf_data: MultiTimeframeData, current_time: pd.Timestamp, rng: np.random.Generator) -> Dict:
        """Analyze Order Blocks using 15m timeframe."""
        tf_15m = mtf_data.tf_15m
        
        try:
            current_idx = self._get_nearest_index(tf_15m.index, current_time)
            current_data = tf_15m.iloc[current_idx]
        except (KeyError, IndexError):
            return {'score': 0, 'factors': []}
        
        if current_idx < 10:
            return {'score': 0, 'factors': []}
        
        confluence_score = 0
        factors = []
        
        # Calculate recent price range for OB analysis
        recent_data = tf_15m.iloc[current_idx-10:current_idx+1]
        high_24h = recent_data['high'].max()
        low_24h = recent_data['low'].min()
        current_price = current_data['close']
        
        range_24h = high_24h - low_24h
        range_percent = (range_24h / current_price) * 100
        
        # Volume analysis
        current_volume = current_data['volume']
        avg_volume = recent_data['volume'].mean()
        volume_factor = min(current_volume / avg_volume, 2.0) if avg_volume > 0 else 1.0
        
        # Order block analysis
        if range_percent > 3:  # Wide range = strong order blocks
            ob_strength = min(range_percent / 10.0, 1.0) * volume_factor
            confluence_score += 0.25 + (ob_strength * 0.10)
            factors.append(f"Order Block Strong ({range_percent:.1f}% range)")
        elif range_percent > 1.5:  # Moderate range = probabilistic OB
            ob_chance = 0.60 + (volume_factor * 0.10)
            if rng.random() < min(ob_chance, 0.90):
                confluence_score += 0.15
                factors.append("Order Block Moderate")
        
        return {'score': confluence_score, 'factors': factors}
    
    def _analyze_market_structure(self, mtf_data: MultiTimeframeData, current_time: pd.Timestamp, market_regime: str, rng: np.random.Generator) -> Dict:
        """Analyze Market Structure Shifts."""
        tf_15m = mtf_data.tf_15m
        
        try:
            current_idx = self._get_nearest_index(tf_15m.index, current_time)
        except (KeyError, IndexError):
            return {'score': 0, 'factors': []}
        
        if current_idx < 5:
            return {'score': 0, 'factors': []}
        
        confluence_score = 0
        factors = []
        
        # Calculate recent momentum
        recent_data = tf_15m.iloc[current_idx-5:current_idx+1]
        price_change = ((recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]) / 
                       recent_data['close'].iloc[0]) * 100
        
        change_magnitude = abs(price_change)
        
        # Structure shift analysis based on regime
        if market_regime == 'trending':
            if change_magnitude > 2.5:  # Strong momentum in trending market
                structure_strength = min(change_magnitude / 5.0, 1.0)
                confluence_score += 0.20 + (structure_strength * 0.10)
                factors.append(f"Structure Shift Strong Trend ({change_magnitude:.1f}%)")
            elif change_magnitude > 1.0:  # Moderate momentum
                if rng.random() < 0.70:  # Higher chance in trending markets
                    confluence_score += 0.15
                    factors.append("Structure Shift Trend")
        else:  # Sideways market
            if change_magnitude > 1.5:  # Structure shift in ranging market
                confluence_score += 0.15
                factors.append("Structure Shift Range")
        
        return {'score': confluence_score, 'factors': factors}
    
    def _analyze_premium_discount(self, mtf_data: MultiTimeframeData, current_time: pd.Timestamp) -> Dict:
        """Analyze Premium/Discount zones."""
        tf_15m = mtf_data.tf_15m
        
        try:
            current_idx = self._get_nearest_index(tf_15m.index, current_time)
        except (KeyError, IndexError):
            return {'score': 0, 'factors': []}
        
        if current_idx < 20:
            return {'score': 0, 'factors': []}
        
        confluence_score = 0
        factors = []
        
        # Calculate position within recent range
        recent_data = tf_15m.iloc[current_idx-20:current_idx+1]
        high_24h = recent_data['high'].max()
        low_24h = recent_data['low'].min()
        current_price = recent_data['close'].iloc[-1]
        
        range_24h = high_24h - low_24h
        if range_24h > 0:
            price_position = (current_price - low_24h) / range_24h
        else:
            price_position = 0.5
        
        # Premium/Discount analysis
        if price_position < 0.20:  # Deep discount
            confluence_score += 0.18
            factors.append("Deep Discount Zone")
        elif price_position < 0.35:  # Standard discount
            confluence_score += 0.12
            factors.append("Discount Zone")
        elif price_position > 0.80:  # Deep premium
            confluence_score += 0.18
            factors.append("Deep Premium Zone")
        elif price_position > 0.65:  # Standard premium
            confluence_score += 0.12
            factors.append("Premium Zone")
        
        return {'score': confluence_score, 'factors': factors}
    
    def _determine_ict_action(self, confluence_factors: List[str], directional_bias: Dict, market_regime: str) -> str:
        """Determine BUY/SELL action based on ICT analysis."""
        # Count bullish vs bearish signals
        bullish_signals = sum(1 for factor in confluence_factors 
                             if any(bullish in factor.lower() for bullish in 
                                   ['demand', 'discount', 'support', 'buy']))
        
        bearish_signals = sum(1 for factor in confluence_factors 
                             if any(bearish in factor.lower() for bearish in 
                                   ['supply', 'premium', 'resistance', 'sell']))
        
        # Bias towards directional bias in trending markets
        if market_regime == 'trending' and directional_bias['strength'] > 0.6:
            if directional_bias['direction'] == 'BULLISH':
                return 'BUY'
            elif directional_bias['direction'] == 'BEARISH':
                return 'SELL'
        
        # Default to confluence factor analysis
        if bullish_signals > bearish_signals:
            return 'BUY'
        else:
            return 'SELL'
    
    def _calculate_smart_take_profit(self, entry_price: float, stop_loss: float, action: str, 
                                     mtf_data: MultiTimeframeData, current_time: pd.Timestamp,
                                     min_rr: float = 1.5) -> Dict:
        """
        Calculate SMART take profit based on actual price levels:
        - Previous swing highs/lows
        - Key psychological levels
        - Liquidity zones
        - ATR-based extensions
        
        Returns actual price target and real R:R ratio (not fixed tiers).
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            action: 'BUY' or 'SELL'
            mtf_data: Multi-timeframe data
            current_time: Current timestamp
            min_rr: Minimum acceptable R:R ratio
            
        Returns:
            Dict with 'take_profit', 'rr_ratio', 'target_type'
        """
        stop_distance = abs(entry_price - stop_loss)
        
        # Get recent price data for level detection
        recent_4h = mtf_data.tf_4h.loc[:current_time].tail(100)
        recent_15m = mtf_data.tf_15m.loc[:current_time].tail(100)
        
        # Calculate potential targets
        targets = []
        
        if action == 'BUY':
            # 1. Previous swing highs on 4H (major levels)
            swing_highs = recent_4h[recent_4h['high'] == recent_4h['high'].rolling(5, center=True).max()]['high']
            for high in swing_highs.tail(5):
                if high > entry_price:
                    rr = (high - entry_price) / stop_distance
                    if rr >= min_rr:
                        targets.append({'price': high, 'rr': rr, 'type': '4H_SWING_HIGH'})
            
            # 2. Previous swing highs on 15m (intermediate levels)
            swing_highs_15m = recent_15m[recent_15m['high'] == recent_15m['high'].rolling(7, center=True).max()]['high']
            for high in swing_highs_15m.tail(5):
                if high > entry_price:
                    rr = (high - entry_price) / stop_distance
                    if rr >= min_rr:
                        targets.append({'price': high, 'rr': rr, 'type': '15M_SWING_HIGH'})
            
            # 3. Psychological levels (round numbers)
            current_level = int(entry_price / 100) * 100
            for i in range(1, 5):
                psych_level = current_level + (i * 100)
                if psych_level > entry_price:
                    rr = (psych_level - entry_price) / stop_distance
                    if rr >= min_rr and rr <= 20:  # Cap at 20R
                        targets.append({'price': psych_level, 'rr': rr, 'type': 'PSYCHOLOGICAL'})
            
            # 4. ATR-based extension (fallback)
            atr = recent_4h['high'].rolling(14).mean().iloc[-1] - recent_4h['low'].rolling(14).mean().iloc[-1]
            for multiplier in [2, 3, 5, 8]:
                target = entry_price + (atr * multiplier)
                rr = (target - entry_price) / stop_distance
                if rr >= min_rr and rr <= 20:
                    targets.append({'price': target, 'rr': rr, 'type': f'ATR_{multiplier}X'})
        
        else:  # SELL
            # 1. Previous swing lows on 4H (major levels)
            swing_lows = recent_4h[recent_4h['low'] == recent_4h['low'].rolling(5, center=True).min()]['low']
            for low in swing_lows.tail(5):
                if low < entry_price:
                    rr = (entry_price - low) / stop_distance
                    if rr >= min_rr:
                        targets.append({'price': low, 'rr': rr, 'type': '4H_SWING_LOW'})
            
            # 2. Previous swing lows on 15m (intermediate levels)
            swing_lows_15m = recent_15m[recent_15m['low'] == recent_15m['low'].rolling(7, center=True).min()]['low']
            for low in swing_lows_15m.tail(5):
                if low < entry_price:
                    rr = (entry_price - low) / stop_distance
                    if rr >= min_rr:
                        targets.append({'price': low, 'rr': rr, 'type': '15M_SWING_LOW'})
            
            # 3. Psychological levels
            current_level = int(entry_price / 100) * 100
            for i in range(1, 5):
                psych_level = current_level - (i * 100)
                if psych_level < entry_price:
                    rr = (entry_price - psych_level) / stop_distance
                    if rr >= min_rr and rr <= 20:
                        targets.append({'price': psych_level, 'rr': rr, 'type': 'PSYCHOLOGICAL'})
            
            # 4. ATR-based extension (fallback)
            atr = recent_4h['high'].rolling(14).mean().iloc[-1] - recent_4h['low'].rolling(14).mean().iloc[-1]
            for multiplier in [2, 3, 5, 8]:
                target = entry_price - (atr * multiplier)
                rr = (entry_price - target) / stop_distance
                if rr >= min_rr and rr <= 20:
                    targets.append({'price': target, 'rr': rr, 'type': f'ATR_{multiplier}X'})
        
        # Select best target (prioritize swing points, then psychological, then ATR)
        if not targets:
            # Fallback to minimum R:R
            if action == 'BUY':
                take_profit = entry_price + (stop_distance * min_rr)
            else:
                take_profit = entry_price - (stop_distance * min_rr)
            return {
                'take_profit': take_profit,
                'rr_ratio': min_rr,
                'target_type': 'FALLBACK_MIN_RR'
            }
        
        # Sort by priority: swing highs/lows > psychological > ATR
        def target_priority(t):
            if 'SWING' in t['type']:
                return (0, -t['rr'])  # Prioritize swing points, prefer higher RR
            elif 'PSYCHOLOGICAL' in t['type']:
                return (1, -t['rr'])
            else:
                return (2, -t['rr'])
        
        targets.sort(key=target_priority)
        best_target = targets[0]
        
        return {
            'take_profit': best_target['price'],
            'rr_ratio': best_target['rr'],
            'target_type': best_target['type']
        }
    
    def _calculate_dynamic_rr(self, confidence: float, market_regime: str, confluence_score: float) -> Dict:
        """Calculate dynamic risk-reward ratio and snap to discrete tiers."""
        base_rr = 2.0
        
        # Confidence bonus
        confidence_bonus = (confidence - 0.35) * 5
        
        # Regime bonus
        regime_bonus = 1.0 if market_regime == 'trending' else 0.5
        
        # Confluence bonus
        confluence_bonus = max(0, (confluence_score - 0.15) * 4)
        
        # Calculate dynamic RR
        dynamic_rr = base_rr + confidence_bonus + regime_bonus + confluence_bonus
        dynamic_rr = max(2.0, min(dynamic_rr, 8.0))
        
        # Snap to discrete tiers
        if dynamic_rr < 3.0:
            rr_target = 3
        elif dynamic_rr < 5.0:
            rr_target = 5
        else:
            rr_target = 8
        
        return {
            'base_rr': base_rr,
            'confidence_bonus': confidence_bonus,
            'regime_bonus': regime_bonus,
            'confluence_bonus': confluence_bonus,
            'final_rr': dynamic_rr,
            'rr_target': rr_target
        }
    
    def _select_execution_timeframe(self, confluence_score: float) -> str:
        """
        Select optimal execution timeframe based on confluence strength.
        Higher confluence = higher timeframe for better quality entries.
        
        Args:
            confluence_score: Total confluence score from analysis
            
        Returns:
            Timeframe string ('4h', '15m', or '5m')
        """
        if confluence_score >= 0.35:
            # Very high confluence - use 4H for swing trades
            return '4h'
        elif confluence_score >= 0.20:
            # Medium confluence - use 15m for intraday
            return '15m'
        else:
            # Lower confluence - use 5m for scalping
            return '5m'
    
    def simulate_ict_strategy(self, symbol: str, df: pd.DataFrame) -> List[ICTTradingSignal]:
        """
        Run ICT strategy simulation on historical data with multi-timeframe analysis.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            df: Historical 1H OHLCV data
            
        Returns:
            List of generated ICT trading signals
        """
        logger.info(f"Running ICT strategy simulation for {symbol} ({len(df)} bars)")
        
        # Prepare multi-timeframe data
        mtf_data = self.prepare_multitimeframe_data(df)
        
        signals = []
        
        # Start from sufficient history (50 bars minimum)
        start_idx = max(50, len(mtf_data.tf_4h) // 4)
        
        # Iterate through time periods for signal generation
        for i in range(start_idx, len(df)):
            try:
                current_time = df.index[i]
                
                # Generate ICT signal at this timestamp
                signal = self.generate_ict_signal(symbol, mtf_data, current_time)
                
                if signal:
                    signals.append(signal)
                    logger.debug(f"ICT Signal generated at {current_time}: {signal.action}")
                    
            except Exception as e:
                logger.error(f"Error generating ICT signal at index {i}: {e}")
                continue
        
        logger.info(f"Generated {len(signals)} ICT signals for {symbol}")
        return signals
    
    def backtest_ict_signals(self, signals: List[ICTTradingSignal], price_data: pd.DataFrame, 
                            starting_balance: float = 10000) -> Dict:
        """
        Backtest ICT signals with enhanced position management.
        
        Args:
            signals: List of ICT trading signals
            price_data: Historical price data for execution
            starting_balance: Starting portfolio balance
            
        Returns:
            Comprehensive backtest results
        """
        logger.info(f"Backtesting {len(signals)} ICT signals with ${starting_balance:,.2f} starting balance")
        
        trades = []
        positions = {}
        portfolio_balance = starting_balance
        max_portfolio_balance = starting_balance
        
        # Enhanced metrics tracking (removed unused variables)
        # daily_balances and monthly_returns were not used in the function
        
        for signal in signals:
            try:
                # Get execution price from price data
                try:
                    execution_row = price_data.loc[signal.timestamp]
                    execution_price = execution_row['close']
                except KeyError:
                    # Use signal entry price if exact timestamp not found
                    execution_price = signal.entry_price
                
                if signal.action == 'BUY':
                    # Calculate position cost
                    trade_cost = signal.position_size * execution_price
                    
                    # Check if we have enough capital and position limits
                    if (trade_cost <= portfolio_balance and 
                        len(positions) < self.ict_params['max_positions']):
                        
                        positions[signal.symbol] = {
                            'symbol': signal.symbol,
                            'side': 'LONG',
                            'entry_price': execution_price,
                            'entry_time': signal.timestamp,
                            'size': signal.position_size,
                            'stop_loss': signal.stop_loss,
                            'take_profit': signal.take_profit,
                            'risk_amount': signal.risk_amount,
                            'rr_ratio': signal.risk_reward_ratio,
                            'confidence': signal.confidence,
                            'confluence_score': signal.confluence_score
                        }
                        
                        portfolio_balance -= trade_cost
                        logger.debug(f"Opened LONG {signal.symbol} @ ${execution_price:.2f} | Size: {signal.position_size:.4f}")
                
                elif signal.action == 'SELL' and signal.symbol in positions:
                    # Close existing position
                    position = positions[signal.symbol]
                    
                    if position['side'] == 'LONG':
                        # Calculate P&L
                        exit_value = position['size'] * execution_price
                        entry_cost = position['size'] * position['entry_price']
                        pnl = exit_value - entry_cost
                        pnl_percent = (pnl / entry_cost) * 100
                        
                        # Update portfolio balance
                        portfolio_balance += exit_value
                        max_portfolio_balance = max(max_portfolio_balance, portfolio_balance)
                        
                        # Calculate hold time
                        hold_time_hours = (signal.timestamp - position['entry_time']).total_seconds() / 3600
                        
                        # Record trade
                        trade_record = {
                            'symbol': signal.symbol,
                            'entry_time': position['entry_time'],
                            'exit_time': signal.timestamp,
                            'entry_price': position['entry_price'],
                            'exit_price': execution_price,
                            'size': position['size'],
                            'pnl': pnl,
                            'pnl_percent': pnl_percent,
                            'hold_time_hours': hold_time_hours,
                            'risk_amount': position['risk_amount'],
                            'rr_ratio': position['rr_ratio'],
                            'confidence': position['confidence'],
                            'confluence_score': position['confluence_score'],
                            'exit_reason': 'MANUAL_EXIT'
                        }
                        
                        trades.append(trade_record)
                        del positions[signal.symbol]
                        
                        logger.debug(f"Closed LONG {signal.symbol} @ ${execution_price:.2f} | P&L: ${pnl:.2f} ({pnl_percent:.1f}%)")
                
            except Exception as e:
                logger.error(f"Error processing ICT signal {signal.timestamp}: {e}")
                continue
        
        # Process remaining open positions (mark-to-market at final price)
        if positions and not price_data.empty:
            final_price_row = price_data.iloc[-1]
            final_timestamp = price_data.index[-1]
            
            for symbol, position in positions.items():
                try:
                    # Get final price for this symbol (use close price)
                    final_price = final_price_row['close']
                    
                    exit_value = position['size'] * final_price
                    entry_cost = position['size'] * position['entry_price']
                    pnl = exit_value - entry_cost
                    pnl_percent = (pnl / entry_cost) * 100
                    
                    portfolio_balance += exit_value
                    
                    hold_time_hours = (final_timestamp - position['entry_time']).total_seconds() / 3600
                    
                    trade_record = {
                        'symbol': symbol,
                        'entry_time': position['entry_time'],
                        'exit_time': final_timestamp,
                        'entry_price': position['entry_price'],
                        'exit_price': final_price,
                        'size': position['size'],
                        'pnl': pnl,
                        'pnl_percent': pnl_percent,
                        'hold_time_hours': hold_time_hours,
                        'risk_amount': position['risk_amount'],
                        'rr_ratio': position['rr_ratio'],
                        'confidence': position['confidence'],
                        'confluence_score': position['confluence_score'],
                        'exit_reason': 'BACKTEST_END'
                    }
                    
                    trades.append(trade_record)
                    
                except Exception as e:
                    logger.error(f"Error closing position for {symbol}: {e}")
        
        # Calculate comprehensive performance metrics
        if trades:
            trades_df = pd.DataFrame(trades)
            winning_trades = trades_df[trades_df['pnl'] > 0]
            losing_trades = trades_df[trades_df['pnl'] <= 0]
            
            # Calculate metrics by RR tier
            rr_performance = {}
            for rr_tier in [3, 5, 8]:
                tier_trades = trades_df[trades_df['rr_ratio'] == rr_tier]
                if not tier_trades.empty:
                    tier_wins = tier_trades[tier_trades['pnl'] > 0]
                    rr_performance[f'rr_{rr_tier}'] = {
                        'total_trades': len(tier_trades),
                        'winning_trades': len(tier_wins),
                        'win_rate': len(tier_wins) / len(tier_trades) * 100,
                        'total_pnl': tier_trades['pnl'].sum(),
                        'avg_pnl': tier_trades['pnl'].mean()
                    }
            
            results = {
                'total_trades': len(trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': len(winning_trades) / len(trades) * 100,
                'total_pnl': trades_df['pnl'].sum(),
                'total_return': ((portfolio_balance - starting_balance) / starting_balance) * 100,
                'average_win': winning_trades['pnl'].mean() if not winning_trades.empty else 0,
                'average_loss': losing_trades['pnl'].mean() if not losing_trades.empty else 0,
                'profit_factor': (abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) 
                                if not losing_trades.empty and losing_trades['pnl'].sum() != 0 else float('inf')),
                'max_drawdown': ((max_portfolio_balance - portfolio_balance) / max_portfolio_balance * 100 
                               if max_portfolio_balance > 0 else 0),
                'final_balance': portfolio_balance,
                'average_hold_time': trades_df['hold_time_hours'].mean(),
                'average_confidence': trades_df['confidence'].mean(),
                'average_confluence': trades_df['confluence_score'].mean(),
                'rr_tier_performance': rr_performance,
                'trades': trades
            }
        else:
            results = {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_return': 0,
                'final_balance': starting_balance,
                'trades': []
            }
        
        logger.info(f"ICT Backtest complete: {results['total_trades']} trades, "
                   f"{results['win_rate']:.1f}% win rate, {results['total_return']:.2f}% return")
        return results


# Legacy compatibility classes (for existing backtest runner)
@dataclass
class TradingSignal:
    """Legacy trading signal for compatibility."""
    timestamp: pd.Timestamp
    symbol: str
    action: str
    confidence: float
    price: float
    stop_loss: float
    take_profit: float
    position_size: float
    market_phase: str
    indicators: Dict[str, float]
    reasoning: str

@dataclass
class BacktestPosition:
    """Legacy position container for compatibility."""
    symbol: str
    side: str
    entry_price: float
    entry_time: pd.Timestamp
    size: float
    stop_loss: float
    take_profit: float
    current_pnl: float = 0.0
    max_pnl: float = 0.0
    min_pnl: float = 0.0


# REMOVED: StrategyEngine wrapper class (unused - use ICTStrategyEngine directly)
# The proven ICT Strategy Engine is the only engine in use

if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Initialize ICT strategy engine (single-engine architecture)
        engine = ICTStrategyEngine()
        
        # Create sample data for testing
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='1h')
        rng = np.random.default_rng(42)
        sample_data = pd.DataFrame({
            'timestamp': dates,
            'open': rng.standard_normal(len(dates)).cumsum() + 50000,
            'high': rng.standard_normal(len(dates)).cumsum() + 50100,
            'low': rng.standard_normal(len(dates)).cumsum() + 49900,
            'close': rng.standard_normal(len(dates)).cumsum() + 50000,
            'volume': rng.integers(100, 1000, len(dates))
        })
        sample_data.set_index('timestamp', inplace=True)
        
        # Test ICT signal generation
        mtf_data = engine.prepare_multitimeframe_data(sample_data)
        signal = engine.generate_ict_signal("BTCUSDT", mtf_data, sample_data.index[-1])
        print(f"Generated ICT signal: {signal.direction if signal else 'None'}")
        
    except Exception as e:
        print(f"Error: {e}")
