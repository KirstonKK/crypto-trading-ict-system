"""
Bybit Demo Trading Client
========================

Core API client for interacting with Bybit's demo trading environment.
Handles authentication, order management, and account data retrieval.
"""

import os
import time
import hmac
import hashlib
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class BybitDemoClient:
    """
    Bybit Demo Trading API Client
    
    Provides interface for:
    - Account management
    - Order placement and management
    - Position tracking
    - Balance retrieval
    """
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = True, demo: bool = False):
        """
        Initialize Bybit Demo Client
        
        Args:
            api_key: Bybit API key (from environment if not provided)
            api_secret: Bybit API secret (from environment if not provided)
            testnet: Use testnet environment (fake prices, fake money)
            demo: Use demo mainnet environment (real prices, fake money) - overrides testnet
        """
        self.api_key = api_key or os.getenv('BYBIT_API_KEY')
        self.api_secret = api_secret or os.getenv('BYBIT_API_SECRET')
        self.testnet = testnet
        self.demo = demo
        
        # Check for missing credentials
        if not self.api_key or not self.api_secret:
            logger.warning("⚠️  Missing Bybit API credentials - some features may not work")
            # Don't raise error, allow fallback to Binance prices
            
        # Demo Mainnet takes precedence (real prices, fake money)
        if demo:
            self.base_url = "https://api-demo.bybit.com"
            self.ws_url = "wss://stream-demo.bybit.com/v5/private"
            env_name = "Demo Mainnet (Real Prices, Fake Money) ✅"
        elif testnet:
            self.base_url = "https://api-testnet.bybit.com"
            self.ws_url = "wss://stream-testnet.bybit.com/v5/private"
            env_name = "Testnet (Fake Prices, Fake Money)"
        else:
            self.base_url = "https://api.bybit.com"
            self.ws_url = "wss://stream.bybit.com/v5/private"
            env_name = "Live Mainnet (Real Money) ⚠️"
            
        self.session = None
        self.last_request_time = 0
        self.rate_limit_delay = 0.1  # 100ms between requests
        
        logger.info(f"🔗 Bybit Client initialized - {env_name}")

    def _generate_signature(self, timestamp: str, params: str) -> str:
        """Generate HMAC SHA256 signature for API authentication"""
        if not self.api_secret:
            return ""
        recv_window = "5000"
        param_str = str(timestamp) + self.api_key + recv_window + params
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _prepare_headers(self, params: str = "") -> Dict[str, str]:
        """Prepare authentication headers for API requests"""
        if not self.api_key or not self.api_secret:
            return {"Content-Type": "application/json"}
            
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, params)
        
        return {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-SIGN-TYPE": "2",
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": "5000",
            "Content-Type": "application/json"
        }

    def _ensure_session(self):
        """Ensure aiohttp session is available"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def _rate_limit(self):
        """Implement rate limiting to avoid API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()

    async def _make_request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        """
        Make authenticated API request to Bybit
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Request parameters
            
        Returns:
            API response data
        """
        if not self.api_key or not self.api_secret:
            logger.error("❌ Missing Bybit API credentials")
            return {}
            
        self._ensure_session()
        await self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        
        if method.upper() == "GET":
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            headers = self._prepare_headers(query_string)
            
            async with self.session.get(url, headers=headers, params=params) as response:
                data = await response.json()
                
        else:  # POST, PUT, DELETE
            payload = json.dumps(params) if params else ""
            headers = self._prepare_headers(payload)
            
            async with self.session.post(url, headers=headers, json=params) as response:
                data = await response.json()
        
        if data.get('retCode') != 0:
            error_msg = data.get('retMsg', 'Unknown error')
            logger.error(f"❌ Bybit API Error: {error_msg}")
            raise RuntimeError(f"Bybit API Error: {error_msg}")
            
        return data.get('result', {})

    # Account Management
    async def get_account_info(self) -> Dict:
        """Get account information including balance and positions"""
        if not self.api_key or not self.api_secret:
            logger.warning("⚠️  Cannot get account info: missing API credentials")
            return {}
        try:
            return await self._make_request("GET", "/v5/account/wallet-balance", {
                "accountType": "UNIFIED"
            })
        except Exception as e:
            logger.error(f"❌ Failed to get account info: {e}")
            return {}

    async def get_balance(self) -> Dict[str, float]:
        """
        Get account balance for all assets
        
        Returns:
            Dictionary with asset balances
        """
        if not self.api_key or not self.api_secret:
            logger.warning("⚠️  Cannot get balance: missing API credentials")
            return {}
        try:
            account_info = await self.get_account_info()
            balances = {}
            
            for coin in account_info.get('list', [{}])[0].get('coin', []):
                symbol = coin.get('coin')
                balance = float(coin.get('walletBalance', 0))
                balances[symbol] = balance
                
            logger.info(f"💰 Account Balances: {balances}")
            return balances
            
        except Exception as e:
            logger.error(f"❌ Failed to get balance: {e}")
            return {}

    # Order Management
    async def place_order(self, 
                         symbol: str, 
                         side: str, 
                         qty: float,
                         order_type: str = "Market",
                         price: float = None,
                         stop_loss: float = None,
                         take_profit: float = None,
                         time_in_force: str = "GTC") -> Dict:
        """
        Place order on Bybit
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            side: "Buy" or "Sell"
            qty: Quantity to trade
            order_type: "Market", "Limit"
            price: Limit price (required for Limit orders)
            stop_loss: Stop loss price
            take_profit: Take profit price
            time_in_force: "GTC", "IOC", "FOK"
            
        Returns:
            Order response with order ID
        """
        try:
            params = {
                "category": "linear",
                "symbol": symbol,
                "side": side,
                "orderType": order_type,
                "qty": str(qty),
                "timeInForce": time_in_force
            }
            
            if price and order_type == "Limit":
                params["price"] = str(price)
                
            if stop_loss:
                params["stopLoss"] = str(stop_loss)
                
            if take_profit:
                params["takeProfit"] = str(take_profit)
            
            result = await self._make_request("POST", "/v5/order/create", params)
            
            order_id = result.get('orderId')
            logger.info(f"📈 Order placed: {symbol} {side} {qty} - ID: {order_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to place order: {e}")
            raise

    async def get_orders(self, symbol: str = None, status: str = None) -> List[Dict]:
        """
        Get orders (active or historical)
        
        Args:
            symbol: Filter by symbol
            status: Filter by status ("New", "Filled", "Cancelled", etc.)
            
        Returns:
            List of orders
        """
        try:
            params = {"category": "linear"}
            
            if symbol:
                params["symbol"] = symbol
            if status:
                params["orderStatus"] = status
                
            result = await self._make_request("GET", "/v5/order/realtime", params)
            orders = result.get('list', [])
            
            logger.info(f"📋 Retrieved {len(orders)} orders")
            return orders
            
        except Exception as e:
            logger.error(f"❌ Failed to get orders: {e}")
            return []

    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Cancel an existing order
        
        Args:
            symbol: Trading pair
            order_id: Order ID to cancel
            
        Returns:
            True if successful
        """
        try:
            params = {
                "category": "linear",
                "symbol": symbol,
                "orderId": order_id
            }
            
            await self._make_request("POST", "/v5/order/cancel", params)
            logger.info(f"❌ Order cancelled: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel order: {e}")
            return False

    # Position Management
    async def get_positions(self, symbol: str = None) -> List[Dict]:
        """
        Get current positions
        
        Args:
            symbol: Filter by symbol
            
        Returns:
            List of positions
        """
        try:
            params = {"category": "linear"}
            if symbol:
                params["symbol"] = symbol
                
            result = await self._make_request("GET", "/v5/position/list", params)
            positions = result.get('list', [])
            
            # Filter out zero positions
            active_positions = [pos for pos in positions if float(pos.get('size', 0)) != 0]
            
            logger.info(f"📊 Active positions: {len(active_positions)}")
            return active_positions
            
        except Exception as e:
            logger.error(f"❌ Failed to get positions: {e}")
            return []

    async def close_position(self, symbol: str) -> bool:
        """
        Close entire position for a symbol
        
        Args:
            symbol: Trading pair to close
            
        Returns:
            True if successful
        """
        try:
            positions = await self.get_positions(symbol)
            
            for position in positions:
                size = float(position.get('size', 0))
                if size == 0:
                    continue
                    
                side = position.get('side')
                close_side = "Sell" if side == "Buy" else "Buy"
                
                await self.place_order(
                    symbol=symbol,
                    side=close_side,
                    qty=abs(size),
                    order_type="Market"
                )
                
            logger.info(f"🔒 Position closed: {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to close position: {e}")
            return False

    # Market Data
    async def get_ticker(self, symbol: str) -> Dict:
        """
        Get current market ticker
        
        Args:
            symbol: Trading pair
            
        Returns:
            Ticker data including price, volume, etc.
        """
        if not self.api_key or not self.api_secret:
            logger.warning(f"⚠️  Cannot get ticker for {symbol}: missing API credentials")
            return {}
        try:
            params = {
                "category": "linear",
                "symbol": symbol
            }
            
            result = await self._make_request("GET", "/v5/market/tickers", params)
            tickers = result.get('list', [])
            
            if tickers:
                return tickers[0]
            else:
                logger.warning(f"No ticker data for {symbol}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Failed to get ticker: {e}")
            return {}

    async def get_kline_data(self, symbol: str, interval: str = "1", limit: int = 200) -> List[Dict]:
        """
        Get candlestick/kline data
        
        Args:
            symbol: Trading pair
            interval: Time interval ("1", "5", "15", "30", "60", "240", "D")
            limit: Number of candles to retrieve
            
        Returns:
            List of candlestick data
        """
        try:
            params = {
                "category": "linear",
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            
            result = await self._make_request("GET", "/v5/market/kline", params)
            return result.get('list', [])
            
        except Exception as e:
            logger.error(f"❌ Failed to get kline data: {e}")
            return []

    # Utility Methods
    async def test_connection(self) -> bool:
        """
        Test connection to Bybit API
        
        Returns:
            True if connection successful
        """
        try:
            await self.get_account_info()
            logger.info("✅ Bybit connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ Bybit connection test failed: {e}")
            return False

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("🔌 Bybit client session closed")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Utility Functions
def format_bybit_symbol(symbol: str) -> str:
    """
    Format symbol for Bybit API
    
    Args:
        symbol: Symbol like "BTCUSDT"
        
    Returns:
        Bybit-formatted symbol
    """
    # Bybit typically uses symbols as-is, but this function
    # can handle any necessary transformations
    return symbol.upper()

def calculate_quantity_precision(symbol: str, quantity: float) -> float:
    """
    Calculate proper quantity precision for Bybit orders
    
    Args:
        symbol: Trading pair
        quantity: Desired quantity
        
    Returns:
        Properly formatted quantity
    """
    # This would typically fetch instrument info from Bybit
    # For now, using common precisions
    precision_map = {
        'BTCUSDT': 0.001,
        'ETHUSDT': 0.01,
        'SOLUSDT': 0.1,
        'XRPUSDT': 1.0
    }
    
    precision = precision_map.get(symbol, 0.01)
    return round(quantity / precision) * precision