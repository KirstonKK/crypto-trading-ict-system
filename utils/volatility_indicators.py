"""
Volatility Indicators for Dynamic Risk Management
=================================================

Implements ATR-based calculations and volatility regime detection
for adaptive stop losses and position sizing.

Author: GitHub Copilot
Date: October 25, 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class VolatilityAnalyzer:
    """Calculate ATR and detect volatility regimes for adaptive risk management."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize volatility analyzer.
        
        Args:
            config: Optional configuration dict with volatility thresholds
        """
        self.config = config or {}
        
        # Volatility regime thresholds (from risk_parameters.json)
        self.regimes = self.config.get('volatility_regimes', {
            'low': {'threshold': 0.02, 'stop_multiplier': 0.8},
            'medium': {'threshold': 0.05, 'stop_multiplier': 1.0},
            'high': {'threshold': 0.08, 'stop_multiplier': 1.3},
            'extreme': {'threshold': 0.15, 'stop_multiplier': 1.5}
        })
        
        # ATR parameters
        self.atr_period = 14
        self.atr_multiplier = 2.0  # From config
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR).
        
        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            period: ATR period (default 14)
            
        Returns:
            Series of ATR values
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate True Range components
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        # True Range is the maximum of the three
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # ATR is EMA of True Range
        atr = tr.ewm(span=period, adjust=False).mean()
        
        return atr
    
    def calculate_normalized_volatility(self, df: pd.DataFrame, lookback: int = 20) -> float:
        """
        Calculate normalized volatility (relative to price).
        
        Args:
            df: DataFrame with OHLC data
            lookback: Period for volatility calculation
            
        Returns:
            Normalized volatility as float (e.g., 0.025 = 2.5%)
        """
        if len(df) < lookback:
            return 0.03  # Default medium volatility
        
        # Calculate returns
        returns = df['close'].pct_change()
        
        # Standard deviation of returns
        volatility = returns.tail(lookback).std()
        
        # Annualize (assumes daily data, adjust if needed)
        # For crypto, we use 365 days
        annualized_vol = volatility * np.sqrt(365)
        
        return annualized_vol
    
    def detect_volatility_regime(self, volatility: float) -> Tuple[str, float]:
        """
        Detect current volatility regime and return appropriate stop multiplier.
        
        Args:
            volatility: Normalized volatility (e.g., 0.05 = 5%)
            
        Returns:
            Tuple of (regime_name, stop_multiplier)
        """
        if volatility < self.regimes['low']['threshold']:
            return 'low', self.regimes['low']['stop_multiplier']
        elif volatility < self.regimes['medium']['threshold']:
            return 'medium', self.regimes['medium']['stop_multiplier']
        elif volatility < self.regimes['high']['threshold']:
            return 'high', self.regimes['high']['stop_multiplier']
        else:
            return 'extreme', self.regimes['extreme']['stop_multiplier']
    
    def calculate_dynamic_stop_loss(
        self,
        entry_price: float,
        atr: float,
        direction: str,
        volatility_regime: str = 'medium'
    ) -> float:
        """
        Calculate dynamic stop loss based on ATR and volatility regime.
        
        Args:
            entry_price: Entry price for the trade
            atr: Current ATR value
            direction: 'BUY' or 'SELL'
            volatility_regime: Current volatility regime
            
        Returns:
            Stop loss price
        """
        # Get regime multiplier
        _, regime_multiplier = self.detect_volatility_regime(
            self._regime_to_volatility(volatility_regime)
        )
        
        # Calculate stop distance
        stop_distance = self.atr_multiplier * atr * regime_multiplier
        
        # Apply stop loss based on direction
        if direction == 'BUY':
            stop_loss = entry_price - stop_distance
        else:  # SELL
            stop_loss = entry_price + stop_distance
        
        return stop_loss
    
    def calculate_dynamic_take_profit(
        self,
        entry_price: float,
        stop_loss: float,
        risk_reward_ratio: float
    ) -> float:
        """
        Calculate take profit based on stop loss and risk-reward ratio.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_reward_ratio: Target R:R ratio (e.g., 3.0 for 1:3)
            
        Returns:
            Take profit price
        """
        stop_distance = abs(entry_price - stop_loss)
        profit_distance = stop_distance * risk_reward_ratio
        
        # Determine direction from stop loss position
        if stop_loss < entry_price:  # Long position
            take_profit = entry_price + profit_distance
        else:  # Short position
            take_profit = entry_price - profit_distance
        
        return take_profit
    
    def _regime_to_volatility(self, regime: str) -> float:
        """Convert regime name to representative volatility value."""
        regime_map = {
            'low': 0.015,
            'medium': 0.035,
            'high': 0.065,
            'extreme': 0.12
        }
        return regime_map.get(regime, 0.035)
    
    def get_atr_analysis(self, df: pd.DataFrame, current_price: float) -> Dict:
        """
        Get comprehensive ATR analysis for current market conditions.
        
        Args:
            df: Historical OHLC DataFrame
            current_price: Current price
            
        Returns:
            Dict with ATR analysis results
        """
        # Calculate ATR
        atr = self.calculate_atr(df, self.atr_period)
        current_atr = atr.iloc[-1] if len(atr) > 0 else current_price * 0.02
        
        # Calculate normalized volatility
        volatility = self.calculate_normalized_volatility(df)
        
        # Detect regime
        regime, stop_multiplier = self.detect_volatility_regime(volatility)
        
        # Calculate ATR percentage
        atr_percent = (current_atr / current_price) * 100
        
        return {
            'atr': current_atr,
            'atr_percent': atr_percent,
            'volatility': volatility,
            'regime': regime,
            'stop_multiplier': stop_multiplier,
            'recommended_stop_distance': current_atr * self.atr_multiplier * stop_multiplier
        }


# Convenience function for quick ATR calculation
def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Quick ATR calculation wrapper."""
    analyzer = VolatilityAnalyzer()
    return analyzer.calculate_atr(df, period)
