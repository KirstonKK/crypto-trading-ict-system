"""
Performance Analytics for Trading Strategy Backtests
===================================================

This module provides comprehensive performance analysis for trading strategies,
calculating institutional-grade risk and return metrics.

Features:
- Sharpe ratio and risk-adjusted returns
- Maximum drawdown analysis
- Win rate and profit factor calculations
- Monthly/yearly performance breakdown
- Risk metrics and volatility analysis
- Benchmark comparison capabilities

Metrics Calculated:
- Total Return, CAGR, Volatility
- Sharpe Ratio, Sortino Ratio, Calmar Ratio
- Maximum Drawdown, Average Drawdown
- Win Rate, Profit Factor, Expectancy
- Trade statistics and distribution analysis

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Container for all performance analysis results."""
    # Return metrics
    total_return: float
    cagr: float
    volatility: float
    
    # Risk-adjusted metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Drawdown analysis
    max_drawdown: float
    avg_drawdown: float
    max_drawdown_duration: int
    
    # Trading statistics
    total_trades: int
    win_rate: float
    profit_factor: float
    expectancy: float
    
    # Additional metrics
    best_trade: float
    worst_trade: float
    avg_trade: float
    avg_win: float
    avg_loss: float
    largest_losing_streak: int
    largest_winning_streak: int
    
    # Time-based analysis
    monthly_returns: Dict[str, float]
    yearly_returns: Dict[str, float]
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for serialization."""
        return {
            'return_metrics': {
                'total_return': self.total_return,
                'cagr': self.cagr,
                'volatility': self.volatility
            },
            'risk_adjusted_metrics': {
                'sharpe_ratio': self.sharpe_ratio,
                'sortino_ratio': self.sortino_ratio,
                'calmar_ratio': self.calmar_ratio
            },
            'drawdown_analysis': {
                'max_drawdown': self.max_drawdown,
                'avg_drawdown': self.avg_drawdown,
                'max_drawdown_duration': self.max_drawdown_duration
            },
            'trading_statistics': {
                'total_trades': self.total_trades,
                'win_rate': self.win_rate,
                'profit_factor': self.profit_factor,
                'expectancy': self.expectancy
            },
            'trade_analysis': {
                'best_trade': self.best_trade,
                'worst_trade': self.worst_trade,
                'avg_trade': self.avg_trade,
                'avg_win': self.avg_win,
                'avg_loss': self.avg_loss,
                'largest_losing_streak': self.largest_losing_streak,
                'largest_winning_streak': self.largest_winning_streak
            },
            'time_based_analysis': {
                'monthly_returns': self.monthly_returns,
                'yearly_returns': self.yearly_returns
            }
        }


class PerformanceAnalyzer:
    """
    Comprehensive performance analysis for trading strategies.
    
    This class calculates institutional-grade performance metrics
    and provides detailed analysis of trading strategy results.
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize performance analyzer.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe ratio calculation
        """
        self.risk_free_rate = risk_free_rate
        logger.info(f"Performance analyzer initialized with {risk_free_rate:.2%} risk-free rate")
    
    def analyze_trades(self, trades: List[Dict]) -> PerformanceMetrics:
        """
        Comprehensive analysis of trading results.
        
        Args:
            trades: List of trade dictionaries from backtesting
            
        Returns:
            PerformanceMetrics object with all calculated metrics
        """
        if not trades:
            logger.warning("No trades provided for analysis")
            return self._empty_metrics()
        
        logger.info(f"Analyzing {len(trades)} trades")
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(trades)
        
        # Calculate basic metrics
        total_pnl = df['pnl'].sum()
        winning_trades = df[df['pnl'] > 0]
        losing_trades = df[df['pnl'] < 0]
        
        # Return calculations
        total_return = self._calculate_total_return(df)
        cagr = self._calculate_cagr(df, total_return)
        volatility = self._calculate_volatility(df)
        
        # Risk-adjusted metrics
        sharpe_ratio = self._calculate_sharpe_ratio(df, volatility)
        sortino_ratio = self._calculate_sortino_ratio(df)
        
        # Drawdown analysis
        drawdown_metrics = self._calculate_drawdown_metrics(df)
        calmar_ratio = cagr / abs(drawdown_metrics['max_drawdown']) if drawdown_metrics['max_drawdown'] != 0 else 0
        
        # Trading statistics
        win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
        profit_factor = self._calculate_profit_factor(winning_trades, losing_trades)
        expectancy = self._calculate_expectancy(winning_trades, losing_trades, len(trades))
        
        # Trade analysis
        best_trade = df['pnl'].max()
        worst_trade = df['pnl'].min()
        avg_trade = df['pnl'].mean()
        avg_win = winning_trades['pnl'].mean() if not winning_trades.empty else 0
        avg_loss = losing_trades['pnl'].mean() if not losing_trades.empty else 0
        
        # Streak analysis
        streaks = self._calculate_streaks(df)
        
        # Time-based analysis
        monthly_returns = self._calculate_monthly_returns(df)
        yearly_returns = self._calculate_yearly_returns(df)
        
        metrics = PerformanceMetrics(
            # Return metrics
            total_return=total_return,
            cagr=cagr,
            volatility=volatility,
            
            # Risk-adjusted metrics
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            
            # Drawdown analysis
            max_drawdown=drawdown_metrics['max_drawdown'],
            avg_drawdown=drawdown_metrics['avg_drawdown'],
            max_drawdown_duration=drawdown_metrics['max_duration'],
            
            # Trading statistics
            total_trades=len(trades),
            win_rate=win_rate,
            profit_factor=profit_factor,
            expectancy=expectancy,
            
            # Trade analysis
            best_trade=best_trade,
            worst_trade=worst_trade,
            avg_trade=avg_trade,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_losing_streak=streaks['max_losing_streak'],
            largest_winning_streak=streaks['max_winning_streak'],
            
            # Time-based analysis
            monthly_returns=monthly_returns,
            yearly_returns=yearly_returns
        )
        
        logger.info(f"Analysis complete: {win_rate:.1f}% win rate, {total_return:.2f}% total return")
        return metrics
    
    def _empty_metrics(self) -> PerformanceMetrics:
        """Return empty metrics for cases with no trades."""
        return PerformanceMetrics(
            total_return=0, cagr=0, volatility=0,
            sharpe_ratio=0, sortino_ratio=0, calmar_ratio=0,
            max_drawdown=0, avg_drawdown=0, max_drawdown_duration=0,
            total_trades=0, win_rate=0, profit_factor=0, expectancy=0,
            best_trade=0, worst_trade=0, avg_trade=0, avg_win=0, avg_loss=0,
            largest_losing_streak=0, largest_winning_streak=0,
            monthly_returns={}, yearly_returns={}
        )
    
    def _calculate_total_return(self, df: pd.DataFrame, initial_capital: float = 10000) -> float:
        """Calculate total return percentage."""
        total_pnl = df['pnl'].sum()
        return (total_pnl / initial_capital) * 100
    
    def _calculate_cagr(self, df: pd.DataFrame, total_return: float) -> float:
        """Calculate Compound Annual Growth Rate."""
        if df.empty:
            return 0
        
        start_date = pd.to_datetime(df['entry_time'].min())
        end_date = pd.to_datetime(df['exit_time'].max())
        years = (end_date - start_date).days / 365.25
        
        if years <= 0:
            return 0
        
        return (((total_return / 100 + 1) ** (1 / years)) - 1) * 100
    
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """Calculate annualized volatility of returns."""
        if len(df) < 2:
            return 0
        
        # Calculate return percentages
        df['return_pct'] = df['pnl'] / (df['size'] * df['entry_price']) * 100
        
        # Annualized volatility (assuming daily returns)
        return df['return_pct'].std() * np.sqrt(252)
    
    def _calculate_sharpe_ratio(self, df: pd.DataFrame, volatility: float) -> float:
        """Calculate Sharpe ratio."""
        if volatility == 0:
            return 0
        
        df['return_pct'] = df['pnl'] / (df['size'] * df['entry_price']) * 100
        excess_return = df['return_pct'].mean() * 252 - (self.risk_free_rate * 100)  # Annualized
        
        return excess_return / volatility
    
    def _calculate_sortino_ratio(self, df: pd.DataFrame) -> float:
        """Calculate Sortino ratio (downside deviation)."""
        df['return_pct'] = df['pnl'] / (df['size'] * df['entry_price']) * 100
        
        negative_returns = df['return_pct'][df['return_pct'] < 0]
        if len(negative_returns) == 0:
            return float('inf')
        
        downside_deviation = np.sqrt(negative_returns.var()) * np.sqrt(252)
        excess_return = df['return_pct'].mean() * 252 - (self.risk_free_rate * 100)
        
        return excess_return / downside_deviation if downside_deviation != 0 else 0
    
    def _calculate_drawdown_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate comprehensive drawdown analysis."""
        # Create equity curve
        df_sorted = df.sort_values('exit_time')
        df_sorted['cumulative_pnl'] = df_sorted['pnl'].cumsum()
        df_sorted['running_max'] = df_sorted['cumulative_pnl'].expanding().max()
        df_sorted['drawdown'] = df_sorted['cumulative_pnl'] - df_sorted['running_max']
        
        # Calculate metrics
        max_drawdown = abs(df_sorted['drawdown'].min())
        avg_drawdown = abs(df_sorted['drawdown'][df_sorted['drawdown'] < 0].mean()) if (df_sorted['drawdown'] < 0).any() else 0
        
        # Calculate maximum drawdown duration
        df_sorted['is_drawdown'] = df_sorted['drawdown'] < 0
        drawdown_periods = []
        current_period = 0
        
        for is_dd in df_sorted['is_drawdown']:
            if is_dd:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                current_period = 0
        
        if current_period > 0:
            drawdown_periods.append(current_period)
        
        max_duration = max(drawdown_periods) if drawdown_periods else 0
        
        return {
            'max_drawdown': max_drawdown,
            'avg_drawdown': avg_drawdown,
            'max_duration': max_duration
        }
    
    def _calculate_profit_factor(self, winning_trades: pd.DataFrame, losing_trades: pd.DataFrame) -> float:
        """Calculate profit factor (gross profit / gross loss)."""
        gross_profit = winning_trades['pnl'].sum() if not winning_trades.empty else 0
        gross_loss = abs(losing_trades['pnl'].sum()) if not losing_trades.empty else 0
        
        return gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
    
    def _calculate_expectancy(self, winning_trades: pd.DataFrame, losing_trades: pd.DataFrame, total_trades: int) -> float:
        """Calculate mathematical expectancy."""
        if total_trades == 0:
            return 0
        
        win_rate = len(winning_trades) / total_trades
        loss_rate = len(losing_trades) / total_trades
        
        avg_win = winning_trades['pnl'].mean() if not winning_trades.empty else 0
        avg_loss = losing_trades['pnl'].mean() if not losing_trades.empty else 0
        
        return (win_rate * avg_win) + (loss_rate * avg_loss)
    
    def _calculate_streaks(self, df: pd.DataFrame) -> Dict[str, int]:
        """Calculate winning and losing streaks."""
        df_sorted = df.sort_values('exit_time')
        df_sorted['is_winner'] = df_sorted['pnl'] > 0
        
        max_winning_streak = 0
        max_losing_streak = 0
        current_winning_streak = 0
        current_losing_streak = 0
        
        for is_winner in df_sorted['is_winner']:
            if is_winner:
                current_winning_streak += 1
                current_losing_streak = 0
                max_winning_streak = max(max_winning_streak, current_winning_streak)
            else:
                current_losing_streak += 1
                current_winning_streak = 0
                max_losing_streak = max(max_losing_streak, current_losing_streak)
        
        return {
            'max_winning_streak': max_winning_streak,
            'max_losing_streak': max_losing_streak
        }
    
    def _calculate_monthly_returns(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate monthly return breakdown."""
        df_sorted = df.sort_values('exit_time')
        df_sorted['exit_month'] = pd.to_datetime(df_sorted['exit_time']).dt.to_period('M')
        
        monthly_pnl = df_sorted.groupby('exit_month')['pnl'].sum()
        return {str(month): pnl for month, pnl in monthly_pnl.items()}
    
    def _calculate_yearly_returns(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate yearly return breakdown."""
        df_sorted = df.sort_values('exit_time')
        df_sorted['exit_year'] = pd.to_datetime(df_sorted['exit_time']).dt.year
        
        yearly_pnl = df_sorted.groupby('exit_year')['pnl'].sum()
        return {str(year): pnl for year, pnl in yearly_pnl.items()}
    
    def generate_performance_report(self, metrics: PerformanceMetrics, 
                                  strategy_name: str = "Trading Strategy") -> str:
        """
        Generate a comprehensive performance report.
        
        Args:
            metrics: PerformanceMetrics object
            strategy_name: Name of the strategy for the report
            
        Returns:
            Formatted string report
        """
        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║                    PERFORMANCE ANALYSIS REPORT               ║
║                      {strategy_name:<30}             ║
╚═══════════════════════════════════════════════════════════════╝

📊 RETURN METRICS
────────────────────────────────────────────────────────────────
Total Return:           {metrics.total_return:>10.2f}%
CAGR:                   {metrics.cagr:>10.2f}%
Volatility:             {metrics.volatility:>10.2f}%

📈 RISK-ADJUSTED METRICS  
────────────────────────────────────────────────────────────────
Sharpe Ratio:           {metrics.sharpe_ratio:>10.2f}
Sortino Ratio:          {metrics.sortino_ratio:>10.2f}
Calmar Ratio:           {metrics.calmar_ratio:>10.2f}

📉 DRAWDOWN ANALYSIS
────────────────────────────────────────────────────────────────
Maximum Drawdown:       {metrics.max_drawdown:>10.2f}
Average Drawdown:       {metrics.avg_drawdown:>10.2f}
Max DD Duration:        {metrics.max_drawdown_duration:>10} trades

🎯 TRADING STATISTICS
────────────────────────────────────────────────────────────────
Total Trades:           {metrics.total_trades:>10}
Win Rate:               {metrics.win_rate:>10.1f}%
Profit Factor:          {metrics.profit_factor:>10.2f}
Expectancy:             {metrics.expectancy:>10.2f}

💰 TRADE ANALYSIS
────────────────────────────────────────────────────────────────
Best Trade:             {metrics.best_trade:>10.2f}
Worst Trade:            {metrics.worst_trade:>10.2f}
Average Trade:          {metrics.avg_trade:>10.2f}
Average Win:            {metrics.avg_win:>10.2f}
Average Loss:           {metrics.avg_loss:>10.2f}
Max Winning Streak:     {metrics.largest_winning_streak:>10}
Max Losing Streak:      {metrics.largest_losing_streak:>10}

📅 PERFORMANCE SUMMARY
────────────────────────────────────────────────────────────────
Strategy Quality:       {self._assess_strategy_quality(metrics)}
Risk Level:             {self._assess_risk_level(metrics)}
Recommendation:         {self._generate_recommendation(metrics)}

"""
        
        # Add monthly breakdown if available
        if metrics.monthly_returns:
            report += "📅 MONTHLY RETURNS\n"
            report += "─" * 64 + "\n"
            for month, return_val in list(metrics.monthly_returns.items())[-12:]:  # Last 12 months
                report += f"{month}:                {return_val:>10.2f}\n"
            report += "\n"
        
        return report
    
    def _assess_strategy_quality(self, metrics: PerformanceMetrics) -> str:
        """Assess overall strategy quality."""
        score = 0
        
        # Sharpe ratio scoring
        if metrics.sharpe_ratio > 2.0:
            score += 3
        elif metrics.sharpe_ratio > 1.5:
            score += 2
        elif metrics.sharpe_ratio > 1.0:
            score += 1
        
        # Win rate scoring
        if metrics.win_rate > 60:
            score += 2
        elif metrics.win_rate > 50:
            score += 1
        
        # Profit factor scoring
        if metrics.profit_factor > 2.0:
            score += 2
        elif metrics.profit_factor > 1.5:
            score += 1
        
        # Max drawdown penalty
        if metrics.max_drawdown > 20:
            score -= 2
        elif metrics.max_drawdown > 10:
            score -= 1
        
        if score >= 6:
            return "EXCELLENT"
        elif score >= 4:
            return "GOOD"
        elif score >= 2:
            return "AVERAGE"
        else:
            return "POOR"
    
    def _assess_risk_level(self, metrics: PerformanceMetrics) -> str:
        """Assess risk level of the strategy."""
        if metrics.max_drawdown > 25 or metrics.volatility > 50:
            return "HIGH"
        elif metrics.max_drawdown > 15 or metrics.volatility > 30:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendation(self, metrics: PerformanceMetrics) -> str:
        """Generate trading recommendation."""
        quality = self._assess_strategy_quality(metrics)
        risk = self._assess_risk_level(metrics)
        
        if quality == "EXCELLENT" and risk == "LOW":
            return "STRONGLY RECOMMENDED"
        elif quality == "GOOD" and risk in ["LOW", "MEDIUM"]:
            return "RECOMMENDED"
        elif quality == "AVERAGE":
            return "ACCEPTABLE WITH CAUTION"
        else:
            return "NOT RECOMMENDED"
    
    def save_analysis(self, metrics: PerformanceMetrics, filepath: str) -> None:
        """Save performance analysis to JSON file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(metrics.to_dict(), f, indent=2, default=str)
            logger.info(f"Performance analysis saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Create sample trades for testing
    sample_trades = [
        {
            'symbol': 'BTC/USDT',
            'entry_time': '2024-01-01 10:00:00',
            'exit_time': '2024-01-01 14:00:00',
            'entry_price': 50000,
            'exit_price': 51000,
            'size': 0.1,
            'pnl': 100,
            'pnl_pct': 2.0,
            'hold_time': 4
        },
        {
            'symbol': 'BTC/USDT',
            'entry_time': '2024-01-02 10:00:00',
            'exit_time': '2024-01-02 16:00:00',
            'entry_price': 51000,
            'exit_price': 50500,
            'size': 0.1,
            'pnl': -50,
            'pnl_pct': -1.0,
            'hold_time': 6
        }
    ]
    
    try:
        analyzer = PerformanceAnalyzer()
        metrics = analyzer.analyze_trades(sample_trades)
        
        report = analyzer.generate_performance_report(metrics, "Test Strategy")
        print(report)
        
    except Exception as e:
        print(f"Error: {e}")
