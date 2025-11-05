#!/usr/bin/env python3
"""
Comprehensive 1-Year Backtest: ICT Strategy with Quant Enhancements
===================================================================

Tests ICT trading strategy with and without quantitative enhancements
to measure the impact of:
1. ATR-based dynamic stops
2. Correlation matrix & portfolio heat
3. Time-decay signal confidence
4. Expectancy filter
5. Mean reversion overlay

Author: GitHub Copilot
Date: October 25, 2025
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting.strategy_engine import ICTStrategyEngine, ICTTradingSignal
from backtesting.performance_analyzer import PerformanceAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backtest_quant_comparison.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ComparativeBacktest:
    """
    Run comparative backtest between baseline ICT strategy and 
    quant-enhanced version.
    """
    
    def __init__(self, start_date: str = "2024-01-01", end_date: str = "2024-12-31"):
        """
        Initialize backtest comparison.
        
        Args:
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
        """
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.initial_capital = 10000  # $10k starting capital
        
        logger.info(f"Initializing 1-Year Backtest: {start_date} to {end_date}")
        logger.info(f"Initial Capital: ${self.initial_capital:,.2f}")
    
    def load_historical_data(self, symbol: str = "BTCUSDT") -> pd.DataFrame:
        """
        Load historical price data for backtesting.
        
        For demonstration, we'll generate synthetic data that resembles
        real crypto price action. In production, use actual historical data.
        
        Args:
            symbol: Trading pair to backtest
            
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"Loading historical data for {symbol}...")
        
        # Generate hourly data for 1 year
        date_range = pd.date_range(
            start=self.start_date,
            end=self.end_date,
            freq='H'
        )
        
        # Generate realistic crypto price movement
        rng = np.random.default_rng(42)  # Reproducible results
        
        # Start price around $45,000 for BTC
        start_price = 45000
        prices = [start_price]
        
        # Generate random walk with crypto-like volatility
        for _ in range(len(date_range) - 1):
            # Crypto volatility: 2-5% hourly moves
            pct_change = rng.normal(0, 0.02)  # 2% std deviation
            new_price = prices[-1] * (1 + pct_change)
            prices.append(new_price)
        
        # Create OHLCV data
        df = pd.DataFrame({
            'timestamp': date_range,
            'open': prices,
            'high': [p * (1 + abs(rng.normal(0, 0.005))) for p in prices],
            'low': [p * (1 - abs(rng.normal(0, 0.005))) for p in prices],
            'close': [p * (1 + rng.normal(0, 0.003)) for p in prices],
            'volume': [rng.uniform(1e9, 5e9) for _ in prices]
        })
        
        df.set_index('timestamp', inplace=True)
        
        logger.info(f"Loaded {len(df)} hourly candles")
        logger.info(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
        
        return df
    
    def run_backtest(
        self,
        data: pd.DataFrame,
        use_quant_enhancements: bool = True
    ) -> Dict:
        """
        Run backtest with specified configuration.
        
        Args:
            data: Historical OHLCV data
            use_quant_enhancements: Whether to use quant enhancements
            
        Returns:
            Dict with backtest results
        """
        mode = "QUANT-ENHANCED" if use_quant_enhancements else "BASELINE"
        logger.info(f"\n{'='*70}")
        logger.info(f"RUNNING {mode} BACKTEST")
        logger.info(f"{'='*70}\n")
        
        # Initialize strategy engine
        engine = ICTStrategyEngine()
        engine.use_quant_enhancements = use_quant_enhancements
        
        # Re-initialize analyzers based on mode
        if use_quant_enhancements:
            from utils.volatility_indicators import VolatilityAnalyzer
            from utils.correlation_matrix import CorrelationAnalyzer
            from utils.signal_quality import SignalQualityAnalyzer
            from utils.mean_reversion import MeanReversionAnalyzer
            
            engine.volatility_analyzer = VolatilityAnalyzer()
            engine.correlation_analyzer = CorrelationAnalyzer()
            engine.signal_quality_analyzer = SignalQualityAnalyzer()
            engine.mean_reversion_analyzer = MeanReversionAnalyzer()
        else:
            engine.volatility_analyzer = None
            engine.correlation_analyzer = None
            engine.signal_quality_analyzer = None
            engine.mean_reversion_analyzer = None
        
        # Run simulation
        signals = engine.simulate_ict_strategy('BTCUSDT', data)
        
        logger.info(f"Generated {len(signals)} signals")
        
        if len(signals) == 0:
            logger.warning("No signals generated!")
            return {
                'mode': mode,
                'signals_count': 0,
                'trades_count': 0,
                'metrics': {}
            }
        
        # Backtest the signals
        backtest_results = engine.backtest_ict_signals(
            signals=signals,
            price_data=data,
            starting_balance=self.initial_capital
        )
        
        # Analyze performance
        analyzer = PerformanceAnalyzer()
        performance_metrics = analyzer.analyze_trades(backtest_results['trades'])
        
        # Convert to dict and add metadata
        performance = {
            'mode': mode,
            'use_quant_enhancements': use_quant_enhancements,
            'metrics': performance_metrics,
            'backtest_results': backtest_results
        }
        
        return performance
    
    def compare_results(
        self,
        baseline_results: Dict,
        enhanced_results: Dict
    ) -> Dict:
        """
        Compare baseline vs enhanced results.
        
        Args:
            baseline_results: Results without quant enhancements
            enhanced_results: Results with quant enhancements
            
        Returns:
            Comparison metrics
        """
        logger.info(f"\n{'='*70}")
        logger.info("COMPARISON ANALYSIS")
        logger.info(f"{'='*70}\n")
        
        # Extract key metrics (dataclass objects)
        baseline_metrics = baseline_results.get('metrics')
        enhanced_metrics = enhanced_results.get('metrics')
        
        # Calculate improvements
        improvements = {}
        
        metrics_to_compare = [
            'total_return',
            'sharpe_ratio',
            'win_rate',
            'profit_factor',
            'max_drawdown',
            'avg_win',
            'avg_loss'
        ]
        
        for metric in metrics_to_compare:
            baseline_val = getattr(baseline_metrics, metric, 0)
            enhanced_val = getattr(enhanced_metrics, metric, 0)
            
            if baseline_val != 0:
                improvement_pct = ((enhanced_val - baseline_val) / abs(baseline_val)) * 100
            else:
                improvement_pct = 0
            
            improvements[metric] = {
                'baseline': baseline_val,
                'enhanced': enhanced_val,
                'improvement_pct': improvement_pct
            }
        
        # Print comparison table
        print("\n" + "="*100)
        print(f"{'METRIC':<30} {'BASELINE':>20} {'ENHANCED':>20} {'IMPROVEMENT':>20}")
        print("="*100)
        
        for metric, values in improvements.items():
            metric_name = metric.replace('_', ' ').title()
            baseline = values['baseline']
            enhanced = values['enhanced']
            improvement = values['improvement_pct']
            
            # Format values
            if 'pct' in metric or 'rate' in metric or 'ratio' in metric:
                baseline_str = f"{baseline:.2f}%"
                enhanced_str = f"{enhanced:.2f}%"
            else:
                baseline_str = f"${baseline:.2f}"
                enhanced_str = f"${enhanced:.2f}"
            
            improvement_str = f"{improvement:+.1f}%"
            improvement_str = f"✅ {improvement_str}" if improvement > 0 else f"❌ {improvement_str}"
            
            print(f"{metric_name:<30} {baseline_str:>20} {enhanced_str:>20} {improvement_str:>20}")
        
        print("="*100 + "\n")
        
        return {
            'improvements': improvements,
            'baseline_summary': baseline_metrics,
            'enhanced_summary': enhanced_metrics
        }
    
    def save_results(self, comparison: Dict, filename: str = "backtest_comparison_results.json"):
        """Save comparison results to file."""
        output_path = os.path.join("results", filename)
        os.makedirs("results", exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(comparison, f, indent=2, default=str)
        
        logger.info(f"\n✅ Results saved to: {output_path}")
    
    def run_full_comparison(self):
        """Run complete A/B comparison backtest."""
        logger.info("\n" + "="*70)
        logger.info("🚀 STARTING 1-YEAR ICT STRATEGY BACKTEST COMPARISON")
        logger.info("="*70 + "\n")
        
        # Load data
        data = self.load_historical_data("BTCUSDT")
        
        # Run baseline backtest
        logger.info("\n📊 Phase 1: Baseline ICT Strategy (No Quant Enhancements)")
        baseline_results = self.run_backtest(data, use_quant_enhancements=False)
        
        # Run enhanced backtest
        logger.info("\n📊 Phase 2: Enhanced ICT Strategy (With Quant Enhancements)")
        enhanced_results = self.run_backtest(data, use_quant_enhancements=True)
        
        # Compare results
        comparison = self.compare_results(baseline_results, enhanced_results)
        
        # Save results
        self.save_results(comparison)
        
        # Final summary
        baseline_m = baseline_results.get('metrics')
        enhanced_m = enhanced_results.get('metrics')
        
        logger.info("\n" + "="*70)
        logger.info("🎉 BACKTEST COMPLETE!")
        logger.info("="*70)
        logger.info("\nTotal Return:")
        logger.info(f"  Baseline:  {baseline_m.total_return:.2f}%")
        logger.info(f"  Enhanced:  {enhanced_m.total_return:.2f}%")
        logger.info("\nSharpe Ratio:")
        logger.info(f"  Baseline:  {baseline_m.sharpe_ratio:.2f}")
        logger.info(f"  Enhanced:  {enhanced_m.sharpe_ratio:.2f}")
        logger.info("\nWin Rate:")
        logger.info(f"  Baseline:  {baseline_m.win_rate:.2f}%")
        logger.info(f"  Enhanced:  {enhanced_m.win_rate:.2f}%")
        logger.info("\n" + "="*70 + "\n")
        
        return comparison


def main():
    """Main entry point for backtest comparison."""
    try:
        # Create backtest instance
        backtest = ComparativeBacktest(
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        
        # Run full comparison
        _results = backtest.run_full_comparison()  # Return for potential use
        
        return 0
    
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
