"""
Cryptocurrency pairs management utility.
Handles supported trading pairs, validation, and pair-specific configurations.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class CryptoPairs:
    """
    Manages cryptocurrency trading pairs and their configurations.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize CryptoPairs with configuration file.
        
        Args:
            config_path: Path to crypto_pairs.json config file
        """
        if config_path is None:
            # Default to config directory relative to this file
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "config" / "crypto_pairs.json"
        
        self.config_path = Path(config_path)
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
            with open(self.config_path, 'r') as f:
                self._config = json.load(f)
        except Exception as e:
            raise ValueError(f"Error loading crypto pairs config: {e}")
    
    def get_supported_pairs(self, category: Optional[str] = None) -> List[Dict]:
        """
        Get list of supported trading pairs.
        
        Args:
            category: Optional category filter ('major', 'defi', 'layer1', 'altcoins')
            
        Returns:
            List of pair dictionaries with configuration
        """
        if not self._config:
            return []
        
        supported = self._config.get('supported_pairs', {})
        
        if category:
            if category not in supported:
                raise ValueError(f"Unknown category: {category}")
            return supported[category]
        
        # Return all pairs from all categories
        all_pairs = []
        for category_pairs in supported.values():
            all_pairs.extend(category_pairs)
        
        return all_pairs
    
    def get_pair_config(self, symbol: str) -> Optional[Dict]:
        """
        Get configuration for a specific trading pair.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Pair configuration dictionary or None if not found
        """
        all_pairs = self.get_supported_pairs()
        
        for pair in all_pairs:
            if pair.get('symbol') == symbol:
                return pair
        
        return None
    
    def is_pair_supported(self, symbol: str) -> bool:
        """
        Check if a trading pair is supported.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            True if pair is supported, False otherwise
        """
        return self.get_pair_config(symbol) is not None
    
    def get_enabled_pairs(self) -> List[str]:
        """
        Get list of enabled trading pair symbols.
        
        Returns:
            List of enabled pair symbols
        """
        all_pairs = self.get_supported_pairs()
        return [
            pair['symbol'] 
            for pair in all_pairs 
            if pair.get('enabled', False)
        ]
    
    def get_pair_by_priority(self, limit: Optional[int] = None) -> List[str]:
        """
        Get trading pairs sorted by priority.
        
        Args:
            limit: Maximum number of pairs to return
            
        Returns:
            List of pair symbols sorted by priority
        """
        all_pairs = self.get_supported_pairs()
        enabled_pairs = [pair for pair in all_pairs if pair.get('enabled', False)]
        
        # Sort by priority (lower number = higher priority)
        sorted_pairs = sorted(enabled_pairs, key=lambda x: x.get('priority', 999))
        
        symbols = [pair['symbol'] for pair in sorted_pairs]
        
        if limit:
            symbols = symbols[:limit]
        
        return symbols
    
    def get_risk_multiplier(self, symbol: str) -> float:
        """
        Get risk multiplier for a specific pair.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Risk multiplier (default 1.0)
        """
        pair_config = self.get_pair_config(symbol)
        if pair_config:
            return pair_config.get('risk_multiplier', 1.0)
        return 1.0
    
    def get_volatility_factor(self, symbol: str) -> float:
        """
        Get volatility factor for a specific pair.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Volatility factor (default 1.0)
        """
        pair_config = self.get_pair_config(symbol)
        if pair_config:
            return pair_config.get('volatility_factor', 1.0)
        return 1.0
    
    def get_min_order_size(self, symbol: str) -> float:
        """
        Get minimum order size for a specific pair.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Minimum order size (default 0.001)
        """
        pair_config = self.get_pair_config(symbol)
        if pair_config:
            return pair_config.get('min_order_size', 0.001)
        return 0.001
    
    def get_tick_size(self, symbol: str) -> float:
        """
        Get tick size (price increment) for a specific pair.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Tick size (default 0.01)
        """
        pair_config = self.get_pair_config(symbol)
        if pair_config:
            return pair_config.get('tick_size', 0.01)
        return 0.01
    
    def get_correlation_matrix(self) -> Dict:
        """
        Get correlation matrix configuration.
        
        Returns:
            Correlation matrix settings
        """
        return self._config.get('correlation_matrix', {})
    
    def get_high_correlation_pairs(self) -> List[List[str]]:
        """
        Get list of highly correlated pair combinations.
        
        Returns:
            List of correlated pair lists
        """
        correlation_config = self.get_correlation_matrix()
        return correlation_config.get('high_correlation_pairs', [])
    
    def validate_symbol_format(self, symbol: str) -> bool:
        """
        Validate trading pair symbol format.
        
        Args:
            symbol: Trading pair symbol to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not isinstance(symbol, str):
            return False
        
        # Basic validation: should end with USDT for our config
        if not symbol.endswith('USDT'):
            return False
        
        # Should be uppercase
        if symbol != symbol.upper():
            return False
        
        # Should have reasonable length
        if len(symbol) < 4 or len(symbol) > 12:
            return False
        
        return True
    
    def get_trading_sessions(self) -> Dict:
        """
        Get trading session information.
        
        Returns:
            Trading session configuration
        """
        return self._config.get('trading_sessions', {})


# Convenience functions for easy access
def get_enabled_pairs() -> List[str]:
    """Get list of enabled trading pairs."""
    pairs_manager = CryptoPairs()
    return pairs_manager.get_enabled_pairs()


def is_pair_supported(symbol: str) -> bool:
    """Check if a trading pair is supported."""
    pairs_manager = CryptoPairs()
    return pairs_manager.is_pair_supported(symbol)


def get_pair_risk_multiplier(symbol: str) -> float:
    """Get risk multiplier for a trading pair."""
    pairs_manager = CryptoPairs()
    return pairs_manager.get_risk_multiplier(symbol)
