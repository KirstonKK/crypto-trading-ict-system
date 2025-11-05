#!/usr/bin/env python3
"""
1-Month Backtest: ETH & SOL with Quant Enhancements
===================================================

Simple backtest for ETHUSDT and SOLUSDT using:
- 1 month of real TradingView data (720 hourly candles)
- Enhanced strategy with all 5 quant modules

Author: GitHub Copilot
Date: October 25, 2025
"""

import sys
import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict
import json

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backtesting.strategy_engine import ICTStrategyEngine
from backtesting.performance_analyzer import PerformanceAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleMonthBacktest:
    """Simple 1-month backtest for ETH and SOL."""
    
    def __init__(self):
        self.initial_capital = 10000
        self.strategy_engine = ICTStrategyEngine()
        self.performance_analyzer = PerformanceAnalyzer()
        
        # Calculate 1 month date range
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=30)
        
        logger.info("=" * 80)
        logger.info("1-MONTH BACKTEST: ETH & SOL with Quant Enhancements")
        logger.info("=" * 80)
        logger.info(f"Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"Capital: ${self.initial_capital:,.2f}")
        logger.info("=" * 80)
    
    def fetch_tradingview_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetch 1 month of hourly data from Bybit (TradingView data source).
        FIXED: Properly limits to 720 candles (1 month).
        """
        try:
            import requests
            
            logger.info(f"\nFetching 1-month data for {symbol}...")
            
            url = "https://api.bybit.com/v5/market/kline"
            
            # Calculate timestamps for EXACTLY 1 month
            end_ts = int(self.end_date.timestamp() * 1000)
            start_ts = int(self.start_date.timestamp() * 1000)
            
            # Target: ~720 hourly candles (30 days * 24 hours)
            target_candles = 720
            
            params = {
                'category': 'linear',
                'symbol': symbol,
                'interval': '60',  # 1 hour
                'start': start_ts,
                'end': end_ts,
                'limit': 1000  # Max per request
            }
            
            logger.info(f"  Requesting candles from {self.start_date} to {self.end_date}")
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('retCode') == 0 and data.get('result', {}).get('list'):
                    candles = data['result']['list']
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(candles, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
                    ])
                    
                    # Convert types
                    df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    df.set_index('timestamp', inplace=True)
                    df.sort_index(inplace=True)
                    df = df[['open', 'high', 'low', 'close', 'volume']]
                    
                    # Filter to exact date range
                    df = df[(df.index >= self.start_date) & (df.index <= self.end_date)]
                    
                    # Limit to target candles
                    if len(df) > target_candles:
                        df = df.tail(target_candles)
                    
                    logger.info(f"  ✅ Loaded {len(df)} candles")
                    logger.info(f"  Date range: {df.index[0]} to {df.index[-1]}")
                    logger.info(f"  Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
                    
                    return df
                else:
                    logger.error("  ❌ API returned no data")
                    return pd.DataFrame()
            else:
                logger.error(f"  ❌ API error: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            return pd.DataFrame()
    
    def backtest_symbol(self, symbol: str, name: str) -> Optional[Dict]:
        """Run backtest for one symbol."""
        logger.info("\n" + "=" * 80)
        logger.info(f"BACKTESTING {name} ({symbol})")
        logger.info("=" * 80)
        
        # Fetch data
        df = self.fetch_tradingview_data(symbol)
        
        if df.empty or len(df) < 100:
            logger.error(f"❌ Insufficient data for {symbol}")
            return None
        
        # Prepare multi-timeframe data
        logger.info("Preparing multi-timeframe data...")
        mtf_data = self.strategy_engine.prepare_multitimeframe_data(df)
        
        # Generate signals
        logger.info("Generating ICT signals...")
        signals = []
        
        for timestamp in df.index[100:]:  # Skip first 100 for indicators
            signal = self.strategy_engine.generate_ict_signal(
                symbol=symbol,
                mtf_data=mtf_data,
                current_time=timestamp,
                account_balance=self.initial_capital
            )
            
            if signal:
                signals.append(signal)
        
        logger.info(f"✅ Generated {len(signals)} signals")
        
        if not signals:
            logger.warning("⚠️ No signals generated")
            return None
        
        # Backtest signals
        logger.info("Backtesting signals...")
        backtest_results = self.strategy_engine.backtest_ict_signals(
            signals=signals,
            price_data=df,
            initial_capital=self.initial_capital
        )
        
        # Analyze performance
        logger.info("Analyzing performance...")
        metrics = self.performance_analyzer.analyze_performance(backtest_results)
        
        # Print results
        logger.info("\n" + "-" * 80)
        logger.info(f"📊 {name} Results:")
        logger.info(f"  Trades: {backtest_results['total_trades']}")
        logger.info(f"  Win Rate: {metrics.win_rate:.2f}%")
        logger.info(f"  Total Return: {metrics.total_return:.2f}%")
        logger.info(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        logger.info(f"  Max Drawdown: ${metrics.max_drawdown:.2f}")
        logger.info(f"  Profit Factor: {metrics.profit_factor:.2f}")
        logger.info(f"  Avg Win: ${metrics.avg_win:.2f}")
        logger.info(f"  Avg Loss: ${metrics.avg_loss:.2f}")
        logger.info("-" * 80)
        
        return {
            'symbol': symbol,
            'name': name,
            'signals': len(signals),
            'trades': backtest_results['total_trades'],
            'metrics': metrics
        }
    
    def run(self):
        """Run backtest for both symbols."""
        results = {}
        
        # ETH
        eth_result = self.backtest_symbol('ETHUSDT', 'Ethereum')
        if eth_result:
            results['ETHUSDT'] = eth_result
        
        # SOL
        sol_result = self.backtest_symbol('SOLUSDT', 'Solana')
        if sol_result:
            results['SOLUSDT'] = sol_result
        
        # Summary
        self.print_summary(results)
        self.save_results(results)
        
        return results
    
    def print_summary(self, results: dict):
        """Print comparison summary."""
        logger.info("\n" + "=" * 80)
        logger.info("📊 1-MONTH BACKTEST SUMMARY")
        logger.info("=" * 80)
        
        print("\n" + "=" * 100)
        print(f"{'PAIR':<15} {'SIGNALS':<10} {'TRADES':<10} {'WIN RATE':<12} {'RETURN':<12} {'SHARPE':<10} {'MAX DD':<12}")
        print("=" * 100)
        
        for symbol, data in results.items():
            metrics = data['metrics']
            print(f"{data['name']:<15} {data['signals']:<10} {data['trades']:<10} "
                  f"{metrics.win_rate:>10.2f}% {metrics.total_return:>10.2f}% "
                  f"{metrics.sharpe_ratio:>9.2f} ${metrics.max_drawdown:>10.2f}")
        
        print("=" * 100)
        
        # Portfolio stats
        if len(results) > 0:
            total_trades = sum(r['trades'] for r in results.values())
            avg_win_rate = sum(r['metrics'].win_rate for r in results.values()) / len(results)
            avg_return = sum(r['metrics'].total_return for r in results.values()) / len(results)
            
            logger.info("\n📈 Portfolio Statistics:")
            logger.info(f"  Total Trades: {total_trades}")
            logger.info(f"  Average Win Rate: {avg_win_rate:.2f}%")
            logger.info(f"  Average Return: {avg_return:.2f}%")
    
    def save_results(self, results: dict):
        """Save results to JSON."""
        output_file = os.path.join(project_root, 'results', 'eth_sol_1month_backtest.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Convert to serializable format
        serializable = {}
        for symbol, data in results.items():
            metrics = data['metrics']
            serializable[symbol] = {
                'name': data['name'],
                'signals': data['signals'],
                'trades': data['trades'],
                'metrics': {
                    'win_rate': float(metrics.win_rate),
                    'total_return': float(metrics.total_return),
                    'sharpe_ratio': float(metrics.sharpe_ratio),
                    'max_drawdown': float(metrics.max_drawdown),
                    'profit_factor': float(metrics.profit_factor),
                    'avg_win': float(metrics.avg_win),
                    'avg_loss': float(metrics.avg_loss),
                    'total_trades': int(metrics.total_trades)
                }
            }
        
        with open(output_file, 'w') as f:
            json.dump(serializable, f, indent=2)
        
        logger.info(f"\n✅ Results saved to: {output_file}")


def main():
    """Main entry point."""
    try:
        backtest = SimpleMonthBacktest()
        backtest.run()
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 BACKTEST COMPLETE!")
        logger.info("=" * 80)
        
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Backtest interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
