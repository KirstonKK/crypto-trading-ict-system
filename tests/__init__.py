"""
Trading Algorithm Test Suite
===========================

Comprehensive testing framework for the crypto trading algorithm system.
Includes unit tests, integration tests, and backtesting scenarios.

Test Structure:
- Unit Tests: Individual component testing (utils, strategies, etc.)
- Integration Tests: API integration, notification systems, data flow
- Backtesting: Historical strategy validation and performance metrics
- Mock Tests: Simulated trading scenarios for risk-free validation

Security Testing:
- API key validation and protection
- Input sanitization and validation  
- Rate limiting compliance
- Error handling edge cases

Performance Testing:
- Memory usage profiling
- API response time validation
- Concurrent execution testing
- High-frequency data processing

Usage:
    pytest tests/                    # Run all tests
    pytest tests/unit/              # Run unit tests only
    pytest tests/integration/       # Run integration tests
    pytest tests/backtesting/       # Run backtesting scenarios
    pytest -v --tb=short           # Verbose output with short traceback
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Test configuration constants
TEST_CONFIG = {
    "API_TIMEOUT": 30,
    "MAX_RETRIES": 3,
    "TEST_SYMBOLS": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
    "TEST_TIMEFRAMES": ["1m", "5m", "15m"],
    "MOCK_TRADING_ENABLED": True,
    "USE_TESTNET": True,
    "LOG_LEVEL": "DEBUG"
}

# Mock data paths for testing
MOCK_DATA_DIR = project_root / "tests" / "mock_data"
MOCK_OHLCV_FILE = MOCK_DATA_DIR / "mock_ohlcv.json"
MOCK_BALANCE_FILE = MOCK_DATA_DIR / "mock_balance.json"

# Test utilities
def get_test_config():
    """Get standardized test configuration"""
    return TEST_CONFIG.copy()

def setup_test_environment():
    """Initialize test environment with proper paths and config"""
    # Ensure mock data directory exists
    MOCK_DATA_DIR.mkdir(exist_ok=True)
    
    # Set environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["USE_TESTNET"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    return True

# Initialize test environment on import
setup_test_environment()

__all__ = ["get_test_config", "setup_test_environment", "TEST_CONFIG"]
