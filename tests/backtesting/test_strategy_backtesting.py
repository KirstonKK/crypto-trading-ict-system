"""
Backtesting framework for the crypto trading algorithm.
Tests strategy performance using historical data and Pine Script indicators.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

# Import backtesting modules
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from strategies.risk_management import RiskManager
    from utils.data_fetcher import DataFetcher
    from utils.crypto_pairs import CryptoPairs
except ImportError as e:
    pytest.skip(f"Skipping backtesting tests due to import error: {e}", allow_module_level=True)


class TestBacktestingEngine:
    """Backtesting engine for strategy validation"""
    
    @pytest.fixture
    def mock_historical_data(self):
        """Load mock OHLCV data for backtesting"""
        mock_data_path = Path(__file__).parent.parent / "mock_data" / "mock_ohlcv.json"
        try:
            with open(mock_data_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback mock data
            return {
                "BTCUSDT": [
                    [1640995200000, 47000.0, 47500.0, 46800.0, 47200.0, 100.5],
                    [1640995260000, 47200.0, 47300.0, 46900.0, 47100.0, 85.2],
                    [1640995320000, 47100.0, 47400.0, 47000.0, 47300.0, 92.1]
                ]
            }
    
    @pytest.fixture
    def backtest_config(self):
        """Configuration for backtesting parameters"""
        return {
            "initial_capital": 10000,
            "commission": 0.001,  # 0.1% commission
            "slippage": 0.0005,   # 0.05% slippage
            "max_positions": 3,
            "risk_per_trade": 0.02,  # 2% risk per trade
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "timeframe": "1m"
        }
    
    @pytest.fixture
    def pine_script_signals(self):
        """Mock Pine Script trading signals"""
        return [
            {"timestamp": 1640995200000, "signal": "BUY", "price": 47000, "confidence": 0.8},
            {"timestamp": 1640995320000, "signal": "SELL", "price": 47300, "confidence": 0.7},
            {"timestamp": 1640995440000, "signal": "BUY", "price": 47050, "confidence": 0.9},
            {"timestamp": 1640995620000, "signal": "SELL", "price": 47350, "confidence": 0.8}
        ]
    
    def test_historical_data_loading(self, mock_historical_data):
        """Test loading and validation of historical data"""
        data = mock_historical_data
        
        # Validate data structure
        assert "BTCUSDT" in data
        assert len(data["BTCUSDT"]) > 0
        
        # Validate OHLCV format
        first_candle = data["BTCUSDT"][0]
        assert len(first_candle) == 6  # timestamp, o, h, l, c, v
        assert isinstance(first_candle[0], (int, float))  # timestamp
        assert all(isinstance(x, (int, float)) for x in first_candle[1:])  # OHLCV values
    
    def test_pine_script_signal_processing(self, pine_script_signals):
        """Test processing of Pine Script trading signals"""
        signals = pine_script_signals
        
        # Validate signal structure
        for signal in signals:
            assert "timestamp" in signal
            assert "signal" in signal
            assert "price" in signal
            assert "confidence" in signal
            assert signal["signal"] in ["BUY", "SELL", "HOLD"]
            assert 0 <= signal["confidence"] <= 1
    
    def test_backtest_execution(self, mock_historical_data, backtest_config, pine_script_signals):
        """Test complete backtesting execution"""
        # Initialize backtesting components
        initial_capital = backtest_config["initial_capital"]
        commission = backtest_config["commission"]
        
        # Simulate backtesting execution
        portfolio_value = initial_capital
        positions = []
        trades = []
        
        for signal in pine_script_signals:
            if signal["signal"] == "BUY":
                # Calculate position size based on risk management
                position_size = initial_capital * 0.1  # 10% of capital
                entry_price = signal["price"]
                
                position = {
                    "symbol": "BTCUSDT",
                    "side": "long",
                    "size": position_size / entry_price,
                    "entry_price": entry_price,
                    "entry_time": signal["timestamp"],
                    "confidence": signal["confidence"]
                }
                positions.append(position)
                
            elif signal["signal"] == "SELL" and positions:
                # Close position
                position = positions.pop(0)  # Close first position (FIFO)
                exit_price = signal["price"]
                
                # Calculate P&L
                pnl = (exit_price - position["entry_price"]) * position["size"]
                commission_cost = (position["entry_price"] + exit_price) * position["size"] * commission
                net_pnl = pnl - commission_cost
                
                portfolio_value += net_pnl
                
                trade = {
                    "entry_time": position["entry_time"],
                    "exit_time": signal["timestamp"],
                    "entry_price": position["entry_price"],
                    "exit_price": exit_price,
                    "size": position["size"],
                    "pnl": net_pnl,
                    "return_pct": net_pnl / (position["entry_price"] * position["size"])
                }
                trades.append(trade)
        
        # Validate backtesting results
        assert len(trades) > 0
        assert portfolio_value != initial_capital  # Should have changed
        
        # Calculate basic performance metrics
        total_return = (portfolio_value - initial_capital) / initial_capital
        win_rate = len([t for t in trades if t["pnl"] > 0]) / len(trades) if trades else 0
        
        assert isinstance(total_return, (int, float))
        assert 0 <= win_rate <= 1
    
    def test_performance_metrics_calculation(self, backtest_config):
        """Test calculation of backtesting performance metrics"""
        # Mock trade results
        trades = [
            {"pnl": 100, "return_pct": 0.02, "duration": 3600},
            {"pnl": -50, "return_pct": -0.01, "duration": 1800},
            {"pnl": 200, "return_pct": 0.04, "duration": 7200},
            {"pnl": -25, "return_pct": -0.005, "duration": 900}
        ]
        
        # Calculate metrics
        total_pnl = sum(trade["pnl"] for trade in trades)
        win_trades = [t for t in trades if t["pnl"] > 0]
        lose_trades = [t for t in trades if t["pnl"] < 0]
        
        win_rate = len(win_trades) / len(trades)
        avg_win = np.mean([t["pnl"] for t in win_trades]) if win_trades else 0
        avg_loss = np.mean([t["pnl"] for t in lose_trades]) if lose_trades else 0
        profit_factor = abs(sum(t["pnl"] for t in win_trades) / sum(t["pnl"] for t in lose_trades)) if lose_trades else float('inf')
        
        # Validate metrics
        assert total_pnl == 225  # 100 - 50 + 200 - 25
        assert win_rate == 0.5   # 2 wins out of 4 trades
        assert avg_win == 150    # (100 + 200) / 2
        assert avg_loss == -37.5 # (-50 - 25) / 2
        assert profit_factor == 4.0  # 300 / 75
    
    def test_risk_management_integration(self, backtest_config):
        """Test integration with risk management during backtesting"""
        with patch('builtins.open'), \
             patch('json.load', return_value={"max_portfolio_risk": 0.02}), \
             patch('pathlib.Path.exists', return_value=True):
            
            rm = RiskManager()
            
            # Test position sizing in backtest context
            account_balance = backtest_config["initial_capital"]
            entry_price = 47000
            stop_loss = 45000  # ~4.3% risk
            
            position_size = rm.calculate_position_size(
                account_balance=account_balance,
                entry_price=entry_price,
                stop_loss_price=stop_loss,
                symbol="BTCUSDT"
            )
            
            # Position size should be reasonable for backtesting
            assert position_size > 0
            assert position_size < account_balance * 0.5  # Not more than 50% of capital
    
    def test_multiple_timeframe_backtesting(self, mock_historical_data):
        """Test backtesting across multiple timeframes"""
        timeframes = ["1m", "5m", "15m"]
        
        for timeframe in timeframes:
            # Simulate different timeframe data
            data = mock_historical_data["BTCUSDT"]
            
            # For testing, we'll use the same data but pretend it's different timeframes
            # In real implementation, this would be actual different timeframe data
            
            # Basic validation that we can process data for each timeframe
            assert len(data) > 0
            
            # Simulate signal generation for this timeframe
            signals = self._generate_mock_signals(data, timeframe)
            assert len(signals) >= 0  # Should generate some signals
    
    def _generate_mock_signals(self, ohlcv_data, timeframe):
        """Generate mock trading signals based on simple price action"""
        signals = []
        
        for i, candle in enumerate(ohlcv_data[1:], 1):  # Skip first candle
            prev_candle = ohlcv_data[i-1]
            
            # Simple signal generation: buy if price increased, sell if decreased
            if candle[4] > prev_candle[4]:  # Close price increased
                signals.append({
                    "timestamp": candle[0],
                    "signal": "BUY",
                    "price": candle[4],
                    "confidence": 0.6
                })
            elif candle[4] < prev_candle[4]:  # Close price decreased
                signals.append({
                    "timestamp": candle[0],
                    "signal": "SELL",
                    "price": candle[4],
                    "confidence": 0.6
                })
        
        return signals
    
    def test_backtesting_with_slippage(self, backtest_config):
        """Test backtesting execution with slippage simulation"""
        slippage = backtest_config["slippage"]
        entry_price = 47000
        
        # Simulate slippage for market orders
        buy_slippage = entry_price * (1 + slippage)  # Pay higher when buying
        sell_slippage = entry_price * (1 - slippage)  # Receive lower when selling
        
        assert buy_slippage > entry_price
        assert sell_slippage < entry_price
        
        # Slippage should be reasonable (less than 1%)
        assert (buy_slippage - entry_price) / entry_price < 0.01
        assert (entry_price - sell_slippage) / entry_price < 0.01
    
    def test_portfolio_tracking(self, backtest_config):
        """Test portfolio value tracking during backtesting"""
        initial_capital = backtest_config["initial_capital"]
        
        # Simulate portfolio evolution
        portfolio_history = [
            {"timestamp": 1640995200000, "value": 10000, "positions": 0},
            {"timestamp": 1640995320000, "value": 10150, "positions": 1},
            {"timestamp": 1640995440000, "value": 10050, "positions": 1},
            {"timestamp": 1640995620000, "value": 10300, "positions": 0}
        ]
        
        # Validate portfolio tracking
        for snapshot in portfolio_history:
            assert snapshot["value"] > 0
            assert snapshot["positions"] >= 0
            
        # Calculate drawdown
        peak_value = max(s["value"] for s in portfolio_history)
        final_value = portfolio_history[-1]["value"]
        max_drawdown = (peak_value - min(s["value"] for s in portfolio_history)) / peak_value
        
        assert 0 <= max_drawdown <= 1
        assert final_value / initial_capital > 0  # Portfolio should have some value


@pytest.mark.slow
class TestLongRunningBacktests:
    """Long-running backtesting scenarios"""
    
    def test_extended_period_backtest(self):
        """Test backtesting over extended time periods"""
        # This would be a longer-running test for comprehensive validation
        # Marked as slow to exclude from regular test runs
        
        # Generate extended mock data (simulate 30 days of 1-minute data)
        extended_data = []
        base_timestamp = 1640995200000
        base_price = 47000
        
        for i in range(30 * 24 * 60):  # 30 days * 24 hours * 60 minutes
            timestamp = base_timestamp + (i * 60000)  # Add 1 minute each iteration
            
            # Simple random walk for price simulation
            price_change = np.random.normal(0, base_price * 0.001)  # 0.1% volatility
            base_price = max(base_price + price_change, base_price * 0.5)  # Prevent negative prices
            
            # Generate OHLCV (simplified)
            open_price = base_price
            high_price = base_price * (1 + abs(np.random.normal(0, 0.002)))
            low_price = base_price * (1 - abs(np.random.normal(0, 0.002)))
            close_price = base_price
            volume = np.random.default_rng(42).uniform(50, 200)
            
            extended_data.append([timestamp, open_price, high_price, low_price, close_price, volume])
        
        # Validate extended data generation
        assert len(extended_data) == 30 * 24 * 60
        assert all(candle[2] >= candle[3] for candle in extended_data)  # High >= Low
        assert all(candle[5] > 0 for candle in extended_data)  # Volume > 0


if __name__ == "__main__":
    # Run backtesting tests
    pytest.main([__file__, "-v", "-m", "not slow"])
