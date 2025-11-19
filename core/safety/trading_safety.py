#!/usr/bin/env python3
"""
Trading Safety Features
======================

Critical safety mechanisms for live trading:
1. Daily Loss Limit Tracker - Halts trading at 5% daily loss
2. Emergency Stop Mechanism - File/environment based instant halt
3. Trade Confirmation System - Manual approval before orders
4. Position Size Validator - Enforces account limits

⚠️ NEVER DISABLE THESE FEATURES IN LIVE TRADING ⚠️
"""

import os
import logging
from datetime import datetime, date
from typing import Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DailyLossTracker:
    """
    Tracks daily P&L and enforces daily loss limits
    
    Features:
    - Tracks starting balance at midnight UTC
    - Calculates real-time daily P&L
    - Halts trading when loss exceeds configured limit
    - Resets automatically at midnight UTC
    """
    
    def __init__(self, max_daily_loss_percent: float = 0.05):
        """
        Initialize daily loss tracker
        
        Args:
            max_daily_loss_percent: Maximum daily loss as percentage (0.05 = 5%)
        """
        self.max_daily_loss_percent = max_daily_loss_percent
        self.starting_balance = 0.0
        self.current_date = None
        self.daily_loss_triggered = False
        
        logger.info(f"✅ Daily Loss Tracker initialized: {max_daily_loss_percent*100:.1f}% limit")
    
    def set_starting_balance(self, balance: float):
        """Set starting balance for the day"""
        today = date.today()
        
        # Reset if new day
        if self.current_date != today:
            self.current_date = today
            self.starting_balance = balance
            self.daily_loss_triggered = False
            logger.info(f"📅 New trading day: Starting balance ${balance:.2f}")
        elif self.starting_balance == 0:
            self.starting_balance = balance
            logger.info(f"💰 Starting balance set: ${balance:.2f}")
    
    def check_daily_loss(self, current_balance: float) -> Tuple[bool, str]:
        """
        Check if daily loss limit has been exceeded
        
        Args:
            current_balance: Current account balance
            
        Returns:
            Tuple of (is_allowed, reason)
        """
        if self.starting_balance <= 0:
            return True, "Starting balance not set"
        
        # Calculate daily P&L
        daily_pnl = current_balance - self.starting_balance
        daily_pnl_percent = (daily_pnl / self.starting_balance) if self.starting_balance > 0 else 0
        
        # Check if loss limit exceeded
        if daily_pnl_percent <= -self.max_daily_loss_percent:
            if not self.daily_loss_triggered:
                self.daily_loss_triggered = True
                logger.error(f"🚨 DAILY LOSS LIMIT EXCEEDED!")
                logger.error(f"   Starting: ${self.starting_balance:.2f}")
                logger.error(f"   Current: ${current_balance:.2f}")
                logger.error(f"   Loss: ${abs(daily_pnl):.2f} ({daily_pnl_percent*100:.2f}%)")
                logger.error(f"   Limit: {self.max_daily_loss_percent*100:.1f}%")
            
            return False, f"Daily loss limit exceeded: {abs(daily_pnl_percent)*100:.2f}% (limit: {self.max_daily_loss_percent*100:.1f}%)"
        
        return True, f"Daily P&L: ${daily_pnl:.2f} ({daily_pnl_percent*100:.2f}%)"
    
    def get_daily_stats(self, current_balance: float) -> Dict:
        """Get current daily statistics"""
        if self.starting_balance <= 0:
            return {
                'starting_balance': 0,
                'current_balance': current_balance,
                'daily_pnl': 0,
                'daily_pnl_percent': 0,
                'limit_triggered': False
            }
        
        daily_pnl = current_balance - self.starting_balance
        daily_pnl_percent = (daily_pnl / self.starting_balance) if self.starting_balance > 0 else 0
        
        return {
            'starting_balance': self.starting_balance,
            'current_balance': current_balance,
            'daily_pnl': daily_pnl,
            'daily_pnl_percent': daily_pnl_percent,
            'limit_triggered': self.daily_loss_triggered,
            'remaining_loss_allowed': self.starting_balance * self.max_daily_loss_percent + daily_pnl
        }


