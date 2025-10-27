"""
Correlation Matrix and Portfolio Heat Calculator
================================================

Calculates real-time correlations between crypto assets and monitors
portfolio heat to prevent over-exposure to correlated positions.

Author: GitHub Copilot
Date: October 25, 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """
    Analyze correlations between crypto assets and calculate portfolio risk.
    
    Prevents "fake diversification" where multiple positions are actually
    correlated (e.g., all moving with BTC).
    """
    
    def __init__(self, correlation_threshold: float = 0.7, max_portfolio_heat: float = 0.06):
        """
        Initialize correlation analyzer.
        
        Args:
            correlation_threshold: Correlation above this is considered high (0.7 default)
            max_portfolio_heat: Maximum allowed portfolio heat (0.06 = 6% default)
        """
        self.correlation_threshold = correlation_threshold
        self.max_portfolio_heat = max_portfolio_heat
        
        # Cache for correlation data
        self.correlation_matrix = {}
        self.last_update = None
        self.update_interval = timedelta(hours=1)  # Recalculate hourly
        
        # Historical price cache for correlation calculation
        self.price_history = {}
        self.lookback_period = 30  # Days for correlation calculation
    
    def update_price_history(self, symbol: str, prices: pd.Series):
        """
        Update price history for correlation calculations.
        
        Args:
            symbol: Symbol (e.g., 'BTC', 'ETH')
            prices: Series of historical prices with datetime index
        """
        # Store only last N days
        cutoff = datetime.now() - timedelta(days=self.lookback_period)
        self.price_history[symbol] = prices[prices.index > cutoff]
        
        logger.debug(f"Updated price history for {symbol}: {len(prices)} data points")
    
    def calculate_correlation_matrix(self, symbols: List[str] = None) -> pd.DataFrame:
        """
        Calculate correlation matrix between all symbols.
        
        Args:
            symbols: List of symbols to analyze (default: all in price_history)
            
        Returns:
            DataFrame with pairwise correlations
        """
        if symbols is None:
            symbols = list(self.price_history.keys())
        
        # Check if we need to recalculate
        if (self.last_update is not None and 
            datetime.now() - self.last_update < self.update_interval and
            self.correlation_matrix):
            logger.debug("Using cached correlation matrix")
            return pd.DataFrame(self.correlation_matrix)
        
        # Build price DataFrame
        price_data = {}
        for symbol in symbols:
            if symbol in self.price_history:
                price_data[symbol] = self.price_history[symbol]
        
        if len(price_data) < 2:
            logger.warning("Need at least 2 symbols for correlation calculation")
            return pd.DataFrame()
        
        # Create aligned DataFrame and calculate returns
        df = pd.DataFrame(price_data)
        df = df.fillna(method='ffill').fillna(method='bfill')
        returns = df.pct_change().dropna()
        
        # Calculate correlation matrix
        correlation_df = returns.corr()
        
        # Cache results
        self.correlation_matrix = correlation_df.to_dict()
        self.last_update = datetime.now()
        
        logger.info(f"Updated correlation matrix for {len(symbols)} symbols")
        return correlation_df
    
    def get_correlation(self, symbol1: str, symbol2: str) -> float:
        """
        Get correlation coefficient between two symbols.
        
        Args:
            symbol1: First symbol
            symbol2: Second symbol
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        if not self.correlation_matrix:
            self.calculate_correlation_matrix()
        
        try:
            return self.correlation_matrix.get(symbol1, {}).get(symbol2, 0.0)
        except Exception as e:
            logger.warning(f"Error getting correlation for {symbol1}/{symbol2}: {e}")
            return 0.0
    
    def calculate_portfolio_heat(
        self,
        active_positions: List[Dict]
    ) -> Tuple[float, Dict]:
        """
        Calculate portfolio heat based on position correlations.
        
        Portfolio heat = sum of (position1_risk × position2_risk × correlation)
        for all pairs of positions.
        
        Args:
            active_positions: List of position dicts with 'symbol' and 'risk_amount'
            
        Returns:
            Tuple of (total_heat, detailed_breakdown_dict)
        """
        if len(active_positions) <= 1:
            return 0.0, {}
        
        total_heat = 0.0
        breakdown = {}
        
        # Calculate pairwise heat
        for i, pos1 in enumerate(active_positions):
            for j, pos2 in enumerate(active_positions):
                if i >= j:  # Skip self and duplicate pairs
                    continue
                
                symbol1 = pos1['symbol']
                symbol2 = pos2['symbol']
                risk1 = pos1.get('risk_amount', 0.0)
                risk2 = pos2.get('risk_amount', 0.0)
                
                # Get correlation
                corr = self.get_correlation(symbol1, symbol2)
                
                # Calculate heat contribution
                pair_heat = risk1 * risk2 * corr
                total_heat += pair_heat
                
                # Store in breakdown
                pair_key = f"{symbol1}/{symbol2}"
                breakdown[pair_key] = {
                    'correlation': corr,
                    'risk1': risk1,
                    'risk2': risk2,
                    'heat_contribution': pair_heat
                }
        
        return total_heat, breakdown
    
    def check_new_position_allowed(
        self,
        new_symbol: str,
        new_risk: float,
        active_positions: List[Dict]
    ) -> Tuple[bool, str, float]:
        """
        Check if a new position would exceed portfolio heat limits.
        
        Args:
            new_symbol: Symbol for new position
            new_risk: Risk amount for new position (as decimal, e.g., 0.01 = 1%)
            active_positions: Current active positions
            
        Returns:
            Tuple of (allowed: bool, reason: str, projected_heat: float)
        """
        # Calculate current heat (not used but good for logging)
        _, _ = self.calculate_portfolio_heat(active_positions)
        
        # Calculate projected heat with new position
        projected_positions = active_positions + [{
            'symbol': new_symbol,
            'risk_amount': new_risk
        }]
        projected_heat, _ = self.calculate_portfolio_heat(projected_positions)
        
        # Check against limit
        if projected_heat > self.max_portfolio_heat:
            reason = (
                f"Portfolio heat would be {projected_heat:.4f} "
                f"(limit: {self.max_portfolio_heat:.4f}). "
                f"High correlation with existing positions."
            )
            return False, reason, projected_heat
        
        # Check individual correlations
        high_corr_symbols = []
        for pos in active_positions:
            corr = self.get_correlation(new_symbol, pos['symbol'])
            if abs(corr) > self.correlation_threshold:
                high_corr_symbols.append(f"{pos['symbol']} ({corr:.2f})")
        
        if high_corr_symbols:
            warning = (
                f"Warning: {new_symbol} highly correlated with: "
                f"{', '.join(high_corr_symbols)}"
            )
            logger.warning(warning)
        
        return True, "Position allowed", projected_heat
    
    def get_portfolio_diversification_score(self, active_positions: List[Dict]) -> float:
        """
        Calculate portfolio diversification score (0-1, higher is better).
        
        Args:
            active_positions: List of active positions
            
        Returns:
            Diversification score (1.0 = perfectly diversified, 0.0 = perfectly correlated)
        """
        if len(active_positions) <= 1:
            return 1.0
        
        # Get average absolute correlation
        correlations = []
        for i, pos1 in enumerate(active_positions):
            for j, pos2 in enumerate(active_positions):
                if i >= j:
                    continue
                corr = self.get_correlation(pos1['symbol'], pos2['symbol'])
                correlations.append(abs(corr))
        
        if not correlations:
            return 1.0
        
        avg_correlation = np.mean(correlations)
        
        # Convert to diversification score (inverse of correlation)
        diversification_score = 1.0 - avg_correlation
        
        return max(0.0, min(1.0, diversification_score))
    
    def get_correlation_report(self, symbols: List[str] = None) -> Dict:
        """
        Generate comprehensive correlation report.
        
        Args:
            symbols: List of symbols to analyze
            
        Returns:
            Dict with correlation analysis
        """
        corr_matrix = self.calculate_correlation_matrix(symbols)
        
        if corr_matrix.empty:
            return {'error': 'Insufficient data for correlation analysis'}
        
        # Find highly correlated pairs
        high_correlations = []
        symbols_list = corr_matrix.columns.tolist()
        
        for i, sym1 in enumerate(symbols_list):
            for j, sym2 in enumerate(symbols_list):
                if i >= j:
                    continue
                corr = corr_matrix.loc[sym1, sym2]
                if abs(corr) > self.correlation_threshold:
                    high_correlations.append({
                        'pair': f"{sym1}/{sym2}",
                        'correlation': corr,
                        'strength': 'Very High' if abs(corr) > 0.85 else 'High'
                    })
        
        return {
            'correlation_matrix': corr_matrix.to_dict(),
            'high_correlations': high_correlations,
            'average_correlation': corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean(),
            'max_correlation': corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].max(),
            'min_correlation': corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].min(),
            'last_updated': self.last_update.isoformat() if self.last_update else None
        }


# Convenience function for quick correlation calculation
def calculate_crypto_correlations(price_data: Dict[str, pd.Series]) -> pd.DataFrame:
    """
    Quick correlation calculation from price data.
    
    Args:
        price_data: Dict of {symbol: price_series}
        
    Returns:
        Correlation matrix DataFrame
    """
    analyzer = CorrelationAnalyzer()
    for symbol, prices in price_data.items():
        analyzer.update_price_history(symbol, prices)
    return analyzer.calculate_correlation_matrix()
