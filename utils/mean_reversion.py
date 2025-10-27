"""
Mean Reversion Indicators and Overlay
=====================================

Implements Bollinger Bands and Z-score calculations to detect
extended moves and prevent chasing overbought/oversold conditions.

Author: GitHub Copilot
Date: October 25, 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class MeanReversionAnalyzer:
    """
    Analyze mean reversion opportunities using Bollinger Bands and Z-scores.
    
    Prevents chasing extended moves by:
    - Reducing position size when overbought
    - Increasing position size when oversold (with trend)
    """
    
    def __init__(
        self,
        bb_period: int = 20,
        bb_std: float = 2.0,
        zscore_period: int = 50,
        overbought_threshold: float = 0.8,
        oversold_threshold: float = 0.2,
        zscore_extreme: float = 2.0
    ):
        """
        Initialize mean reversion analyzer.
        
        Args:
            bb_period: Bollinger Band period (20 default)
            bb_std: Number of standard deviations (2.0 default)
            zscore_period: Z-score moving average period (50 default)
            overbought_threshold: BB position threshold for overbought (0.8 = 80%)
            oversold_threshold: BB position threshold for oversold (0.2 = 20%)
            zscore_extreme: Z-score threshold for extreme readings (2.0 default)
        """
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.zscore_period = zscore_period
        self.overbought_threshold = overbought_threshold
        self.oversold_threshold = oversold_threshold
        self.zscore_extreme = zscore_extreme
    
    def calculate_bollinger_bands(
        self,
        df: pd.DataFrame,
        price_column: str = 'close'
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands.
        
        Args:
            df: DataFrame with price data
            price_column: Column to use for calculation
            
        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        prices = df[price_column]
        
        # Middle band (SMA)
        middle_band = prices.rolling(window=self.bb_period).mean()
        
        # Standard deviation
        std = prices.rolling(window=self.bb_period).std()
        
        # Upper and lower bands
        upper_band = middle_band + (self.bb_std * std)
        lower_band = middle_band - (self.bb_std * std)
        
        return upper_band, middle_band, lower_band
    
    def calculate_bb_position(
        self,
        current_price: float,
        upper_band: float,
        lower_band: float
    ) -> float:
        """
        Calculate relative position within Bollinger Bands.
        
        Args:
            current_price: Current price
            upper_band: Upper Bollinger Band
            lower_band: Lower Bollinger Band
            
        Returns:
            Position (0-1, where 0.5 is middle, >0.8 is overbought, <0.2 is oversold)
        """
        if upper_band == lower_band:
            return 0.5  # Bands collapsed, assume neutral
        
        bb_position = (current_price - lower_band) / (upper_band - lower_band)
        
        # Clamp to 0-1 range (price can be outside bands)
        return max(0.0, min(1.0, bb_position))
    
    def calculate_zscore(
        self,
        df: pd.DataFrame,
        price_column: str = 'close'
    ) -> pd.Series:
        """
        Calculate Z-score relative to moving average.
        
        Z-score = (Price - MA) / StdDev
        
        Args:
            df: DataFrame with price data
            price_column: Column to use
            
        Returns:
            Series of Z-scores
        """
        prices = df[price_column]
        
        # Moving average
        ma = prices.rolling(window=self.zscore_period).mean()
        
        # Standard deviation
        std = prices.rolling(window=self.zscore_period).std()
        
        # Z-score
        zscore = (prices - ma) / std
        
        return zscore.fillna(0)
    
    def detect_extended_move(
        self,
        bb_position: float,
        zscore: float
    ) -> Tuple[str, str]:
        """
        Detect if price is in an extended move (overbought/oversold).
        
        Args:
            bb_position: Bollinger Band position (0-1)
            zscore: Z-score value
            
        Returns:
            Tuple of (condition, severity)
            condition: 'overbought', 'oversold', or 'neutral'
            severity: 'extreme', 'moderate', or 'mild'
        """
        # Check Bollinger Band position
        bb_signal = 'neutral'
        if bb_position > self.overbought_threshold:
            bb_signal = 'overbought'
        elif bb_position < self.oversold_threshold:
            bb_signal = 'oversold'
        
        # Check Z-score
        zscore_signal = 'neutral'
        if zscore > self.zscore_extreme:
            zscore_signal = 'overbought'
        elif zscore < -self.zscore_extreme:
            zscore_signal = 'oversold'
        
        # Combine signals
        if bb_signal == zscore_signal and bb_signal != 'neutral':
            condition = bb_signal
            # Determine severity
            if abs(zscore) > self.zscore_extreme * 1.5:
                severity = 'extreme'
            elif bb_signal == 'overbought' and bb_position > 0.9:
                severity = 'extreme'
            elif bb_signal == 'oversold' and bb_position < 0.1:
                severity = 'extreme'
            else:
                severity = 'moderate'
        elif bb_signal != 'neutral' or zscore_signal != 'neutral':
            condition = bb_signal if bb_signal != 'neutral' else zscore_signal
            severity = 'mild'
        else:
            condition = 'neutral'
            severity = 'none'
        
        return condition, severity
    
    def calculate_position_adjustment(
        self,
        signal_direction: str,
        bb_position: float,
        zscore: float
    ) -> Tuple[float, str]:
        """
        Calculate position size adjustment based on mean reversion.
        
        Strategy:
        - COUNTER-TREND: Reduce size when signal goes with extended move
        - WITH-TREND: Increase size when signal goes against extended move
        
        Args:
            signal_direction: 'BUY' or 'SELL'
            bb_position: Bollinger Band position
            zscore: Z-score
            
        Returns:
            Tuple of (multiplier, reasoning)
        """
        condition, severity = self.detect_extended_move(bb_position, zscore)
        
        # Neutral conditions - no adjustment
        if condition == 'neutral':
            return 1.0, "Neutral position, no adjustment"
        
        # Check if signal is with or against the extended move
        is_counter_trend = (
            (signal_direction == 'BUY' and condition == 'overbought') or
            (signal_direction == 'SELL' and condition == 'oversold')
        )
        
        if is_counter_trend:
            # Chasing extended move - REDUCE size
            if severity == 'extreme':
                multiplier = 0.5  # Half size
                reasoning = f"Extreme {condition}, counter-trend signal - 50% size"
            elif severity == 'moderate':
                multiplier = 0.7  # 30% reduction
                reasoning = f"Moderate {condition}, counter-trend signal - 70% size"
            else:
                multiplier = 0.85  # 15% reduction
                reasoning = f"Mild {condition}, counter-trend signal - 85% size"
        else:
            # Trading WITH mean reversion - INCREASE size
            if severity == 'extreme':
                multiplier = 1.5  # 50% increase
                reasoning = f"Extreme {condition}, with-trend signal - 150% size"
            elif severity == 'moderate':
                multiplier = 1.3  # 30% increase
                reasoning = f"Moderate {condition}, with-trend signal - 130% size"
            else:
                multiplier = 1.15  # 15% increase
                reasoning = f"Mild {condition}, with-trend signal - 115% size"
        
        return multiplier, reasoning
    
    def analyze_price_extension(
        self,
        df: pd.DataFrame,
        signal_direction: str
    ) -> Dict:
        """
        Comprehensive price extension analysis.
        
        Args:
            df: DataFrame with OHLC data
            signal_direction: 'BUY' or 'SELL'
            
        Returns:
            Dict with complete analysis
        """
        # Calculate indicators
        upper_bb, middle_bb, lower_bb = self.calculate_bollinger_bands(df)
        zscore = self.calculate_zscore(df)
        
        # Current values
        current_price = df['close'].iloc[-1]
        current_bb_position = self.calculate_bb_position(
            current_price,
            upper_bb.iloc[-1],
            lower_bb.iloc[-1]
        )
        current_zscore = zscore.iloc[-1]
        
        # Detect condition
        condition, severity = self.detect_extended_move(
            current_bb_position,
            current_zscore
        )
        
        # Calculate adjustment
        multiplier, reasoning = self.calculate_position_adjustment(
            signal_direction,
            current_bb_position,
            current_zscore
        )
        
        # Additional metrics
        distance_to_upper = ((upper_bb.iloc[-1] - current_price) / current_price) * 100
        distance_to_lower = ((current_price - lower_bb.iloc[-1]) / current_price) * 100
        
        return {
            'bb_position': current_bb_position,
            'zscore': current_zscore,
            'condition': condition,
            'severity': severity,
            'position_multiplier': multiplier,
            'reasoning': reasoning,
            'bollinger_bands': {
                'upper': upper_bb.iloc[-1],
                'middle': middle_bb.iloc[-1],
                'lower': lower_bb.iloc[-1],
                'distance_to_upper_pct': distance_to_upper,
                'distance_to_lower_pct': distance_to_lower
            },
            'recommendation': self._generate_recommendation(
                condition, severity, signal_direction
            )
        }
    
    def _generate_recommendation(
        self,
        condition: str,
        severity: str,
        signal_direction: str
    ) -> str:
        """Generate trading recommendation based on analysis."""
        if condition == 'neutral':
            return "Execute signal normally"
        
        is_counter_trend = (
            (signal_direction == 'BUY' and condition == 'overbought') or
            (signal_direction == 'SELL' and condition == 'oversold')
        )
        
        if is_counter_trend:
            if severity == 'extreme':
                return f"⚠️  EXTREME {condition.upper()} - Consider waiting for pullback"
            elif severity == 'moderate':
                return f"⚠️  {condition.upper()} - Reduce position size"
            else:
                return f"ℹ️  Mildly {condition} - Slight caution"
        else:
            if severity == 'extreme':
                return f"✅ EXCELLENT - Extreme {condition}, high probability mean reversion"
            elif severity == 'moderate':
                return f"✅ GOOD - {condition.capitalize()}, favorable for mean reversion"
            else:
                return "✅ Execute normally with slight size increase"


# Convenience function for quick BB calculation
def calculate_bollinger_bands(
    prices: pd.Series,
    period: int = 20,
    num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Quick Bollinger Bands calculation."""
    analyzer = MeanReversionAnalyzer(bb_period=period, bb_std=num_std)
    df = pd.DataFrame({'close': prices})
    return analyzer.calculate_bollinger_bands(df)