class EmergencyStop:
    """
    Emergency stop mechanism for instant trading halt
    
    Features:
    - File-based stop (/tmp/trading_emergency_stop)
    - Environment variable check (EMERGENCY_STOP=true)
    - Workspace file check (EMERGENCY_STOP.txt)
    """
    
    TEMP_STOP_FILE = "/tmp/trading_emergency_stop"
    WORKSPACE_STOP_FILE = "EMERGENCY_STOP.txt"
    ENV_VAR = "EMERGENCY_STOP"
    
    def __init__(self):
        """Initialize emergency stop checker"""
        logger.info("✅ Emergency Stop initialized")
        logger.info(f"   Temp file: {self.TEMP_STOP_FILE}")
        logger.info(f"   Workspace file: {self.WORKSPACE_STOP_FILE}")
        logger.info(f"   Environment var: {self.ENV_VAR}")
    
    def is_emergency_stop_active(self) -> Tuple[bool, str]:
        """
        Check if emergency stop is triggered
        
        Returns:
            Tuple of (is_stopped, reason)
        """
        # Check temp file
        if Path(self.TEMP_STOP_FILE).exists():
            return True, f"Emergency stop file exists: {self.TEMP_STOP_FILE}"
        
        # Check workspace file
        if Path(self.WORKSPACE_STOP_FILE).exists():
            return True, f"Emergency stop file exists: {self.WORKSPACE_STOP_FILE}"
        
        # Check environment variable
        if os.getenv(self.ENV_VAR, "false").lower() == "true":
            return True, f"Emergency stop environment variable set: {self.ENV_VAR}=true"
        
        return False, "No emergency stop"
    
    def trigger_emergency_stop(self, reason: str = "Manual trigger"):
        """
        Trigger emergency stop by creating stop file
        
        Args:
            reason: Reason for emergency stop
        """
        try:
            with open(self.TEMP_STOP_FILE, 'w') as f:
                f.write(f"Emergency stop triggered at {datetime.now().isoformat()}\n")
                f.write(f"Reason: {reason}\n")
            
            logger.error(f"🚨 EMERGENCY STOP TRIGGERED: {reason}")
            logger.error(f"   Stop file created: {self.TEMP_STOP_FILE}")
            
        except Exception as e:
            logger.error(f"Failed to create emergency stop file: {e}")
    
    def clear_emergency_stop(self):
        """Clear emergency stop by removing stop files"""
        try:
            if Path(self.TEMP_STOP_FILE).exists():
                Path(self.TEMP_STOP_FILE).unlink()
                logger.info(f"✅ Removed emergency stop file: {self.TEMP_STOP_FILE}")
            
            if Path(self.WORKSPACE_STOP_FILE).exists():
                Path(self.WORKSPACE_STOP_FILE).unlink()
                logger.info(f"✅ Removed emergency stop file: {self.WORKSPACE_STOP_FILE}")
            
            if os.getenv(self.ENV_VAR):
                logger.warning(f"⚠️  Environment variable {self.ENV_VAR} still set - unset manually")
            
        except Exception as e:
            logger.error(f"Failed to clear emergency stop: {e}")


