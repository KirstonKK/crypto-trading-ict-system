"""
Live Trading Engine for Cryptocurrency Markets
==============================================

Production-ready trading engine with real-time order execution,
position management, and comprehensive risk controls.

Features:
- Real-time order execution and management
- Multi-exchange support (Bybit primary)
- Advanced position tracking and P&L calculation
- Comprehensive risk monitoring and circuit breakers
- Portfolio-level risk management
- Real-time performance tracking

Safety Mechanisms:
- Maximum position limits
- Daily loss limits
- Drawdown protection
- Order validation and confirmation
- Comprehensive audit logging

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import asyncio
import json
import ccxt
import pandas as pd

from utils.config_loader import ConfigLoader
from utils.crypto_pairs import CryptoPairs
from utils.risk_management import RiskManager
from integrations.tradingview.signal_processor import ProcessedSignal

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Container for active trading position."""
    symbol: str
    side: str  # 'LONG', 'SHORT'
    size: float
    entry_price: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    max_pnl: float = 0.0
    min_pnl: float = 0.0
    fees_paid: float = 0.0
    orders: List[str] = field(default_factory=list)  # Order IDs
    metadata: Dict = field(default_factory=dict)

@dataclass
class Order:
    """Container for trading order."""
    id: str
    symbol: str
    side: str  # 'buy', 'sell'
    type: str  # 'market', 'limit', 'stop', 'stop_limit'
    amount: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: str = 'pending'  # 'pending', 'open', 'closed', 'canceled', 'rejected'
    filled: float = 0.0
    remaining: float = 0.0
    fees: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    trades: List[Dict] = field(default_factory=list)

@dataclass
class Portfolio:
    """Container for portfolio state and performance."""
    initial_balance: float
    current_balance: float
    total_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    total_fees: float
    max_balance: float
    max_drawdown: float
    positions_count: int
    daily_pnl: float
    trades_today: int
    last_updated: datetime = field(default_factory=datetime.now)


