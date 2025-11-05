"""
Signal Quality and Time-Decay Analysis
======================================

Implements time-decay for signal confidence and expectancy filtering
to ensure only high-quality signals are executed.

Author: GitHub Copilot
Date: October 25, 2025
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SignalQualityAnalyzer:
    """
    Analyze signal quality with time-decay and expectancy calculations.
    
    Features:
    - Exponential time-decay for aging signals
    - Mathematical expectancy calculation (positive EV filter)
    - Position size adjustment based on signal quality
    """
    
    def __init__(
        self,
        decay_rate: float = 0.3,
        signal_lifetime_minutes: int = 5,
        min_expectancy: float = 0.2
    ):
        """
        Initialize signal quality analyzer.
        
        Args:
            decay_rate: Exponential decay rate (0.3 = ~75% decay in 5 min)
            signal_lifetime_minutes: Maximum signal lifetime (5 min default)
            min_expectancy: Minimum expectancy in R-multiples (0.2R default)
        """
        self.decay_rate = decay_rate
        self.signal_lifetime_minutes = signal_lifetime_minutes
        self.min_expectancy = min_expectancy
        
        # Cache for historical performance by symbol/timeframe
        self.performance_cache = {}
    
    def calculate_time_decay(
        self,
        signal_timestamp: datetime,
        current_time: Optional[datetime] = None
    ) -> Tuple[float, float]:
        """
        Calculate exponential time decay for signal confidence.
        
        Signal quality decreases exponentially as time passes since generation.
        
        Args:
            signal_timestamp: When signal was generated
            current_time: Current time (default: now)
            
        Returns:
            Tuple of (decay_factor, minutes_elapsed)
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Calculate time elapsed in minutes
        time_elapsed = (current_time - signal_timestamp).total_seconds() / 60.0
        
        # Exponential decay: e^(-decay_rate * time)
        decay_factor = np.exp(-self.decay_rate * time_elapsed)
        
        # Signal is expired if beyond lifetime
        if time_elapsed > self.signal_lifetime_minutes:
            decay_factor = 0.0
        
        return decay_factor, time_elapsed
    
    def adjust_confidence_for_time(
        self,
        original_confidence: float,
        signal_timestamp: datetime,
        current_time: Optional[datetime] = None
    ) -> Dict:
        """
        Adjust signal confidence based on time decay.
        
        Args:
            original_confidence: Original signal confidence (0-1)
            signal_timestamp: When signal was generated
            current_time: Current time (default: now)
            
        Returns:
            Dict with adjusted confidence and decay details
        """
        decay_factor, minutes_elapsed = self.calculate_time_decay(
            signal_timestamp, current_time
        )
        
        adjusted_confidence = original_confidence * decay_factor
        
        # Determine freshness category
        if minutes_elapsed < 1:
            freshness = 'very_fresh'
        elif minutes_elapsed < 2:
            freshness = 'fresh'
        elif minutes_elapsed < 4:
            freshness = 'aging'
        elif minutes_elapsed < self.signal_lifetime_minutes:
            freshness = 'stale'
        else:
            freshness = 'expired'
        
        return {
            'original_confidence': original_confidence,
            'adjusted_confidence': adjusted_confidence,
            'decay_factor': decay_factor,
            'minutes_elapsed': minutes_elapsed,
            'freshness': freshness,
            'is_expired': decay_factor < 0.01  # Effectively zero
        }
    
    def calculate_position_size_multiplier(self, decay_factor: float) -> float:
        """
        Calculate position size multiplier based on signal freshness.
        
        Reduces position size for older signals:
        - decay_factor >= 0.8: Full size (1.0x)
        - decay_factor 0.5-0.8: Reduced size (0.85x)
        - decay_factor < 0.5: Significantly reduced (0.7x)
        
        Args:
            decay_factor: Time decay factor (0-1)
            
        Returns:
            Position size multiplier (0.7-1.0)
        """
        if decay_factor >= 0.8:
            return 1.0  # Fresh signal, full size
        elif decay_factor >= 0.5:
            return 0.85  # Aging signal, slight reduction
        else:
            return 0.7  # Stale signal, 30% reduction
    
    def calculate_expectancy(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        win_rate: float
    ) -> Dict:
        """
        Calculate mathematical expectancy for a trade.
        
        Expectancy = (Win Rate × Avg Win) - ((1 - Win Rate) × Avg Loss)
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            win_rate: Historical win rate (0-1, e.g., 0.55 = 55%)
            
        Returns:
            Dict with expectancy analysis
        """
        # Calculate win and loss amounts
        avg_win = abs(take_profit - entry_price)
        avg_loss = abs(entry_price - stop_loss)
        
        if avg_loss == 0:
            logger.warning("Stop loss equals entry price, cannot calculate expectancy")
            return {
                'expectancy': 0.0,
                'expectancy_ratio': 0.0,
                'is_positive': False
            }
        
        # Mathematical expectancy
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        # Expectancy ratio (in R-multiples)
        expectancy_ratio = expectancy / avg_loss
        
        # Determine if trade is profitable in expectation
        is_positive = expectancy > 0
        passes_threshold = expectancy_ratio >= self.min_expectancy
        
        return {
            'expectancy': expectancy,
            'expectancy_ratio': expectancy_ratio,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'win_rate': win_rate,
            'is_positive': is_positive,
            'passes_threshold': passes_threshold,
            'recommendation': 'TAKE' if passes_threshold else 'SKIP'
        }
    
    def update_performance_stats(
        self,
        symbol: str,
        timeframe: str,
        was_winner: bool,
        pnl: float
    ):
        """
        Update historical performance statistics.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC')
            timeframe: Timeframe (e.g., '15m')
            was_winner: Whether trade was profitable
            pnl: Profit/loss amount
        """
        key = f"{symbol}_{timeframe}"
        
        if key not in self.performance_cache:
            self.performance_cache[key] = {
                'total_trades': 0,
                'winning_trades': 0,
                'total_pnl': 0.0,
                'winning_pnl': 0.0,
                'losing_pnl': 0.0
            }
        
        stats = self.performance_cache[key]
        stats['total_trades'] += 1
        stats['total_pnl'] += pnl
        
        if was_winner:
            stats['winning_trades'] += 1
            stats['winning_pnl'] += pnl
        else:
            stats['losing_pnl'] += abs(pnl)
    
    def get_win_rate(self, symbol: str, timeframe: str, default: float = 0.50) -> float:
        """
        Get historical win rate for symbol/timeframe combination.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            default: Default win rate if no history (0.50 = 50%)
            
        Returns:
            Win rate as decimal (0-1)
        """
        key = f"{symbol}_{timeframe}"
        
        if key not in self.performance_cache:
            return default
        
        stats = self.performance_cache[key]
        if stats['total_trades'] == 0:
            return default
        
        win_rate = stats['winning_trades'] / stats['total_trades']
        return win_rate
    
    def get_avg_win_loss_ratio(
        self,
        symbol: str,
        timeframe: str,
        default: float = 2.0
    ) -> float:
        """
        Get average win/loss ratio.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            default: Default ratio if no history (2.0 default)
            
        Returns:
            Win/loss ratio
        """
        key = f"{symbol}_{timeframe}"
        
        if key not in self.performance_cache:
            return default
        
        stats = self.performance_cache[key]
        
        if stats['winning_trades'] == 0 or stats['total_trades'] <= stats['winning_trades']:
            return default
        
        avg_win = stats['winning_pnl'] / stats['winning_trades']
        losing_trades = stats['total_trades'] - stats['winning_trades']
        avg_loss = stats['losing_pnl'] / losing_trades if losing_trades > 0 else 1.0
        
        if avg_loss == 0:
            return default
        
        return avg_win / avg_loss
    
    def analyze_signal_quality(
        self,
        signal: Dict,
        current_time: Optional[datetime] = None
    ) -> Dict:
        """
        Comprehensive signal quality analysis.
        
        Combines time-decay and expectancy analysis to provide
        complete signal evaluation.
        
        Args:
            signal: Signal dict with required fields
            current_time: Current time (default: now)
            
        Returns:
            Dict with complete analysis
        """
        # Extract signal data
        signal_timestamp = signal.get('timestamp', datetime.now())
        if isinstance(signal_timestamp, str):
            signal_timestamp = datetime.fromisoformat(signal_timestamp)
        
        original_confidence = signal.get('confidence', 0.5)
        entry_price = signal.get('entry_price', 0)
        stop_loss = signal.get('stop_loss', 0)
        take_profit = signal.get('take_profit', 0)
        symbol = signal.get('symbol', 'UNKNOWN')
        timeframe = signal.get('timeframe', '15m')
        
        # Time-decay analysis
        decay_analysis = self.adjust_confidence_for_time(
            original_confidence, signal_timestamp, current_time
        )
        
        # Position size adjustment
        size_multiplier = self.calculate_position_size_multiplier(
            decay_analysis['decay_factor']
        )
        
        # Expectancy analysis
        win_rate = self.get_win_rate(symbol, timeframe)
        expectancy_analysis = self.calculate_expectancy(
            entry_price, stop_loss, take_profit, win_rate
        )
        
        # Overall recommendation
        should_take = (
            not decay_analysis['is_expired'] and
            expectancy_analysis['passes_threshold'] and
            decay_analysis['adjusted_confidence'] > 0.3
        )
        
        return {
            'time_decay': decay_analysis,
            'position_size_multiplier': size_multiplier,
            'expectancy': expectancy_analysis,
            'should_take_signal': should_take,
            'rejection_reason': self._get_rejection_reason(
                decay_analysis, expectancy_analysis
            )
        }
    
    def _get_rejection_reason(self, decay_analysis: Dict, expectancy_analysis: Dict) -> Optional[str]:
        """Determine why signal should be rejected, if applicable."""
        if decay_analysis['is_expired']:
            return f"Signal expired ({decay_analysis['minutes_elapsed']:.1f} min old)"
        
        if not expectancy_analysis['passes_threshold']:
            return f"Low expectancy ({expectancy_analysis['expectancy_ratio']:.2f}R < {self.min_expectancy}R)"
        
        if decay_analysis['adjusted_confidence'] <= 0.3:
            return f"Low confidence ({decay_analysis['adjusted_confidence']:.2f})"
        
        return None
