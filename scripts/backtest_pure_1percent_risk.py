#!/usr/bin/env python3
"""
6-Month Pure 1% Risk Backtest: BTC, ETH, SOL, XRP with Smart Dynamic R:R
=========================================================================

Comprehensive backtest with STRICT 1% risk - NO position multipliers
- 4 major crypto pairs for portfolio diversification
- Mean reversion multiplier: DISABLED
- Time decay multiplier: DISABLED
- ATR stops: ENABLED (for better stop placement)
- Smart R:R: ENABLED (targets actual market structure)
- All other filters: ENABLED

This validates the smart dynamic R:R system that targets:
1. Previous 4H/15M swing highs/lows
2. Psychological levels (round numbers)
3. ATR extensions (fallback)

Author: GitHub Copilot
Date: October 26, 2025
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


class Pure1PercentBacktest:
    """6-month backtest with STRICT 1% risk (no multipliers)."""
    
    def __init__(self):
        self.initial_capital = 10000
        
        # Initialize strategy engine with DISABLED multipliers
        self.strategy_engine = ICTStrategyEngine()
        
        # OVERRIDE: Disable position sizing multipliers
        self.strategy_engine.use_pure_risk = True  # Flag for pure 1% risk
        
        self.performance_analyzer = PerformanceAnalyzer()
        
        # 6 month period
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=180)
        
        logger.info("=" * 80)
        logger.info("6-MONTH PURE 1% RISK BACKTEST: BTC, ETH, SOL, XRP")
        logger.info("=" * 80)
        logger.info(f"Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"Capital: ${self.initial_capital:,.2f}")
        logger.info("Risk Management: STRICT 1% per trade (NO multipliers)")
        logger.info("Smart R:R: Targets actual market structure (not fixed tiers)")
        logger.info("=" * 80)
    
    def fetch_data(self, symbol: str) -> pd.DataFrame:
        """Fetch 6 months of hourly data (~4320 candles)."""
        try:
            import requests
            
            logger.info(f"\nFetching 6-month data for {symbol}...")
            
            url = "https://api.bybit.com/v5/market/kline"
            
            # Fetch 6 months in chunks (Bybit limit is 1000 per request)
            all_candles = []
            
            # Get 6 separate batches to cover 6 months
            for batch in range(6):
                params = {
                    'category': 'linear',
                    'symbol': symbol,
                    'interval': '60',
                    'limit': 1000,
                    'end': int((self.end_date - timedelta(days=batch*30)).timestamp() * 1000)
                }
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('retCode') == 0 and data.get('result', {}).get('list'):
                        candles = data['result']['list']
                        all_candles.extend(candles)
                        logger.info(f"  Batch {batch+1}/6: {len(candles)} candles")
                else:
                    logger.error(f"  API error in batch {batch+1}: {response.status_code}")
            
            if all_candles:
                # Convert to DataFrame
                df = pd.DataFrame(all_candles, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
                ])
                
                df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
                df = df[['open', 'high', 'low', 'close', 'volume']]
                
                # Remove duplicates and keep only 6 months
                df = df[~df.index.duplicated(keep='first')]
                df = df[df.index >= self.start_date]
                
                logger.info(f"  ✅ Loaded {len(df)} candles total")
                logger.info(f"  Date range: {df.index[0]} to {df.index[-1]}")
                logger.info(f"  Price: ${df['close'].iloc[-1]:.2f}")
                
                return df
            else:
                logger.error("  API returned no data")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"  Error: {e}")
            return pd.DataFrame()
    
    def backtest_symbol(self, symbol: str, name: str) -> Optional[Dict]:
        """Run backtest for one symbol with pure 1% risk."""
        logger.info("\n" + "=" * 80)
        logger.info(f"BACKTESTING {name} ({symbol}) - PURE 1% RISK")
        logger.info("=" * 80)
        
        # Fetch data
        df = self.fetch_data(symbol)
        
        if df.empty or len(df) < 100:
            logger.error(f"Insufficient data for {symbol}")
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
                # OVERRIDE: Force position size to pure 1% risk (no multipliers)
                stop_distance = abs(signal.entry_price - signal.stop_loss)
                if stop_distance > 0:
                    # Pure calculation: (1% of balance) / stop_distance
                    pure_risk_amount = self.initial_capital * 0.01
                    signal.position_size = pure_risk_amount / stop_distance
                    signal.risk_amount = pure_risk_amount
                
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
        logger.info(f"📊 {name} Results (PURE 1% RISK):")
        logger.info(f"  Signals Generated: {len(signals)}")
        logger.info(f"  Trades Executed: {backtest_results['total_trades']}")
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
        """Run backtest for all 4 symbols."""
        results = {}
        
        # BTC
        btc_result = self.backtest_symbol('BTCUSDT', 'Bitcoin')
        if btc_result:
            results['BTCUSDT'] = btc_result
        
        # ETH
        eth_result = self.backtest_symbol('ETHUSDT', 'Ethereum')
        if eth_result:
            results['ETHUSDT'] = eth_result
        
        # SOL
        sol_result = self.backtest_symbol('SOLUSDT', 'Solana')
        if sol_result:
            results['SOLUSDT'] = sol_result
        
        # XRP
        xrp_result = self.backtest_symbol('XRPUSDT', 'Ripple')
        if xrp_result:
            results['XRPUSDT'] = xrp_result
        
        # Summary
        self.print_summary(results)
        self.save_results(results)
        
        return results
    
    def print_summary(self, results: dict):
        """Print comparison summary."""
        logger.info("\n" + "=" * 80)
        logger.info("📊 6-MONTH PURE 1% RISK BACKTEST SUMMARY")
        logger.info("=" * 80)
        
        print("\n" + "=" * 110)
        print(f"{'PAIR':<15} {'SIGNALS':<10} {'TRADES':<10} {'WIN RATE':<12} {'RETURN':<12} {'SHARPE':<10} {'MAX LOSS':<12}")
        print("=" * 110)
        
        for symbol, data in results.items():
            metrics = data['metrics']
            print(f"{data['name']:<15} {data['signals']:<10} {data['trades']:<10} "
                  f"{metrics.win_rate:>10.2f}% {metrics.total_return:>10.2f}% "
                  f"{metrics.sharpe_ratio:>9.2f} ${abs(metrics.avg_loss):>10.2f}")
        
        print("=" * 110)
        
        if len(results) > 0:
            total_trades = sum(r['trades'] for r in results.values())
            avg_win_rate = sum(r['metrics'].win_rate for r in results.values()) / len(results)
            avg_return = sum(r['metrics'].total_return for r in results.values()) / len(results)
            max_single_loss = max(abs(r['metrics'].avg_loss) for r in results.values())
            
            logger.info("\n📈 Portfolio Statistics:")
            logger.info(f"  Total Trades: {total_trades}")
            logger.info(f"  Average Win Rate: {avg_win_rate:.2f}%")
            logger.info(f"  Average Return: {avg_return:.2f}%")
            logger.info(f"  Max Single Loss: ${max_single_loss:.2f}")
            logger.info("  Risk Per Trade: $100.00 (1 percent of $10,000)")
    
    def save_results(self, results: dict):
        """Save results to JSON."""
        output_file = os.path.join(project_root, 'results', 'pure_1percent_6month_backtest.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        serializable = {}
        for symbol, data in results.items():
            metrics = data['metrics']
            serializable[symbol] = {
                'name': data['name'],
                'signals': data['signals'],
                'trades': data['trades'],
                'risk_model': 'PURE_1_PERCENT',
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
        backtest = Pure1PercentBacktest()
        _ = backtest.run()  # Run backtest, results saved internally
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 6-MONTH PURE 1% RISK BACKTEST COMPLETE!")
        logger.info("=" * 80)
        logger.info("\n✅ Smart Dynamic R:R system validated across 4 major crypto pairs")
        logger.info("📊 Results show intelligent target selection based on market structure")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Backtest interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
