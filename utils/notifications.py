"""
Secure notification system for trading alerts and updates.
Supports Discord, Telegram, and Email notifications with rate limiting.
"""

import os
import json
import time
import logging
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path

# External dependencies with graceful degradation
try:
    import requests
except ImportError:
    requests = None

try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False


class NotificationManager:
    """
    Manages secure notifications for trading events with rate limiting.
    """
    
    def __init__(self):
        """Initialize notification manager with environment configuration."""
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting (prevent spam)
        self.last_notification_time = {}
        self.min_interval_seconds = 60  # Minimum 1 minute between similar notifications
        
        # Load configuration
        self._load_config()
    
    def _load_config(self) -> None:
        """Load notification configuration from environment."""
        # Discord webhook
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
        
        # Telegram
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Email
        self.email_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.email_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        
        # Notification preferences
        self.enable_discord = bool(self.discord_webhook)
        self.enable_telegram = bool(self.telegram_token and self.telegram_chat_id)
        self.enable_email = bool(self.email_address and self.email_password and EMAIL_AVAILABLE)
    
    def _should_send_notification(self, notification_type: str) -> bool:
        """
        Check if notification should be sent based on rate limiting.
        
        Args:
            notification_type: Type of notification for rate limiting
            
        Returns:
            True if notification should be sent, False if rate limited
        """
        current_time = time.time()
        last_time = self.last_notification_time.get(notification_type, 0)
        
        if current_time - last_time < self.min_interval_seconds:
            return False
        
        self.last_notification_time[notification_type] = current_time
        return True
    
    def send_trade_alert(self, alert_type: str, symbol: str, price: float, 
                        message: str, urgent: bool = False) -> bool:
        """
        Send trading alert notification.
        
        Args:
            alert_type: Type of alert ('BUY', 'SELL', 'STOP_LOSS', etc.)
            symbol: Trading pair symbol
            price: Current price
            message: Alert message
            urgent: Whether to bypass rate limiting
            
        Returns:
            True if at least one notification was sent successfully
        """
        notification_key = f"trade_{alert_type}_{symbol}"
        
        if not urgent and not self._should_send_notification(notification_key):
            self.logger.info("Rate limited notification: {notification_key}")
            return False
        
        # Format the message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        formatted_message = f"""
🚨 **TRADING ALERT** 🚨
Type: {alert_type}
Symbol: {symbol}
Price: ${price:,.4f}
Time: {timestamp}

{message}
        """.strip()
        
        success_count = 0
        
        # Send to Discord
        if self.enable_discord:
            if self._send_discord_message(formatted_message):
                success_count += 1
        
        # Send to Telegram
        if self.enable_telegram:
            if self._send_telegram_message(formatted_message):
                success_count += 1
        
        # Send email for urgent alerts
        if urgent and self.enable_email:
            subject = f"URGENT: {alert_type} Alert for {symbol}"
            if self._send_email(subject, formatted_message):
                success_count += 1
        
        return success_count > 0
    
    def send_system_alert(self, alert_type: str, message: str, urgent: bool = True) -> bool:
        """
        Send system/error alert notification.
        
        Args:
            alert_type: Type of system alert ('ERROR', 'WARNING', 'INFO')
            message: Alert message
            urgent: Whether to bypass rate limiting
            
        Returns:
            True if at least one notification was sent successfully
        """
        notification_key = f"system_{alert_type}"
        
        if not urgent and not self._should_send_notification(notification_key):
            return False
        
        # Format the message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        emoji = "🔴" if alert_type == "ERROR" else "⚠️" if alert_type == "WARNING" else "ℹ️"
        
        formatted_message = f"""
{emoji} **SYSTEM {alert_type}** {emoji}
Time: {timestamp}

