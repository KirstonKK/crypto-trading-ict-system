"""
Bybit WebSocket Client
====================

Real-time data streaming from Bybit for:
- Market data (price updates, orderbook)
- Account updates (orders, positions, balance)
- Trade execution monitoring
"""

import asyncio
import json
import logging
import websockets
import hmac
import hashlib
import time
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SubscriptionType(Enum):
    """WebSocket subscription types"""
    TICKER = "tickers"
    ORDERBOOK = "orderbook"
    TRADE = "publicTrade"
    KLINE = "kline"
    POSITION = "position"
    ORDER = "order"
    EXECUTION = "execution"
    WALLET = "wallet"

@dataclass
class MarketData:
    """Market data from WebSocket"""
    symbol: str
    price: float
    timestamp: datetime
    volume: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    change_24h: Optional[float] = None

@dataclass
class OrderUpdate:
    """Order update from WebSocket"""
    order_id: str
    symbol: str
    side: str
    status: str
    quantity: float
    price: float
    filled_quantity: float
    timestamp: datetime

@dataclass
class PositionUpdate:
    """Position update from WebSocket"""
    symbol: str
    side: str
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    timestamp: datetime

class BybitWebSocketClient:
    """
    Bybit WebSocket client for real-time data
    
    Features:
    - Multiple topic subscriptions
    - Automatic reconnection
    - Authentication for private streams
    - Data parsing and callbacks
    """
    
    def __init__(self, 
                 api_key: str = None, 
                 api_secret: str = None,
                 testnet: bool = True):
        """
        Initialize WebSocket client
        
        Args:
            api_key: Bybit API key for private streams
            api_secret: Bybit API secret
            testnet: Use testnet environment
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # WebSocket URLs
        if testnet:
            self.public_url = "wss://stream-testnet.bybit.com/v5/public/linear"
            self.private_url = "wss://stream-testnet.bybit.com/v5/private"
        else:
            self.public_url = "wss://stream.bybit.com/v5/public/linear"
            self.private_url = "wss://stream.bybit.com/v5/private"
        
        # Connection state
        self.public_ws = None
        self.private_ws = None
        self.connected = False
        self.authenticated = False
        
        # Subscriptions and callbacks
        self.subscriptions: Dict[str, SubscriptionType] = {}
        self.callbacks: Dict[SubscriptionType, List[Callable]] = {
            sub_type: [] for sub_type in SubscriptionType
        }
        
        # Data storage
        self.latest_prices: Dict[str, float] = {}
        self.latest_orders: Dict[str, OrderUpdate] = {}
        self.latest_positions: Dict[str, PositionUpdate] = {}
        
        # Connection management
        self.reconnect_interval = 5
        self.max_reconnect_attempts = 10
        self.ping_interval = 20
        
        logger.info(f"📡 Bybit WebSocket client initialized - {'Testnet' if testnet else 'Mainnet'}")

    def _generate_auth_signature(self, expires: str) -> str:
        """Generate authentication signature"""
        if not self.api_secret:
            raise ValueError("API secret required for authentication")
            
        param_str = f"GET/realtime{expires}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    async def _authenticate(self, websocket):
        """Authenticate private WebSocket connection"""
        try:
            expires = str(int(time.time() * 1000) + 10000)
            signature = self._generate_auth_signature(expires)
            
            auth_message = {
                "op": "auth",
                "args": [self.api_key, expires, signature]
            }
            
            await websocket.send(json.dumps(auth_message))
            
            # Wait for auth response
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("success"):
                self.authenticated = True
                logger.info("✅ WebSocket authentication successful")
            else:
                logger.error(f"❌ WebSocket authentication failed: {data}")
                raise Exception("Authentication failed")
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            raise

    async def _handle_public_message(self, message: str):
        """Handle public WebSocket messages"""
        try:
            data = json.loads(message)
            
            if data.get("topic"):
                topic = data["topic"]
                
                # Parse ticker data
                if "tickers" in topic:
                    await self._handle_ticker_data(data)
                    
                # Parse trade data
                elif "publicTrade" in topic:
                    await self._handle_trade_data(data)
                    
                # Parse kline data
                elif "kline" in topic:
                    await self._handle_kline_data(data)
                    
        except Exception as e:
            logger.error(f"❌ Error handling public message: {e}")

    async def _handle_private_message(self, message: str):
        """Handle private WebSocket messages"""
        try:
            data = json.loads(message)
            
            if data.get("topic"):
                topic = data["topic"]
                
                # Parse order updates
                if "order" in topic:
                    await self._handle_order_update(data)
                    
                # Parse position updates
                elif "position" in topic:
                    await self._handle_position_update(data)
                    
                # Parse execution updates
                elif "execution" in topic:
                    await self._handle_execution_update(data)
                    
                # Parse wallet updates
                elif "wallet" in topic:
                    await self._handle_wallet_update(data)
                    
        except Exception as e:
            logger.error(f"❌ Error handling private message: {e}")

    async def _handle_ticker_data(self, data: Dict):
        """Handle ticker data updates"""
        try:
            ticker_data = data.get("data", {})
            
            if isinstance(ticker_data, list):
                for ticker in ticker_data:
                    symbol = ticker.get("symbol")
                    price = float(ticker.get("lastPrice", 0))
                    
                    self.latest_prices[symbol] = price
                    
                    market_data = MarketData(
                        symbol=symbol,
                        price=price,
                        timestamp=datetime.now(),
                        volume=float(ticker.get("volume24h", 0)),
                        bid=float(ticker.get("bid1Price", 0)),
                        ask=float(ticker.get("ask1Price", 0)),
                        change_24h=float(ticker.get("price24hPcnt", 0))
                    )
                    
                    # Call registered callbacks
                    for callback in self.callbacks[SubscriptionType.TICKER]:
                        try:
                            await callback(market_data)
                        except Exception as e:
                            logger.error(f"❌ Ticker callback error: {e}")
                            
        except Exception as e:
            logger.error(f"❌ Error handling ticker data: {e}")

    async def _handle_order_update(self, data: Dict):
        """Handle order update messages"""
        try:
            order_data = data.get("data", [])
            
            for order in order_data:
                order_id = order.get("orderId")
                
                order_update = OrderUpdate(
                    order_id=order_id,
                    symbol=order.get("symbol"),
                    side=order.get("side"),
                    status=order.get("orderStatus"),
                    quantity=float(order.get("qty", 0)),
                    price=float(order.get("price", 0)),
                    filled_quantity=float(order.get("cumExecQty", 0)),
                    timestamp=datetime.now()
                )
                
                self.latest_orders[order_id] = order_update
                
                # Call registered callbacks
                for callback in self.callbacks[SubscriptionType.ORDER]:
                    try:
                        await callback(order_update)
                    except Exception as e:
                        logger.error(f"❌ Order callback error: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Error handling order update: {e}")

    async def _handle_position_update(self, data: Dict):
        """Handle position update messages"""
        try:
            position_data = data.get("data", [])
            
            for position in position_data:
                symbol = position.get("symbol")
                
                position_update = PositionUpdate(
                    symbol=symbol,
                    side=position.get("side"),
                    size=float(position.get("size", 0)),
                    entry_price=float(position.get("entryPrice", 0)),
                    mark_price=float(position.get("markPrice", 0)),
                    unrealized_pnl=float(position.get("unrealisedPnl", 0)),
                    timestamp=datetime.now()
                )
                
                self.latest_positions[symbol] = position_update
                
                # Call registered callbacks
                for callback in self.callbacks[SubscriptionType.POSITION]:
                    try:
                        await callback(position_update)
                    except Exception as e:
                        logger.error(f"❌ Position callback error: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Error handling position update: {e}")

    async def _handle_trade_data(self, data: Dict):
        """Handle public trade data"""
        try:
            trade_data = data.get("data", [])
            
            for trade in trade_data:
                symbol = trade.get("s")
                price = float(trade.get("p", 0))
                
                self.latest_prices[symbol] = price
                
                # Call trade callbacks if needed
                for callback in self.callbacks[SubscriptionType.TRADE]:
                    try:
                        await callback(trade)
                    except Exception as e:
                        logger.error(f"❌ Trade callback error: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Error handling trade data: {e}")

    async def _handle_kline_data(self, data: Dict):
        """Handle kline/candlestick data"""
        try:
            kline_data = data.get("data", [])
            
            for callback in self.callbacks[SubscriptionType.KLINE]:
                try:
                    await callback(kline_data)
                except Exception as e:
                    logger.error(f"❌ Kline callback error: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error handling kline data: {e}")

    async def _handle_execution_update(self, data: Dict):
        """Handle execution/fill updates"""
        try:
            execution_data = data.get("data", [])
            
            for callback in self.callbacks[SubscriptionType.EXECUTION]:
                try:
                    await callback(execution_data)
                except Exception as e:
                    logger.error(f"❌ Execution callback error: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error handling execution update: {e}")

    async def _handle_wallet_update(self, data: Dict):
        """Handle wallet/balance updates"""
        try:
            wallet_data = data.get("data", [])
            
            for callback in self.callbacks[SubscriptionType.WALLET]:
                try:
                    await callback(wallet_data)
                except Exception as e:
                    logger.error(f"❌ Wallet callback error: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error handling wallet update: {e}")

    async def _public_connection_handler(self):
        """Handle public WebSocket connection"""
        while True:
            try:
                async with websockets.connect(self.public_url) as websocket:
                    self.public_ws = websocket
                    logger.info("🔗 Public WebSocket connected")
                    
                    # Send subscriptions
                    await self._send_public_subscriptions(websocket)
                    
                    # Handle messages
                    async for message in websocket:
                        await self._handle_public_message(message)
                        
            except websockets.exceptions.ConnectionClosed:
                logger.warning("🔌 Public WebSocket disconnected, reconnecting...")
                await asyncio.sleep(self.reconnect_interval)
            except Exception as e:
                logger.error(f"❌ Public WebSocket error: {e}")
                await asyncio.sleep(self.reconnect_interval)

    async def _private_connection_handler(self):
        """Handle private WebSocket connection"""
        if not self.api_key or not self.api_secret:
            logger.info("🔒 Skipping private WebSocket (no API credentials)")
            return
            
        while True:
            try:
                async with websockets.connect(self.private_url) as websocket:
                    self.private_ws = websocket
                    
                    # Authenticate
                    await self._authenticate(websocket)
                    logger.info("🔗 Private WebSocket connected and authenticated")
                    
                    # Send subscriptions
                    await self._send_private_subscriptions(websocket)
                    
                    # Handle messages
                    async for message in websocket:
                        await self._handle_private_message(message)
                        
            except websockets.exceptions.ConnectionClosed:
                logger.warning("🔌 Private WebSocket disconnected, reconnecting...")
                self.authenticated = False
                await asyncio.sleep(self.reconnect_interval)
            except Exception as e:
                logger.error(f"❌ Private WebSocket error: {e}")
                self.authenticated = False
                await asyncio.sleep(self.reconnect_interval)

    async def _send_public_subscriptions(self, websocket):
        """Send public subscription requests"""
        public_subs = []
        
        for topic, sub_type in self.subscriptions.items():
            if sub_type in [SubscriptionType.TICKER, SubscriptionType.TRADE, SubscriptionType.KLINE]:
                public_subs.append(topic)
        
        if public_subs:
            subscribe_message = {
                "op": "subscribe",
                "args": public_subs
            }
            await websocket.send(json.dumps(subscribe_message))
            logger.info(f"📡 Subscribed to public topics: {public_subs}")

    async def _send_private_subscriptions(self, websocket):
        """Send private subscription requests"""
        private_subs = []
        
        for topic, sub_type in self.subscriptions.items():
            if sub_type in [SubscriptionType.ORDER, SubscriptionType.POSITION, 
                          SubscriptionType.EXECUTION, SubscriptionType.WALLET]:
                private_subs.append(topic)
        
        if private_subs:
            subscribe_message = {
                "op": "subscribe",
                "args": private_subs
            }
            await websocket.send(json.dumps(subscribe_message))
            logger.info(f"🔒 Subscribed to private topics: {private_subs}")

    # Public API Methods
    def subscribe_ticker(self, symbol: str, callback: Callable = None):
        """Subscribe to ticker updates for a symbol"""
        topic = f"tickers.{symbol}"
        self.subscriptions[topic] = SubscriptionType.TICKER
        
        if callback:
            self.callbacks[SubscriptionType.TICKER].append(callback)
            
        logger.info(f"📊 Subscribed to ticker: {symbol}")

    def subscribe_trades(self, symbol: str, callback: Callable = None):
        """Subscribe to public trades for a symbol"""
        topic = f"publicTrade.{symbol}"
        self.subscriptions[topic] = SubscriptionType.TRADE
        
        if callback:
            self.callbacks[SubscriptionType.TRADE].append(callback)
            
        logger.info(f"💱 Subscribed to trades: {symbol}")

    def subscribe_orders(self, callback: Callable = None):
        """Subscribe to order updates"""
        if not self.api_key:
            logger.warning("🔒 API key required for order subscription")
            return
            
        topic = "order"
        self.subscriptions[topic] = SubscriptionType.ORDER
        
        if callback:
            self.callbacks[SubscriptionType.ORDER].append(callback)
            
        logger.info("📋 Subscribed to order updates")

    def subscribe_positions(self, callback: Callable = None):
        """Subscribe to position updates"""
        if not self.api_key:
            logger.warning("🔒 API key required for position subscription")
            return
            
        topic = "position"
        self.subscriptions[topic] = SubscriptionType.POSITION
        
        if callback:
            self.callbacks[SubscriptionType.POSITION].append(callback)
            
        logger.info("📈 Subscribed to position updates")

    def subscribe_executions(self, callback: Callable = None):
        """Subscribe to execution/fill updates"""
        if not self.api_key:
            logger.warning("🔒 API key required for execution subscription")
            return
            
        topic = "execution"
        self.subscriptions[topic] = SubscriptionType.EXECUTION
        
        if callback:
            self.callbacks[SubscriptionType.EXECUTION].append(callback)
            
        logger.info("⚡ Subscribed to execution updates")

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a symbol"""
        return self.latest_prices.get(symbol)

    def get_latest_order(self, order_id: str) -> Optional[OrderUpdate]:
        """Get latest order update"""
        return self.latest_orders.get(order_id)

    def get_latest_position(self, symbol: str) -> Optional[PositionUpdate]:
        """Get latest position update"""
        return self.latest_positions.get(symbol)

    async def start(self):
        """Start WebSocket connections"""
        try:
            # Start both public and private connections
            tasks = [
                asyncio.create_task(self._public_connection_handler()),
            ]
            
            if self.api_key and self.api_secret:
                tasks.append(asyncio.create_task(self._private_connection_handler()))
            
            self.connected = True
            logger.info("🚀 WebSocket client started")
            
            # Run connections concurrently
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"❌ Error starting WebSocket client: {e}")
            raise

    async def stop(self):
        """Stop WebSocket connections"""
        self.connected = False
        
        if self.public_ws:
            await self.public_ws.close()
        if self.private_ws:
            await self.private_ws.close()
            
        logger.info("🛑 WebSocket client stopped")