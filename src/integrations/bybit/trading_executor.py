"""
Bybit Trading Executor
=====================

Integrates ICT Enhanced Trading Monitor signals with Bybit demo trading.
Executes trades based on signals while managing risk and position limits.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from enum import Enum

from .bybit_client import BybitDemoClient, format_bybit_symbol, calculate_quantity_precision

logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"

class PositionSide(Enum):
    """Position side enumeration"""
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"

@dataclass
class TradingSignal:
    """Trading signal from ICT Enhanced Monitor"""
    symbol: str
    action: str  # "BUY" or "SELL"
    confidence: float
    price: float
    timestamp: datetime
    confluence_factors: List[str]
    
    # Risk management
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None
    
    # Signal metadata
    signal_id: str = None
    session_multiplier: float = 1.0
    market_session: str = "Unknown"

@dataclass
class TradeExecution:
    """Trade execution record"""
    signal_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    order_id: str
    status: OrderStatus
    timestamp: datetime
    
    # Optional fields
    exit_price: Optional[float] = None
    exit_order_id: Optional[str] = None
    exit_timestamp: Optional[datetime] = None
    pnl: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class BybitTradingExecutor:
    """
    Executes ICT trading signals on Bybit demo environment
    
    Features:
    - Signal validation and filtering
    - Position size calculation
    - Risk management
    - Order execution and monitoring
    - Performance tracking
    """
    
    def __init__(self, 
                 bybit_client: BybitDemoClient,
                 max_positions: int = 3,
                 max_risk_per_trade: float = 0.02,  # 2% per trade
                 max_portfolio_risk: float = 0.05,   # 5% total portfolio
                 min_confidence: float = 0.6):       # 60% minimum confidence
        """
        Initialize trading executor
        
        Args:
            bybit_client: Configured Bybit API client
            max_positions: Maximum concurrent positions
            max_risk_per_trade: Maximum risk per individual trade
            max_portfolio_risk: Maximum total portfolio risk
            min_confidence: Minimum signal confidence to trade
        """
        self.client = bybit_client
        self.max_positions = max_positions
        self.max_risk_per_trade = max_risk_per_trade
        self.max_portfolio_risk = max_portfolio_risk
        self.min_confidence = min_confidence
        
        # Trading state
        self.active_trades: Dict[str, TradeExecution] = {}
        self.signal_history: List[TradingSignal] = []
        self.execution_history: List[TradeExecution] = []
        
        # Risk tracking
        self.portfolio_value: float = 0.0
        self.current_portfolio_risk: float = 0.0
        
        # Performance metrics
        self.total_trades: int = 0
        self.winning_trades: int = 0
        self.total_pnl: float = 0.0
        
        logger.info("🤖 Bybit Trading Executor initialized")
        logger.info(f"   Max Positions: {max_positions}")
        logger.info(f"   Max Risk/Trade: {max_risk_per_trade*100:.1f}%")
        logger.info(f"   Max Portfolio Risk: {max_portfolio_risk*100:.1f}%")
        logger.info(f"   Min Confidence: {min_confidence*100:.1f}%")

    async def initialize(self):
        """Initialize executor by updating portfolio state"""
        try:
            await self._update_portfolio_state()
            await self._sync_positions()
            logger.info("✅ Trading executor initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize executor: {e}")
            raise

    async def _update_portfolio_state(self):
        """Update current portfolio value and risk"""
        try:
            balances = await self.client.get_balance()
            self.portfolio_value = balances.get('USDT', 0.0)
            
            # Calculate current risk from active positions
            positions = await self.client.get_positions()
            total_risk = 0.0
            
            for position in positions:
                size = float(position.get('size', 0))
                if size > 0:
                    entry_price = float(position.get('avgPrice', 0))
                    current_value = size * entry_price
                    # Estimate risk as percentage of portfolio
                    risk = (current_value / self.portfolio_value) if self.portfolio_value > 0 else 0
                    total_risk += risk
            
            self.current_portfolio_risk = total_risk
            
            logger.debug(f"📊 Portfolio: ${self.portfolio_value:.2f}, Risk: {total_risk*100:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ Failed to update portfolio state: {e}")

    async def _sync_positions(self):
        """Sync active trades with current Bybit positions"""
        try:
            positions = await self.client.get_positions()
            
            # Clear trades that no longer have positions
            active_symbols = {pos.get('symbol') for pos in positions if float(pos.get('size', 0)) > 0}
            
            trades_to_remove = []
            for trade_id, trade in self.active_trades.items():
                if trade.symbol not in active_symbols:
                    # Position was closed outside our system
                    trade.status = OrderStatus.FILLED
                    trades_to_remove.append(trade_id)
            
            for trade_id in trades_to_remove:
                closed_trade = self.active_trades.pop(trade_id)
                self.execution_history.append(closed_trade)
                logger.info(f"🔄 Synced closed position: {closed_trade.symbol}")
                
        except Exception as e:
            logger.error(f"❌ Failed to sync positions: {e}")

    def validate_signal(self, signal: TradingSignal) -> tuple[bool, str]:
        """
        Validate if signal should be traded
        
        Args:
            signal: Trading signal to validate
            
        Returns:
            (is_valid, reason)
        """
        # Check confidence threshold
        if signal.confidence < self.min_confidence:
            return False, f"Confidence {signal.confidence:.1%} below threshold {self.min_confidence:.1%}"
        
        # Check if we already have position in this symbol
        for trade in self.active_trades.values():
            if trade.symbol == signal.symbol and trade.status == OrderStatus.PENDING:
                return False, f"Already have active trade in {signal.symbol}"
        
        # Check maximum positions
        active_count = len([t for t in self.active_trades.values() if t.status == OrderStatus.PENDING])
        if active_count >= self.max_positions:
            return False, f"Maximum positions reached ({self.max_positions})"
        
        # Check portfolio risk
        if self.current_portfolio_risk >= self.max_portfolio_risk:
            return False, f"Portfolio risk limit reached ({self.max_portfolio_risk:.1%})"
        
        # Check if symbol is supported
        bybit_symbol = format_bybit_symbol(signal.symbol)
        if not bybit_symbol:
            return False, f"Symbol {signal.symbol} not supported"
        
        return True, "Signal validated"

    def calculate_position_size(self, signal: TradingSignal, current_price: float) -> float:
        """
        Calculate appropriate position size based on risk management
        
        Args:
            signal: Trading signal
            current_price: Current market price
            
        Returns:
            Position size in base currency
        """
        if self.portfolio_value <= 0:
            return 0.0
        
        # Calculate risk amount
        risk_amount = self.portfolio_value * self.max_risk_per_trade
        
        # Adjust by confidence (higher confidence = larger size)
        confidence_multiplier = 0.5 + (signal.confidence * 0.5)  # 0.5 to 1.0 range
        adjusted_risk = risk_amount * confidence_multiplier
        
        # Calculate position size based on stop loss distance
        if signal.stop_loss:
            price_diff = abs(current_price - signal.stop_loss)
            if price_diff > 0:
                # Position size = Risk Amount / Price Distance
                position_value = adjusted_risk / (price_diff / current_price)
                position_size = position_value / current_price
            else:
                position_size = adjusted_risk / current_price
        else:
            # Default to 2% price movement as stop loss
            default_stop_distance = current_price * 0.02
            position_value = adjusted_risk / 0.02
            position_size = position_value / current_price
        
        # Apply quantity precision
        bybit_symbol = format_bybit_symbol(signal.symbol)
        position_size = calculate_quantity_precision(bybit_symbol, position_size)
        
        # Ensure minimum trade size
        min_trade_value = 10.0  # $10 minimum
        min_size = min_trade_value / current_price
        position_size = max(position_size, min_size)
        
        logger.debug(f"💰 Position size for {signal.symbol}: {position_size:.6f}")
        return position_size

    async def execute_signal(self, signal: TradingSignal) -> Optional[TradeExecution]:
        """
        Execute trading signal on Bybit
        
        Args:
            signal: Validated trading signal
            
        Returns:
            Trade execution record if successful
        """
        try:
            # Validate signal
            is_valid, reason = self.validate_signal(signal)
            if not is_valid:
                logger.warning(f"🚫 Signal rejected: {reason}")
                return None
            
            # Get current market price
            bybit_symbol = format_bybit_symbol(signal.symbol)
            ticker = await self.client.get_ticker(bybit_symbol)
            current_price = float(ticker.get('lastPrice', signal.price))
            
            # Calculate position size
            position_size = self.calculate_position_size(signal, current_price)
            if position_size <= 0:
                logger.warning(f"🚫 Invalid position size for {signal.symbol}")
                return None
            
            # Determine order side
            side = "Buy" if signal.action.upper() == "BUY" else "Sell"
            
            # Place order
            order_result = await self.client.place_order(
                symbol=bybit_symbol,
                side=side,
                qty=position_size,
                order_type="Market",
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit
            )
            
            # Create trade execution record
            trade_execution = TradeExecution(
                signal_id=signal.signal_id or f"{signal.symbol}_{int(signal.timestamp.timestamp())}",
                symbol=bybit_symbol,
                side=side,
                quantity=position_size,
                entry_price=current_price,
                order_id=order_result.get('orderId'),
                status=OrderStatus.PENDING,
                timestamp=datetime.now(),
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit
            )
            
            # Store active trade
            self.active_trades[trade_execution.signal_id] = trade_execution
            
            # Update statistics
            self.total_trades += 1
            
            logger.info(f"🚀 Trade executed: {bybit_symbol} {side} {position_size:.6f} @ ${current_price:.4f}")
            logger.info(f"   Order ID: {trade_execution.order_id}")
            logger.info(f"   Confidence: {signal.confidence:.1%}")
            logger.info(f"   Confluences: {', '.join(signal.confluence_factors)}")
            
            # Update portfolio state
            await self._update_portfolio_state()
            
            return trade_execution
            
        except Exception as e:
            logger.error(f"❌ Failed to execute signal: {e}")
            return None

    async def monitor_trades(self):
        """Monitor active trades and update their status"""
        try:
            if not self.active_trades:
                return
            
            for trade_id, trade in list(self.active_trades.items()):
                if trade.status != OrderStatus.PENDING:
                    continue
                
                # Check order status
                orders = await self.client.get_orders(trade.symbol)
                current_order = None
                
                for order in orders:
                    if order.get('orderId') == trade.order_id:
                        current_order = order
                        break
                
                if current_order:
                    order_status = current_order.get('orderStatus', '')
                    
                    if order_status == 'Filled':
                        # Order filled
                        trade.status = OrderStatus.FILLED
                        trade.entry_price = float(current_order.get('avgPrice', trade.entry_price))
                        
                        logger.info(f"✅ Trade filled: {trade.symbol} @ ${trade.entry_price:.4f}")
                        
                    elif order_status in ['Cancelled', 'Rejected']:
                        # Order cancelled/rejected
                        trade.status = OrderStatus.CANCELLED
                        self.active_trades.pop(trade_id)
                        self.execution_history.append(trade)
                        
                        logger.warning(f"❌ Trade cancelled: {trade.symbol}")
                
                # Check for position closure
                positions = await self.client.get_positions(trade.symbol)
                has_position = any(float(pos.get('size', 0)) > 0 for pos in positions)
                
                if trade.status == OrderStatus.FILLED and not has_position:
                    # Position was closed
                    await self._close_trade(trade_id)
                    
        except Exception as e:
            logger.error(f"❌ Error monitoring trades: {e}")

    async def _close_trade(self, trade_id: str):
        """Close a trade and calculate PnL"""
        try:
            trade = self.active_trades.get(trade_id)
            if not trade:
                return
            
            # Get current price for PnL calculation
            ticker = await self.client.get_ticker(trade.symbol)
            exit_price = float(ticker.get('lastPrice', trade.entry_price))
            
            # Calculate PnL
            if trade.side == "Buy":
                pnl = (exit_price - trade.entry_price) * trade.quantity
            else:
                pnl = (trade.entry_price - exit_price) * trade.quantity
            
            trade.exit_price = exit_price
            trade.exit_timestamp = datetime.now()
            trade.pnl = pnl
            trade.status = OrderStatus.FILLED
            
            # Update statistics
            self.total_pnl += pnl
            if pnl > 0:
                self.winning_trades += 1
            
            # Move to history
            self.active_trades.pop(trade_id)
            self.execution_history.append(trade)
            
            logger.info(f"🏁 Trade closed: {trade.symbol}")
            logger.info(f"   Entry: ${trade.entry_price:.4f} | Exit: ${exit_price:.4f}")
            logger.info(f"   PnL: ${pnl:.2f} ({'✅' if pnl > 0 else '❌'})")
            
        except Exception as e:
            logger.error(f"❌ Error closing trade: {e}")

    async def close_all_positions(self):
        """Emergency close all positions"""
        try:
            positions = await self.client.get_positions()
            
            for position in positions:
                symbol = position.get('symbol')
                size = float(position.get('size', 0))
                
                if size > 0:
                    await self.client.close_position(symbol)
                    logger.info(f"🔒 Emergency close: {symbol}")
            
            # Clear active trades
            for trade_id in list(self.active_trades.keys()):
                await self._close_trade(trade_id)
                
        except Exception as e:
            logger.error(f"❌ Error closing all positions: {e}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get trading performance summary"""
        try:
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            avg_pnl = self.total_pnl / self.total_trades if self.total_trades > 0 else 0
            
            return {
                "total_trades": self.total_trades,
                "winning_trades": self.winning_trades,
                "win_rate": f"{win_rate:.1f}%",
                "total_pnl": f"${self.total_pnl:.2f}",
                "average_pnl": f"${avg_pnl:.2f}",
                "active_positions": len(self.active_trades),
                "portfolio_value": f"${self.portfolio_value:.2f}",
                "portfolio_risk": f"{self.current_portfolio_risk*100:.1f}%"
            }
        except Exception as e:
            logger.error(f"❌ Error generating performance summary: {e}")
            return {}

    async def process_ict_signal(self, signal_data: Dict) -> Optional[TradeExecution]:
        """
        Process signal from ICT Enhanced Monitor
        
        Args:
            signal_data: Signal data from ICT monitor
            
        Returns:
            Trade execution if processed successfully
        """
        try:
            # Convert signal data to TradingSignal object
            signal = TradingSignal(
                symbol=signal_data.get('symbol', ''),
                action=signal_data.get('action', ''),
                confidence=signal_data.get('confidence', 0.0),
                price=signal_data.get('price', 0.0),
                timestamp=datetime.fromisoformat(signal_data.get('timestamp', datetime.now().isoformat())),
                confluence_factors=signal_data.get('confluence_factors', []),
                stop_loss=signal_data.get('stop_loss'),
                take_profit=signal_data.get('take_profit'),
                position_size=signal_data.get('position_size'),
                signal_id=signal_data.get('signal_id'),
                session_multiplier=signal_data.get('session_multiplier', 1.0),
                market_session=signal_data.get('market_session', 'Unknown')
            )
            
            # Store signal in history
            self.signal_history.append(signal)
            
            # Execute if valid
            execution = await self.execute_signal(signal)
            
            return execution
            
        except Exception as e:
            logger.error(f"❌ Error processing ICT signal: {e}")
            return None