{message}
        """.strip()
        
        success_count = 0
        
        # Send to all enabled channels for system alerts
        if self.enable_discord:
            if self._send_discord_message(formatted_message):
                success_count += 1
        
        if self.enable_telegram:
            if self._send_telegram_message(formatted_message):
                success_count += 1
        
        if urgent and self.enable_email:
            subject = f"System {alert_type}: Trading Algorithm"
            if self._send_email(subject, formatted_message):
                success_count += 1
        
        return success_count > 0
    
    def send_performance_report(self, report_data: Dict) -> bool:
        """
        Send performance report notification.
        
        Args:
            report_data: Dictionary containing performance metrics
            
        Returns:
            True if at least one notification was sent successfully
        """
        if not self._should_send_notification("performance_report"):
            return False
        
        # Format performance report
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        message = f"""
📊 **PERFORMANCE REPORT** 📊
Time: {timestamp}

💰 Total P&L: ${report_data.get('total_pnl', 0):,.2f}
📈 Win Rate: {report_data.get('win_rate', 0):.1%}
📉 Drawdown: {report_data.get('drawdown', 0):.1%}
🎯 Trades Today: {report_data.get('trades_today', 0)}
⚡ Active Positions: {report_data.get('active_positions', 0)}

Risk Level: {report_data.get('risk_level', 'UNKNOWN')}
        """.strip()
        
        success_count = 0
        
        if self.enable_discord:
            if self._send_discord_message(message):
                success_count += 1
        
        if self.enable_telegram:
            if self._send_telegram_message(message):
                success_count += 1
        
        return success_count > 0
    
    def _send_discord_message(self, message: str) -> bool:
        """Send message to Discord webhook."""
        if not requests or not self.discord_webhook:
            return False
        
        try:
            payload = {
                "content": message,
                "username": "Crypto Trading Bot"
            }
            
            response = requests.post(
                self.discord_webhook,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 204:
                self.logger.info("Discord notification sent successfully")
                return True
            else:
                self.logger.error(f"Discord notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Discord notification: {e}")
            return False
    
    def _send_telegram_message(self, message: str) -> bool:
        """Send message to Telegram."""
        if not requests or not self.telegram_token or not self.telegram_chat_id:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("Telegram notification sent successfully")
                return True
            else:
                self.logger.error(f"Telegram notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram notification: {e}")
            return False
    
    def _send_email(self, subject: str, message: str) -> bool:
        """Send email notification."""
        if not EMAIL_AVAILABLE or not self.email_address or not self.email_password:
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = self.email_address  # Send to self
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(message, 'plain'))
            
            # Connect to server and send
            server = smtplib.SMTP(self.email_server, self.email_port)
            server.starttls()
            server.login(self.email_address, self.email_password)
            
            text = msg.as_string()
            server.sendmail(self.email_address, self.email_address, text)
            server.quit()
            
            self.logger.info("Email notification sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {e}")
            return False
    
    def test_notifications(self) -> Dict[str, bool]:
        """
        Test all notification channels.
        
        Returns:
            Dictionary showing which channels work
        """
        results = {}
        test_message = "🧪 Test notification from Crypto Trading Algorithm"
        
        if self.enable_discord:
            results['discord'] = self._send_discord_message(test_message)
        
        if self.enable_telegram:
            results['telegram'] = self._send_telegram_message(test_message)
        
        if self.enable_email:
            results['email'] = self._send_email("Test Notification", test_message)
        
        return results


# Global notification manager instance
_notification_manager = None


def get_notification_manager() -> NotificationManager:
    """Get or create global notification manager instance."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager


# Convenience functions
def send_trade_alert(alert_type: str, symbol: str, price: float, 
                    message: str, urgent: bool = False) -> bool:
    """Send trade alert notification."""
    manager = get_notification_manager()
    return manager.send_trade_alert(alert_type, symbol, price, message, urgent)


def send_system_alert(alert_type: str, message: str, urgent: bool = True) -> bool:
    """Send system alert notification.""" 
    manager = get_notification_manager()
    return manager.send_system_alert(alert_type, message, urgent)


def send_performance_report(report_data: Dict) -> bool:
    """Send performance report notification."""
    manager = get_notification_manager()
    return manager.send_performance_report(report_data)
