"""
Secure data fetching utility for cryptocurrency market data.
Handles API connections, rate limiting, and data validation.
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# External dependencies (will be installed via requirements.txt)
try:
    import ccxt
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    # Graceful degradation for development
    ccxt = None
    requests = None
    HTTPAdapter = None
    Retry = None


class DataFetcher:
    """
    Secure data fetcher for cryptocurrency market data with rate limiting and error handling.
    """
    
    def __init__(self, exchange_name: str = 'bybit', testnet: bool = True):
        """
        Initialize DataFetcher with exchange configuration.
        
        Args:
            exchange_name: Name of the exchange ('bybit', 'binance', etc.)
            testnet: Whether to use testnet (True) or mainnet (False)
        """
        self.exchange_name = exchange_name
        self.testnet = testnet
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self._load_config()
        
        # Initialize exchange connection
        self.exchange = None
        self._init_exchange()
        
        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_per_second = 10
        
        # Session for HTTP requests with retry strategy
        self.session = self._create_session()
    
    def _load_config(self) -> None:
        """Load API configuration from environment and config files."""
        # Load from environment variables
        if self.testnet:
            self.api_key = os.getenv('BYBIT_TESTNET_API_KEY')
            self.api_secret = os.getenv('BYBIT_TESTNET_API_SECRET')
        else:
            self.api_key = os.getenv('BYBIT_API_KEY')
            self.api_secret = os.getenv('BYBIT_API_SECRET')
        
        # Load API settings
        config_path = Path(__file__).parent.parent.parent / "config" / "api_settings.json"
        try:
            with open(config_path, 'r') as f:
                self.api_config = json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load API config: {e}")
            self.api_config = {}
    
    def _create_session(self) -> Optional[Any]:
        """Create HTTP session with retry strategy."""
        if requests is None:
            return None
        
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _init_exchange(self) -> None:
        """Initialize exchange connection with security measures."""
        if ccxt is None:
            self.logger.warning("ccxt not available, some features will be limited")
            return
        
        try:
            # Exchange configuration
            config = {
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'sandbox': self.testnet,  # Use testnet
                'enableRateLimit': True,  # Enable built-in rate limiting
                'timeout': 10000,  # 10 second timeout
            }
            
            # Remove None values
            config = {k: v for k, v in config.items() if v is not None}
            
            if self.exchange_name.lower() == 'bybit':
                self.exchange = ccxt.bybit(config)
            elif self.exchange_name.lower() == 'binance':
                self.exchange = ccxt.binance(config)
            else:
                raise ValueError(f"Unsupported exchange: {self.exchange_name}")
            
            # Test connection (only if API keys are provided)
            if self.api_key and self.api_secret:
                self._test_connection()
                
        except Exception as e:
            self.logger.error(f"Failed to initialize exchange: {e}")
            self.exchange = None
    
    def _test_connection(self) -> bool:
        """Test exchange connection."""
        try:
            if self.exchange:
                # Test with a simple API call
                self.exchange.fetch_status()
                self.logger.info(f"Successfully connected to {self.exchange_name}")
                return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
        
        return False
    
    def _rate_limit_check(self) -> None:
        """Enforce rate limiting to prevent API abuse."""
        current_time = time.time()
        
        # Reset counter every second
        if current_time - self.last_request_time >= 1.0:
            self.request_count = 0
            self.last_request_time = current_time
        
        # Check rate limit
        if self.request_count >= self.rate_limit_per_second:
            sleep_time = 1.0 - (current_time - self.last_request_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.request_count = 0
                self.last_request_time = time.time()
        
        self.request_count += 1
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', 
                    limit: int = 100, since: Optional[int] = None) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data for a symbol with security and validation.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of candles to fetch (max depends on exchange)
            since: Start timestamp in milliseconds
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        if not self.exchange:
            self.logger.error("Exchange not initialized")
            return None
        
        # Input validation
        if not self._validate_symbol(symbol):
            self.logger.error(f"Invalid symbol format: {symbol}")
            return None
        
        if not self._validate_timeframe(timeframe):
            self.logger.error(f"Invalid timeframe: {timeframe}")
            return None
        
        # Rate limiting
        self._rate_limit_check()
        
        try:
            # Fetch data from exchange
            ohlcv_data = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=since,
                limit=min(limit, 1000)  # Limit to prevent excessive requests
            )
            
            if not ohlcv_data:
                self.logger.warning(f"No data returned for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv_data,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Data validation
            if not self._validate_ohlcv_data(df):
                self.logger.error(f"Data validation failed for {symbol}")
                return None
            
            self.logger.info(f"Fetched {len(df)} candles for {symbol} ({timeframe})")
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return None
    
    def fetch_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Fetch current ticker data for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Ticker dictionary or None if error
        """
        if not self.exchange:
            return None
        
        if not self._validate_symbol(symbol):
            return None
        
        self._rate_limit_check()
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            self.logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None
    
    def fetch_orderbook(self, symbol: str, limit: int = 5) -> Optional[Dict]:
        """
        Fetch order book data for a symbol.
        
        Args:
            symbol: Trading pair symbol
            limit: Depth of order book
            
        Returns:
            Order book dictionary or None if error
        """
        if not self.exchange:
            return None
        
        if not self._validate_symbol(symbol):
            return None
        
        self._rate_limit_check()
        
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit)
            return orderbook
        except Exception as e:
            self.logger.error(f"Error fetching orderbook for {symbol}: {e}")
            return None
    
    def _validate_symbol(self, symbol: str) -> bool:
        """Validate trading pair symbol."""
        if not isinstance(symbol, str) or len(symbol) < 3:
            return False
        
        # Check if symbol contains '/'
        if '/' not in symbol:
            return False
        
        parts = symbol.split('/')
        if len(parts) != 2:
            return False
        
        base, quote = parts
        if not base or not quote:
            return False
        
        return True
    
    def _validate_timeframe(self, timeframe: str) -> bool:
        """Validate timeframe format."""
        valid_timeframes = [
            '1m', '3m', '5m', '15m', '30m',
            '1h', '2h', '4h', '6h', '8h', '12h',
            '1d', '3d', '1w', '1M'
        ]
        return timeframe in valid_timeframes
    
    def _validate_ohlcv_data(self, df: pd.DataFrame) -> bool:
        """Validate OHLCV DataFrame."""
        if df.empty:
            return False
        
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            return False
        
        # Check for negative values (should not happen in OHLCV data)
        if (df[required_columns] < 0).any().any():
            return False
        
        # Check that high >= low, high >= open, high >= close
        if not ((df['high'] >= df['low']) & 
                (df['high'] >= df['open']) & 
                (df['high'] >= df['close'])).all():
            return False
        
        return True
    
    def get_exchange_info(self) -> Optional[Dict]:
        """
        Get exchange information and trading rules.
        
        Returns:
            Exchange info dictionary or None if error
        """
        if not self.exchange:
            return None
        
        try:
            return self.exchange.load_markets()
        except Exception as e:
            self.logger.error(f"Error fetching exchange info: {e}")
            return None


# Convenience functions
def fetch_crypto_data(symbol: str, timeframe: str = '1h', 
                     days: int = 30) -> Optional[pd.DataFrame]:
    """
    Convenience function to fetch crypto data.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        timeframe: Timeframe string
        days: Number of days of historical data
        
    Returns:
        DataFrame with OHLCV data or None
    """
    fetcher = DataFetcher(testnet=True)
    
    # Calculate since timestamp
    since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    
    return fetcher.fetch_ohlcv(symbol, timeframe, since=since)


def get_current_price(symbol: str) -> Optional[float]:
    """
    Get current price for a symbol.
    
    Args:
        symbol: Trading pair symbol
        
    Returns:
        Current price or None
    """
    fetcher = DataFetcher(testnet=True)
    ticker = fetcher.fetch_ticker(symbol)
    
    if ticker:
        return ticker.get('last')
    
    return None
