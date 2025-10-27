#!/usr/bin/env python3
"""
Multi-Pair Backtest with Real TradingView Data
==============================================

1-MONTH backtest for ETH and SOL:
- ETHUSDT  
- SOLUSDT

Using REAL historical data from TradingView
Tests ENHANCED strategy with all 5 quant modules

Author: GitHub Copilot
Date: October 25, 2025
"""

import sys
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List
import gc

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backtesting.strategy_engine import ICTStrategyEngine
from backtesting.performance_analyzer import PerformanceAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiPairRealDataBacktest:
    """
    Multi-pair backtest using real TradingView historical data.
    Tests all 4 pairs with enhanced quant strategy.
    """
    
    def __init__(self, start_date: str, end_date: str):
        """
        Initialize multi-pair backtest.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        """
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.initial_capital = 10000  # $10k starting capital
        
        # Trading pairs (ETH and SOL first)
        self.symbols = {
            'ETHUSDT': 'Ethereum',
            'SOLUSDT': 'Solana'
        }
        
        # Initialize engines
        self.strategy_engine = ICTStrategyEngine()
        self.performance_analyzer = PerformanceAnalyzer()
        
        logger.info(f"🚀 Multi-Pair Backtest: {start_date} to {end_date}")
        logger.info(f"💰 Initial Capital: ${self.initial_capital:,.2f}")
        logger.info(f"📊 Trading Pairs: {', '.join(self.symbols.keys())}")
    
    def fetch_tradingview_data(self, symbol: str, timeframe: str = '1h') -> pd.DataFrame:
        """
        Fetch real historical data from TradingView API.
        
        For this demo, we'll use Bybit's historical data endpoint which provides
        TradingView-compatible OHLCV data.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe: Candle timeframe ('1h', '4h', '1d')
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            import requests
            
            logger.info(f"📡 Fetching TradingView data for {symbol}...")
            
            # Use Bybit public API (TradingView data source)
            url = "https://api.bybit.com/v5/market/kline"
            
            # Convert timeframe to Bybit format
            interval_map = {'1h': '60', '4h': '240', '1d': 'D'}
            interval = interval_map.get(timeframe, '60')
            
            # Calculate timestamps
            start_ts = int(self.start_date.timestamp() * 1000)
            end_ts = int(self.end_date.timestamp() * 1000)
            
            all_candles = []
            current_start = start_ts
            
            # Fetch data in chunks (max 1000 candles per request)
            while current_start < end_ts:
                params = {
                    'category': 'linear',
                    'symbol': symbol,
                    'interval': interval,
                    'start': current_start,
                    'limit': 1000
                }
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('retCode') == 0 and data.get('result', {}).get('list'):
                        candles = data['result']['list']
                        all_candles.extend(candles)
                        
                        # Update start time for next chunk
                        last_timestamp = int(candles[-1][0])
                        current_start = last_timestamp + 1
                        
                        logger.info(f"   Fetched {len(candles)} candles (total: {len(all_candles)})")
                    else:
                        logger.warning(f"   No more data available")
                        break
                else:
                    logger.error(f"   API error: {response.status_code}")
                    break
            
            if not all_candles:
                logger.error(f"❌ No data fetched for {symbol}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(all_candles, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])
            
            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Set index and sort
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            # Filter to exact date range
            df = df[(df.index >= self.start_date) & (df.index <= self.end_date)]
            
            logger.info(f"✅ Loaded {len(df)} candles for {symbol}")
            logger.info(f"   Date range: {df.index[0]} to {df.index[-1]}")
            logger.info(f"   Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def run_pair_backtest(self, symbol: str, symbol_name: str) -> Dict:
        """
        Run backtest for a single trading pair.
        
        Args:
            symbol: Trading pair symbol
            symbol_name: Readable name
            
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 BACKTESTING {symbol_name} ({symbol})")
        logger.info(f"{'='*70}\n")
        
        # Fetch real data
        df_1h = self.fetch_tradingview_data(symbol, '1h')
        
        if df_1h.empty:
            logger.error(f"❌ No data for {symbol}, skipping")
            return None
        
        # Prepare multi-timeframe data
        mtf_data = self.strategy_engine.prepare_multitimeframe_data(df_1h)
        
        # Generate signals
        logger.info(f"🔍 Generating ICT signals for {symbol}...")
        signals = []
        
        for i, timestamp in enumerate(df_1h.index[100:]):  # Skip first 100 for indicators
            if i % 100 == 0:
                logger.info(f"   Processing candle {i}/{len(df_1h)-100}...")
            
            signal = self.strategy_engine.generate_ict_signal(
                symbol=symbol,
                mtf_data=mtf_data,
                current_time=timestamp,
                account_balance=self.initial_capital
            )
            
            if signal:
                signals.append(signal)
        
        logger.info(f"✅ Generated {len(signals)} signals for {symbol}")
        
        if not signals:
            logger.warning(f"⚠️ No signals generated for {symbol}")
            return None
        
        # Run backtest
        logger.info(f"🎯 Backtesting {len(signals)} signals...")
        backtest_results = self.strategy_engine.backtest_ict_signals(
            signals=signals,
            historical_data=df_1h,
            starting_balance=self.initial_capital
        )
        
        # Analyze performance
        logger.info(f"📈 Analyzing performance...")
        performance = self.performance_analyzer.analyze_trades(
            backtest_results['trades']
        )
        
        # Prepare results
        results = {
            'symbol': symbol,
            'name': symbol_name,
            'data_points': len(df_1h),
            'signals_generated': len(signals),
            'trades_executed': backtest_results['total_trades'],
            'metrics': performance,
            'backtest_results': backtest_results
        }
        
        # Log summary
        logger.info(f"\n📊 {symbol_name} Results:")
        logger.info(f"   Total Return: {performance.total_return:.2f}%")
        logger.info(f"   Win Rate: {performance.win_rate:.2f}%")
        logger.info(f"   Sharpe Ratio: {performance.sharpe_ratio:.2f}")
        logger.info(f"   Max Drawdown: ${performance.max_drawdown:.2f}")
        logger.info(f"   Profit Factor: {performance.profit_factor:.2f}")
        
        return results
    
    def run_full_backtest(self) -> Dict:
        """
        Run backtest for all trading pairs.
        MEMORY OPTIMIZED: Processes one pair at a time, saves checkpoint after each.
        
        Returns:
            Dictionary with all results
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 STARTING MULTI-PAIR BACKTEST WITH REAL TRADINGVIEW DATA")
        logger.info(f"🧠 MEMORY-OPTIMIZED: Processing pairs sequentially")
        logger.info(f"{'='*80}\n")
        
        all_results = {}
        checkpoint_dir = os.path.join(project_root, 'results', 'checkpoints')
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        # Load existing checkpoints
        existing_results = self.load_checkpoints(checkpoint_dir)
        if existing_results:
            logger.info(f"✅ Found {len(existing_results)} existing checkpoints")
            all_results.update(existing_results)
        
        # Run backtest for each pair
        for symbol, name in self.symbols.items():
            # Skip if already completed
            if symbol in all_results:
                logger.info(f"⏭️  Skipping {symbol} (checkpoint exists)")
                continue
            
            try:
                logger.info(f"\n💾 Memory before {symbol}: {self.get_memory_usage():.2f} MB")
                
                # Run backtest
                results = self.run_pair_backtest(symbol, name)
                
                if results:
                    all_results[symbol] = results
                    
                    # Save checkpoint immediately
                    self.save_checkpoint(checkpoint_dir, symbol, results)
                    logger.info(f"✅ Checkpoint saved for {symbol}")
                
                # Clear memory
                import gc
                gc.collect()
                
                logger.info(f"💾 Memory after {symbol}: {self.get_memory_usage():.2f} MB\n")
                
            except MemoryError:
                logger.error(f"❌ Out of memory while processing {symbol}")
                logger.info(f"💡 Progress saved. You can resume by running the script again.")
                break
            except Exception as e:
                logger.error(f"❌ Error backtesting {symbol}: {e}")
                continue
        
        # Generate comparison report
        self.generate_comparison_report(all_results)
        
        # Save final results
        self.save_results(all_results)
        
        return all_results
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def save_checkpoint(self, checkpoint_dir: str, symbol: str, results: Dict):
        """Save checkpoint for a single pair."""
        checkpoint_file = os.path.join(checkpoint_dir, f'{symbol}_checkpoint.json')
        
        metrics = results['metrics']
        checkpoint_data = {
            'symbol': symbol,
            'name': results['name'],
            'data_points': results['data_points'],
            'signals_generated': results['signals_generated'],
            'trades_executed': results['trades_executed'],
            'metrics': {
                'total_return': float(metrics.total_return),
                'win_rate': float(metrics.win_rate),
                'sharpe_ratio': float(metrics.sharpe_ratio),
                'max_drawdown': float(metrics.max_drawdown),
                'profit_factor': float(metrics.profit_factor),
                'avg_win': float(metrics.avg_win),
                'avg_loss': float(metrics.avg_loss),
                'total_trades': int(metrics.total_trades)
            }
        }
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
    
    def load_checkpoints(self, checkpoint_dir: str) -> Dict:
        """Load existing checkpoints."""
        if not os.path.exists(checkpoint_dir):
            return {}
        
        results = {}
        for filename in os.listdir(checkpoint_dir):
            if filename.endswith('_checkpoint.json'):
                checkpoint_file = os.path.join(checkpoint_dir, filename)
                try:
                    with open(checkpoint_file, 'r') as f:
                        data = json.load(f)
                        symbol = data['symbol']
                        
                        # Reconstruct results format
                        from dataclasses import dataclass
                        
                        @dataclass
                        class SimpleMetrics:
                            total_return: float
                            win_rate: float
                            sharpe_ratio: float
                            max_drawdown: float
                            profit_factor: float
                            avg_win: float
                            avg_loss: float
                            total_trades: int
                        
                        metrics = SimpleMetrics(**data['metrics'])
                        
                        results[symbol] = {
                            'symbol': symbol,
                            'name': data['name'],
                            'data_points': data['data_points'],
                            'signals_generated': data['signals_generated'],
                            'trades_executed': data['trades_executed'],
                            'metrics': metrics,
                            'backtest_results': None  # Not needed for comparison
                        }
                except Exception as e:
                    logger.warning(f"⚠️  Could not load checkpoint {filename}: {e}")
        
        return results
    
    def generate_comparison_report(self, results: Dict):
        """Generate comparison report across all pairs."""
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 MULTI-PAIR PERFORMANCE COMPARISON")
        logger.info(f"{'='*80}\n")
        
        # Create comparison table
        print("\n" + "="*120)
        print(f"{'PAIR':<15} {'TRADES':<10} {'WIN RATE':<12} {'RETURN':<12} {'SHARPE':<10} {'MAX DD':<12} {'P.FACTOR':<10}")
        print("="*120)
        
        total_trades = 0
        total_wins = 0
        
        for symbol, data in results.items():
            if not data:
                continue
            
            metrics = data['metrics']
            name = data['name']
            trades = data['trades_executed']
            
            total_trades += trades
            total_wins += int(trades * metrics.win_rate / 100)
            
            print(f"{name:<15} {trades:<10} {metrics.win_rate:>10.2f}% "
                  f"{metrics.total_return:>10.2f}% {metrics.sharpe_ratio:>9.2f} "
                  f"${metrics.max_drawdown:>10.2f} {metrics.profit_factor:>9.2f}")
        
        print("="*120)
        
        # Portfolio aggregate stats
        if total_trades > 0:
            portfolio_win_rate = (total_wins / total_trades) * 100
            
            logger.info(f"\n📈 PORTFOLIO AGGREGATE METRICS:")
            logger.info(f"   Total Trades: {total_trades}")
            logger.info(f"   Portfolio Win Rate: {portfolio_win_rate:.2f}%")
            logger.info(f"   Pairs Tested: {len(results)}")
        
        # Best performers
        logger.info(f"\n🏆 TOP PERFORMERS:")
        
        if results:
            # Best by return
            best_return = max(results.items(), key=lambda x: x[1]['metrics'].total_return if x[1] else -999)
            logger.info(f"   Highest Return: {best_return[1]['name']} ({best_return[1]['metrics'].total_return:.2f}%)")
            
            # Best by win rate
            best_wr = max(results.items(), key=lambda x: x[1]['metrics'].win_rate if x[1] else 0)
            logger.info(f"   Highest Win Rate: {best_wr[1]['name']} ({best_wr[1]['metrics'].win_rate:.2f}%)")
            
            # Best by Sharpe
            best_sharpe = max(results.items(), key=lambda x: x[1]['metrics'].sharpe_ratio if x[1] else -999)
            logger.info(f"   Best Sharpe Ratio: {best_sharpe[1]['name']} ({best_sharpe[1]['metrics'].sharpe_ratio:.2f})")
    
    def save_results(self, results: Dict):
        """Save results to JSON file."""
        output_file = os.path.join(project_root, 'results', 'multi_pair_backtest_results.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Convert to serializable format
        serializable_results = {}
        for symbol, data in results.items():
            if not data:
                continue
            
            metrics = data['metrics']
            serializable_results[symbol] = {
                'name': data['name'],
                'data_points': data['data_points'],
                'signals_generated': data['signals_generated'],
                'trades_executed': data['trades_executed'],
                'metrics': {
                    'total_return': float(metrics.total_return),
                    'win_rate': float(metrics.win_rate),
                    'sharpe_ratio': float(metrics.sharpe_ratio),
                    'max_drawdown': float(metrics.max_drawdown),
                    'profit_factor': float(metrics.profit_factor),
                    'avg_win': float(metrics.avg_win),
                    'avg_loss': float(metrics.avg_loss),
                    'total_trades': int(metrics.total_trades)
                }
            }
        
        with open(output_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"\n✅ Results saved to: {output_file}")


def main():
    """Main entry point."""
    # Set backtest period (1 MONTH)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Format dates
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    logger.info("🎯 Multi-Pair Backtest Configuration:")
    logger.info(f"   Start Date: {start_str}")
    logger.info(f"   End Date: {end_str}")
    logger.info("   Duration: 30 days (1 month)")
    logger.info("   Pairs: ETHUSDT, SOLUSDT")
    logger.info("   Data Source: TradingView via Bybit")
    
    # Run backtest
    backtest = MultiPairRealDataBacktest(start_str, end_str)
    backtest.run_full_backtest()
    
    logger.info("\n" + "="*80)
    logger.info("🎉 MULTI-PAIR BACKTEST COMPLETE!")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    main()