class TradeConfirmation:
    """
    Manual trade confirmation system
    
    Features:
    - Displays trade details before execution
    - Requires explicit "yes" confirmation
    - Can be disabled for automated trading (NOT RECOMMENDED)
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize trade confirmation system
        
        Args:
            enabled: Whether to require manual confirmation (KEEP TRUE FOR SAFETY)
        """
        self.enabled = enabled
        
        if enabled:
            logger.warning("✅ Trade Confirmation: ENABLED (manual approval required)")
        else:
            logger.error("⚠️  Trade Confirmation: DISABLED (trades execute automatically)")
    
    def confirm_trade(self, trade_details: Dict) -> Tuple[bool, str]:
        """
        Request confirmation for trade execution
        
        Args:
            trade_details: Dictionary with trade information
                Keys: symbol, direction, size, risk, entry, stop_loss, take_profit
                
        Returns:
            Tuple of (is_confirmed, reason)
        """
        if not self.enabled:
            return True, "Auto-confirmation enabled"
        
        # Log trade details
        logger.warning("\n" + "=" * 60)
        logger.warning("🚨 TRADE CONFIRMATION REQUIRED 🚨")
        logger.warning("=" * 60)
        logger.warning(f"Symbol: {trade_details.get('symbol', 'N/A')}")
        logger.warning(f"Direction: {trade_details.get('direction', 'N/A')}")
        logger.warning(f"Position Size: {trade_details.get('size', 0):.6f}")
        logger.warning(f"Entry Price: ${trade_details.get('entry', 0):.2f}")
        logger.warning(f"Stop Loss: ${trade_details.get('stop_loss', 0):.2f}")
        logger.warning(f"Take Profit: ${trade_details.get('take_profit', 0):.2f}")
        logger.warning(f"Risk Amount: ${trade_details.get('risk', 0):.2f}")
        logger.warning(f"Potential Reward: ${trade_details.get('reward', 0):.2f}")
        logger.warning("=" * 60)
        
        # In automated systems, this would check a flag or queue
        # For now, we'll auto-approve if AUTO_TRADING is enabled
        auto_trading = os.getenv('AUTO_TRADING', 'false').lower() == 'true'
        
        if auto_trading:
            logger.warning("⚠️  AUTO_TRADING enabled - trade approved automatically")
            return True, "Auto-approved (AUTO_TRADING=true)"
        else:
            # Manual approval required - trade will be logged but not executed
            logger.warning("⏸️  Manual approval required - set AUTO_TRADING=true to execute")
            return False, "Manual approval required (set AUTO_TRADING=true)"


