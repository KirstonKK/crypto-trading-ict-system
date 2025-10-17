#!/usr/bin/env python3
"""
Bybit Real-Time Price Data Module
=================================

This module replaces CoinGecko price feeds with real-time Bybit market data
for more accurate signal generation and execution timing.

Features:
- WebSocket real-time price feeds
- Multi-symbol price tracking
- High-frequency price updates
- Market data validation
- Fallback to REST API if WebSocket fails
"""

import asyncio
import json
import logging
import websockets
import aiohttp
from typing import Dict, List, Optional, Callable
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class BybitRealTimePrices:
    """
    Real-time price data from Bybit WebSocket
    
    Provides:
    - Live price updates via WebSocket
    - Multiple symbol tracking
    - Price change calculations
    - Volume and volatility metrics
    """
    
    def __init__(self, symbols: List[str], testnet: bool = True):
        """
        Initialize real-time price tracker
        
        Args:
            symbols: List of symbols to track (e.g., ['BTCUSDT', 'ETHUSDT'])
            testnet: Use testnet WebSocket URLs
        """
        self.symbols = [self._format_symbol(symbol) for symbol in symbols]
        self.testnet = testnet
        
        # WebSocket configuration
        if testnet:
            self.ws_url = "wss://stream-testnet.bybit.com/v5/public/linear"
            self.rest_url = "https://api-testnet.bybit.com"
        else:
            self.ws_url = "wss://stream.bybit.com/v5/public/linear"
            self.rest_url = "https://api.bybit.com"
        
        # Price data storage
        self.prices: Dict[str, Dict] = {}
        self.price_history: Dict[str, List] = {}
        self.callbacks: List[Callable] = []
        
        # Connection state
        self.ws_connected = False
        self.ws_connection = None
        self.last_update = {}
        self.delta_skip_count: Dict[str, int] = {}  # Track skipped deltas during startup
        
        # Statistics
        self.update_count = 0
        self.start_time = datetime.now()
        
        logger.info("📊 Bybit Real-Time Prices initialized")
        logger.info("   Symbols: {', '.join(self.symbols)}")
        logger.info("   Environment: {'Testnet' if testnet else 'Mainnet'}")

    def _format_symbol(self, symbol: str) -> str:
        """Format symbol for Bybit (ensure USDT suffix)"""
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'
        return symbol

    def add_price_callback(self, callback: Callable):
        """Add callback for price updates"""
        self.callbacks.append(callback)
        logger.debug(f"📡 Price callback added: {len(self.callbacks)} total")

    async def start(self):
        """Start real-time price monitoring"""
        logger.info("🚀 Starting Bybit real-time price monitoring...")
        
        # Initialize price data with REST API
        await self._initialize_prices()
        
        # Start WebSocket connection
        await self._start_websocket()

    async def _initialize_prices(self):
        """Initialize prices using REST API"""
        try:
            logger.info("🔄 Initializing prices from REST API...")
            
            async with aiohttp.ClientSession() as session:
                for symbol in self.symbols:
                    try:
                        url = f"{self.rest_url}/v5/market/tickers"
                        params = {"category": "linear", "symbol": symbol}
                        
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                result = data.get('result', {})
                                tickers = result.get('list', [])
                                
                                if tickers:
                                    ticker = tickers[0]
                                    price_data = self._parse_ticker_data(ticker)
                                    self.prices[symbol] = price_data
                                    
                                    logger.info("✅ {symbol}: ${price_data['price']:,.4f}")
                                else:
                                    logger.warning(f"⚠️  No ticker data for {symbol}")
                                    
                            else:
                                if response.status == 403:
                                    logger.debug(f"🔒 API rate limit for {symbol} (using WebSocket instead)")
                                elif response.status == 429:
                                    logger.debug(f"⏳ Rate limited for {symbol} (using WebSocket instead)")
                                else:
                                    logger.warning(f"⚠️  REST API error for {symbol}: {response.status}")
                                
                    except Exception as e:
                        logger.error(f"❌ Error getting price for {symbol}: {e}")
                        # Set fallback price
                        self.prices[symbol] = {
                            'price': 0.0,
                            'symbol': symbol,
                            'timestamp': datetime.now(),
                            'volume_24h': 0.0,
                            'change_24h': 0.0,
                            'source': 'fallback'
                        }
            
            logger.info("✅ Initialized prices for {len(self.prices)} symbols")
            
        except Exception as e:
            logger.error(f"❌ Error initializing prices: {e}")

    def _parse_ticker_data(self, ticker: Dict) -> Dict:
        """Parse ticker data from Bybit API"""
        try:
            return {
                'price': float(ticker.get('lastPrice', 0)),
                'symbol': ticker.get('symbol', ''),
                'timestamp': datetime.now(),
                'volume_24h': float(ticker.get('volume24h', 0)),
                'change_24h': float(ticker.get('price24hPcnt', 0)) * 100,  # Convert to percentage
                'bid': float(ticker.get('bid1Price', 0)),
                'ask': float(ticker.get('ask1Price', 0)),
                'high_24h': float(ticker.get('highPrice24h', 0)),
                'low_24h': float(ticker.get('lowPrice24h', 0)),
                'source': 'bybit_rest'
            }
        except Exception as e:
            logger.error(f"❌ Error parsing ticker data: {e}")
            return {
                'price': 0.0,
                'symbol': ticker.get('symbol', ''),
                'timestamp': datetime.now(),
                'source': 'error'
            }

    async def _start_websocket(self):
        """Start WebSocket connection for real-time updates"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info("🔗 Connecting to Bybit WebSocket... (attempt {retry_count + 1})")
                
                async with websockets.connect(self.ws_url) as websocket:
                    self.ws_connection = websocket
                    self.ws_connected = True
                    logger.info("✅ WebSocket connected")
                    
                    # Subscribe to ticker streams
                    await self._subscribe_to_tickers(websocket)
                    
                    # Handle incoming messages
                    async for message in websocket:
                        await self._handle_websocket_message(message)
                        
            except websockets.exceptions.ConnectionClosed:
                self.ws_connected = False
                retry_count += 1
                wait_time = min(2 ** retry_count, 30)  # Exponential backoff, max 30s
                logger.warning(f"🔌 WebSocket disconnected, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                self.ws_connected = False
                retry_count += 1
                logger.error(f"❌ WebSocket error: {e}")
                await asyncio.sleep(5)
        
        logger.error(f"❌ Failed to connect after {max_retries} attempts")

    async def _subscribe_to_tickers(self, websocket):
        """Subscribe to ticker streams for all symbols"""
        try:
            # Create subscription topics
            topics = [f"tickers.{symbol}" for symbol in self.symbols]
            
            subscribe_message = {
                "op": "subscribe",
                "args": topics
            }
            
            await websocket.send(json.dumps(subscribe_message))
            logger.info("📡 Subscribed to {len(topics)} ticker streams")
            
            # Wait for subscription confirmation
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("success"):
                logger.info("✅ Ticker subscription confirmed")
            else:
                logger.warning(f"⚠️  Subscription response: {data}")
                
        except Exception as e:
            logger.error(f"❌ Error subscribing to tickers: {e}")

    async def _handle_websocket_message(self, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            
            # Handle ticker updates (both updates and snapshots)
            if data.get("topic") and "tickers" in data["topic"]:
                await self._process_ticker_update(data)
                
            # Handle ping messages
            elif data.get("op") == "ping":
                # Respond to ping
                pong_message = {"op": "pong"}
                await self.ws_connection.send(json.dumps(pong_message))
                
            # Handle subscription confirmations
            elif data.get("success") is not None:
                if data.get("success"):
                    logger.info("✅ WebSocket subscription confirmed: {data.get('op', 'unknown')}")
                else:
                    logger.warning(f"⚠️ WebSocket subscription failed: {data}")
                
        except Exception as e:
            logger.error(f"❌ Error handling WebSocket message: {e}")
            logger.error(f"❌ Message content: {message[:500]}...")

    def _handle_snapshot_message(self, ticker_data, symbol):
        """Handle snapshot message type"""
        price_data = self._parse_ws_ticker_data(ticker_data, symbol)
        old_price = self.prices.get(symbol, {}).get('price', 0)
        self.prices[symbol] = price_data
        return price_data, old_price
    
    def _handle_delta_message(self, ticker_data, symbol):
        """Handle delta message type"""
        if symbol in self.prices:
            price_data = self._update_ticker_delta(ticker_data, symbol)
            old_price = self.prices.get(symbol, {}).get('price', 0)
            self.prices[symbol] = price_data
            return price_data, old_price
        else:
            # No existing data to update, skip delta
            if symbol not in self.delta_skip_count:
                self.delta_skip_count[symbol] = 0
            self.delta_skip_count[symbol] += 1
            
            if self.delta_skip_count[symbol] <= 3:
                logger.debug(f"🔄 Building {symbol} baseline data (delta #{self.delta_skip_count[symbol]})")
            elif self.delta_skip_count[symbol] == 10:
                logger.info(f"📊 {symbol} baseline initialization in progress...")
            return None, None
    
    def _update_price_history(self, symbol, price_data):
        """Update price history for symbol"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append({
            'price': price_data['price'],
            'timestamp': price_data['timestamp']
        })
        
        if len(self.price_history[symbol]) > 100:
            self.price_history[symbol] = self.price_history[symbol][-100:]
    
    def _log_price_change(self, symbol, price_data, old_price):
        """Log significant price changes"""
        if old_price <= 0 or price_data['price'] <= 0:
            return
        
        price_change = ((price_data['price'] - old_price) / old_price) * 100
        
        if abs(price_change) > 0.1:  # 0.1% or more
            direction = "📈" if price_change > 0 else "📉"
            logger.debug(f"{direction} {symbol}: ${price_data['price']:,.4f} ({price_change:+.2f}%)")
        
        return price_change
    
    async def _notify_callbacks(self, symbol, price_data, price_change):
        """Notify registered callbacks of price update"""
        for callback in self.callbacks:
            try:
                await callback(symbol, price_data, price_change)
            except Exception as e:
                logger.error(f"❌ Price callback error: {e}")
    
    async def _process_ticker_update(self, data: Dict):
        """Process ticker update from WebSocket"""
        try:
            topic = data.get("topic", "")
            ticker_data = data.get("data", {})
            message_type = data.get("type", "unknown")
            
            logger.debug(f"🔍 Raw WebSocket data for topic {topic}, type: {message_type}")
            logger.debug(f"🔍 Ticker data keys: {list(ticker_data.keys()) if ticker_data else 'None'}")
            if ticker_data and 'lastPrice' in ticker_data:
                logger.debug(f"🔍 lastPrice value: '{ticker_data['lastPrice']}' (type: {type(ticker_data['lastPrice'])})")
            
            symbol = topic.split(".")[-1] if "." in topic else ""
            
            if not symbol or not ticker_data:
                return
            
            # Handle different message types
            if message_type == "snapshot":
                price_data, old_price = self._handle_snapshot_message(ticker_data, symbol)
            elif message_type == "delta":
                result = self._handle_delta_message(ticker_data, symbol)
                if result[0] is None:  # Skip delta
                    return
                price_data, old_price = result
            else:
                logger.warning(f"⚠️ Unknown message type '{message_type}' for {symbol}, treating as snapshot")
                price_data, old_price = self._handle_snapshot_message(ticker_data, symbol)
            
            # Update tracking
            self._update_price_history(symbol, price_data)
            self.update_count += 1
            self.last_update[symbol] = datetime.now()
            
            # Log and notify
            price_change = self._log_price_change(symbol, price_data, old_price)
            await self._notify_callbacks(symbol, price_data, price_change)
                        
        except Exception as e:
            logger.error(f"❌ Error processing ticker update: {e}")

    def _parse_ws_ticker_data(self, ticker: Dict, symbol: str) -> Dict:
        """Parse WebSocket ticker data (for snapshot messages)"""
        try:
            # Extract lastPrice and ensure it's a valid number
            last_price_str = ticker.get('lastPrice', '0')
            
            # Log the raw data for debugging (only for snapshots with actual price data)
            if 'lastPrice' in ticker:
                logger.info("🔍 SNAPSHOT {symbol}: lastPrice = '{last_price_str}' (type: {type(last_price_str)})")
            
            # Convert to float, handling both string and numeric types
            try:
                price_value = float(last_price_str) if last_price_str else 0.0
                if 'lastPrice' in ticker:
                    logger.info("✅ SNAPSHOT {symbol}: Converted to float: {price_value}")
            except (ValueError, TypeError) as e:
                logger.error(f"❌ SNAPSHOT {symbol}: Invalid lastPrice format '{last_price_str}': {e}")
                price_value = 0.0
                
            logger.debug(f"🔍 {symbol}: lastPrice='{last_price_str}' -> {price_value}")
            
            # Don't reject 0 prices - they might be valid. Only reject if parsing failed
            if price_value < 0:  # Only reject negative prices
                logger.warning(f"⚠️ Received negative price for {symbol}: {price_value}")
                return {
                    'price': 0.0,
                    'symbol': symbol,
                    'timestamp': datetime.now(),
                    'source': 'invalid_price'
                }
            
            # Log when we get 0 prices but don't reject them
            if price_value == 0:
                logger.info("⚠️ Received zero price for {symbol}: {price_value} (might be valid)")
            
            # Parse other fields safely
            volume_24h = self._safe_float(ticker.get('volume24h', '0'))
            price_24h_pct = self._safe_float(ticker.get('price24hPcnt', '0')) * 100
            bid_price = self._safe_float(ticker.get('bid1Price', '0'))
            ask_price = self._safe_float(ticker.get('ask1Price', '0'))
            high_24h = self._safe_float(ticker.get('highPrice24h', '0'))
            low_24h = self._safe_float(ticker.get('lowPrice24h', '0'))
            
            return {
                'price': price_value,
                'symbol': symbol,
                'timestamp': datetime.now(),
                'volume_24h': volume_24h,
                'change_24h': price_24h_pct,
                'bid': bid_price,
                'ask': ask_price,
                'high_24h': high_24h,
                'low_24h': low_24h,
                'source': 'bybit_ws'
            }
        except Exception as e:
            logger.error(f"❌ Error parsing WebSocket ticker for {symbol}: {e}")
            logger.error(f"❌ Ticker data: {ticker}")
            return {
                'price': 0.0,
                'symbol': symbol,
                'timestamp': datetime.now(),
                'source': 'error'
            }

    def _update_ticker_delta(self, delta_data: Dict, symbol: str) -> Dict:
        """Update existing ticker data with delta changes"""
        try:
            # Get existing price data or create new if not exists
            existing_data = self.prices.get(symbol, {
                'price': 0.0,
                'symbol': symbol,
                'timestamp': datetime.now(),
                'volume_24h': 0.0,
                'change_24h': 0.0,
                'bid': 0.0,
                'ask': 0.0,
                'high_24h': 0.0,
                'low_24h': 0.0,
                'source': 'bybit_ws'
            })
            
            # Update only fields that are present in delta
            if 'lastPrice' in delta_data:
                new_price = self._safe_float(delta_data['lastPrice'])
                if new_price > 0:  # Only update if valid price
                    existing_data['price'] = new_price
                    logger.info("✅ DELTA UPDATE {symbol}: price=${new_price}")
                else:
                    logger.warning(f"⚠️ DELTA UPDATE {symbol}: received invalid lastPrice {new_price}")
            # Don't update price if lastPrice is not in delta - preserve existing price
            
            if 'volume24h' in delta_data:
                existing_data['volume_24h'] = self._safe_float(delta_data['volume24h'])
            
            if 'price24hPcnt' in delta_data:
                existing_data['change_24h'] = self._safe_float(delta_data['price24hPcnt']) * 100
            
            if 'bid1Price' in delta_data:
                existing_data['bid'] = self._safe_float(delta_data['bid1Price'])
            
            if 'ask1Price' in delta_data:
                existing_data['ask'] = self._safe_float(delta_data['ask1Price'])
            
            if 'highPrice24h' in delta_data:
                existing_data['high_24h'] = self._safe_float(delta_data['highPrice24h'])
            
            if 'lowPrice24h' in delta_data:
                existing_data['low_24h'] = self._safe_float(delta_data['lowPrice24h'])
            
            existing_data['timestamp'] = datetime.now()
            return existing_data
            
        except Exception as e:
            logger.error(f"❌ Error updating delta for {symbol}: {e}")
            return self.prices.get(symbol, {'price': 0.0, 'symbol': symbol, 'timestamp': datetime.now(), 'source': 'error'})

    def _safe_float(self, value) -> float:
        """Safely convert a value to float"""
        try:
            if isinstance(value, str):
                return float(value) if value else 0.0
            return float(value) if value else 0.0
        except (ValueError, TypeError):
            return 0.0

    # Public API methods
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        symbol = self._format_symbol(symbol)
        price_data = self.prices.get(symbol, {})
        price = price_data.get('price', 0.0)
        
        # Debug logging to see what's happening
        if price < 0.001:  # Effectively zero for crypto prices
            logger.debug(f"🔍 GET_PRICE {symbol}: returning 0.0 - stored data: {price_data}")
        else:
            logger.debug(f"✅ GET_PRICE {symbol}: returning ${price}")
            
        return price

    def get_price_data(self, symbol: str) -> Optional[Dict]:
        """Get full price data for a symbol"""
        symbol = self._format_symbol(symbol)
        return self.prices.get(symbol)

    def get_all_prices(self) -> Dict[str, float]:
        """Get current prices for all symbols"""
        return {symbol: data.get('price', 0.0) for symbol, data in self.prices.items()}

    def get_price_change(self, symbol: str, minutes: int = 5) -> float:
        """Calculate price change over specified minutes"""
        try:
            symbol = self._format_symbol(symbol)
            history = self.price_history.get(symbol, [])
            
            if len(history) < 2:
                return 0.0
            
            current_time = datetime.now()
            cutoff_time = current_time - datetime.timedelta(minutes=minutes)
            
            # Find price from specified minutes ago
            old_price = None
            for entry in reversed(history):
                if entry['timestamp'] <= cutoff_time:
                    old_price = entry['price']
                    break
            
            if old_price is None:
                old_price = history[0]['price']  # Use oldest available
            
            current_price = history[-1]['price']
            
            if old_price > 0:
                return ((current_price - old_price) / old_price) * 100
            
            return 0.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating price change: {e}")
            return 0.0

    def get_volatility(self, symbol: str, minutes: int = 15) -> float:
        """Calculate price volatility over specified minutes"""
        try:
            symbol = self._format_symbol(symbol)
            history = self.price_history.get(symbol, [])
            
            if len(history) < 10:  # Need at least 10 data points
                return 0.0
            
            current_time = datetime.now()
            cutoff_time = current_time - datetime.timedelta(minutes=minutes)
            
            # Get prices from specified time period
            recent_prices = [
                entry['price'] for entry in history 
                if entry['timestamp'] >= cutoff_time
            ]
            
            if len(recent_prices) < 3:
                return 0.0
            
            # Calculate standard deviation as volatility measure
            mean_price = sum(recent_prices) / len(recent_prices)
            variance = sum((price - mean_price) ** 2 for price in recent_prices) / len(recent_prices)
            volatility = (variance ** 0.5) / mean_price * 100  # As percentage
            
            return volatility
            
        except Exception as e:
            logger.error(f"❌ Error calculating volatility: {e}")
            return 0.0

    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.ws_connected

    def get_stats(self) -> Dict:
        """Get connection and update statistics"""
        uptime = datetime.now() - self.start_time
        updates_per_minute = (self.update_count / max(uptime.total_seconds() / 60, 1))
        
        return {
            'connected': self.ws_connected,
            'symbols_tracked': len(self.symbols),
            'total_updates': self.update_count,
            'updates_per_minute': round(updates_per_minute, 1),
            'uptime_minutes': round(uptime.total_seconds() / 60, 1),
            'last_updates': {
                symbol: timestamp.strftime('%H:%M:%S') 
                for symbol, timestamp in self.last_update.items()
            }
        }

    async def stop(self):
        """Stop the price monitoring"""
        try:
            logger.info("🛑 Stopping price monitoring...")
            
            self.ws_connected = False
            
            if self.ws_connection:
                await self.ws_connection.close()
            
            logger.info("✅ Price monitoring stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping price monitoring: {e}")


# Utility function for easy integration
async def create_price_monitor(symbols: List[str], testnet: bool = True) -> BybitRealTimePrices:
    """
    Create and start a price monitor
    
    Args:
        symbols: List of symbols to monitor
        testnet: Use testnet environment
        
    Returns:
        Configured and started BybitRealTimePrices instance
    """
    monitor = BybitRealTimePrices(symbols, testnet)
    await monitor.start()
    return monitor