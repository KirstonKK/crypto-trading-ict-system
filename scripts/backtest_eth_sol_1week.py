#!/usr/bin/env python3
"""
1-Week Quick Backtest: ETH & SOL with Quant Enhancements
========================================================

Quick backtest for ETHUSDT and SOLUSDT using:
- 1 WEEK of data (~168 hourly candles)
- Enhanced strategy with all 5 quant modules

Author: GitHub Copilot
Date: October 25, 2025
"""

import sys
import os
import logging
import pandas as pd
from datetime import datetime, timedelta
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


class QuickWeekBacktest:
    """Quick 3-week backtest for ETH and SOL."""
    
    def __init__(self):
        self.initial_capital = 10000
        self.strategy_engine = ICTStrategyEngine()
        self.performance_analyzer = PerformanceAnalyzer()
        
        # 3 weeks for better sample size
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=21)
        
        logger.info("=" * 80)
        logger.info("3-WEEK BACKTEST: ETH & SOL with Quant Enhancements")
        logger.info("=" * 80)
        logger.info(f"Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"Capital: ${self.initial_capital:,.2f}")
        logger.info("Target: ~500 hourly candles per pair")
        logger.info("=" * 80)
    
    def fetch_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetch 3 weeks of hourly data (~504 candles).
        """
        try:
            import requests
            
            logger.info(f"\nFetching 3-week data for {symbol}...")
            
            url = "https://api.bybit.com/v5/market/kline"
            
            # Get last 600 candles (covers 3 weeks + buffer)
            params = {
                'category': 'linear',
                'symbol': symbol,
                'interval': '60',
                'limit': 600  # 600 candles for 3 weeks
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('retCode') == 0 and data.get('result', {}).get('list'):
                    candles = data['result']['list']
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(candles, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
                    ])
                    
                    df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    df.set_index('timestamp', inplace=True)
                    df.sort_index(inplace=True)
                    df = df[['open', 'high', 'low', 'close', 'volume']]
                    
                    logger.info(f"  ✅ Loaded {len(df)} candles")
                    logger.info(f"  Date range: {df.index[0]} to {df.index[-1]}")
                    logger.info(f"  Price: ${df['close'].iloc[-1]:.2f}")
                    
                    return df
                else:
                    logger.error("  API returned no data")
                    return pd.DataFrame()
            else:
                logger.error(f"  API error: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"  Error: {e}")
            return pd.DataFrame()
    
    def backtest_symbol(self, symbol: str, name: str) -> dict:
        """Run backtest for one symbol."""
        logger.info("\n" + "=" * 80)
        logger.info(f"BACKTESTING {name} ({symbol})")
        logger.info("=" * 80)
        
        # Fetch data
        df = self.fetch_data(symbol)
        
        if df.empty or len(df) < 50:
            logger.error(f"Insufficient data for {symbol}")
            return None
        
        # Prepare multi-timeframe data
        logger.info("Preparing multi-timeframe data...")
        mtf_data = self.strategy_engine.prepare_multitimeframe_data(df)
        
        # Generate signals
        logger.info("Generating ICT signals...")
        signals = []
        
        for timestamp in df.index[50:]:  # Skip first 50 for indicators
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
            logger.warning("No signals generated")
            return None
        
        # Run backtest
        logger.info("Backtesting signals...")
        backtest_results = self.strategy_engine.backtest_ict_signals(
            signals=signals,
            price_data=df,
            starting_balance=self.initial_capital
        )
        
        # Analyze performance
        logger.info("Analyzing performance...")
        metrics = self.performance_analyzer.analyze_trades(
            backtest_results['trades']
        )
        
        # Print results
        logger.info("\n" + "-" * 80)
        logger.info(f"📊 {name} Results:")
        logger.info(f"  Signals Generated: {len(signals)}")
        logger.info(f"  Trades Executed: {backtest_results['total_trades']}")
        logger.info(f"  Win Rate: {metrics.win_rate:.2f}%")
        logger.info(f"  Total Return: {metrics.total_return:.2f}%")
        logger.info(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        logger.info(f"  Max Drawdown: ${metrics.max_drawdown:.2f}")
        logger.info(f"  Profit Factor: {metrics.profit_factor:.2f}")
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
        logger.info("📊 3-WEEK BACKTEST SUMMARY")
        logger.info("=" * 80)
        
        print("\n" + "=" * 100)
        print(f"{'PAIR':<15} {'SIGNALS':<10} {'TRADES':<10} {'WIN RATE':<12} {'RETURN':<12} {'SHARPE':<10}")
        print("=" * 100)
        
        for symbol, data in results.items():
            metrics = data['metrics']
            print(f"{data['name']:<15} {data['signals']:<10} {data['trades']:<10} "
                  f"{metrics.win_rate:>10.2f}% {metrics.total_return:>10.2f}% "
                  f"{metrics.sharpe_ratio:>9.2f}")
        
        print("=" * 100)
        
        if len(results) > 0:
            total_trades = sum(r['trades'] for r in results.values())
            avg_win_rate = sum(r['metrics'].win_rate for r in results.values()) / len(results)
            avg_return = sum(r['metrics'].total_return for r in results.values()) / len(results)
            
            logger.info(f"\n📈 Portfolio Statistics:")
            logger.info(f"  Total Trades: {total_trades}")
            logger.info(f"  Average Win Rate: {avg_win_rate:.2f}%")
            logger.info(f"  Average Return: {avg_return:.2f}%")
    
    def save_results(self, results: dict):
        """Save results to JSON."""
        output_file = os.path.join(project_root, 'results', 'eth_sol_3week_backtest.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
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
                    'avg_loss': float(metrics.avg_loss)
                }
            }
        
        with open(output_file, 'w') as f:
            json.dump(serializable, f, indent=2)
        
        logger.info(f"\n✅ Results saved to: {output_file}")


def main():
    """Main entry point."""
    try:
        backtest = QuickWeekBacktest()
        backtest.run()
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 BACKTEST COMPLETE!")
        logger.info("=" * 80)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Backtest interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