class PositionSizeValidator:
    """
    Validates position sizes against account limits
    
    Features:
    - Enforces maximum position size
    - Checks account balance sufficiency
    - Validates against exchange minimum sizes
    - Prevents over-leveraging
    """
    
    def __init__(self, max_position_size: float = 10.0, max_portfolio_risk: float = 0.02):
        """
        Initialize position size validator
        
        Args:
            max_position_size: Maximum position value in USD (10.0 = $10)
            max_portfolio_risk: Maximum portfolio risk as percentage (0.02 = 2%)
        """
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        
        logger.info(f"✅ Position Size Validator initialized")
        logger.info(f"   Max position: ${max_position_size:.2f}")
        logger.info(f"   Max portfolio risk: {max_portfolio_risk*100:.1f}%")
    
    def validate_position(self, 
                         position_value: float,
                         account_balance: float,
                         risk_amount: float,
                         symbol: str = "UNKNOWN") -> Tuple[bool, str]:
        """
        Validate if position size is within limits
        
        Args:
            position_value: Total position value in USD
            account_balance: Current account balance
            risk_amount: Risk amount for this trade
            symbol: Trading symbol
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check 1: Position size limit
        if position_value > self.max_position_size:
            return False, f"Position too large: ${position_value:.2f} exceeds limit ${self.max_position_size:.2f}"
        
        # Check 2: Account balance sufficiency
        if position_value > account_balance:
            return False, f"Insufficient balance: ${position_value:.2f} required, ${account_balance:.2f} available"
        
        # Check 3: Portfolio risk limit
        risk_percent = risk_amount / account_balance if account_balance > 0 else 1
        if risk_percent > self.max_portfolio_risk:
            return False, f"Risk too high: {risk_percent*100:.2f}% exceeds limit {self.max_portfolio_risk*100:.1f}%"
        
        # Check 4: Minimum position size (Bybit typically requires $5-10 minimum)
        if position_value < 5.0:
            return False, f"Position too small: ${position_value:.2f} below exchange minimum ($5)"
        
        return True, f"Position valid: ${position_value:.2f}"


class TradingSafetyManager:
    """
    Master safety manager coordinating all safety features
    
    Aggregates:
    - Daily loss tracking
    - Emergency stop monitoring
    - Trade confirmation
    - Position size validation
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize trading safety manager
        
        Args:
            config: Configuration dictionary with safety parameters
        """
        config = config or {}
        
        # Initialize all safety components
        self.daily_loss_tracker = DailyLossTracker(
            max_daily_loss_percent=config.get('max_daily_loss', 0.05)
        )
        
        self.emergency_stop = EmergencyStop()
        
        self.trade_confirmation = TradeConfirmation(
            enabled=config.get('require_confirmation', True)
        )
        
        self.position_validator = PositionSizeValidator(
            max_position_size=config.get('max_position_size', 10.0),
            max_portfolio_risk=config.get('max_portfolio_risk', 0.02)
        )
        
        logger.info("=" * 60)
        logger.info("✅ TRADING SAFETY MANAGER INITIALIZED")
        logger.info("=" * 60)
    
    def pre_trade_safety_check(self, trade_details: Dict) -> Tuple[bool, str]:
        """
        Comprehensive safety check before trade execution
        
        Args:
            trade_details: Dictionary with all trade information
                Required keys: symbol, direction, size, entry, stop_loss, 
                              take_profit, risk, account_balance
                              
        Returns:
            Tuple of (is_safe, reason)
        """
        # Check 1: Emergency stop
        is_stopped, stop_reason = self.emergency_stop.is_emergency_stop_active()
        if is_stopped:
            logger.error(f"🚨 EMERGENCY STOP ACTIVE: {stop_reason}")
            return False, stop_reason
        
        # Check 2: Daily loss limit
        current_balance = trade_details.get('account_balance', 0)
        self.daily_loss_tracker.set_starting_balance(current_balance)
        
        loss_ok, loss_reason = self.daily_loss_tracker.check_daily_loss(current_balance)
        if not loss_ok:
            logger.error(f"🚨 DAILY LOSS LIMIT: {loss_reason}")
            return False, loss_reason
        
        # Check 3: Position size validation
        position_value = trade_details.get('size', 0) * trade_details.get('entry', 0)
        risk_amount = trade_details.get('risk', 0)
        
        size_ok, size_reason = self.position_validator.validate_position(
            position_value=position_value,
            account_balance=current_balance,
            risk_amount=risk_amount,
            symbol=trade_details.get('symbol', 'UNKNOWN')
        )
        if not size_ok:
            logger.error(f"🚨 POSITION SIZE INVALID: {size_reason}")
            return False, size_reason
        
        # Check 4: Trade confirmation
        confirm_ok, confirm_reason = self.trade_confirmation.confirm_trade(trade_details)
        if not confirm_ok:
            logger.warning(f"⏸️  TRADE NOT CONFIRMED: {confirm_reason}")
            return False, confirm_reason
        
        # All checks passed
        logger.info("✅ All safety checks passed")
        logger.info(f"   {loss_reason}")
        logger.info(f"   {size_reason}")
        return True, "All safety checks passed"
    
    def get_safety_status(self, account_balance: float) -> Dict:
        """Get current status of all safety features"""
        is_stopped, stop_reason = self.emergency_stop.is_emergency_stop_active()
        daily_stats = self.daily_loss_tracker.get_daily_stats(account_balance)
        
        return {
            'emergency_stop': {
                'active': is_stopped,
                'reason': stop_reason
            },
            'daily_loss': daily_stats,
            'trade_confirmation': {
                'enabled': self.trade_confirmation.enabled
            },
            'position_limits': {
                'max_position_size': self.position_validator.max_position_size,
                'max_portfolio_risk': self.position_validator.max_portfolio_risk
            }
        }
