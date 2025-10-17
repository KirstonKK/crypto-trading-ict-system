#!/usr/bin/env python3
"""
Visual TradingView Alert Monitor
Real-time dashboard to monitor webhook alerts from TradingView
"""

import asyncio
import json
import time
import threading
from datetime import datetime
from collections import deque
import requests
import os
import sys

# Add the project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class AlertMonitor:
    def __init__(self, webhook_url="http://localhost:8080", max_alerts=50):
        self.webhook_url = webhook_url
        self.alerts = deque(maxlen=max_alerts)
        self.stats = {
            'total_alerts': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'last_alert': None,
            'uptime': datetime.now()
        }
        self.running = False
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def format_timestamp(self, timestamp):
        """Format timestamp for display"""
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime('%H:%M:%S')
            except:
                return timestamp[:8] if len(timestamp) > 8 else timestamp
        return datetime.now().strftime('%H:%M:%S')
    
    def format_price(self, price):
        """Format price for display"""
        if isinstance(price, (int, float)):
            return f"${price:,.2f}"
        return str(price)
    
    def get_signal_color(self, action):
        """Get ANSI color code for signal type"""
        colors = {
            'BUY': '\033[92m',   # Green
            'SELL': '\033[91m',  # Red
            'LONG': '\033[92m',  # Green
            'SHORT': '\033[91m', # Red
        }
        return colors.get(action.upper(), '\033[93m')  # Yellow for unknown
    
    def reset_color(self):
        """Reset ANSI color"""
        return '\033[0m'
    
    def test_webhook_connection(self):
        """Test if webhook server is running"""
        try:
            response = requests.get(f"{self.webhook_url}/health", timeout=2)
            return response.status_code == 200
        except:
            try:
                # Fallback: test webhook endpoint
                test_data = {"test": "connection"}
                response = requests.post(f"{self.webhook_url}/webhook/tradingview", 
                                       json=test_data, timeout=2)
                return True  # Any response means server is up
            except:
                return False
    
    def simulate_alert(self, symbol="BTCUSDT", action="BUY"):
        """Simulate a TradingView alert for testing"""
        import random
        
        price_ranges = {
            "BTCUSDT": (60000, 70000),
            "ETHUSDT": (2500, 3500),
            "BNBUSDT": (500, 700),
            "ADAUSDT": (0.3, 0.6)
        }
        
        price_min, price_max = price_ranges.get(symbol, (100, 1000))
        
        alert = {
            "symbol": symbol,
            "action": action,
            "price": round(random.uniform(price_min, price_max), 2),
            "timestamp": datetime.now().isoformat() + "Z",
            "confidence": round(random.uniform(0.6, 0.9), 2),
            "timeframe": random.choice(["1h", "4h", "1d"]),
            "rsi": round(random.uniform(30, 70), 1)
        }
        
        try:
            response = requests.post(f"{self.webhook_url}/webhook/tradingview", 
                                   json=alert, timeout=5)
            if response.status_code == 200:
                self.add_alert(alert, "✅ SUCCESS")
            else:
                self.add_alert(alert, f"❌ FAILED ({response.status_code})")
        except Exception as e:
            self.add_alert(alert, f"❌ ERROR: {str(e)[:30]}")
    
    def add_alert(self, alert_data, status="✅ RECEIVED"):
        """Add alert to monitoring queue"""
        alert = {
            'data': alert_data,
            'status': status,
            'received_at': datetime.now(),
            'display_time': self.format_timestamp(alert_data.get('timestamp', ''))
        }
        
        self.alerts.appendleft(alert)
        self.update_stats(alert_data)
    
    def update_stats(self, alert_data):
        """Update statistics"""
        self.stats['total_alerts'] += 1
        self.stats['last_alert'] = datetime.now()
        
        action = alert_data.get('action', '').upper()
        if action in ['BUY', 'LONG']:
            self.stats['buy_signals'] += 1
        elif action in ['SELL', 'SHORT']:
            self.stats['sell_signals'] += 1
    
    def draw_header(self):
        """Draw the dashboard header"""
        uptime = datetime.now() - self.stats['uptime']
        uptime_str = f"{int(uptime.total_seconds() // 60)}m {int(uptime.total_seconds() % 60)}s"
        
        webhook_status = "🟢 ONLINE" if self.test_webhook_connection() else "🔴 OFFLINE"
        
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 20 + "🎯 TRADINGVIEW ALERT MONITOR" + " " * 29 + "║")
        print("╠" + "═" * 78 + "╣")
        print(f"║ Webhook: {webhook_status:<10} │ Uptime: {uptime_str:<8} │ Total Alerts: {self.stats['total_alerts']:<6} ║")
        print(f"║ BUY: {self.stats['buy_signals']:<6} │ SELL: {self.stats['sell_signals']:<6} │ URL: {self.webhook_url:<25} ║")
        print("╚" + "═" * 78 + "╝")
        print()
    
    def draw_alerts_table(self):
        """Draw the alerts table"""
        if not self.alerts:
            print("📭 No alerts received yet...")
            print("\n💡 Test options:")
            print("   • Press 's' to simulate BUY alert")
            print("   • Press 'x' to simulate SELL alert")
            print("   • Set up TradingView Pine Script for real alerts")
            return
        
        print("┌──────────┬────────────┬────────────┬─────────────┬──────────┬────────────┐")
        print("│   TIME   │   SYMBOL   │   ACTION   │    PRICE    │   RSI    │   STATUS   │")
        print("├──────────┼────────────┼────────────┼─────────────┼──────────┼────────────┤")
        
        for alert in list(self.alerts)[:15]:  # Show last 15 alerts
            data = alert['data']
            symbol = data.get('symbol', 'N/A')[:10]
            action = data.get('action', 'N/A')[:10]
            price = self.format_price(data.get('price', 0))[:11]
            rsi = str(data.get('rsi', 'N/A'))[:8]
            status = alert['status'][:10]
            
            color = self.get_signal_color(action)
            reset = self.reset_color()
            
            print(f"│ {alert['display_time']:<8} │ {symbol:<10} │ {color}{action:<10}{reset} │ {price:<11} │ {rsi:<8} │ {status:<10} │")
        
        print("└──────────┴────────────┴────────────┴─────────────┴──────────┴────────────┘")
    
    def draw_instructions(self):
        """Draw usage instructions"""
        print("\n📋 Controls:")
        print("   🔹 's' - Simulate BUY alert    🔹 'x' - Simulate SELL alert")
        print("   🔹 'c' - Clear alerts         🔹 'q' - Quit monitor")
        print("   🔹 'r' - Refresh display      🔹 't' - Test webhook connection")
        print("\n🌐 TradingView Webhook URL:")
        print(f"   {self.webhook_url}/webhook/tradingview")
        
        # Check for ngrok
        try:
            import subprocess
            result = subprocess.run(['pgrep', 'ngrok'], capture_output=True)
            if result.returncode == 0:
                print("\n🔗 ngrok tunnel should be running for external access")
            else:
                print("\n⚠️  ngrok not detected - only local testing available")
        except:
            pass
    
    def handle_input(self):
        """Handle user input in separate thread"""
        import select
        import sys
        import tty
        import termios
        
        # Set terminal to raw mode for single character input
        old_settings = termios.tcgetattr(sys.stdin)
        
        try:
            tty.setraw(sys.stdin)
            while self.running:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    ch = sys.stdin.read(1)
                    
                    if ch.lower() == 'q':
                        self.running = False
                        break
                    elif ch.lower() == 's':
                        self.simulate_alert("BTCUSDT", "BUY")
                    elif ch.lower() == 'x':
                        self.simulate_alert("ETHUSDT", "SELL")
                    elif ch.lower() == 'c':
                        self.alerts.clear()
                        self.stats['total_alerts'] = 0
                        self.stats['buy_signals'] = 0
                        self.stats['sell_signals'] = 0
                    elif ch.lower() == 't':
                        connection_status = self.test_webhook_connection()
                        status_msg = "✅ Connected" if connection_status else "❌ Disconnected"
                        test_alert = {
                            "symbol": "TEST",
                            "action": "STATUS",
                            "price": 0,
                            "timestamp": datetime.now().isoformat() + "Z",
                            "message": f"Connection test: {status_msg}"
                        }
                        self.add_alert(test_alert, status_msg)
                        
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    
    def run(self):
        """Run the monitoring dashboard"""
        self.running = True
        
        # Start input handler in separate thread
        input_thread = threading.Thread(target=self.handle_input, daemon=True)
        input_thread.start()
        
        print("🚀 Starting TradingView Alert Monitor...")
        time.sleep(1)
        
        try:
            while self.running:
                self.clear_screen()
                self.draw_header()
                self.draw_alerts_table()
                self.draw_instructions()
                
                time.sleep(1)  # Refresh every second
                
        except KeyboardInterrupt:
            self.running = False
            
        print("\n👋 Monitor stopped. Goodbye!")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TradingView Alert Monitor')
    parser.add_argument('--url', default='http://localhost:8080', 
                       help='Webhook server URL (default: http://localhost:8080)')
    parser.add_argument('--max-alerts', type=int, default=50,
                       help='Maximum alerts to keep in memory (default: 50)')
    
    args = parser.parse_args()
    
    monitor = AlertMonitor(args.url, args.max_alerts)
    monitor.run()

if __name__ == "__main__":
    main()