"""
Backtesting Engine for Crypto Trading Algorithm
=====================================================

This module provides comprehensive backtesting capabilities for validating
trading strategies before live deployment.

Components:
- data_loader: Historical market data retrieval and processing
- strategy_engine: Trading strategy simulation and signal generation  
- performance_analyzer: Risk metrics and performance evaluation
- backtest_runner: Main backtesting orchestration

Security Features:
- Rate limiting for API calls
- Data validation and sanitization
- Memory-efficient data processing
- Comprehensive error handling

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

from .data_loader import DataLoader
from .strategy_engine import StrategyEngine  
from .performance_analyzer import PerformanceAnalyzer

__version__ = "1.0.0"
__all__ = ["DataLoader", "StrategyEngine", "PerformanceAnalyzer"]
