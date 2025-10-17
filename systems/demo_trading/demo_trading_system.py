#!/usr/bin/env python3
"""
ICT-Bybit Demo Trading System
============================

Complete demo trading system that integrates ICT Enhanced Trading Monitor
with Bybit testnet for paper trading validation and model training.

This system provides:
- Real-time Bybit price integration
- ICT signal execution on demo account
- Performance tracking and comparison
- ML model training data collection
- Risk management and safety controls

Usage:
    python demo_trading_system.py [options]
"""

import asyncio
import logging
import json
import sys
import argparse
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp

# Add the current directory to path
sys.path.append('/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm')

from bybit_integration.real_time_prices import BybitRealTimePrices
from bybit_integration.bybit_client import BybitDemoClient
from bybit_integration.config import load_config_from_env, validate_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('demo_trading_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class DemoTradingSystem:
    """
    Complete demo trading system for ICT-Bybit integration
    
    Features:
    - Real-time price monitoring
    - ICT signal processing
    - Demo trade execution
    - Performance tracking
    - Model training data collection
    """
    
    def __init__(self, 
                 symbols: List[str] = None,
                 auto_trading: bool = False,
                 dry_run: bool = False):
        """
        Initialize demo trading system
        
        Args:
            symbols: Trading symbols to monitor
            auto_trading: Enable automatic trade execution
            dry_run: Test mode without actual trades
        """
        self.symbols = symbols or ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT']
        self.auto_trading = auto_trading
        self.dry_run = dry_run
        self.running = False
        
        # Risk Management & Slippage Configuration
        self.slippage_tolerance = 0.001  # 0.1% slippage tolerance
        self.max_position_size_usd = 10000  # Max $10k per position
        self.risk_per_trade = 0.01  # 1% risk per trade
        self.min_balance_required = 1000  # Min $1k balance to trade
        
        # Leverage & Margin Configuration
        self.leverage = 10  # 10x leverage for demo trading
        self.margin_mode = "CROSS_MARGIN"  # Cross margin mode
        self.order_type = "Market"  # Default order type
        self.position_mode = "MergedSingle"  # Position mode
        
        # Advanced Order Configuration
        self.time_in_force = "IOC"  # Immediate or Cancel
        self.reduce_only = False  # Allow position increases
        self.close_on_trigger = False  # Keep positions open on trigger
        
        # System components
        self.price_monitor = None
        self.bybit_client = None
        self.ict_session = None
        self.demo_mode = False  # Flag for demo mode without API calls
        
        # Trading state
        self.active_positions = {}
        self.signal_history = []
        self.trade_history = []
        self.performance_data = {
            'demo_balance': 100000.0,  # Starting demo balance
            'paper_balance': 100.0,    # From ICT monitor
            'total_trades': 0,
            'winning_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'signals_received': 0,
            'signals_executed': 0
        }
        
        # Configuration
        self.config = None
        
        logger.info("🎮 Demo Trading System initialized")
        logger.info(f"   Symbols: {', '.join(self.symbols)}")
        logger.info(f"   Auto Trading: {'ON' if auto_trading else 'OFF'}")
        logger.info(f"   Dry Run: {'ON' if dry_run else 'OFF'}")

    async def initialize(self):
        """Initialize all system components"""
        try:
            logger.info("🔧 Initializing Demo Trading System...")
            
            # Load configuration from environment (using existing API keys)
            self.config = load_config_from_env()
            
            if not self.dry_run:
                is_valid, errors = validate_config(self.config)
                
                if not is_valid:
                    logger.error("❌ Configuration validation failed:")
                    for error in errors:
                        logger.error(f"   - {error}")
                    # For demo mode, continue with available config but mark as demo
                    logger.info("🎮 Continuing in demo mode with available configuration")
                    self.demo_mode = True
                else:
                    logger.info("✅ Configuration validated successfully")
                    self.demo_mode = False
            else:
                # In dry run mode, create minimal config
                logger.info("🧪 Dry run mode - using default configuration")
                from bybit_integration.config import BybitConfig, TradingConfig, ICTConfig, WebSocketConfig, IntegrationConfig
                
                self.config = IntegrationConfig(
                    bybit=BybitConfig(api_key="dry_run", api_secret="dry_run", testnet=True),
                    trading=TradingConfig(),
                    ict=ICTConfig(),
                    websocket=WebSocketConfig()
                )
                self.demo_mode = True
            
            # Initialize price monitor
            logger.info("📊 Starting real-time price monitoring...")
            self.price_monitor = BybitRealTimePrices(
                symbols=self.symbols,
                testnet=self.config.bybit.testnet if self.config else True
            )
            
            # Add price update callback
            self.price_monitor.add_price_callback(self._on_price_update)
            
            # Start price monitoring in background
            asyncio.create_task(self.price_monitor.start())
            
            # Wait for initial prices
            await asyncio.sleep(3)
            
            # Initialize Bybit client (if not dry run and not demo mode)
            if not self.dry_run and self.config and not self.demo_mode:
                logger.info("🏪 Initializing Bybit demo client...")
                # Use demo=True for Demo Mainnet (real prices, fake money)
                use_demo = getattr(self.config.bybit, 'demo', False)
                self.bybit_client = BybitDemoClient(
                    api_key=self.config.bybit.api_key,
                    api_secret=self.config.bybit.api_secret,
                    testnet=self.config.bybit.testnet,
                    demo=use_demo
                )
                
                # Test connection
                try:
                    connection_test = await self.bybit_client.test_connection()
                    if not connection_test:
                        logger.warning("⚠️  Bybit connection test failed, continuing in demo mode")
                        self.demo_mode = True
                        self.bybit_client = None
                    else:
                        # Setup leverage and margin mode for all symbols
                        await self._setup_leverage_and_margin()
                        logger.info("✅ Bybit demo client ready")
                except Exception as e:
                    logger.warning(f"⚠️  Bybit connection failed: {e}")
                    logger.info("🎮 Continuing in demo mode without API calls")
                    self.demo_mode = True
                    self.bybit_client = None
            else:
                logger.info("🎮 Running in demo mode - price monitoring only")
            
            # Initialize ICT monitor session with explicit connector
            connector = aiohttp.TCPConnector(
                ssl=False,
                enable_cleanup_closed=True
            )
            self.ict_session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=10)
            )
            
            # Test ICT monitor connection
            await self._test_ict_connection()
            
            logger.info("✅ Demo Trading System initialization complete")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            if not self.dry_run:
                raise

    async def _test_ict_connection(self):
        """Test ICT Enhanced Monitor connection"""
        try:
            async with self.ict_session.get("http://localhost:5001/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ ICT Monitor connected")
                    logger.info(f"   Status: {data.get('status', 'Unknown')}")
                    logger.info(f"   Signals Today: {data.get('signals_today', 0)}")
                    self.performance_data['paper_balance'] = data.get('paper_balance', 100.0)
                else:
                    raise Exception(f"ICT Monitor status: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ ICT Monitor connection failed: {e}")
            if not self.dry_run:
                raise

    async def _on_price_update(self, symbol: str, price_data: Dict, price_change: float):
        """Handle real-time price updates"""
        try:
            # Log significant price movements
            if abs(price_change) > 1.0:  # 1% or more
                direction = "📈" if price_change > 0 else "📉"
                logger.info(f"{direction} {symbol}: ${price_data['price']:,.4f} ({price_change:+.2f}%)")
            
            # Check for any position management needs
            await self._check_position_management(symbol, price_data)
            
        except Exception as e:
            logger.error(f"❌ Error handling price update: {e}")

    async def _check_position_management(self, symbol: str, price_data: Dict):
        """Check if any positions need management"""
        try:
            if symbol in self.active_positions:
                position = self.active_positions[symbol]
                current_price = price_data['price']
                entry_price = position['entry_price']
                
                # Calculate P&L
                if position['side'] == 'BUY':
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                else:
                    pnl_pct = ((entry_price - current_price) / entry_price) * 100
                
                position['current_pnl'] = pnl_pct
                position['current_price'] = current_price
                
                # Check stop loss
                if position.get('stop_loss'):
                    if (position['side'] == 'BUY' and current_price <= position['stop_loss']) or \
                       (position['side'] == 'SELL' and current_price >= position['stop_loss']):
                        await self._close_position(symbol, 'Stop Loss Hit')
                
                # Check take profit
                if position.get('take_profit'):
                    if (position['side'] == 'BUY' and current_price >= position['take_profit']) or \
                       (position['side'] == 'SELL' and current_price <= position['take_profit']):
                        await self._close_position(symbol, 'Take Profit Hit')
                        
        except Exception as e:
            logger.error(f"❌ Error checking position management: {e}")

    async def monitor_ict_signals(self):
        """Monitor ICT Enhanced Trading Monitor for new signals"""
        logger.info("📡 Starting ICT signal monitoring...")
        # Start from beginning of today to catch all signals from today
        last_check_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        while self.running:
            try:
                # Get latest signals from ICT monitor
                async with self.ict_session.get("http://localhost:5001/api/signals/latest") as response:
                    if response.status == 200:
                        data = await response.json()
                        # ICT monitor returns list directly, not dict with 'signals' key
                        signals = data if isinstance(data, list) else data.get('signals', [])
                        
                        # Process new signals
                        for signal in signals:
                            signal_time = datetime.fromisoformat(signal.get('entry_time', ''))
                            if signal_time > last_check_time:
                                await self._process_ict_signal(signal)
                        
                        last_check_time = datetime.now()
                
                # Update performance from ICT monitor
                await self._update_ict_performance()
                
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"❌ Error monitoring ICT signals: {e}")
                await asyncio.sleep(5)

    async def _process_ict_signal(self, signal: Dict[str, Any]):
        """Process a new ICT signal"""
        try:
            self.performance_data['signals_received'] += 1
            
            symbol = signal.get('symbol', '')
            action = signal.get('direction', '')  # ICT uses 'direction' not 'action'
            confidence = signal.get('confluence_score', 0)  # ICT uses 'confluence_score'
            price = signal.get('entry_price', 0)
            
            logger.info(f"📡 New ICT Signal: {symbol} {action}")
            logger.info(f"   Raw Confidence: {confidence} (type: {type(confidence)})")
            logger.info(f"   Price: ${price:,.4f}")
            logger.info(f"   Signal ID: {signal.get('signal_id', 'N/A')}")
            
            # Store signal history
            self.signal_history.append({
                **signal,
                'received_time': datetime.now(),
                'market_price': self.price_monitor.get_price(symbol) if self.price_monitor else price
            })
            
            # Validate and potentially execute signal
            if await self._validate_signal(signal):
                if self.auto_trading:
                    await self._execute_signal(signal)
                else:
                    logger.info("📊 Signal logged (auto-trading disabled)")
            else:
                logger.info("🚫 Signal rejected (validation failed)")
                
        except Exception as e:
            logger.error(f"❌ Error processing ICT signal: {e}")

    async def _validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate signal for execution"""
        try:
            # Check confidence threshold
            confidence = signal.get('confluence_score', 0)
            
            # Convert percentage to decimal if needed (ICT sends 85.4, we need 0.854)
            if confidence > 1.0:
                confidence = confidence / 100.0
                
            min_confidence = self.config.trading.min_confidence if self.config else 0.6
            logger.info(f"🔍 Validating signal - Confidence: {confidence:.3f}, Threshold: {min_confidence:.3f}")
            
            if confidence < min_confidence:
                logger.info(f"⚠️  Confidence {confidence:.1%} below threshold {min_confidence:.1%}")
                return False
            
            # Check if symbol is being tracked
            symbol = signal.get('symbol', '')
            logger.info(f"🔍 Symbol check - Symbol: {symbol}, Tracked: {self.symbols}")
            # ICT sends BTCUSDT format, demo system tracks BTCUSDT format
            if symbol not in self.symbols:
                logger.info(f"⚠️  Symbol {symbol} not in tracked symbols")
                return False
            
            # Check for existing position
            formatted_symbol = symbol + 'USDT' if not symbol.endswith('USDT') else symbol
            if formatted_symbol in self.active_positions:
                logger.info(f"⚠️  Already have position in {formatted_symbol}")
                return False
            
            # Check required fields - ICT uses different field names
            required_fields = ['symbol', 'direction', 'entry_price', 'confluence_score']  # ICT field names
            logger.info(f"🔍 Field check - Available fields: {list(signal.keys())}")
            for field in required_fields:
                if field not in signal or signal[field] is None:
                    logger.info(f"⚠️  Missing required field: {field}")
                    return False
            
            # Check max positions
            max_positions = self.config.trading.max_positions if self.config else 3
            if len(self.active_positions) >= max_positions:
                logger.debug(f"⚠️  Max positions ({max_positions}) reached")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validating signal: {e}")
            return False

    async def _execute_signal(self, signal: Dict[str, Any]):
        """Execute signal as demo trade"""
        try:
            symbol = signal.get('symbol', '')
            action = signal.get('direction', '')
            confidence = signal.get('confluence_score', 0)
            entry_price = signal.get('entry_price', 0)
            
            # Format symbol for Bybit
            bybit_symbol = symbol + 'USDT' if not symbol.endswith('USDT') else symbol
            
            # Get current market price
            market_price = self.price_monitor.get_price(bybit_symbol) if self.price_monitor else entry_price
            
            # Validate price data
            if market_price <= 0:
                logger.error(f"❌ Invalid market price: {market_price} for {bybit_symbol} - skipping signal")
                return
                
            # Calculate position size based on confidence and risk management
            position_size = self._calculate_position_size_for_symbol(confidence, market_price, bybit_symbol)
            
            if position_size <= 0:
                logger.error(f"❌ Invalid position size calculated: {position_size}")
                return
                
            # Check if we can afford this trade (with demo account having $224k equity)
            estimated_margin = (position_size * market_price) / self.leverage
            max_demo_margin = 1000.0  # Reasonable limit with $224k equity available
            
            if estimated_margin > max_demo_margin:
                logger.warning(f"⚠️ Large trade - estimated margin: ${estimated_margin:.2f}")
                # Reduce position size for safety
                max_position_size = (max_demo_margin * self.leverage) / market_price
                position_size = min(position_size, max_position_size)
                logger.info(f"📉 Adjusted position size to: {position_size:.6f}")
            else:
                logger.info(f"✅ Trade size acceptable - estimated margin: ${estimated_margin:.2f}")
            
            if self.dry_run:
                # Simulate execution
                logger.info("🧪 DRY RUN - Simulated Trade Execution:")
                logger.info(f"   Symbol: {bybit_symbol}")
                logger.info(f"   Action: {action}")
                logger.info(f"   Size: {position_size:.6f}")
                logger.info(f"   Market Price: ${market_price:,.4f}")
                logger.info(f"   Entry Price: ${entry_price:,.4f}")
                
                # Create simulated position
                await self._create_demo_position(signal, bybit_symbol, market_price, position_size, 'simulated')
                
            else:
                # Execute on Bybit
                logger.info("🚀 Executing signal on Bybit demo...")
                
                side = "Buy" if action.upper() == "BUY" else "Sell"
                
                # Apply slippage adjustment for realistic execution
                adjusted_price = self._apply_slippage(market_price, side)
                logger.info(f"💰 Market Price: ${market_price:.4f} → Adjusted: ${adjusted_price:.4f} (slippage: {self.slippage_tolerance*100:.1f}%)")
                
                # Calculate leveraged position size
                leveraged_position_size = position_size * self.leverage
                logger.info(f"⚡ Leverage: {self.leverage}x | Position Size: {position_size:.6f} → {leveraged_position_size:.6f}")
                
                order_result = await self.bybit_client.place_order(
                    symbol=bybit_symbol,
                    side=side,
                    qty=leveraged_position_size,  # Use leveraged size
                    order_type=self.order_type,
                    price=adjusted_price if self.order_type == "Limit" else None,
                    time_in_force=self.time_in_force,
                    stop_loss=signal.get('stop_loss'),
                    take_profit=signal.get('take_profit')
                )
                
                if order_result:
                    logger.info("✅ Order placed successfully")
                    logger.info(f"   Order ID: {order_result.get('orderId')}")
                    
                    # Create position record
                    await self._create_demo_position(signal, bybit_symbol, market_price, position_size, 'executed')
                else:
                    logger.error("❌ Order placement failed")
            
            self.performance_data['signals_executed'] += 1
            
        except Exception as e:
            logger.error(f"❌ Error executing signal: {e}")

    def _calculate_position_size(self, confidence: float, price: float) -> float:
        """Calculate position size based on confidence, risk management, and leverage"""
        try:
            # Validate price to prevent division by zero
            if price <= 0:
                logger.error(f"❌ Invalid price for position calculation: {price}")
                return 0.001
            
            # Increased base position size since demo account has sufficient funds ($224k equity)
            base_size_usd = 50.0  # $50 base position (account can handle this)
            
            # Adjust by confidence (0.5x to 1.5x)
            confidence_multiplier = 0.5 + confidence
            adjusted_size = base_size_usd * confidence_multiplier
            
            # Account for leverage in position sizing
            # With leverage, we need less base capital for the same exposure
            effective_size = adjusted_size / self.leverage
            
            # Convert to quantity
            quantity = effective_size / price
            
            # Apply Bybit minimum quantity requirements (based on actual exchange limits)
            min_quantities = {
                'BTCUSDT': 0.00001,  # 0.00001 BTC minimum (~$1.20)
                'ETHUSDT': 0.001,    # 0.001 ETH minimum (~$4.50)  
                'SOLUSDT': 0.01,     # 0.01 SOL minimum (~$2.30)
                'XRPUSDT': 1.0,      # 1.0 XRP minimum (~$3.00)
            }
            
            # Get minimum for current symbol (simplified approach)
            min_qty = 0.001  # Conservative default
            
            # Round to appropriate precision for each symbol
            if 'BTC' in str(price):  # Approximate symbol detection
                quantity = round(quantity, 5)
                min_qty = 0.00001
            elif 'ETH' in str(price):
                quantity = round(quantity, 3)  
                min_qty = 0.001
            elif 'SOL' in str(price):
                quantity = round(quantity, 2)
                min_qty = 0.01
            elif 'XRP' in str(price):
                quantity = round(quantity, 1)
                min_qty = 1.0
            else:
                quantity = round(quantity, 6)
                
            logger.info(f"📊 Position Calculation:")
            logger.info(f"   Base Size: ${base_size_usd}")
            logger.info(f"   Confidence Multiplier: {confidence_multiplier:.2f}")
            logger.info(f"   Adjusted Size: ${adjusted_size:.2f}")
            logger.info(f"   Leverage: {self.leverage}x")
            logger.info(f"   Effective Size: ${effective_size:.2f}")
            logger.info(f"   Final Quantity: {quantity:.6f}")
            logger.info(f"   Minimum Required: {min_qty}")
            
            final_qty = max(quantity, min_qty)  # Ensure minimum size
            logger.info(f"   Using Quantity: {final_qty:.6f}")
            
            return final_qty
            
        except Exception as e:
            logger.error(f"❌ Error calculating position size: {e}")
            return 0.001

    def _calculate_position_size_for_symbol(self, confidence: float, price: float, symbol: str) -> float:
        """Calculate position size with symbol-specific minimums"""
        try:
            # Validate price to prevent division by zero
            if price <= 0:
                logger.error(f"❌ Invalid price for position calculation: {price}")
                return self._get_min_quantity_for_symbol(symbol)
            
            # Increased base position size since demo account has sufficient funds ($224k equity)
            base_size_usd = 50.0  # $50 base position
            
            # Adjust by confidence (0.5x to 1.5x)
            confidence_multiplier = 0.5 + confidence
            adjusted_size = base_size_usd * confidence_multiplier
            
            # Account for leverage in position sizing
            effective_size = adjusted_size / self.leverage
            
            # Convert to quantity
            quantity = effective_size / price
            
            # Apply symbol-specific formatting and minimums
            quantity = self._format_quantity_for_symbol(quantity, symbol)
            min_qty = self._get_min_quantity_for_symbol(symbol)
            
            logger.info(f"📊 Position Calculation for {symbol}:")
            logger.info(f"   Base Size: ${base_size_usd}")
            logger.info(f"   Confidence Multiplier: {confidence_multiplier:.2f}")
            logger.info(f"   Adjusted Size: ${adjusted_size:.2f}")
            logger.info(f"   Leverage: {self.leverage}x")
            logger.info(f"   Effective Size: ${effective_size:.2f}")
            logger.info(f"   Calculated Quantity: {quantity}")
            logger.info(f"   Minimum Required: {min_qty}")
            
            final_qty = max(quantity, min_qty)
            logger.info(f"   Final Quantity: {final_qty}")
            
            return final_qty
            
        except Exception as e:
            logger.error(f"❌ Error calculating position size for {symbol}: {e}")
            return self._get_min_quantity_for_symbol(symbol)
    
    def _get_min_quantity_for_symbol(self, symbol: str) -> float:
        """Get minimum order quantity for symbol"""
        minimums = {
            'BTCUSDT': 0.00001,  # ~$1.20
            'ETHUSDT': 0.001,    # ~$4.50
            'SOLUSDT': 0.01,     # ~$2.30
            'XRPUSDT': 1.0,      # ~$3.00
        }
        return minimums.get(symbol, 0.001)
    
    def _format_quantity_for_symbol(self, quantity: float, symbol: str) -> float:
        """Format quantity with appropriate precision for symbol"""
        if symbol == 'BTCUSDT':
            return round(quantity, 5)
        elif symbol == 'ETHUSDT':
            return round(quantity, 3)
        elif symbol == 'SOLUSDT':
            return round(quantity, 2)
        elif symbol == 'XRPUSDT':
            return round(quantity, 1)
        else:
            return round(quantity, 6)

    def _apply_slippage(self, price: float, side: str) -> float:
        """Apply realistic slippage to market orders"""
        try:
            if side.upper() == "BUY":
                # For buy orders, price goes up (worse fill)
                slipped_price = price * (1 + self.slippage_tolerance)
            else:
                # For sell orders, price goes down (worse fill)  
                slipped_price = price * (1 - self.slippage_tolerance)
            
            return round(slipped_price, 4)
            
        except Exception as e:
            logger.error(f"❌ Error applying slippage: {e}")
            return price

    async def _setup_leverage_and_margin(self):
        """Setup leverage and margin mode for all trading symbols"""
        try:
            logger.info(f"⚙️ Setting up leverage and margin for demo trading...")
            logger.info(f"📊 Leverage: {self.leverage}x")
            logger.info(f"💳 Margin Mode: {self.margin_mode}")
            logger.info(f"📋 Position Mode: {self.position_mode}")
            
            for symbol in self.symbols:
                try:
                    # Set leverage for each symbol
                    leverage_result = await self._set_symbol_leverage(symbol, self.leverage)
                    if leverage_result:
                        logger.info(f"✅ {symbol}: Leverage set to {self.leverage}x")
                    
                    # Set margin mode
                    margin_result = await self._set_margin_mode(symbol)
                    if margin_result:
                        logger.info(f"✅ {symbol}: Margin mode set to {self.margin_mode}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ {symbol}: Setup failed - {e}")
                    
            logger.info("🎯 Leverage and margin setup complete")
            
        except Exception as e:
            logger.error(f"❌ Error setting up leverage/margin: {e}")

    async def _set_symbol_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a specific symbol"""
        try:
            # This would be implemented in the Bybit client
            # For now, we'll simulate it
            logger.info(f"📊 Setting {symbol} leverage to {leverage}x")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set leverage for {symbol}: {e}")
            return False

    async def _set_margin_mode(self, symbol: str) -> bool:
        """Set margin mode for a specific symbol"""
        try:
            # This would be implemented in the Bybit client
            # For now, we'll simulate it
            logger.info(f"💳 Setting {symbol} margin mode to {self.margin_mode}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set margin mode for {symbol}: {e}")
            return False

    async def _create_demo_position(self, signal: Dict, symbol: str, price: float, size: float, status: str):
        """Create demo position record"""
        try:
            position = {
                'signal_id': signal.get('id') or f"{symbol}_{int(datetime.now().timestamp())}",
                'symbol': symbol,
                'side': signal.get('direction', '').upper(),
                'entry_price': price,
                'size': size,
                'confidence': signal.get('confluence_score', 0),
                'confluence_factors': signal.get('confluence_factors', []),
                'stop_loss': signal.get('stop_loss'),
                'take_profit': signal.get('take_profit'),
                'open_time': datetime.now(),
                'status': status,
                'current_price': price,
                'current_pnl': 0.0
            }
            
            self.active_positions[symbol] = position
            self.performance_data['total_trades'] += 1
            
            logger.info(f"📊 Demo position created: {symbol} {position['side']} {size:.6f}")
            
        except Exception as e:
            logger.error(f"❌ Error creating demo position: {e}")

    async def _close_position(self, symbol: str, reason: str):
        """Close demo position"""
        try:
            if symbol not in self.active_positions:
                return
            
            position = self.active_positions[symbol]
            current_price = position['current_price']
            entry_price = position['entry_price']
            
            # Calculate final P&L
            if position['side'] == 'BUY':
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_pct = ((entry_price - current_price) / entry_price) * 100
            
            pnl_usd = (position['size'] * entry_price) * (pnl_pct / 100)
            
            # Update performance
            self.performance_data['total_pnl'] += pnl_usd
            if pnl_usd > 0:
                self.performance_data['winning_trades'] += 1
            
            # Close position
            position['close_time'] = datetime.now()
            position['close_price'] = current_price
            position['final_pnl'] = pnl_usd
            position['close_reason'] = reason
            
            # Move to history
            self.trade_history.append(position)
            del self.active_positions[symbol]
            
            direction = "✅" if pnl_usd > 0 else "❌"
            logger.info(f"{direction} Position closed: {symbol}")
            logger.info(f"   Reason: {reason}")
            logger.info(f"   P&L: ${pnl_usd:.2f} ({pnl_pct:+.2f}%)")
            logger.info(f"   Duration: {position['close_time'] - position['open_time']}")
            
        except Exception as e:
            logger.error(f"❌ Error closing position: {e}")

    async def _update_ict_performance(self):
        """Update performance data from ICT monitor"""
        try:
            async with self.ict_session.get("http://localhost:5001/api/data") as response:
                if response.status == 200:
                    data = await response.json()
                    self.performance_data['paper_balance'] = data.get('paper_balance', 100.0)
                    
        except Exception as e:
            logger.debug(f"Error updating ICT performance: {e}")

    async def generate_performance_report(self):
        """Generate performance comparison report"""
        try:
            # Calculate statistics
            total_trades = self.performance_data['total_trades']
            winning_trades = self.performance_data['winning_trades']
            win_rate = (winning_trades / max(total_trades, 1)) * 100
            
            demo_balance = self.performance_data['demo_balance'] + self.performance_data['total_pnl']
            demo_return = (self.performance_data['total_pnl'] / self.performance_data['demo_balance']) * 100
            
            paper_balance = self.performance_data['paper_balance']
            paper_return = (paper_balance - 100.0) / 100.0 * 100  # Assuming starting balance of 100
            
            logger.info("📊 PERFORMANCE REPORT")
            logger.info("=" * 60)
            logger.info(f"📈 Demo Trading (Bybit):")
            logger.info(f"   Starting Balance: ${self.performance_data['demo_balance']:,.2f}")
            logger.info(f"   Current Balance: ${demo_balance:,.2f}")
            logger.info(f"   Total P&L: ${self.performance_data['total_pnl']:,.2f}")
            logger.info(f"   Return: {demo_return:+.2f}%")
            logger.info(f"   Total Trades: {total_trades}")
            logger.info(f"   Win Rate: {win_rate:.1f}%")
            logger.info("")
            logger.info(f"📊 Paper Trading (ICT):")
            logger.info(f"   Current Balance: ${paper_balance:.2f}")
            logger.info(f"   Return: {paper_return:+.2f}%")
            logger.info("")
            logger.info(f"📡 Signal Processing:")
            logger.info(f"   Signals Received: {self.performance_data['signals_received']}")
            logger.info(f"   Signals Executed: {self.performance_data['signals_executed']}")
            if self.performance_data['signals_received'] > 0:
                execution_rate = (self.performance_data['signals_executed'] / self.performance_data['signals_received']) * 100
                logger.info(f"   Execution Rate: {execution_rate:.1f}%")
            logger.info("")
            logger.info(f"📊 Active Positions: {len(self.active_positions)}")
            for symbol, position in self.active_positions.items():
                pnl = position['current_pnl']
                direction = "📈" if pnl > 0 else "📉"
                logger.info(f"   {direction} {symbol}: {position['side']} {pnl:+.2f}%")
            
            # Price monitoring stats
            if self.price_monitor:
                price_stats = self.price_monitor.get_stats()
                logger.info("")
                logger.info(f"📡 Price Monitoring:")
                logger.info(f"   WebSocket Connected: {'✅' if price_stats['connected'] else '❌'}")
                logger.info(f"   Updates/min: {price_stats['updates_per_minute']}")
                logger.info(f"   Total Updates: {price_stats['total_updates']}")
                
        except Exception as e:
            logger.error(f"❌ Error generating performance report: {e}")

    async def run(self):
        """Main execution loop"""
        try:
            logger.info("🚀 Starting Demo Trading System")
            logger.info("=" * 50)
            
            self.running = True
            
            # Start monitoring tasks
            tasks = [
                asyncio.create_task(self.monitor_ict_signals()),
            ]
            
            # Performance reporting every 5 minutes
            async def periodic_reports():
                while self.running:
                    await asyncio.sleep(300)  # 5 minutes
                    await self.generate_performance_report()
            
            tasks.append(asyncio.create_task(periodic_reports()))
            
            # Run all tasks
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Demo system runtime error: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Clean shutdown"""
        try:
            logger.info("🛑 Shutting down Demo Trading System...")
            
            self.running = False
            
            # Close HTTP session
            if self.ict_session:
                await self.ict_session.close()
            
            # Stop price monitor
            if self.price_monitor:
                await self.price_monitor.stop()
            
            # Close Bybit client
            if self.bybit_client:
                await self.bybit_client.close()
            
            # Final performance report
            await self.generate_performance_report()
            
            logger.info("✅ Demo Trading System shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="ICT-Bybit Demo Trading System")
    parser.add_argument(
        "--auto-trading", 
        action="store_true", 
        help="Enable automatic trade execution"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Test mode without actual trades"
    )
    parser.add_argument(
        "--symbols", 
        nargs="+", 
        default=["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"],
        help="Trading symbols to monitor"
    )
    
    args = parser.parse_args()
    
    # Create system instance
    system = DemoTradingSystem(
        symbols=args.symbols,
        auto_trading=args.auto_trading,
        dry_run=args.dry_run
    )
    
    # Setup signal handler for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"🛑 Received signal {signum}, shutting down...")
        asyncio.create_task(system.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize and run
        await system.initialize()
        await system.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    """
    ICT-Bybit Demo Trading System
    
    This system provides complete integration between ICT Enhanced Trading Monitor
    and Bybit testnet for demo trading validation.
    
    Usage:
    1. Test mode:      python demo_trading_system.py --dry-run
    2. Demo trading:   python demo_trading_system.py --auto-trading
    3. Monitor only:   python demo_trading_system.py
    
    Prerequisites:
    - ICT Enhanced Trading Monitor running
    - Bybit testnet credentials configured
    - Required dependencies installed
    """
    
    print("🎮 ICT-Bybit Demo Trading System")
    print("=================================")
    print()
    print("This system integrates ICT signals with Bybit demo trading")
    print("for real exchange validation and model training.")
    print()
    print("Modes:")
    print("  --dry-run       : Test without actual trades")
    print("  --auto-trading  : Execute trades automatically")
    print("  (no flags)      : Monitor signals only")
    print()
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(130)