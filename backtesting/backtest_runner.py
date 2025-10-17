"""
Comprehensive Backtesting Runner
===============================

This module orchestrates the complete backtesting process, integrating
data loading, strategy simulation, and performance analysis.

Features:
- Multi-symbol backtesting
- Parameter optimization
- Walk-forward analysis
- Out-of-sample testing
- Comprehensive reporting

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import json

from .data_loader import DataLoader
from .strategy_engine import StrategyEngine
from .performance_analyzer import PerformanceAnalyzer

logger = logging.getLogger(__name__)


class BacktestRunner:
    """
    Comprehensive backtesting orchestration system.
    
    This class coordinates data loading, strategy execution, and performance
    analysis to provide complete backtesting capabilities.
    """
    
    def __init__(self, config_path: str = "config/"):
        """Initialize backtesting components."""
        self.config_path = config_path
        
        # Initialize components
        self.data_loader = DataLoader(config_path)
        self.strategy_engine = StrategyEngine(config_path)
        self.performance_analyzer = PerformanceAnalyzer()
        
        # Results storage
        self.results_directory = "results/backtests/"
        os.makedirs(self.results_directory, exist_ok=True)
        
        logger.info("Backtesting runner initialized")
    
    def run_single_backtest(self, symbol: str, timeframe: str, start_date: str, 
                           end_date: str, save_results: bool = True) -> Dict:
        """
        Run backtest for a single symbol and timeframe.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Candlestick timeframe (e.g., '1h', '4h')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            save_results: Whether to save results to file
            
        Returns:
            Dictionary containing all backtest results
        """
        logger.info(f"Starting backtest: {symbol} {timeframe} from {start_date} to {end_date}")
        
        try:
            # Step 1: Load historical data
            logger.info("Loading historical data...")
            price_data = self.data_loader.download_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if price_data.empty:
                raise ValueError(f"No price data available for {symbol}")
            
            # Step 2: Validate data quality
            data_quality = self.data_loader.validate_data_quality(price_data, symbol)
            logger.info(f"Data quality: {data_quality['status']}")
            
            # Step 3: Generate trading signals
            logger.info("Generating trading signals...")
            signals = self.strategy_engine.simulate_strategy(symbol, price_data)
            
            if not signals:
                logger.warning(f"No signals generated for {symbol}")
                return self._empty_backtest_result(symbol, timeframe, start_date, end_date)
            
            # Step 4: Execute backtest
            logger.info("Running backtest simulation...")
            backtest_results = self.strategy_engine.backtest_signals(signals, price_data)
            
            # Step 5: Analyze performance
            logger.info("Analyzing performance...")
            if backtest_results['trades']:
                performance_metrics = self.performance_analyzer.analyze_trades(backtest_results['trades'])
            else:
                performance_metrics = self.performance_analyzer._empty_metrics()
            
            # Step 6: Compile comprehensive results
            comprehensive_results = {
                'backtest_info': {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'start_date': start_date,
                    'end_date': end_date,
                    'data_points': len(price_data),
                    'data_quality': data_quality,
                    'backtest_timestamp': datetime.now().isoformat()
                },
                'signals': {
                    'total_signals': len(signals),
                    'buy_signals': len([s for s in signals if s.action == 'BUY']),
                    'sell_signals': len([s for s in signals if s.action == 'SELL']),
                    'average_confidence': sum(s.confidence for s in signals) / len(signals) if signals else 0,
                    'signals_detail': [self._signal_to_dict(s) for s in signals[:50]]  # Limit for file size
                },
                'backtest_results': backtest_results,
                'performance_metrics': performance_metrics.to_dict(),
                'summary': {
                    'total_return': performance_metrics.total_return,
                    'cagr': performance_metrics.cagr,
                    'sharpe_ratio': performance_metrics.sharpe_ratio,
                    'max_drawdown': performance_metrics.max_drawdown,
                    'win_rate': performance_metrics.win_rate,
                    'profit_factor': performance_metrics.profit_factor,
                    'total_trades': performance_metrics.total_trades
                }
            }
            
            # Step 7: Save results if requested
            if save_results:
                filename = f"backtest_{symbol.replace('/', '_')}_{timeframe}_{start_date}_{end_date}.json"
                filepath = os.path.join(self.results_directory, filename)
                self._save_results(comprehensive_results, filepath)
                
                # Generate and save performance report
                report = self.performance_analyzer.generate_performance_report(
                    performance_metrics, f"{symbol} {timeframe} Strategy"
                )
                report_filepath = filepath.replace('.json', '_report.txt')
                with open(report_filepath, 'w') as f:
                    f.write(report)
            
            logger.info(f"Backtest completed: {performance_metrics.total_return:.2f}% return, {performance_metrics.win_rate:.1f}% win rate")
            return comprehensive_results
            
        except Exception as e:
            logger.error(f"Backtest failed for {symbol}: {e}")
            raise
    
    def run_multi_symbol_backtest(self, symbols: List[str], timeframe: str, 
                                 start_date: str, end_date: str) -> Dict[str, Dict]:
        """
        Run backtests for multiple symbols.
        
        Args:
            symbols: List of trading pair symbols
            timeframe: Candlestick timeframe
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary mapping symbol to backtest results
        """
        logger.info(f"Running multi-symbol backtest for {len(symbols)} symbols")
        
        results = {}
        
        for i, symbol in enumerate(symbols):
            try:
                logger.info(f"Processing {symbol} ({i+1}/{len(symbols)})")
                
                result = self.run_single_backtest(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date,
                    save_results=True
                )
                
                results[symbol] = result
                
            except Exception as e:
                logger.error(f"Failed to backtest {symbol}: {e}")
                results[symbol] = self._empty_backtest_result(symbol, timeframe, start_date, end_date)
                continue
        
        # Generate comparative analysis
        comparison_report = self._generate_comparison_report(results, timeframe, start_date, end_date)
        
        # Save consolidated results
        consolidated_filepath = os.path.join(
            self.results_directory, 
            f"multi_symbol_backtest_{timeframe}_{start_date}_{end_date}.json"
        )
        consolidated_results = {
            'backtest_info': {
                'symbols': symbols,
                'timeframe': timeframe,
                'start_date': start_date,
                'end_date': end_date,
                'backtest_timestamp': datetime.now().isoformat()
            },
            'individual_results': results,
            'comparison_analysis': comparison_report
        }
        
        self._save_results(consolidated_results, consolidated_filepath)
        
        logger.info(f"Multi-symbol backtest completed for {len(results)} symbols")
        return results
    
    def run_walk_forward_analysis(self, symbol: str, timeframe: str, 
                                 start_date: str, end_date: str, 
                                 window_months: int = 6, step_months: int = 1) -> Dict:
        """
        Run walk-forward analysis to test strategy robustness.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Candlestick timeframe
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            window_months: Analysis window in months
            step_months: Step size in months
            
        Returns:
            Dictionary containing walk-forward analysis results
        """
        logger.info(f"Starting walk-forward analysis for {symbol}")
        
        # Generate date windows
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        windows = []
        current_start = start_dt
        
        while current_start + pd.DateOffset(months=window_months) <= end_dt:
            window_end = current_start + pd.DateOffset(months=window_months)
            windows.append((
                current_start.strftime('%Y-%m-%d'),
                window_end.strftime('%Y-%m-%d')
            ))
            current_start += pd.DateOffset(months=step_months)
        
        logger.info(f"Running {len(windows)} walk-forward windows")
        
        # Run backtests for each window
        window_results = []
        
        for i, (window_start, window_end) in enumerate(windows):
            try:
                logger.info(f"Processing window {i+1}/{len(windows)}: {window_start} to {window_end}")
                
                result = self.run_single_backtest(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=window_start,
                    end_date=window_end,
                    save_results=False  # Save consolidated results only
                )
                
                window_results.append({
                    'window_id': i + 1,
                    'start_date': window_start,
                    'end_date': window_end,
                    'results': result
                })
                
            except Exception as e:
                logger.error(f"Failed to process window {window_start} to {window_end}: {e}")
                continue
        
        # Analyze walk-forward consistency
        consistency_analysis = self._analyze_walk_forward_consistency(window_results)
        
        # Compile results
        walk_forward_results = {
            'analysis_info': {
                'symbol': symbol,
                'timeframe': timeframe,
                'total_period': f"{start_date} to {end_date}",
                'window_months': window_months,
                'step_months': step_months,
                'total_windows': len(window_results),
                'analysis_timestamp': datetime.now().isoformat()
            },
            'window_results': window_results,
            'consistency_analysis': consistency_analysis
        }
        
        # Save results
        filepath = os.path.join(
            self.results_directory,
            f"walk_forward_{symbol.replace('/', '_')}_{timeframe}_{start_date}_{end_date}.json"
        )
        self._save_results(walk_forward_results, filepath)
        
        logger.info(f"Walk-forward analysis completed: {consistency_analysis['overall_consistency']}")
        return walk_forward_results
    
    def _signal_to_dict(self, signal) -> Dict:
        """Convert TradingSignal to dictionary."""
        return {
            'timestamp': signal.timestamp.isoformat(),
            'symbol': signal.symbol,
            'action': signal.action,
            'confidence': signal.confidence,
            'price': signal.price,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'position_size': signal.position_size,
            'market_phase': signal.market_phase,
            'indicators': signal.indicators,
            'reasoning': signal.reasoning
        }
    
    def _empty_backtest_result(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> Dict:
        """Generate empty backtest result."""
        return {
            'backtest_info': {
                'symbol': symbol,
                'timeframe': timeframe,
                'start_date': start_date,
                'end_date': end_date,
                'data_points': 0,
                'backtest_timestamp': datetime.now().isoformat()
            },
            'signals': {'total_signals': 0, 'buy_signals': 0, 'sell_signals': 0},
            'backtest_results': {'total_trades': 0, 'total_return': 0},
            'performance_metrics': {},
            'summary': {'total_return': 0, 'win_rate': 0, 'total_trades': 0}
        }
    
    def _save_results(self, results: Dict, filepath: str) -> None:
        """Save results to JSON file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save results to {filepath}: {e}")
    
    def _generate_comparison_report(self, results: Dict[str, Dict], 
                                  timeframe: str, start_date: str, end_date: str) -> Dict:
        """Generate comparative analysis report."""
        successful_results = {k: v for k, v in results.items() 
                            if v['summary']['total_trades'] > 0}
        
        if not successful_results:
            return {'status': 'No successful backtests to compare'}
        
        # Extract key metrics
        metrics = {}
        for symbol, result in successful_results.items():
            summary = result['summary']
            metrics[symbol] = {
                'total_return': summary.get('total_return', 0),
                'sharpe_ratio': summary.get('sharpe_ratio', 0),
                'max_drawdown': summary.get('max_drawdown', 0),
                'win_rate': summary.get('win_rate', 0),
                'total_trades': summary.get('total_trades', 0)
            }
        
        # Calculate rankings
        rankings = {
            'by_return': sorted(metrics.items(), key=lambda x: x[1]['total_return'], reverse=True),
            'by_sharpe': sorted(metrics.items(), key=lambda x: x[1]['sharpe_ratio'], reverse=True),
            'by_win_rate': sorted(metrics.items(), key=lambda x: x[1]['win_rate'], reverse=True),
            'by_drawdown': sorted(metrics.items(), key=lambda x: x[1]['max_drawdown'])
        }
        
        # Calculate portfolio statistics
        portfolio_stats = {
            'average_return': sum(m['total_return'] for m in metrics.values()) / len(metrics),
            'best_performer': rankings['by_return'][0][0] if rankings['by_return'] else None,
            'worst_performer': rankings['by_return'][-1][0] if rankings['by_return'] else None,
            'most_consistent': rankings['by_sharpe'][0][0] if rankings['by_sharpe'] else None,
            'total_symbols_tested': len(results),
            'successful_symbols': len(successful_results)
        }
        
        return {
            'status': 'Success',
            'portfolio_stats': portfolio_stats,
            'rankings': rankings,
            'individual_metrics': metrics
        }
    
    def _analyze_walk_forward_consistency(self, window_results: List[Dict]) -> Dict:
        """Analyze consistency across walk-forward windows."""
        if not window_results:
            return {'overall_consistency': 'No data'}
        
        returns = []
        win_rates = []
        sharpe_ratios = []
        
        for window in window_results:
            summary = window['results']['summary']
            returns.append(summary.get('total_return', 0))
            win_rates.append(summary.get('win_rate', 0))
            sharpe_ratios.append(summary.get('sharpe_ratio', 0))
        
        # Calculate consistency metrics
        return_consistency = 1 - (pd.Series(returns).std() / (abs(pd.Series(returns).mean()) + 1e-6))
        positive_windows = sum(1 for r in returns if r > 0)
        consistency_ratio = positive_windows / len(returns)
        
        # Overall assessment
        if consistency_ratio > 0.8 and return_consistency > 0.5:
            overall_consistency = 'EXCELLENT'
        elif consistency_ratio > 0.6 and return_consistency > 0.3:
            overall_consistency = 'GOOD'
        elif consistency_ratio > 0.4:
            overall_consistency = 'MODERATE'
        else:
            overall_consistency = 'POOR'
        
        return {
            'overall_consistency': overall_consistency,
            'positive_windows': positive_windows,
            'total_windows': len(returns),
            'consistency_ratio': consistency_ratio,
            'return_consistency': return_consistency,
            'average_return': pd.Series(returns).mean(),
            'return_volatility': pd.Series(returns).std(),
            'average_win_rate': pd.Series(win_rates).mean(),
            'average_sharpe': pd.Series(sharpe_ratios).mean()
        }


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Initialize backtesting runner
        runner = BacktestRunner()
        
        # Run single symbol backtest
        print("Running single symbol backtest...")
        result = runner.run_single_backtest(
            symbol="BTC/USDT",
            timeframe="1h",
            start_date="2024-01-01",
            end_date="2024-01-07"
        )
        
        print("Backtest completed: {result['summary']['total_return']:.2f}% return")
        
    except Exception as e:
        print("Error: {e}")
