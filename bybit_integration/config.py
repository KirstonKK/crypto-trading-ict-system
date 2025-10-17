"""
Bybit Integration Configuration
==============================

Configuration settings for Bybit demo trading integration.
Create a .env file in your project root with these settings.
"""

import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class BybitConfig:
    """Bybit API configuration"""
    api_key: str = ""
    api_secret: str = ""
    testnet: bool = True
    base_url: str = ""
    
    def __post_init__(self):
        if self.testnet:
            self.base_url = "https://api-testnet.bybit.com"
        else:
            self.base_url = "https://api.bybit.com"

@dataclass
class TradingConfig:
    """Trading configuration"""
    auto_trading: bool = False
    max_positions: int = 3
    max_risk_per_trade: float = 0.01  # 1% - STRICT RISK LIMIT
    max_portfolio_risk: float = 0.03  # 3% total exposure
    min_confidence: float = 0.7       # 70% - Higher quality threshold
    
    # Position sizing
    default_position_size: float = 100.0  # USD
    confidence_multiplier: bool = True
    
    # Risk management
    use_stop_loss: bool = True
    use_take_profit: bool = True
    default_stop_loss_pct: float = 0.01  # 1% - matches risk per trade
    
    # Dynamic take profit based on signal quality (1:2 to 1:5 RR)
    dynamic_take_profit: bool = True
    min_take_profit_pct: float = 0.02  # 1:2 RR minimum
    max_take_profit_pct: float = 0.05  # 1:5 RR maximum

@dataclass
class ICTConfig:
    """ICT Monitor configuration"""
    monitor_url: str = "http://localhost:5001"
    signal_poll_interval: int = 2  # seconds
    signal_timeout: int = 300      # 5 minutes
    
    # Signal filtering
    min_confluence_factors: int = 2
    required_sessions: list = None
    
    def __post_init__(self):
        if self.required_sessions is None:
            self.required_sessions = ["London", "New York"]

@dataclass
class WebSocketConfig:
    """WebSocket configuration"""
    enable_public_stream: bool = True
    enable_private_stream: bool = True
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 10
    ping_interval: int = 20

@dataclass
class IntegrationConfig:
    """Main integration configuration"""
    bybit: BybitConfig
    trading: TradingConfig
    ict: ICTConfig
    websocket: WebSocketConfig
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "bybit_integration.log"
    
    # Performance tracking
    enable_performance_tracking: bool = True
    performance_update_interval: int = 60  # seconds

def load_config_from_env(env_file: str = ".env") -> IntegrationConfig:
    """
    Load configuration from environment variables
    
    Args:
        env_file: Path to environment file to load
    
    Required environment variables:
    - BYBIT_API_KEY: Your Bybit API key
    - BYBIT_API_SECRET: Your Bybit API secret
    
    Optional environment variables:
    - BYBIT_TESTNET: "true" or "false" (default: true)
    - AUTO_TRADING_ENABLED: "true" or "false" (default: false)
    - ICT_MONITOR_URL: ICT monitor URL (default: http://localhost:5001)
    - MAX_CONCURRENT_POSITIONS: Maximum concurrent positions (default: 3)
    - MAX_RISK_PER_TRADE: Maximum risk per trade as decimal (default: 0.02)
    - MAX_PORTFOLIO_RISK: Maximum portfolio risk as decimal (default: 0.05)
    - CONFIDENCE_THRESHOLD: Minimum signal confidence as decimal (default: 0.6)
    """
    
    # Load environment file if it exists
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    
    # Bybit configuration
    bybit_config = BybitConfig(
        api_key=os.getenv("BYBIT_API_KEY", ""),
        api_secret=os.getenv("BYBIT_API_SECRET", ""),
        testnet=os.getenv("BYBIT_TESTNET", "true").lower() == "true"
    )
    
    # Trading configuration
    trading_config = TradingConfig(
        auto_trading=os.getenv("AUTO_TRADING_ENABLED", "false").lower() == "true",
        max_positions=int(os.getenv("MAX_CONCURRENT_POSITIONS", "3")),
        max_risk_per_trade=float(os.getenv("MAX_RISK_PER_TRADE", "0.01")),  # Updated to 1%
        max_portfolio_risk=float(os.getenv("MAX_PORTFOLIO_RISK", "0.03")),   # Updated to 3%
        min_confidence=float(os.getenv("CONFIDENCE_THRESHOLD", "0.7")),       # Updated to 70%
        default_position_size=float(os.getenv("MAX_POSITION_SIZE_USD", "100.0")),
        use_stop_loss=os.getenv("USE_STOP_LOSS", "true").lower() == "true",
        use_take_profit=os.getenv("USE_TAKE_PROFIT", "true").lower() == "true",
        default_stop_loss_pct=float(os.getenv("DEFAULT_STOP_LOSS_PCT", "0.01")),  # Updated to 1%
        # Dynamic take profit configuration
        dynamic_take_profit=os.getenv("DYNAMIC_TAKE_PROFIT", "true").lower() == "true",
        min_take_profit_pct=float(os.getenv("MIN_TAKE_PROFIT_PCT", "0.02")),      # 1:2 RR
        max_take_profit_pct=float(os.getenv("MAX_TAKE_PROFIT_PCT", "0.05"))       # 1:5 RR
    )
    
    # ICT Monitor configuration
    ict_config = ICTConfig(
        monitor_url=os.getenv("ICT_MONITOR_URL", "http://localhost:5001"),
        signal_poll_interval=int(os.getenv("SIGNAL_POLL_INTERVAL", "2")),
        signal_timeout=int(os.getenv("SIGNAL_TIMEOUT", "300")),
        min_confluence_factors=int(os.getenv("MIN_CONFLUENCE_FACTORS", "2"))
    )
    
    # WebSocket configuration
    websocket_config = WebSocketConfig(
        enable_public_stream=os.getenv("ENABLE_PUBLIC_STREAM", "true").lower() == "true",
        enable_private_stream=os.getenv("ENABLE_PRIVATE_STREAM", "true").lower() == "true",
        reconnect_interval=int(os.getenv("WS_RECONNECT_INTERVAL", "5")),
        max_reconnect_attempts=int(os.getenv("WS_MAX_RECONNECT_ATTEMPTS", "10")),
        ping_interval=int(os.getenv("WS_PING_INTERVAL", "20"))
    )
    
    # Main configuration
    config = IntegrationConfig(
        bybit=bybit_config,
        trading=trading_config,
        ict=ict_config,
        websocket=websocket_config,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE", "bybit_integration.log"),
        enable_performance_tracking=os.getenv("ENABLE_PERFORMANCE_TRACKING", "true").lower() == "true",
        performance_update_interval=int(os.getenv("PERFORMANCE_UPDATE_INTERVAL", "60"))
    )
    
    return config

