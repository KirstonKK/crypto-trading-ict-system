"""
Notification Service for ICT Trading System
Supports Email, SMS, and Push notifications for trading events
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

class NotificationService:
    """Multi-channel notification service"""
    
    def __init__(self):
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        
        # SMS configuration (Twilio)
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_from = os.getenv('TWILIO_FROM_NUMBER')
        
        # Push notification configuration
        self.push_enabled = os.getenv('PUSH_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
        
        # User notification preferences (load from database)
        self.user_preferences = {}
    
    def send_email(self, to_email: str, subject: str, body: str, html_body: str = None):
        """Send email notification"""
        if not self.smtp_user or not self.smtp_password:
            print("⚠️  Email not configured, skipping email notification")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add plain text and HTML versions
            msg.attach(MIMEText(body, 'plain'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def send_sms(self, to_number: str, message: str):
        """Send SMS notification via Twilio"""
        if not self.twilio_sid or not self.twilio_token:
            print("⚠️  SMS not configured, skipping SMS notification")
            return False
        
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"
            
            response = requests.post(
                url,
                auth=(self.twilio_sid, self.twilio_token),
                data={
                    'From': self.twilio_from,
                    'To': to_number,
                    'Body': message
                }
            )
            
            if response.status_code == 201:
                print(f"✅ SMS sent to {to_number}")
                return True
            else:
                print(f"❌ SMS failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send SMS: {e}")
            return False
    
    def send_push(self, title: str, body: str):
        """Send push notification (placeholder for Firebase/OneSignal integration)"""
        if not self.push_enabled:
            return False
        
        # TODO: Implement Firebase Cloud Messaging or OneSignal
        print(f"📱 Push notification: {title} - {body}")
        return True
    
    # ============ Trading Event Notifications ============
    
    def notify_new_signal(self, signal: Dict, recipients: List[str]):
        """Notify about new trading signal"""
        symbol = signal.get('symbol', 'Unknown')
        direction = signal.get('direction', 'Unknown')
        entry_price = signal.get('entry_price', 0)
        confidence = signal.get('confluence_score', 0)
        
        subject = f"🎯 New {direction} Signal: {symbol}"
        
        body = f"""
New Trading Signal Generated

Symbol: {symbol}
Direction: {direction}
Entry Price: ${entry_price:,.2f}
Confidence: {confidence:.1f}%
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Stop Loss: ${signal.get('stop_loss', 0):,.2f}
Take Profit: ${signal.get('take_profit', 0):,.2f}

Check your dashboard for more details.
        """
        
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px;">
        <h2 style="color: #6366f1;">🎯 New {direction} Signal</h2>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <p><strong>Symbol:</strong> {symbol}</p>
            <p><strong>Direction:</strong> <span style="color: {'#10b981' if direction == 'BUY' else '#ef4444'};">{direction}</span></p>
            <p><strong>Entry Price:</strong> ${entry_price:,.2f}</p>
            <p><strong>Confidence:</strong> {confidence:.1f}%</p>
        </div>
        <div style="margin: 20px 0;">
            <p><strong>Stop Loss:</strong> ${signal.get('stop_loss', 0):,.2f}</p>
            <p><strong>Take Profit:</strong> ${signal.get('take_profit', 0):,.2f}</p>
        </div>
        <p style="color: #666; font-size: 14px;">Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <a href="http://localhost:3000" style="display: inline-block; margin-top: 20px; padding: 12px 24px; background: #6366f1; color: white; text-decoration: none; border-radius: 5px;">View Dashboard</a>
    </div>
</body>
</html>
        """
        
        # Send to all recipients
        for recipient in recipients:
            self.send_email(recipient, subject, body, html_body)
    
    def notify_trade_closed(self, trade: Dict, recipients: List[str]):
        """Notify about closed trade"""
        symbol = trade.get('symbol', 'Unknown')
        direction = trade.get('direction', 'Unknown')
        pnl = trade.get('realized_pnl', 0)
        status = trade.get('status', 'CLOSED')
        
        is_win = pnl > 0
        emoji = "✅" if is_win else "❌"
        
        subject = f"{emoji} Trade Closed: {symbol} {'+' if is_win else ''}{pnl:.2f} USD"
        
        body = f"""
Trade Closed

Symbol: {symbol}
Direction: {direction}
Status: {status}
P&L: ${pnl:,.2f}

Entry: ${trade.get('entry_price', 0):,.2f}
Exit: ${trade.get('exit_price', 0):,.2f}
Position Size: {trade.get('position_size', 0):.6f}

Check your dashboard for updated performance metrics.
        """
        
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px;">
        <h2 style="color: {'#10b981' if is_win else '#ef4444'};">{emoji} Trade Closed</h2>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <p><strong>Symbol:</strong> {symbol}</p>
            <p><strong>Direction:</strong> {direction}</p>
            <p><strong>Status:</strong> {status}</p>
            <p><strong>P&L:</strong> <span style="color: {'#10b981' if is_win else '#ef4444'}; font-size: 24px; font-weight: bold;">${pnl:,.2f}</span></p>
        </div>
        <div style="margin: 20px 0;">
            <p><strong>Entry:</strong> ${trade.get('entry_price', 0):,.2f}</p>
            <p><strong>Exit:</strong> ${trade.get('exit_price', 0):,.2f}</p>
            <p><strong>Position Size:</strong> {trade.get('position_size', 0):.6f}</p>
        </div>
        <a href="http://localhost:3000" style="display: inline-block; margin-top: 20px; padding: 12px 24px; background: #6366f1; color: white; text-decoration: none; border-radius: 5px;">View Dashboard</a>
    </div>
</body>
</html>
        """
        
        # Send to all recipients
        for recipient in recipients:
            self.send_email(recipient, subject, body, html_body)
    
    def notify_daily_summary(self, stats: Dict, recipients: List[str]):
        """Send daily performance summary"""
        subject = f"📊 Daily Trading Summary - {datetime.now().strftime('%Y-%m-%d')}"
        
        total_pnl = stats.get('total_pnl', 0)
        trades = stats.get('total_trades', 0)
        win_rate = stats.get('win_rate', 0)
        
        body = f"""
Daily Trading Summary

Date: {datetime.now().strftime('%Y-%m-%d')}

Total Trades: {trades}
Total P&L: ${total_pnl:,.2f}
Win Rate: {win_rate:.1f}%
Best Trade: ${stats.get('best_trade', 0):,.2f}
Worst Trade: ${stats.get('worst_trade', 0):,.2f}

Keep up the great work!
        """
        
        # Send to all recipients
        for recipient in recipients:
            self.send_email(recipient, subject, body)

# Global instance
notification_service = NotificationService()

if __name__ == '__main__':
    # Test notifications
    print("🧪 Testing Notification Service...")
    
    # Test signal notification
    test_signal = {
        'symbol': 'BTCUSDT',
        'direction': 'BUY',
        'entry_price': 65000,
        'stop_loss': 64000,
        'take_profit': 68000,
        'confluence_score': 85
    }
    
    test_email = os.getenv('TEST_EMAIL', 'trader@example.com')
    notification_service.notify_new_signal(test_signal, [test_email])
    
    print("✅ Notification service test complete")
