"""
Configuration Loader Utility
============================

Centralized configuration management for the trading algorithm.
Loads and validates configuration files with fallback defaults.

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Centralized configuration loader with validation and defaults.
    
    This class loads configuration files from the configs/ directory,
    providing fallback defaults and validation for all system configurations.
    """
    
    def __init__(self, config_dir: str = "project/configuration/"):
        """
        Initialize ConfigLoader with configuration directory.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self._config_cache = {}
        
        # Ensure config directory exists
        if not self.config_dir.exists():
            raise FileNotFoundError(f"Configuration directory not found: {config_dir}")
    
    def get_config(self, config_name: str) -> Dict[str, Any]:
        """
        Load configuration from JSON file with caching.
        
        Args:
            config_name: Name of configuration file (without .json extension)
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If JSON is invalid
        """
        # Check cache first
        if config_name in self._config_cache:
            return self._config_cache[config_name]
        
        config_file = self.config_dir / f"{config_name}.json"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Cache the configuration
            self._config_cache[config_name] = config
            
            logger.debug(f"Loaded configuration: {config_name}")
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {config_file}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading config {config_name}: {e}")
    
    def reload_config(self, config_name: str) -> Dict[str, Any]:
        """
        Force reload configuration from disk.
        
        Args:
            config_name: Name of configuration to reload
            
        Returns:
            Reloaded configuration dictionary
        """
        # Clear from cache
        if config_name in self._config_cache:
            del self._config_cache[config_name]
        
        return self.get_config(config_name)
    
    def get_config_with_defaults(self, config_name: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load configuration with fallback defaults.
        
        Args:
            config_name: Name of configuration file
            defaults: Default values to use if keys are missing
            
        Returns:
            Configuration dictionary with defaults applied
        """
        try:
            config = self.get_config(config_name)
        except (FileNotFoundError, ValueError):
            logger.warning(f"Using default configuration for: {config_name}")
            config = {}
        
        # Apply defaults for missing keys
        result = defaults.copy()
        result.update(config)
        
        return result
    
    def validate_config(self, config_name: str, required_keys: list) -> bool:
        """
        Validate that configuration contains required keys.
        
        Args:
            config_name: Name of configuration to validate
            required_keys: List of required configuration keys
            
        Returns:
            True if all required keys are present, False otherwise
        """
        try:
            config = self.get_config(config_name)
            
            for key in required_keys:
                if key not in config:
                    logger.error(f"Missing required key '{key}' in {config_name}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating config {config_name}: {e}")
            return False
    
    def list_available_configs(self) -> list:
        """
        List all available configuration files.
        
        Returns:
            List of available configuration names (without .json extension)
        """
        config_files = []
        
        for file_path in self.config_dir.glob("*.json"):
            config_files.append(file_path.stem)
        
        return sorted(config_files)
    
    def clear_cache(self) -> None:
        """Clear configuration cache."""
        self._config_cache.clear()
        logger.debug("Configuration cache cleared")


# Convenience functions for common configurations
def load_exchange_config() -> Dict[str, Any]:
    """Load exchange configuration with defaults."""
    loader = ConfigLoader()
    defaults = {
        "exchange": "bybit",
        "testnet": True,
        "api_key": "",
        "api_secret": "",
        "rate_limit_ms": 100
    }
    return loader.get_config_with_defaults("exchange", defaults)


def load_risk_parameters() -> Dict[str, Any]:
    """Load risk management parameters with defaults."""
    loader = ConfigLoader()
    defaults = {
        "max_portfolio_risk": 0.02,
        "max_position_risk": 0.01,
        "daily_loss_limit": 500.0,
        "max_drawdown": 0.10
    }
    return loader.get_config_with_defaults("risk_parameters", defaults)


def load_crypto_pairs() -> Dict[str, Any]:
    """Load cryptocurrency pairs configuration."""
    loader = ConfigLoader()
    return loader.get_config("crypto_pairs")


if __name__ == "__main__":
    # Test the configuration loader
    try:
        loader = ConfigLoader()
        
        print("Available configurations:")
        for config in loader.list_available_configs():
            print("  - {config}")
        
        # Test loading exchange config
        exchange_config = load_exchange_config()
        print("\\nExchange: {exchange_config['exchange']}")
        print("Testnet: {exchange_config['testnet']}")
        
    except Exception as e:
        print("Error testing configuration loader: {e}")
