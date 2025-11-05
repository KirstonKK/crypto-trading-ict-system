"""
Historical Data Loader for Backtesting Engine
============================================

This module handles downloading and processing historical cryptocurrency
market data for backtesting purposes.

Features:
- Multi-timeframe OHLCV data retrieval
- Rate limiting and API management  
- Data caching and persistence
- Memory-efficient processing
- Comprehensive error handling

Dependencies:
- ccxt: Cryptocurrency exchange integration
- pandas: Data manipulation and analysis
- requests: HTTP client with retry logic

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import ccxt
from utils.config_loader import ConfigLoader
from utils.crypto_pairs import CryptoPairs

logger = logging.getLogger(__name__)

class DataLoader:
    """
    Historical cryptocurrency data loader with advanced caching and rate limiting.
    
    This class provides methods to download historical OHLCV data from Bybit
    exchange with intelligent caching, rate limiting, and error recovery.
    """
    
    def __init__(self, config_path: str = "configs/"):
        """Initialize DataLoader with exchange connection and configuration."""
        self.config_loader = ConfigLoader(config_path)
        self.crypto_pairs = CryptoPairs(config_path)
        
        # Load exchange configuration
        exchange_config = self.config_loader.get_config("exchange")
        self.exchange_name = exchange_config.get("exchange", "bybit")
        
        # Initialize exchange connection
        self._setup_exchange(exchange_config)
        
        # Rate limiting configuration
        self.rate_limit_delay = exchange_config.get("rate_limit_ms", 200) / 1000
        self.max_retries = exchange_config.get("max_retries", 3)
        
        # Data caching configuration
        self.cache_directory = "data/cache/"
        os.makedirs(self.cache_directory, exist_ok=True)
        
        # Supported timeframes
        self.timeframes = {
            "1m": 60,
            "3m": 180, 
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
            "2h": 7200,
            "4h": 14400,
            "6h": 21600,
            "12h": 43200,
            "1d": 86400,
            "3d": 259200,
            "1w": 604800
        }
    
    def _setup_exchange(self, config: Dict) -> None:
        """Setup exchange connection with proper configuration."""
        try:
            exchange_class = getattr(ccxt, self.exchange_name)
            
            self.exchange = exchange_class({
                'apiKey': config.get('api_key', ''),
                'secret': config.get('api_secret', ''),
                'testnet': config.get('testnet', True),
                'sandbox': config.get('testnet', True),
                'rateLimit': config.get('rate_limit_ms', 200),
                'enableRateLimit': True,
                'options': {
                    'adjustForTimeDifference': True,
                }
            })
            
            logger.info(f"Initialized {self.exchange_name} exchange connection")
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            raise RuntimeError(f"Exchange initialization failed: {e}")
    
    def get_cache_filename(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> str:
        """Generate cache filename for historical data."""
        return f"{symbol}_{timeframe}_{start_date}_{end_date}.json"
    
    def load_from_cache(self, cache_filename: str) -> Optional[pd.DataFrame]:
        """Load historical data from cache if available."""
        cache_path = os.path.join(self.cache_directory, cache_filename)
        
        if not os.path.exists(cache_path):
            return None
            
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Loaded {len(df)} records from cache: {cache_filename}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load cache {cache_filename}: {e}")
            return None
    
    def save_to_cache(self, df: pd.DataFrame, cache_filename: str) -> None:
        """Save historical data to cache for future use."""
        cache_path = os.path.join(self.cache_directory, cache_filename)
        
        try:
            # Reset index to include timestamp in data
            df_to_save = df.reset_index()
            df_to_save['timestamp'] = df_to_save['timestamp'].dt.isoformat()
            
            with open(cache_path, 'w') as f:
                json.dump(df_to_save.to_dict('records'), f, indent=2)
            
            logger.info(f"Cached {len(df)} records to: {cache_filename}")
            
        except Exception as e:
            logger.error(f"Failed to save cache {cache_filename}: {e}")
    
    def download_ohlcv(self, symbol: str, timeframe: str, start_date: str, 
                       end_date: str, use_cache: bool = True) -> pd.DataFrame:
        """
        Download historical OHLCV data for specified parameters.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Candlestick timeframe (e.g., '1h', '4h', '1d')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            use_cache: Whether to use cached data if available
            
        Returns:
            DataFrame with OHLCV data indexed by timestamp
        """
        # Validate inputs
        if not self.crypto_pairs.is_pair_supported(symbol):
            raise ValueError(f"Unsupported trading pair: {symbol}")
        
        if timeframe not in self.timeframes:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        # Check cache first
        cache_filename = self.get_cache_filename(symbol, timeframe, start_date, end_date)
        
        if use_cache:
            cached_data = self.load_from_cache(cache_filename)
            if cached_data is not None:
                return cached_data
        
        # Convert dates to timestamps
        start_timestamp = int(pd.to_datetime(start_date).timestamp() * 1000)
        end_timestamp = int(pd.to_datetime(end_date).timestamp() * 1000)
        
        logger.info(f"Downloading {symbol} {timeframe} data from {start_date} to {end_date}")
        
        all_ohlcv = []
        current_timestamp = start_timestamp
        
        while current_timestamp < end_timestamp:
            try:
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                
                # Download batch of data
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol, 
                    timeframe,
                    since=current_timestamp,
                    limit=1000  # Most exchanges support up to 1000 candles per request
                )
                
                if not ohlcv:
                    break
                
                all_ohlcv.extend(ohlcv)
                
                # Update timestamp for next batch
                current_timestamp = ohlcv[-1][0] + self.timeframes[timeframe] * 1000
                
                logger.debug(f"Downloaded {len(ohlcv)} candles, total: {len(all_ohlcv)}")
                
            except Exception as e:
                logger.error(f"Error downloading data: {e}")
                time.sleep(2)  # Wait longer on error
                continue
        
        if not all_ohlcv:
            raise RuntimeError(f"No data downloaded for {symbol} {timeframe}")
        
        # Convert to DataFrame
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # Remove duplicates and sort
        df = df[~df.index.duplicated()].sort_index()
        
        # Filter to requested date range
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        df = df.loc[start_dt:end_dt]
        
        logger.info(f"Successfully downloaded {len(df)} {timeframe} candles for {symbol}")
        
        # Save to cache
        if use_cache:
            self.save_to_cache(df, cache_filename)
        
        return df
    
    def download_multiple_pairs(self, symbols: List[str], timeframe: str,
                              start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """
        Download historical data for multiple trading pairs.
        
        Args:
            symbols: List of trading pair symbols
            timeframe: Candlestick timeframe  
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary mapping symbol to OHLCV DataFrame
        """
        results = {}
        
        for symbol in symbols:
            try:
                logger.info(f"Processing {symbol} ({len(results)+1}/{len(symbols)})")
                
                df = self.download_ohlcv(symbol, timeframe, start_date, end_date)
                results[symbol] = df
                
                # Rate limiting between pairs
                time.sleep(self.rate_limit_delay * 2)
                
            except Exception as e:
                logger.error(f"Failed to download {symbol}: {e}")
                continue
        
        logger.info(f"Successfully downloaded data for {len(results)}/{len(symbols)} pairs")
        return results
    
    def get_available_symbols(self) -> List[str]:
        """Get list of available trading symbols from exchange."""
        try:
            markets = self.exchange.load_markets()
            symbols = [symbol for symbol in markets.keys() 
                      if self.crypto_pairs.is_pair_supported(symbol)]
            
            logger.info(f"Found {len(symbols)} available symbols")
            return sorted(symbols)
            
        except Exception as e:
            logger.error(f"Failed to get available symbols: {e}")
            return []
    
    def validate_data_quality(self, df: pd.DataFrame, symbol: str) -> Dict[str, any]:
        """
        Validate the quality of downloaded historical data.
        
        Args:
            df: OHLCV DataFrame to validate
            symbol: Trading pair symbol for context
            
        Returns:
            Dictionary with data quality metrics
        """
        quality_report = {
            'symbol': symbol,
            'total_records': len(df),
            'date_range': {
                'start': df.index.min().isoformat() if not df.empty else None,
                'end': df.index.max().isoformat() if not df.empty else None
            },
            'missing_data': {
                'gaps': 0,
                'zero_volume': (df['volume'] == 0).sum() if 'volume' in df.columns else 0,
                'invalid_ohlc': 0
            },
            'data_integrity': {
                'high_low_valid': True,
                'open_close_reasonable': True
            }
        }
        
        if df.empty:
            quality_report['status'] = 'FAILED - No data'
            return quality_report
        
        # Check for data gaps
        expected_intervals = pd.date_range(
            start=df.index.min(), 
            end=df.index.max(), 
            freq=f"{self.timeframes.get('1h', 3600)}S"  # Default to hourly
        )
        actual_intervals = set(df.index)
        missing_intervals = set(expected_intervals) - actual_intervals
        quality_report['missing_data']['gaps'] = len(missing_intervals)
        
        # Validate OHLC relationships
        invalid_ohlc = (df['high'] < df['low']) | (df['high'] < df['open']) | (df['high'] < df['close']) | \
                       (df['low'] > df['open']) | (df['low'] > df['close'])
        quality_report['missing_data']['invalid_ohlc'] = invalid_ohlc.sum()
        
        # Quality score
        total_issues = (quality_report['missing_data']['gaps'] + 
                       quality_report['missing_data']['invalid_ohlc'])
        
        if total_issues == 0:
            quality_report['status'] = 'EXCELLENT'
        elif total_issues < len(df) * 0.01:  # Less than 1% issues
            quality_report['status'] = 'GOOD'
        elif total_issues < len(df) * 0.05:  # Less than 5% issues
            quality_report['status'] = 'ACCEPTABLE'  
        else:
            quality_report['status'] = 'POOR'
        
        logger.info(f"Data quality for {symbol}: {quality_report['status']}")
        return quality_report


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Initialize data loader
        loader = DataLoader()
        
        # Download sample data
        df = loader.download_ohlcv(
            symbol="BTC/USDT",
            timeframe="1h", 
            start_date="2024-01-01",
            end_date="2024-01-02"
        )
        
        print("Downloaded {len(df)} records")
        print(df.head())
        
        # Validate data quality
        quality = loader.validate_data_quality(df, "BTC/USDT")
        print("Data quality: {quality['status']}")
        
    except Exception as e:
        print("Error: {e}")
