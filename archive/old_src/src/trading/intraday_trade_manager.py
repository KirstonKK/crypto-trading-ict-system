"""
Intraday Trade Manager - Automatic trade management for 5m/15m scalping
Ensures trades don't exceed max hold time and closes all positions at session end
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytz

logger = logging.getLogger(__name__)

class IntradayTradeManager:
    """
    Manages intraday trades with strict time-based exit rules
    
    Rules:
    1. Max hold time: 4 hours per trade
    2. Session close: Close all trades at NY session close (4 PM EST)
    3. No overnight holdings: Force close before market close
    4. Emergency close: Close stale trades (> 4 hours)
    """
    
    def __init__(self, max_hold_hours: float = 4.0):
        """
        Initialize trade manager
        
        Args:
            max_hold_hours: Maximum hours to hold a trade (default: 4.0)
        """
        self.max_hold_hours = max_hold_hours
        self.ny_timezone = pytz.timezone('America/New_York')
        
        # NY Session times (EST)
        self.ny_session_open = {'hour': 9, 'minute': 30}  # 9:30 AM EST
        self.ny_session_close = {'hour': 16, 'minute': 0}  # 4:00 PM EST
        
        logger.info(f"🕐 Intraday Trade Manager initialized - Max hold time: {max_hold_hours} hours")
    
    def get_ny_time(self) -> datetime:
        """Get current time in NY timezone"""
        return datetime.now(self.ny_timezone)
    
    def is_ny_session_active(self) -> bool:
        """Check if NY session is currently active"""
        ny_now = self.get_ny_time()
        
        # Get session times for today
        session_open = ny_now.replace(
            hour=self.ny_session_open['hour'],
            minute=self.ny_session_open['minute'],
            second=0,
            microsecond=0
        )
        session_close = ny_now.replace(
            hour=self.ny_session_close['hour'],
            minute=self.ny_session_close['minute'],
            second=0,
            microsecond=0
        )
        
        return session_open <= ny_now <= session_close
    
    def minutes_until_session_close(self) -> int:
        """Get minutes until NY session closes"""
        ny_now = self.get_ny_time()
        session_close = ny_now.replace(
            hour=self.ny_session_close['hour'],
            minute=self.ny_session_close['minute'],
            second=0,
            microsecond=0
        )
        
        if ny_now > session_close:
            # Session already closed
            return 0
        
        delta = session_close - ny_now
        return int(delta.total_seconds() / 60)
    
    def should_close_for_session_end(self) -> bool:
        """
        Check if we should close all trades due to session ending
        Close all trades 15 minutes before session close
        """
        minutes_left = self.minutes_until_session_close()
        return 0 < minutes_left <= 15  # Close in last 15 minutes
    
    def check_trade_duration(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if trade has exceeded max hold time
        
        Args:
            trade: Trade dictionary with entry_time
            
        Returns:
            Dict with: should_close (bool), reason (str), hours_open (float)
        """
        try:
            # Parse entry time
            entry_time_str = trade.get('entry_time', '')
            if not entry_time_str:
                return {'should_close': False, 'reason': 'No entry time', 'hours_open': 0}
            
            # Handle ISO format with microseconds
            if 'T' in entry_time_str:
                # ISO format: 2025-10-27T20:49:46.836472
                entry_time = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00'))
            else:
                # Standard format: 2025-10-27 13:23:51
                entry_time = datetime.strptime(entry_time_str, '%Y-%m-%d %H:%M:%S')
            
            # Make timezone-aware if naive
            if entry_time.tzinfo is None:
                entry_time = pytz.UTC.localize(entry_time)
            
            # Calculate time open
            now = datetime.now(pytz.UTC)
            time_delta = now - entry_time
            hours_open = time_delta.total_seconds() / 3600
            
            # Check if exceeded max hold time
            if hours_open >= self.max_hold_hours:
                return {
                    'should_close': True,
                    'reason': f'MAX_HOLD_TIME_EXCEEDED ({hours_open:.1f}h > {self.max_hold_hours}h)',
                    'hours_open': hours_open
                }
            
            # Check if session is ending
            if self.should_close_for_session_end():
                return {
                    'should_close': True,
                    'reason': f'SESSION_CLOSE (NY session ending in {self.minutes_until_session_close()} min)',
                    'hours_open': hours_open
                }
            
            return {
                'should_close': False,
                'reason': f'Within time limit ({hours_open:.1f}h < {self.max_hold_hours}h)',
                'hours_open': hours_open
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking trade duration: {e}")
            return {'should_close': False, 'reason': f'Error: {e}', 'hours_open': 0}
    
    def get_trades_to_close(self, active_trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get list of trades that should be closed due to time limits
        
        Args:
            active_trades: List of active trade dictionaries
            
        Returns:
            List of trades that should be closed with close reasons
        """
        trades_to_close = []
        
        for trade in active_trades:
            check_result = self.check_trade_duration(trade)
            
            if check_result['should_close']:
                trade_copy = trade.copy()
                trade_copy['close_reason'] = check_result['reason']
                trade_copy['hours_open'] = check_result['hours_open']
                trades_to_close.append(trade_copy)
                
                logger.warning(
                    f"⏰ Trade {trade.get('symbol', 'UNKNOWN')} "
                    f"{trade.get('direction', 'UNKNOWN')} should close: {check_result['reason']}"
                )
        
        return trades_to_close
    
    def log_trade_status(self, active_trades: List[Dict[str, Any]]):
        """Log status of all active trades"""
        if not active_trades:
            logger.info("📊 No active trades to monitor")
            return
        
        ny_now = self.get_ny_time()
        session_status = "OPEN" if self.is_ny_session_active() else "CLOSED"
        minutes_left = self.minutes_until_session_close()
        
        logger.info(f"📊 Trade Status Report - NY Time: {ny_now.strftime('%H:%M:%S')} EST")
        logger.info(f"   Session: {session_status} | Minutes until close: {minutes_left}")
        logger.info(f"   Active Trades: {len(active_trades)}")
        
        for trade in active_trades:
            check_result = self.check_trade_duration(trade)
            symbol = trade.get('symbol', 'UNKNOWN')
            direction = trade.get('direction', 'UNKNOWN')
            hours_open = check_result['hours_open']
            
            status_icon = "⚠️" if check_result['should_close'] else "✅"
            logger.info(
                f"   {status_icon} {symbol} {direction}: {hours_open:.1f}h open "
                f"(max: {self.max_hold_hours}h) - {check_result['reason']}"
            )


def create_trade_manager(max_hold_hours: float = 4.0) -> IntradayTradeManager:
    """
    Factory function to create trade manager
    
    Args:
        max_hold_hours: Maximum hours to hold a trade
        
    Returns:
        IntradayTradeManager instance
    """
    return IntradayTradeManager(max_hold_hours=max_hold_hours)
