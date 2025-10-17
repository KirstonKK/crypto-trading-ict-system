"""
Strategy Simulation Engine for Backtesting
==========================================

This module simulates trading strategies and generates buy/sell signals
based on technical analysis and market conditions.

Features:
- Pine Script logic simulation
- Multi-timeframe analysis
- Technical indicator calculations
- Signal generation and validation
- Risk-adjusted position sizing

Technical Indicators:
- Moving averages (SMA, EMA, WMA)
- RSI, MACD, Bollinger Bands
- Volume analysis
- Support/resistance levels
- Market phase detection

Author: GitHub Copilot Trading Algorithm  
Date: September 2025
"""

import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass
from utils.crypto_pairs import CryptoPairs
from utils.risk_management import RiskManager

logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    """Container for trading signal information."""
    timestamp: pd.Timestamp
    symbol: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0.0 to 1.0
    price: float
    stop_loss: float
    take_profit: float
    position_size: float
    market_phase: str  # 'ACCUMULATION', 'MARKUP', 'DISTRIBUTION', 'MARKDOWN'
    indicators: Dict[str, float]
    reasoning: str

@dataclass
class BacktestPosition:
    """Container for position information during backtesting."""
    symbol: str
    side: str  # 'LONG', 'SHORT'
    entry_price: float
    entry_time: pd.Timestamp
    size: float
    stop_loss: float
    take_profit: float
    current_pnl: float = 0.0
    max_pnl: float = 0.0
    min_pnl: float = 0.0