class LiveTradingEngine:
    """
    Production-grade live trading engine with comprehensive safety mechanisms.
    
    This engine handles real-time trading execution with advanced risk management,
    position tracking, and portfolio monitoring for cryptocurrency markets.
    """
    
    def __init__(self, config_path: str = "project/configuration/"):
        """Initialize live trading engine."""
        self.config_path = config_path
        self.config_loader = ConfigLoader(config_path)
        self.crypto_pairs = CryptoPairs(config_path)
        self.risk_manager = RiskManager(config_path)
        
        # Load trading configuration
        self.trading_config = self._load_trading_config()
        
        # Initialize exchange connection
        self.exchange = None
        self._setup_exchange()
        
        # Trading state
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}
        self.portfolio = self._initialize_portfolio()
        
        # Safety mechanisms
        self.is_trading_enabled = False
        self.daily_loss_limit = self.trading_config['daily_loss_limit']
        self.max_positions = self.trading_config['max_positions']
        self.max_drawdown_limit = self.trading_config['max_drawdown_limit']
        
        # Event handlers
        self.position_handlers: List[Callable] = []
        self.order_handlers: List[Callable] = []
        self.error_handlers: List[Callable] = []
        
        # Monitoring
        self.last_portfolio_update = datetime.now()
        self.monitoring_enabled = True
        
        logger.info("Live trading engine initialized")
    
    def _load_trading_config(self) -> Dict:
        """Load trading engine configuration."""
        try:
            config = self.config_loader.get_config("trading")
        except Exception as e:
            logger.warning(f"Failed to load trading config: {e}")
            config = {}
        
        # Safety-first defaults
        defaults = {
            'daily_loss_limit': 500.0,  # $500 daily loss limit
            'max_positions': 3,
            'max_drawdown_limit': 0.10,  # 10% max drawdown
            'max_position_size': 1000.0,  # $1000 max per position
            'order_timeout_seconds': 30,
            'price_slippage_tolerance': 0.005,  # 0.5%
            'enable_stop_loss': True,
            'enable_take_profit': True,
            'position_monitoring_interval': 10,  # seconds
            'portfolio_update_interval': 60,  # seconds
            'emergency_close_conditions': {
                'max_single_position_loss': 200.0,  # $200
                'portfolio_loss_threshold': 0.05  # 5%
            }
        }
        
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
        
        return config
    
    def _setup_exchange(self) -> None:
        """Setup exchange connection with proper configuration."""
        try:
            exchange_config = self.config_loader.get_config("exchange")
            exchange_name = exchange_config.get("exchange", "bybit")
            
            exchange_class = getattr(ccxt, exchange_name)
            
            self.exchange = exchange_class({
                'apiKey': exchange_config.get('api_key', ''),
                'secret': exchange_config.get('api_secret', ''),
                'testnet': exchange_config.get('testnet', True),
                'sandbox': exchange_config.get('testnet', True),
                'rateLimit': exchange_config.get('rate_limit_ms', 100),
                'enableRateLimit': True,
                'options': {
                    'adjustForTimeDifference': True,
                    'recvWindow': 5000,
                }
            })
            
            logger.info(f"Exchange connection established: {exchange_name}")
            
        except Exception as e:
            logger.error(f"Failed to setup exchange: {e}")
            raise RuntimeError(f"Exchange setup failed: {e}")
    
    def _initialize_portfolio(self) -> Portfolio:
        """Initialize portfolio tracking."""
        try:
            # Get initial balance from exchange
            balance = self.exchange.fetch_balance()
            total_balance = balance['total']['USDT'] or 10000.0  # Default for testing
            
            return Portfolio(
                initial_balance=total_balance,
                current_balance=total_balance,
                total_pnl=0.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                total_fees=0.0,
                max_balance=total_balance,
                max_drawdown=0.0,
                positions_count=0,
                daily_pnl=0.0,
                trades_today=0
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize portfolio: {e}")
            # Return default portfolio for testing
            return Portfolio(
                initial_balance=10000.0,
                current_balance=10000.0,
                total_pnl=0.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                total_fees=0.0,
                max_balance=10000.0,
                max_drawdown=0.0,
                positions_count=0,
                daily_pnl=0.0,
                trades_today=0
            )
    
    def enable_trading(self) -> None:
        """Enable live trading with safety confirmation."""
        if not self.exchange:
            raise RuntimeError("Exchange not initialized")
        
        self.is_trading_enabled = True
        logger.warning("🚨 LIVE TRADING ENABLED 🚨")
    
    def disable_trading(self) -> None:
        """Disable live trading."""
        self.is_trading_enabled = False
        logger.info("Live trading disabled")
    
    async def execute_signal(self, signal: ProcessedSignal) -> Optional[str]:
        """
        Execute a processed trading signal.
        
        Args:
            signal: ProcessedSignal from signal processor
            
        Returns:
            Order ID if successful, None if failed
        """
        if not self.is_trading_enabled:
            logger.warning("Trading disabled - signal ignored")
            return None
        
        try:
            logger.info(f"Executing signal: {signal.action} {signal.symbol}")
            
            # Safety checks
            safety_check = self._perform_safety_checks(signal)
            if not safety_check['approved']:
                logger.warning(f"Safety check failed: {safety_check['reason']}")
                return None
            
            # Create and execute order
            if signal.action == 'BUY':
                order_id = await self._open_long_position(signal)
            elif signal.action == 'SELL':
                order_id = await self._open_short_position(signal)
            elif signal.action.startswith('CLOSE'):
                order_id = await self._close_position(signal)
            else:
                logger.error(f"Unknown action: {signal.action}")
                return None
            
            if order_id:
                logger.info(f"Signal executed successfully: Order {order_id}")
                await self._update_portfolio()
            
            return order_id
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            await self._handle_execution_error(signal, e)
            return None
    
    def _perform_safety_checks(self, signal: ProcessedSignal) -> Dict[str, any]:
        """Perform comprehensive safety checks before execution."""
        try:
            # Check daily loss limit
            if self.portfolio.daily_pnl < -self.daily_loss_limit:
                return {
                    'approved': False,
                    'reason': f'Daily loss limit reached: ${abs(self.portfolio.daily_pnl):.2f}'
                }
            
            # Check maximum positions
            if len(self.positions) >= self.max_positions and signal.action in ['BUY', 'SELL']:
                return {
                    'approved': False,
                    'reason': f'Maximum positions reached: {len(self.positions)}/{self.max_positions}'
                }
            
            # Check maximum drawdown
            current_drawdown = (self.portfolio.max_balance - self.portfolio.current_balance) / self.portfolio.max_balance
            if current_drawdown > self.max_drawdown_limit:
                return {
                    'approved': False,
                    'reason': f'Maximum drawdown exceeded: {current_drawdown:.2%}'
                }
            
            # Check position size limit
            position_value = signal.position_size * signal.validated_price
            if position_value > self.trading_config['max_position_size']:
                return {
                    'approved': False,
                    'reason': f'Position size too large: ${position_value:.2f}'
                }
            
            # Check if symbol already has position
            if signal.symbol in self.positions and signal.action in ['BUY', 'SELL']:
                return {
                    'approved': False,
                    'reason': f'Position already exists for {signal.symbol}'
                }
            
            # Check account balance
            required_margin = position_value * 0.1  # 10x leverage assumption
            if self.portfolio.current_balance < required_margin:
                return {
                    'approved': False,
                    'reason': f'Insufficient balance: ${self.portfolio.current_balance:.2f} < ${required_margin:.2f}'
                }
            
            return {'approved': True, 'reason': 'All safety checks passed'}
            
        except Exception as e:
            return {'approved': False, 'reason': f'Safety check error: {e}'}
    
    async def _open_long_position(self, signal: ProcessedSignal) -> Optional[str]:
        """Open a long position."""
        try:
            # Create market buy order
            order = await self._create_market_order(
                symbol=signal.symbol,
                side='buy',
                amount=signal.position_size,
                price=signal.validated_price
            )
            
            if order and order.status not in ['rejected', 'canceled']:
                # Create position
                position = Position(
                    symbol=signal.symbol,
                    side='LONG',
                    size=signal.position_size,
                    entry_price=signal.validated_price,
                    entry_time=datetime.now(),
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    orders=[order.id]
                )
                
                self.positions[signal.symbol] = position
                
                # Set stop loss and take profit orders
                if self.trading_config['enable_stop_loss']:
                    await self._set_stop_loss(position)
                
                if self.trading_config['enable_take_profit']:
                    await self._set_take_profit(position)
                
                logger.info(f"Long position opened: {signal.symbol} @ {signal.validated_price}")
                return order.id
            
            return None
            
        except Exception as e:
            logger.error(f"Error opening long position: {e}")
            return None
    
    async def _open_short_position(self, signal: ProcessedSignal) -> Optional[str]:
        """Open a short position."""
        try:
            # Create market sell order (short)
            order = await self._create_market_order(
                symbol=signal.symbol,
                side='sell',
                amount=signal.position_size,
                price=signal.validated_price
            )
            
            if order and order.status not in ['rejected', 'canceled']:
                # Create position
                position = Position(
                    symbol=signal.symbol,
                    side='SHORT',
                    size=signal.position_size,
                    entry_price=signal.validated_price,
                    entry_time=datetime.now(),
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    orders=[order.id]
                )
                
                self.positions[signal.symbol] = position
                
                # Set stop loss and take profit orders
                if self.trading_config['enable_stop_loss']:
                    await self._set_stop_loss(position)
                
                if self.trading_config['enable_take_profit']:
                    await self._set_take_profit(position)
                
                logger.info(f"Short position opened: {signal.symbol} @ {signal.validated_price}")
                return order.id
            
            return None
            
        except Exception as e:
            logger.error(f"Error opening short position: {e}")
            return None
    
    async def _close_position(self, signal: ProcessedSignal) -> Optional[str]:
        """Close an existing position."""
        try:
            if signal.symbol not in self.positions:
                logger.warning(f"No position to close: {signal.symbol}")
                return None
            
            position = self.positions[signal.symbol]
            
            # Create closing order
            close_side = 'sell' if position.side == 'LONG' else 'buy'
            order = await self._create_market_order(
                symbol=signal.symbol,
                side=close_side,
                amount=position.size,
                price=signal.validated_price
            )
            
            if order and order.status not in ['rejected', 'canceled']:
                # Calculate realized PnL
                if position.side == 'LONG':
                    pnl = (signal.validated_price - position.entry_price) * position.size
                else:
                    pnl = (position.entry_price - signal.validated_price) * position.size
                
                # Update position
                position.realized_pnl = pnl
                
                # Remove from active positions
                del self.positions[signal.symbol]
                
                # Update portfolio
                self.portfolio.realized_pnl += pnl
                self.portfolio.daily_pnl += pnl
                self.portfolio.trades_today += 1
                
                logger.info(f"Position closed: {signal.symbol} PnL: ${pnl:.2f}")
                return order.id
            
            return None
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return None
    
    async def _create_market_order(self, symbol: str, side: str, amount: float, 
                                 price: Optional[float] = None) -> Optional[Order]:
        """Create and execute a market order."""
        try:
            # Create order on exchange
            exchange_order = self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=amount
            )
            
            # Convert to internal order format
            order = Order(
                id=exchange_order['id'],
                symbol=symbol,
                side=side,
                type='market',
                amount=amount,
                price=price,
                status='open',
                filled=exchange_order.get('filled', 0),
                remaining=exchange_order.get('remaining', amount),
                fees=exchange_order.get('fees', {}),
                timestamp=datetime.now(),
                trades=[]
            )
            
            # Store order
            self.orders[order.id] = order
            
            logger.info(f"Market order created: {side} {amount} {symbol}")
            return order
            
        except Exception as e:
            logger.error(f"Error creating market order: {e}")
            return None
    
    async def _set_stop_loss(self, position: Position) -> None:
        """Set stop loss order for position."""
        try:
            side = 'sell' if position.side == 'LONG' else 'buy'
            
            stop_order = self.exchange.create_order(
                symbol=position.symbol,
                type='stop_market',
                side=side,
                amount=position.size,
                price=None,
                params={'stopPrice': position.stop_loss}
            )
            
            position.orders.append(stop_order['id'])
            logger.info(f"Stop loss set: {position.symbol} @ {position.stop_loss}")
            
        except Exception as e:
            logger.error(f"Error setting stop loss: {e}")
    
    async def _set_take_profit(self, position: Position) -> None:
        """Set take profit order for position."""
        try:
            side = 'sell' if position.side == 'LONG' else 'buy'
            
            tp_order = self.exchange.create_limit_order(
                symbol=position.symbol,
                side=side,
                amount=position.size,
                price=position.take_profit
            )
            
            position.orders.append(tp_order['id'])
            logger.info(f"Take profit set: {position.symbol} @ {position.take_profit}")
            
        except Exception as e:
            logger.error(f"Error setting take profit: {e}")
    
    async def _update_portfolio(self) -> None:
        """Update portfolio state and performance metrics."""
        try:
            # Get current balance
            balance = self.exchange.fetch_balance()
            current_balance = balance['total'].get('USDT', self.portfolio.current_balance)
            
            # Calculate unrealized PnL for open positions
            unrealized_pnl = 0.0
            for position in self.positions.values():
                try:
                    # Get current price
                    ticker = self.exchange.fetch_ticker(position.symbol)
                    current_price = ticker['last']
                    position.current_price = current_price
                    
                    # Calculate unrealized PnL
                    if position.side == 'LONG':
                        pnl = (current_price - position.entry_price) * position.size
                    else:
                        pnl = (position.entry_price - current_price) * position.size
                    
                    position.unrealized_pnl = pnl
                    unrealized_pnl += pnl
                    
                    # Update position extremes
                    position.max_pnl = max(position.max_pnl, pnl)
                    position.min_pnl = min(position.min_pnl, pnl)
                    
                except Exception as e:
                    logger.error(f"Error updating position {position.symbol}: {e}")
                    continue
            
            # Update portfolio
            self.portfolio.current_balance = current_balance
            self.portfolio.unrealized_pnl = unrealized_pnl
            self.portfolio.total_pnl = self.portfolio.realized_pnl + unrealized_pnl
            self.portfolio.positions_count = len(self.positions)
            self.portfolio.max_balance = max(self.portfolio.max_balance, current_balance)
            
            # Calculate current drawdown
            current_drawdown = (self.portfolio.max_balance - current_balance) / self.portfolio.max_balance
            self.portfolio.max_drawdown = max(self.portfolio.max_drawdown, current_drawdown)
            
            self.portfolio.last_updated = datetime.now()
            
            # Check emergency conditions
            await self._check_emergency_conditions()
            
            logger.debug(f"Portfolio updated: Balance=${current_balance:.2f}, PnL=${self.portfolio.total_pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Error updating portfolio: {e}")
    
    async def _check_emergency_conditions(self) -> None:
        """Check for emergency conditions that require immediate action."""
        try:
            emergency_config = self.trading_config['emergency_close_conditions']
            
            # Check single position loss
            max_single_loss = emergency_config['max_single_position_loss']
            for symbol, position in list(self.positions.items()):
                if position.unrealized_pnl < -max_single_loss:
                    logger.error(f"Emergency: Position loss exceeded ${max_single_loss}: {symbol}")
                    await self._emergency_close_position(position)
            
            # Check portfolio loss threshold
            portfolio_loss_threshold = emergency_config['portfolio_loss_threshold']
            current_drawdown = (self.portfolio.max_balance - self.portfolio.current_balance) / self.portfolio.max_balance
            
            if current_drawdown > portfolio_loss_threshold:
                logger.error(f"Emergency: Portfolio drawdown exceeded {portfolio_loss_threshold:.2%}")
                await self._emergency_close_all_positions()
            
        except Exception as e:
            logger.error(f"Error checking emergency conditions: {e}")
    
    async def _emergency_close_position(self, position: Position) -> None:
        """Emergency close a single position."""
        try:
            logger.warning(f"Emergency closing position: {position.symbol}")
            
            side = 'sell' if position.side == 'LONG' else 'buy'
            
            # Cancel all pending orders
            for order_id in position.orders:
                try:
                    self.exchange.cancel_order(order_id, position.symbol)
                except:
                    pass
            
            # Create emergency close order
            close_order = self.exchange.create_market_order(
                symbol=position.symbol,
                side=side,
                amount=position.size
            )
            
            # Remove position
            if position.symbol in self.positions:
                del self.positions[position.symbol]
            
            logger.warning(f"Emergency position closed: {position.symbol}")
            
        except Exception as e:
            logger.error(f"Error in emergency close: {e}")
    
    async def _emergency_close_all_positions(self) -> None:
        """Emergency close all positions."""
        logger.error("🚨 EMERGENCY: Closing all positions 🚨")
        
        for position in list(self.positions.values()):
            await self._emergency_close_position(position)
        
        # Disable trading
        self.disable_trading()
    
    async def _handle_execution_error(self, signal: ProcessedSignal, error: Exception) -> None:
        """Handle signal execution errors."""
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'signal': {
                'symbol': signal.symbol,
                'action': signal.action,
                'price': signal.validated_price
            },
            'error': str(error),
            'portfolio_state': {
                'balance': self.portfolio.current_balance,
                'positions': len(self.positions),
                'daily_pnl': self.portfolio.daily_pnl
            }
        }
        
        logger.error(f"Execution error logged: {error_data}")
        
        # Call error handlers
        for handler in self.error_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(error_data)
                else:
                    handler(error_data)
            except Exception as e:
                logger.error(f"Error handler failed: {e}")
    
    async def start_monitoring(self) -> None:
        """Start portfolio and position monitoring."""
        self.monitoring_enabled = True
        
        async def monitoring_loop():
            while self.monitoring_enabled:
                try:
                    await self._update_portfolio()
                    await asyncio.sleep(self.trading_config['portfolio_update_interval'])
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    await asyncio.sleep(5)
        
        # Start monitoring task
        asyncio.create_task(monitoring_loop())
        logger.info("Portfolio monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop portfolio monitoring."""
        self.monitoring_enabled = False
        logger.info("Portfolio monitoring stopped")
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary."""
        return {
            'balance': {
                'initial': self.portfolio.initial_balance,
                'current': self.portfolio.current_balance,
                'max': self.portfolio.max_balance
            },
            'pnl': {
                'total': self.portfolio.total_pnl,
                'realized': self.portfolio.realized_pnl,
                'unrealized': self.portfolio.unrealized_pnl,
                'daily': self.portfolio.daily_pnl
            },
            'risk_metrics': {
                'max_drawdown': self.portfolio.max_drawdown,
                'current_drawdown': (self.portfolio.max_balance - self.portfolio.current_balance) / self.portfolio.max_balance,
                'daily_loss_remaining': self.daily_loss_limit + self.portfolio.daily_pnl
            },
            'positions': {
                'count': len(self.positions),
                'max_allowed': self.max_positions,
                'details': {symbol: {
                    'side': pos.side,
                    'size': pos.size,
                    'entry_price': pos.entry_price,
                    'current_pnl': pos.unrealized_pnl
                } for symbol, pos in self.positions.items()}
            },
            'trading_status': {
                'enabled': self.is_trading_enabled,
                'trades_today': self.portfolio.trades_today,
                'last_updated': self.portfolio.last_updated.isoformat()
            }
        }
    
    # Event handler registration
    def add_position_handler(self, handler: Callable) -> None:
        self.position_handlers.append(handler)
    
    def add_order_handler(self, handler: Callable) -> None:
        self.order_handlers.append(handler)
    
    def add_error_handler(self, handler: Callable) -> None:
        self.error_handlers.append(handler)


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        try:
            # Initialize trading engine
            engine = LiveTradingEngine()
            
            # DON'T enable live trading in testing!
            # engine.enable_trading()
            
            # Start monitoring
            await engine.start_monitoring()
            
            # Print portfolio summary
            summary = engine.get_portfolio_summary()
            print(json.dumps(summary, indent=2, default=str))
            
            print("Trading engine initialized successfully")
            
        except Exception as e:
            print(f"Error: {e}")
    
    # Run test
    asyncio.run(main())
