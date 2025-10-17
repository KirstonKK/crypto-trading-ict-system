"""
Production-ready configuration management for Trading Algorithm
Version: 1.0 - CodeRabbit Review Target
"""
import os
from pathlib import Path
from typing import Dict, Any

# Base directory
BASE_DIR = Path(__file__).parent.parent

class Config:
    """Base configuration class"""
    
    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # API Configuration
    BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
    BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')
    BYBIT_TESTNET = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
    BYBIT_DEMO = os.getenv('BYBIT_DEMO', 'false').lower() == 'true'
    BYBIT_BASE_URL = os.getenv('BYBIT_BASE_URL', 'https://api-testnet.bybit.com')
    BYBIT_ENVIRONMENT = os.getenv('BYBIT_ENVIRONMENT', 'testnet')  # testnet, demo_mainnet, live_mainnet
    
    # Trading Configuration
    RISK_PER_TRADE = float(os.getenv('RISK_PER_TRADE', '100.0'))
    MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', '10'))
    RISK_REWARD_RATIO = float(os.getenv('RISK_REWARD_RATIO', '3.0'))
    
    # ICT Monitor Configuration - SECURITY FIX: Default to localhost only
    ICT_MONITOR_PORT = int(os.getenv('ICT_MONITOR_PORT', '5001'))
    ICT_MONITOR_HOST = os.getenv('ICT_MONITOR_HOST', '127.0.0.1')  # Changed from 0.0.0.0 to localhost
    
    # Signal Generation
    SIGNAL_PROBABILITY_BASE = float(os.getenv('SIGNAL_PROBABILITY_BASE', '0.035'))
    CONFLUENCE_THRESHOLD = float(os.getenv('CONFLUENCE_THRESHOLD', '0.35'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = BASE_DIR / 'logs'
    
    # Data Storage
    DATA_DIR = BASE_DIR / 'data'
    RESULTS_DIR = BASE_DIR / 'results'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    BYBIT_TESTNET = True
    LOG_LEVEL = 'DEBUG'

class StagingConfig(Config):
    """Staging configuration"""
    DEBUG = False
    BYBIT_TESTNET = True
    LOG_LEVEL = 'INFO'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    BYBIT_TESTNET = False
    LOG_LEVEL = 'WARNING'

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig
}

def get_config() -> Config:
    """Get configuration based on environment"""
    env = os.getenv('ENVIRONMENT', 'development')
    return config_map.get(env, DevelopmentConfig)()