def validate_config(config: IntegrationConfig) -> tuple[bool, list[str]]:
    """
    Validate configuration settings
    
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    # Validate Bybit configuration
    if not config.bybit.api_key:
        errors.append("BYBIT_API_KEY is required")
    
    if not config.bybit.api_secret:
        errors.append("BYBIT_API_SECRET is required")
    
    # Validate trading configuration
    if config.trading.max_risk_per_trade <= 0 or config.trading.max_risk_per_trade > 0.1:
        errors.append("MAX_RISK_PER_TRADE must be between 0 and 0.1 (10%)")
    
    if config.trading.max_portfolio_risk <= 0 or config.trading.max_portfolio_risk > 0.2:
        errors.append("MAX_PORTFOLIO_RISK must be between 0 and 0.2 (20%)")
    
    if config.trading.min_confidence <= 0 or config.trading.min_confidence > 1:
        errors.append("MIN_CONFIDENCE must be between 0 and 1")
    
    if config.trading.max_positions <= 0:
        errors.append("MAX_POSITIONS must be greater than 0")
    
    # Validate ICT configuration
    if not config.ict.monitor_url:
        errors.append("ICT_MONITOR_URL is required")
    
    if config.ict.signal_poll_interval <= 0:
        errors.append("SIGNAL_POLL_INTERVAL must be greater than 0")
    
    return len(errors) == 0, errors

# Default configuration template for .env file
ENV_TEMPLATE = """
# Bybit API Configuration
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
BYBIT_TESTNET=true

# Trading Configuration (Updated for 1% Strict Risk)
AUTO_TRADING=false
MAX_POSITIONS=3
MAX_RISK_PER_TRADE=0.01          # 1% strict risk limit
MAX_PORTFOLIO_RISK=0.03          # 3% total portfolio risk
MIN_CONFIDENCE=0.7               # 70% minimum confidence
DEFAULT_POSITION_SIZE=100.0
USE_STOP_LOSS=true
USE_TAKE_PROFIT=true
DEFAULT_STOP_LOSS_PCT=0.01       # 1% stop loss
DYNAMIC_TAKE_PROFIT=true         # Enable dynamic RR ratios
MIN_TAKE_PROFIT_PCT=0.02         # 1:2 RR minimum
MAX_TAKE_PROFIT_PCT=0.05         # 1:5 RR maximum

# ICT Monitor Configuration
ICT_MONITOR_URL=http://localhost:5001
SIGNAL_POLL_INTERVAL=2
SIGNAL_TIMEOUT=300
MIN_CONFLUENCE_FACTORS=2

# WebSocket Configuration
ENABLE_PUBLIC_STREAM=true
ENABLE_PRIVATE_STREAM=true
WS_RECONNECT_INTERVAL=5
WS_MAX_RECONNECT_ATTEMPTS=10
WS_PING_INTERVAL=20

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=bybit_integration.log
ENABLE_PERFORMANCE_TRACKING=true
PERFORMANCE_UPDATE_INTERVAL=60
"""

def create_env_template(filename: str = ".env.template"):
    """Create environment template file"""
    with open(filename, 'w') as f:
        f.write(ENV_TEMPLATE.strip())
    
    print("✅ Environment template created: {filename}")
    print("📝 Copy this to .env and update with your API credentials")

if __name__ == "__main__":
    # Create environment template
    create_env_template()
    
    # Test configuration loading
    try:
        config = load_config_from_env()
        is_valid, errors = validate_config(config)
        
        if is_valid:
            print("✅ Configuration is valid")
        else:
            print("❌ Configuration errors:")
            for error in errors:
                print("   - {error}")
                
    except Exception as e:
        print("❌ Error loading configuration: {e}")