"""
TradingView Integration Module
=============================

This module provides secure integration with TradingView alerts,
enabling automated trading based on Pine Script signals.

Components:
- webhook_server: Secure webhook endpoint for TradingView alerts
- signal_processor: Alert validation and signal processing
- pine_connector: Pine Script to Python trading bridge

Security Features:
- HMAC signature verification
- IP whitelist validation
- Rate limiting and DDoS protection
- Input sanitization and validation
- Comprehensive logging and monitoring

Author: GitHub Copilot Trading Algorithm
Date: September 2025
"""

from .webhook_server import WebhookServer
from .signal_processor import SignalProcessor

__version__ = "1.0.0"
__all__ = ["WebhookServer", "SignalProcessor"]
