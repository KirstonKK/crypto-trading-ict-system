#!/usr/bin/env python3
"""
TradingView Alert Simulator
Simulates TradingView alerts locally without needing ngrok
"""

import json
import time
import requests
from datetime import datetime
import random

class TradingViewSimulator:
    def __init__(self, webhook_url="http://localhost:8080/webhook/tradingview"):
        self.webhook_url = webhook_url
        self.symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT"]
        
    def generate_alert(self, symbol=None, action=None):
        """Generate a realistic TradingView alert"""
        
        if symbol is None:
            symbol = random.choice(self.symbols)
            
        if action is None:
            action = random.choice(["BUY", "SELL"])
            
        # Generate realistic price based on symbol
        price_ranges = {
            "BTCUSDT": (60000, 70000),
            "ETHUSDT": (2500, 3500),
            "BNBUSDT": (500, 700),
            "ADAUSDT": (0.3, 0.6)
        }
        
        price_min, price_max = price_ranges.get(symbol, (100, 1000))
        price = round(random.uniform(price_min, price_max), 2)
        
        alert = {
            "symbol": symbol,
            "action": action,
            "price": price,
            "timestamp": datetime.now().isoformat() + "Z",
            "confidence": round(random.uniform(0.6, 0.9), 2),
            "timeframe": random.choice(["1h", "4h", "1d"]),
            "stop_loss_pct": round(random.uniform(2.0, 5.0), 1),
            "volume_spike": random.choice([True, False]),
            "rsi": round(random.uniform(30, 70), 1)
        }
        
        return alert
        
    def send_alert(self, alert):
        """Send alert to webhook server"""
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(self.webhook_url, 
                                   json=alert, 
                                   headers=headers, 
                                   timeout=10)
            
            if response.status_code == 200:
                print("✅ Alert sent successfully: {alert['action']} {alert['symbol']} @ ${alert['price']}")
                return True
            else:
                print("❌ Failed to send alert: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print("❌ Connection error: {e}")
            return False
    
    def simulate_trading_session(self, duration_minutes=10, alert_interval=30):
        """Simulate a trading session with multiple alerts"""
        
        print("""
╔══════════════════════════════════════════════════════════════════╗
║               🎯 TRADINGVIEW ALERT SIMULATOR                     ║
╠══════════════════════════════════════════════════════════════════╣
║  Duration: {duration_minutes} minutes                                            ║
║  Alert Interval: {alert_interval} seconds                                    ║
║  Webhook URL: {self.webhook_url:<40} ║
╚══════════════════════════════════════════════════════════════════╝
""")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        alert_count = 0
        
        while time.time() < end_time:
            # Generate and send alert
            alert = self.generate_alert()
            success = self.send_alert(alert)
            
            if success:
                alert_count += 1
                
            # Wait for next alert
            print("⏱️  Waiting {alert_interval} seconds until next alert...")
            time.sleep(alert_interval)
            
        print("\n🎉 Simulation complete! Sent {alert_count} alerts in {duration_minutes} minutes")

def main():
    simulator = TradingViewSimulator()
    
    print("🚀 TradingView Alert Simulator")
    print("="*50)
    print("1. Single Alert Test")
    print("2. Trading Session (10 minutes)")
    print("3. Custom Alert")
    print("4. Exit")
    
    while True:
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            # Single alert test
            alert = simulator.generate_alert()
            print("\n📡 Sending test alert: {json.dumps(alert, indent=2)}")
            simulator.send_alert(alert)
            
        elif choice == "2":
            # Trading session
            duration = int(input("Duration in minutes (default 5): ") or "5")
            interval = int(input("Alert interval in seconds (default 30): ") or "30")
            simulator.simulate_trading_session(duration, interval)
            
        elif choice == "3":
            # Custom alert
            symbol = input("Symbol (default BTCUSDT): ").upper() or "BTCUSDT"
            action = input("Action BUY/SELL (default BUY): ").upper() or "BUY"
            alert = simulator.generate_alert(symbol, action)
            print("\n📡 Sending custom alert: {json.dumps(alert, indent=2)}")
            simulator.send_alert(alert)
            
        elif choice == "4":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    main()