class StrategyEngine:
    """
    Trading strategy simulation engine with Pine Script compatibility.
    
    This class implements the core trading logic from your Pine Script
    indicator, providing buy/sell signals based on market phase analysis
    and technical indicators.
    """
    
    def __init__(self, config_path: str = "configs/"):
        """Initialize strategy engine with configuration."""
        self.crypto_pairs = CryptoPairs(config_path)
        self.risk_manager = RiskManager(config_path)
        
        # Strategy parameters (matching Pine Script settings)
        self.strategy_params = {
            'lookback_period': 20,
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'macd_fast': 12,
            'macd_slow': 26, 
            'macd_signal': 9,
            'bb_period': 20,
            'bb_std': 2.0,
            'volume_sma_period': 20,
            'min_confidence': 0.6,
            'max_positions': 3
        }
        
        # Market phase thresholds
        self.phase_thresholds = {
            'accumulation_volume_ratio': 1.2,
            'markup_momentum_threshold': 0.15,
            'distribution_rsi_threshold': 75,
            'markdown_momentum_threshold': -0.10
        }
        
        # Active positions tracking
        self.positions: Dict[str, BacktestPosition] = {}
        
        logger.info("Strategy engine initialized with Pine Script parameters")
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators needed for strategy.
        
        Args:
            df: OHLCV DataFrame with price data
            
        Returns:
            DataFrame with additional indicator columns
        """
        indicators = df.copy()
        
        # Moving averages
        indicators['sma_20'] = indicators['close'].rolling(window=20).mean()
        indicators['ema_20'] = indicators['close'].ewm(span=20).mean()
        indicators['sma_50'] = indicators['close'].rolling(window=50).mean()
        indicators['ema_50'] = indicators['close'].ewm(span=50).mean()
        
        # RSI calculation
        delta = indicators['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.strategy_params['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.strategy_params['rsi_period']).mean()
        rs = gain / loss
        indicators['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD calculation
        ema_fast = indicators['close'].ewm(span=self.strategy_params['macd_fast']).mean()
        ema_slow = indicators['close'].ewm(span=self.strategy_params['macd_slow']).mean()
        indicators['macd'] = ema_fast - ema_slow
        indicators['macd_signal'] = indicators['macd'].ewm(span=self.strategy_params['macd_signal']).mean()
        indicators['macd_histogram'] = indicators['macd'] - indicators['macd_signal']
        
        # Bollinger Bands
        bb_sma = indicators['close'].rolling(window=self.strategy_params['bb_period']).mean()
        bb_std = indicators['close'].rolling(window=self.strategy_params['bb_period']).std()
        indicators['bb_upper'] = bb_sma + (bb_std * self.strategy_params['bb_std'])
        indicators['bb_lower'] = bb_sma - (bb_std * self.strategy_params['bb_std'])
        indicators['bb_middle'] = bb_sma
        indicators['bb_width'] = (indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle']
        
        # Volume indicators
        indicators['volume_sma'] = indicators['volume'].rolling(window=self.strategy_params['volume_sma_period']).mean()
        indicators['volume_ratio'] = indicators['volume'] / indicators['volume_sma']
        
        # Price momentum
        indicators['momentum_5'] = indicators['close'].pct_change(5)
        indicators['momentum_10'] = indicators['close'].pct_change(10)
        indicators['momentum_20'] = indicators['close'].pct_change(20)
        
        # Volatility
        indicators['atr'] = self._calculate_atr(indicators, 14)
        indicators['price_volatility'] = indicators['close'].rolling(window=20).std() / indicators['close'].rolling(window=20).mean()
        
        logger.debug(f"Calculated {len(indicators.columns) - 6} technical indicators")
        return indicators
    
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(window=period).mean()
    
    def detect_market_phase(self, indicators: pd.DataFrame, index: int) -> str:
        """
        Detect current market phase based on Pine Script logic.
        
        Args:
            indicators: DataFrame with technical indicators
            index: Current bar index
            
        Returns:
            Market phase: 'ACCUMULATION', 'MARKUP', 'DISTRIBUTION', 'MARKDOWN'
        """
        if index < self.strategy_params['lookback_period']:
            return 'UNKNOWN'
        
        current = indicators.iloc[index]
        
        # Volume and momentum analysis
        volume_increasing = current['volume_ratio'] > self.phase_thresholds['accumulation_volume_ratio']
        momentum_positive = current['momentum_10'] > self.phase_thresholds['markup_momentum_threshold']
        momentum_negative = current['momentum_10'] < self.phase_thresholds['markdown_momentum_threshold']
        rsi_overbought = current['rsi'] > self.phase_thresholds['distribution_rsi_threshold']
        
        # Price relative to moving averages
        above_sma20 = current['close'] > current['sma_20']
        above_sma50 = current['close'] > current['sma_50']
        sma20_above_sma50 = current['sma_20'] > current['sma_50']
        
        # Market phase detection logic (matches Pine Script)
        if volume_increasing and not above_sma20 and current['rsi'] < 40:
            return 'ACCUMULATION'
        elif momentum_positive and above_sma20 and above_sma50 and sma20_above_sma50:
            return 'MARKUP'  
        elif rsi_overbought and current['bb_width'] > 0.05 and current['volume_ratio'] > 1.5:
            return 'DISTRIBUTION'
        elif momentum_negative and not above_sma20:
            return 'MARKDOWN'
        else:
            return 'TRANSITION'
    
    def generate_signal(self, symbol: str, indicators: pd.DataFrame, index: int) -> Optional[TradingSignal]:
        """
        Generate trading signal based on strategy logic.
        
        Args:
            symbol: Trading pair symbol
            indicators: DataFrame with technical indicators
            index: Current bar index
            
        Returns:
            TradingSignal object or None if no signal
        """
        if index < self.strategy_params['lookback_period']:
            return None
        
        current = indicators.iloc[index]
        market_phase = self.detect_market_phase(indicators, index)
        
        # Signal generation logic based on market phase
        signal_strength = 0.0
        action = 'HOLD'
        reasoning = []
        
        # BUY signal conditions
        buy_conditions = []
        
        # 1. Accumulation phase + oversold RSI
        if market_phase == 'ACCUMULATION' and current['rsi'] < self.strategy_params['rsi_oversold']:
            buy_conditions.append(0.3)
            reasoning.append("Accumulation phase with oversold RSI")
        
        # 2. MACD bullish crossover
        if (current['macd'] > current['macd_signal'] and 
            indicators.iloc[index-1]['macd'] <= indicators.iloc[index-1]['macd_signal']):
            buy_conditions.append(0.25)
            reasoning.append("MACD bullish crossover")
        
        # 3. Price bouncing from BB lower band
        if (current['close'] > current['bb_lower'] and 
            indicators.iloc[index-1]['close'] <= indicators.iloc[index-1]['bb_lower']):
            buy_conditions.append(0.2)
            reasoning.append("Bounce from Bollinger Band lower")
        
        # 4. Volume confirmation
        if current['volume_ratio'] > 1.2:
            buy_conditions.append(0.15)
            reasoning.append("High volume confirmation")
        
        # 5. Momentum turning positive
        if (current['momentum_5'] > 0 and indicators.iloc[index-1]['momentum_5'] <= 0):
            buy_conditions.append(0.1)
            reasoning.append("Momentum turning positive")
        
        # SELL signal conditions  
        sell_conditions = []
        
        # 1. Distribution phase + overbought RSI
        if market_phase == 'DISTRIBUTION' and current['rsi'] > self.strategy_params['rsi_overbought']:
            sell_conditions.append(0.3)
            reasoning.append("Distribution phase with overbought RSI")
        
        # 2. MACD bearish crossover
        if (current['macd'] < current['macd_signal'] and 
            indicators.iloc[index-1]['macd'] >= indicators.iloc[index-1]['macd_signal']):
            sell_conditions.append(0.25)
            reasoning.append("MACD bearish crossover")
        
        # 3. Price rejection at BB upper band
        if (current['close'] < current['bb_upper'] and 
            indicators.iloc[index-1]['close'] >= indicators.iloc[index-1]['bb_upper']):
            sell_conditions.append(0.2)
            reasoning.append("Rejection at Bollinger Band upper")
        
        # 4. Volume spike (distribution)
        if current['volume_ratio'] > 2.0 and market_phase in ['DISTRIBUTION', 'MARKDOWN']:
            sell_conditions.append(0.15)
            reasoning.append("High volume distribution")
        
        # 5. Negative momentum acceleration
        if (current['momentum_5'] < -0.02 and current['momentum_10'] < -0.05):
            sell_conditions.append(0.1)
            reasoning.append("Accelerating negative momentum")
        
        # Calculate signal strength
        buy_strength = sum(buy_conditions)
        sell_strength = sum(sell_conditions)
        
        if buy_strength > sell_strength and buy_strength >= self.strategy_params['min_confidence']:
            action = 'BUY'
            signal_strength = buy_strength
        elif sell_strength > buy_strength and sell_strength >= self.strategy_params['min_confidence']:
            action = 'SELL' 
            signal_strength = sell_strength
        
        if action == 'HOLD':
            return None
        
        # Calculate position sizing and risk levels
        try:
            # Calculate stop loss first
            stop_loss = self.risk_manager.calculate_stop_loss(
                symbol=symbol,
                entry_price=current['close'],
                side=action.lower()
            )
            
            position_size = self.risk_manager.calculate_position_size(
                symbol=symbol,
                entry_price=current['close'],
                stop_loss_price=stop_loss
            )
            
        except Exception as e:
            logger.error(f"Error calculating position size/stop loss: {e}")
            return None
        
        # Calculate take profit (2:1 risk/reward ratio)
        if action == 'BUY':
            risk_amount = current['close'] - stop_loss
            take_profit = current['close'] + (risk_amount * 2)
        else:
            risk_amount = stop_loss - current['close']
            take_profit = current['close'] - (risk_amount * 2)
        
        # Create trading signal
        signal = TradingSignal(
            timestamp=current.name,
            symbol=symbol,
            action=action,
            confidence=signal_strength,
            price=current['close'],
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            market_phase=market_phase,
            indicators={
                'rsi': current['rsi'],
                'macd': current['macd'],
                'macd_signal': current['macd_signal'],
                'bb_position': (current['close'] - current['bb_lower']) / (current['bb_upper'] - current['bb_lower']),
                'volume_ratio': current['volume_ratio'],
                'momentum_10': current['momentum_10']
            },
            reasoning="; ".join(reasoning)
        )
        
        logger.info(f"{action} signal for {symbol}: confidence={signal_strength:.2f}, phase={market_phase}")
        return signal
    
    def simulate_strategy(self, symbol: str, df: pd.DataFrame) -> List[TradingSignal]:
        """
        Run strategy simulation on historical data.
        
        Args:
            symbol: Trading pair symbol
            df: Historical OHLCV data
            
        Returns:
            List of generated trading signals
        """
        logger.info(f"Running strategy simulation for {symbol} ({len(df)} bars)")
        
        # Calculate technical indicators
        indicators = self.calculate_technical_indicators(df)
        
        # Generate signals
        signals = []
        
        for i in range(len(indicators)):
            try:
                signal = self.generate_signal(symbol, indicators, i)
                if signal:
                    signals.append(signal)
                    
            except Exception as e:
                logger.error(f"Error generating signal at index {i}: {e}")
                continue
        
        logger.info(f"Generated {len(signals)} signals for {symbol}")
        return signals
    
    def backtest_signals(self, signals: List[TradingSignal], 
                        price_data: pd.DataFrame) -> Dict[str, any]:
        """
        Backtest generated signals against historical price data.
        
        Args:
            signals: List of trading signals to backtest
            price_data: Historical price data for execution simulation
            
        Returns:
            Dictionary with backtest results and performance metrics
        """
        logger.info(f"Backtesting {len(signals)} signals")
        
        trades = []
        positions = {}
        portfolio_value = 10000  # Starting capital
        max_portfolio_value = portfolio_value
        
        for signal in signals:
            try:
                # Get current price data
                current_price_row = price_data.loc[signal.timestamp]
                current_price = current_price_row['close']
                
                if signal.action == 'BUY':
                    # Open long position
                    trade_cost = signal.position_size * current_price
                    
                    if trade_cost <= portfolio_value and len(positions) < self.strategy_params['max_positions']:
                        positions[signal.symbol] = BacktestPosition(
                            symbol=signal.symbol,
                            side='LONG',
                            entry_price=current_price,
                            entry_time=signal.timestamp,
                            size=signal.position_size,
                            stop_loss=signal.stop_loss,
                            take_profit=signal.take_profit
                        )
                        
                        portfolio_value -= trade_cost
                        logger.debug(f"Opened LONG {signal.symbol} at {current_price}")
                
                elif signal.action == 'SELL' and signal.symbol in positions:
                    # Close position
                    position = positions[signal.symbol]
                    
                    if position.side == 'LONG':
                        trade_value = position.size * current_price
                        pnl = trade_value - (position.size * position.entry_price)
                        
                        portfolio_value += trade_value
                        max_portfolio_value = max(max_portfolio_value, portfolio_value)
                        
                        trades.append({
                            'symbol': signal.symbol,
                            'entry_time': position.entry_time,
                            'exit_time': signal.timestamp,
                            'entry_price': position.entry_price,
                            'exit_price': current_price,
                            'size': position.size,
                            'pnl': pnl,
                            'pnl_pct': (pnl / (position.size * position.entry_price)) * 100,
                            'hold_time': (signal.timestamp - position.entry_time).total_seconds() / 3600  # hours
                        })
                        
                        del positions[signal.symbol]
                        logger.debug(f"Closed LONG {signal.symbol} at {current_price}, PnL: ${pnl:.2f}")
                
            except Exception as e:
                logger.error(f"Error processing signal {signal.timestamp}: {e}")
                continue
        
        # Calculate performance metrics
        if trades:
            trade_df = pd.DataFrame(trades)
            winning_trades = trade_df[trade_df['pnl'] > 0]
            losing_trades = trade_df[trade_df['pnl'] < 0]
            
            results = {
                'total_trades': len(trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': len(winning_trades) / len(trades) * 100,
                'total_pnl': trade_df['pnl'].sum(),
                'average_win': winning_trades['pnl'].mean() if not winning_trades.empty else 0,
                'average_loss': losing_trades['pnl'].mean() if not losing_trades.empty else 0,
                'profit_factor': abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if not losing_trades.empty and losing_trades['pnl'].sum() != 0 else float('inf'),
                'max_drawdown': (max_portfolio_value - min(portfolio_value, 0)) / max_portfolio_value * 100,
                'final_portfolio_value': portfolio_value,
                'total_return': ((portfolio_value - 10000) / 10000) * 100,
                'average_hold_time': trade_df['hold_time'].mean(),
                'trades': trades
            }
        else:
            results = {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_return': 0,
                'trades': []
            }
        
        logger.info(f"Backtest complete: {results['total_trades']} trades, {results['win_rate']:.1f}% win rate, {results['total_return']:.2f}% return")
        return results


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Initialize strategy engine
        engine = StrategyEngine()
        
        # Create sample data for testing
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='1H')
        sample_data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.randn(len(dates)).cumsum() + 50000,
            'high': np.random.randn(len(dates)).cumsum() + 50100,
            'low': np.random.randn(len(dates)).cumsum() + 49900,
            'close': np.random.randn(len(dates)).cumsum() + 50000,
            'volume': np.random.default_rng(42).integers(100, 1000, len(dates))
        })
        sample_data.set_index('timestamp', inplace=True)
        
        # Test signal generation
        signals = engine.simulate_strategy("BTC/USDT", sample_data)
        print("Generated {len(signals)} signals")
        
        # Test backtesting
        if signals:
            results = engine.backtest_signals(signals, sample_data)
            print("Backtest results: {results['win_rate']:.1f}% win rate")
        
    except Exception as e:
        print("Error: {e}")
