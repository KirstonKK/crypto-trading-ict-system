#!/usr/bin/env python3
"""
Intraday Trade Manager
Manages intraday trading positions with time-based exit logic
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class IntradayTradeManager:
    """Manages intraday trades with automatic time-based exits"""
    
    def __init__(self, max_hold_hours: float = 4.0):
        """Initialize trade manager
        
        Args:
            max_hold_hours: Maximum hours to hold a position
        """
        self.max_hold_hours = max_hold_hours
        self.active_trades = {}
        logger.info(f"✅ Intraday Trade Manager initialized (max hold: {max_hold_hours}h)")
    
    def add_trade(self, trade_id: int, symbol: str, entry_time: datetime, entry_price: float):
        """Add a new trade to track
        
        Args:
            trade_id: Unique trade identifier
            symbol: Trading symbol
            entry_time: Time of entry
            entry_price: Entry price
        """
        self.active_trades[trade_id] = {
            'symbol': symbol,
            'entry_time': entry_time,
            'entry_price': entry_price,
            'max_exit_time': entry_time + timedelta(hours=self.max_hold_hours)
        }
        logger.debug(f"Added trade {trade_id} for {symbol} @ ${entry_price}")
    
    def should_exit(self, trade_id: int) -> bool:
        """Check if a trade should be exited based on time
        
        Args:
            trade_id: Trade to check
            
        Returns:
            True if trade should be exited
        """
        if trade_id not in self.active_trades:
            return False
        
        trade = self.active_trades[trade_id]
        current_time = datetime.now()
        
        return current_time >= trade['max_exit_time']
    
    def remove_trade(self, trade_id: int):
        """Remove a trade from active tracking
        
        Args:
            trade_id: Trade to remove
        """
        if trade_id in self.active_trades:
            del self.active_trades[trade_id]
            logger.debug(f"Removed trade {trade_id} from tracking")
    
    def get_active_trades(self) -> List[Dict]:
        """Get all active trades
        
        Returns:
            List of active trade dictionaries
        """
        return list(self.active_trades.values())
    
    def check_all_trades(self) -> List[int]:
        """Check all trades for time-based exits
        
        Returns:
            List of trade IDs that should be exited
        """
        current_time = datetime.now()
        trades_to_exit = []
        
        for trade_id, trade in self.active_trades.items():
            if current_time >= trade['max_exit_time']:
                trades_to_exit.append(trade_id)
        
        return trades_to_exit


def create_trade_manager(max_hold_hours: float = 4.0) -> IntradayTradeManager:
    """Factory function to create a trade manager
    
    Args:
        max_hold_hours: Maximum hours to hold positions
        
    Returns:
        Configured IntradayTradeManager instance
    """
    return IntradayTradeManager(max_hold_hours=max_hold_hours)
