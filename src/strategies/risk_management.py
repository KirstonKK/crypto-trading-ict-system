"""
Advanced risk management system for cryptocurrency trading.
Implements position sizing, stop losses, and portfolio protection.
"""

import json
import logging
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class VolatilityRegime(Enum):
    """Market volatility classification."""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class Position:
    """Represents a trading position."""
    symbol: str
    side: str  # 'long' or 'short'
    size: float
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    unrealized_pnl: float = 0.0
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class RiskMetrics:
    """Risk metrics for portfolio monitoring."""
    total_risk: float
    position_count: int
    max_drawdown: float
    daily_pnl: float
    portfolio_value: float
    risk_level: str
    alerts: List[str]


class RiskManager:
    """
    Advanced risk management system with crypto-specific optimizations.
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        """
        Initialize risk manager.
        
        Args:
            initial_capital: Starting portfolio value in USD
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.logger = logging.getLogger(__name__)
        
        # Load risk parameters
        self._load_risk_config()
        
        # Portfolio tracking
        self.positions: Dict[str, Position] = {}
        self.daily_pnl_history: List[Tuple[datetime, float]] = []
        self.max_portfolio_drawdown = 0.0
        
        # Risk limits
        self.position_limit_reached = False
        self.daily_loss_limit_reached = False
        
    def _load_risk_config(self) -> None:
        """Load risk management configuration."""
        config_path = Path(__file__).parent.parent.parent / "config" / "risk_parameters.json"
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.risk_config = config.get('risk_management', {})
        except Exception as e:
            self.logger.error(f"Error loading risk config: {e}")
            # Default risk parameters
            self.risk_config = {
                'position_sizing': {
                    'max_risk_per_trade': 0.02,
                    'max_portfolio_risk': 0.08,
                    'base_position_size': 0.05
                },
                'stop_loss': {
                    'crypto_default': 0.04
                },
                'drawdown_protection': {
                    'max_portfolio_drawdown': 0.15,
                    'daily_loss_limit': 0.05
                }
            }
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                              stop_loss_price: float, volatility: float = 1.0) -> float:
        """
        Calculate optimal position size based on risk parameters.
        
        Args:
            symbol: Trading pair symbol
            entry_price: Planned entry price
            stop_loss_price: Stop loss price
            volatility: Volatility multiplier (1.0 = normal)
            
        Returns:
            Position size in USD
        """
        # Get risk parameters
        max_risk_per_trade = self.risk_config['position_sizing']['max_risk_per_trade']
        base_position_size = self.risk_config['position_sizing']['base_position_size']
        
        # Calculate risk per share/unit
        risk_per_unit = abs(entry_price - stop_loss_price)
        if risk_per_unit <= 0:
            self.logger.error("Invalid stop loss price")
            return 0.0
        
        # Maximum risk amount in USD
        max_risk_amount = self.current_capital * max_risk_per_trade
        
        # Calculate position size based on risk
        risk_based_size = max_risk_amount / risk_per_unit
        risk_based_position_value = risk_based_size * entry_price
        
        # Apply volatility adjustment
        volatility_adjustment = 1.0 / max(volatility, 0.5)  # Reduce size for higher volatility
        adjusted_size = risk_based_position_value * volatility_adjustment
        
        # Apply base position size limit
        max_base_position = self.current_capital * base_position_size
        final_position_size = min(adjusted_size, max_base_position)
        
        # Check portfolio risk limits
        current_portfolio_risk = self.get_current_portfolio_risk()
        max_portfolio_risk = self.risk_config['position_sizing']['max_portfolio_risk']
        
        if current_portfolio_risk >= max_portfolio_risk:
            self.logger.warning("Portfolio risk limit reached")
            return 0.0
        
        # Ensure we don't exceed portfolio risk limit
        remaining_risk_capacity = max_portfolio_risk - current_portfolio_risk
        max_allowed_position = self.current_capital * remaining_risk_capacity
        
        final_size = min(final_position_size, max_allowed_position)
        
        self.logger.info(f"Position size for {symbol}: ${final_size:,.2f}")
        return max(final_size, 0.0)
    
    def calculate_stop_loss(self, symbol: str, entry_price: float, 
                           side: str, volatility: float = 1.0) -> float:
        """
        Calculate stop loss price based on volatility and pair-specific settings.
        
        Args:
            symbol: Trading pair symbol
            entry_price: Entry price
            side: 'long' or 'short'
            volatility: Current volatility measure
            
        Returns:
            Stop loss price
        """
        # Get base stop loss percentage
        crypto_default = self.risk_config['stop_loss']['crypto_default']
        
        # Apply volatility adjustment
        volatility_regime = self.classify_volatility(volatility)
        volatility_multiplier = {
            VolatilityRegime.LOW: 0.8,
            VolatilityRegime.MEDIUM: 1.0,
            VolatilityRegime.HIGH: 1.3,
            VolatilityRegime.EXTREME: 1.5
        }.get(volatility_regime, 1.0)
        
        adjusted_stop_loss_pct = crypto_default * volatility_multiplier
        
        # Calculate stop loss price
        if side.lower() == 'long':
            stop_loss_price = entry_price * (1 - adjusted_stop_loss_pct)
        else:  # short
            stop_loss_price = entry_price * (1 + adjusted_stop_loss_pct)
        
        self.logger.info(f"Stop loss for {symbol} ({side}): ${stop_loss_price:.4f} ({adjusted_stop_loss_pct:.1%})")
        return stop_loss_price
    
    def classify_volatility(self, volatility: float) -> VolatilityRegime:
        """
        Classify current volatility regime.
        
        Args:
            volatility: Volatility measure (typically ATR/Price ratio)
            
        Returns:
            Volatility regime classification
        """
        if volatility <= 0.02:
            return VolatilityRegime.LOW
        elif volatility <= 0.05:
            return VolatilityRegime.MEDIUM
        elif volatility <= 0.08:
            return VolatilityRegime.HIGH
        else:
            return VolatilityRegime.EXTREME
    
    def add_position(self, position: Position) -> bool:
        """
        Add new position to portfolio with risk checks.
        
        Args:
            position: Position object to add
            
        Returns:
            True if position was added, False if rejected
        """
        # Check if we already have a position in this symbol
        if position.symbol in self.positions:
            self.logger.warning(f"Position already exists for {position.symbol}")
            return False
        
        # Calculate position risk
        position_risk = self.calculate_position_risk(position)
        current_risk = self.get_current_portfolio_risk()
        max_portfolio_risk = self.risk_config['position_sizing']['max_portfolio_risk']
        
        if current_risk + position_risk > max_portfolio_risk:
            self.logger.warning("Adding position would exceed portfolio risk limit")
            return False
        
        # Add position
        self.positions[position.symbol] = position
        self.logger.info(f"Added position: {position.symbol} ({position.side}) ${position.size:,.2f}")
        
        return True
    
    def update_position(self, symbol: str, current_price: float) -> None:
        """
        Update position with current market price.
        
        Args:
            symbol: Trading pair symbol
            current_price: Current market price
        """
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        position.current_price = current_price
        
        # Calculate unrealized P&L
        if position.side.lower() == 'long':
            position.unrealized_pnl = (current_price - position.entry_price) * (position.size / position.entry_price)
        else:  # short
            position.unrealized_pnl = (position.entry_price - current_price) * (position.size / position.entry_price)
        
        # Check stop loss
        if self.should_trigger_stop_loss(position):
            self.logger.warning(f"Stop loss triggered for {symbol}")
            # Note: Actual order execution would happen in trading strategy
    
    def close_position(self, symbol: str, exit_price: float) -> Optional[float]:
        """
        Close position and calculate realized P&L.
        
        Args:
            symbol: Trading pair symbol
            exit_price: Exit price
            
        Returns:
            Realized P&L or None if position doesn't exist
        """
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        
        # Calculate realized P&L
        if position.side.lower() == 'long':
            realized_pnl = (exit_price - position.entry_price) * (position.size / position.entry_price)
        else:  # short
            realized_pnl = (position.entry_price - exit_price) * (position.size / position.entry_price)
        
        # Update capital
        self.current_capital += realized_pnl
        
        # Record P&L
        self.daily_pnl_history.append((datetime.now(), realized_pnl))
        
        # Remove position
        del self.positions[symbol]
        
        self.logger.info(f"Closed position: {symbol} P&L: ${realized_pnl:,.2f}")
        return realized_pnl
    
    def should_trigger_stop_loss(self, position: Position) -> bool:
        """Check if position should trigger stop loss."""
        if position.stop_loss is None:
            return False
        
        if position.side.lower() == 'long':
            return position.current_price <= position.stop_loss
        else:  # short
            return position.current_price >= position.stop_loss
    
    def calculate_position_risk(self, position: Position) -> float:
        """
        Calculate risk of a position as percentage of portfolio.
        
        Args:
            position: Position to analyze
            
        Returns:
            Risk as percentage of portfolio
        """
        if position.stop_loss is None:
            # Assume maximum possible loss if no stop loss
            return position.size / self.current_capital
        
        # Calculate maximum loss
        if position.side.lower() == 'long':
            max_loss = (position.entry_price - position.stop_loss) * (position.size / position.entry_price)
        else:  # short
            max_loss = (position.stop_loss - position.entry_price) * (position.size / position.entry_price)
        
        return abs(max_loss) / self.current_capital
    
    def get_current_portfolio_risk(self) -> float:
        """
        Get current total portfolio risk.
        
        Returns:
            Total portfolio risk as percentage
        """
        total_risk = 0.0
        for position in self.positions.values():
            total_risk += self.calculate_position_risk(position)
        return total_risk
    
    def get_portfolio_metrics(self) -> RiskMetrics:
        """
        Get comprehensive portfolio risk metrics.
        
        Returns:
            RiskMetrics object with current portfolio status
        """
        # Calculate total unrealized P&L
        total_unrealized = sum(pos.unrealized_pnl for pos in self.positions.values())
        
        # Calculate daily P&L
        today = datetime.now().date()
        daily_pnl = sum(
            pnl for date, pnl in self.daily_pnl_history 
            if date.date() == today
        )
        
        # Calculate drawdown
        current_value = self.current_capital + total_unrealized
        max_value = max(self.initial_capital, current_value)
        current_drawdown = (max_value - current_value) / max_value
        self.max_portfolio_drawdown = max(self.max_portfolio_drawdown, current_drawdown)
        
        # Determine risk level
        current_risk = self.get_current_portfolio_risk()
        if current_risk > 0.06:
            risk_level = "HIGH"
        elif current_risk > 0.04:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Generate alerts
        alerts = []
        max_drawdown_limit = self.risk_config['drawdown_protection']['max_portfolio_drawdown']
        daily_loss_limit = self.risk_config['drawdown_protection']['daily_loss_limit']
        
        if current_drawdown > max_drawdown_limit * 0.8:
            alerts.append("Approaching maximum drawdown limit")
        
        if daily_pnl < -self.current_capital * daily_loss_limit * 0.8:
            alerts.append("Approaching daily loss limit")
        
        if len(self.positions) > 5:
            alerts.append("High number of open positions")
        
        return RiskMetrics(
            total_risk=current_risk,
            position_count=len(self.positions),
            max_drawdown=self.max_portfolio_drawdown,
            daily_pnl=daily_pnl,
            portfolio_value=current_value,
            risk_level=risk_level,
            alerts=alerts
        )
    
    def check_risk_limits(self) -> Dict[str, bool]:
        """
        Check all risk limits and return status.
        
        Returns:
            Dictionary with risk limit status
        """
        metrics = self.get_portfolio_metrics()
        
        # Risk limit checks
        max_drawdown_limit = self.risk_config['drawdown_protection']['max_portfolio_drawdown']
        daily_loss_limit = self.risk_config['drawdown_protection']['daily_loss_limit']
        max_portfolio_risk = self.risk_config['position_sizing']['max_portfolio_risk']
        
        return {
            'drawdown_limit_ok': metrics.max_drawdown < max_drawdown_limit,
            'daily_loss_limit_ok': abs(metrics.daily_pnl) < self.current_capital * daily_loss_limit,
            'portfolio_risk_ok': metrics.total_risk < max_portfolio_risk,
            'position_count_ok': metrics.position_count <= 10
        }


# Convenience functions
def calculate_crypto_position_size(capital: float, entry_price: float, 
                                 stop_loss_price: float, risk_pct: float = 0.02) -> float:
    """
    Calculate position size for crypto trading.
    
    Args:
        capital: Available capital
        entry_price: Entry price
        stop_loss_price: Stop loss price
        risk_pct: Risk percentage (default 2%)
        
    Returns:
        Position size in USD
    """
    risk_amount = capital * risk_pct
    risk_per_unit = abs(entry_price - stop_loss_price)
    
    if risk_per_unit <= 0:
        return 0.0
    
    return risk_amount / risk_per_unit * entry_price
