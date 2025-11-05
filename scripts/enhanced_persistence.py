#!/usr/bin/env python3
"""
Enhanced Data Persistence System
Ensures trading data survives system restarts
"""

import json
import os
import datetime
import requests
from pathlib import Path

class TradingDataPersistence:
    def __init__(self, base_dir="/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data" / "persistence"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.data_dir / "trading_state.json"
        self.daily_file = self.data_dir / f"daily_{datetime.date.today().strftime('%Y%m%d')}.json"
        
    def save_current_state(self):
        """Save current system state from database"""
        try:
            import sqlite3
            
            # Connect to database
            db_path = self.base_dir / "trading_data.db"
            if not db_path.exists():
                print("Database not found at {db_path}")
                return None
                
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            today = datetime.date.today().strftime('%Y-%m-%d')
            
            # Get scan count for today
            cursor.execute("""
                SELECT COUNT(*) FROM scan_history 
                WHERE date(timestamp) = ?
            """, (today,))
            scan_count = cursor.fetchone()[0]
            
            # Get signals for today
            cursor.execute("""
                SELECT COUNT(*) FROM signals 
                WHERE date(entry_time) = ?
            """, (today,))
            signals_count = cursor.fetchone()[0]
            
            # Calculate paper balance from PnL (default 100.0 if no trades)
            cursor.execute("""
                SELECT SUM(realized_pnl) FROM paper_trades 
                WHERE status = 'CLOSED' AND realized_pnl IS NOT NULL
            """)
            result = cursor.fetchone()
            total_pnl = float(result[0]) if result and result[0] else 0.0
            paper_balance = 100.0 + total_pnl  # Starting balance + realized PnL
            
            conn.close()
            
            state_data = {
                "last_update": datetime.datetime.now().isoformat(),
                "scan_count": scan_count,
                "signals_today": signals_count,
                "paper_balance": paper_balance,
                "service_status": "restored_from_db",
                "session_start": today,
                "ml_model_status": {"loaded": True, "status": "loaded"},
                "symbols": ["BTC", "SOL", "ETH", "XRP"]
            }
            
            # Save current state
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            # Save daily snapshot
            daily_data = {
                "date": today,
                "final_scan_count": scan_count,
                "total_signals": signals_count,
                "final_paper_balance": paper_balance,
                "session_complete": False,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            with open(self.daily_file, 'w') as f:
                json.dump(daily_data, f, indent=2)
            
            return state_data
            
        except Exception:
            print("Error saving state from database")
            return None
    
    def get_last_state(self):
        """Get the last saved state for restoration"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            return None
        except Exception:
            print("Error loading state")
            return None

# Create and use persistence system
if __name__ == "__main__":
    persistence = TradingDataPersistence()
    
    print("💾 ENHANCED PERSISTENCE SYSTEM")
    print("=" * 40)
    
    # Save current state
    current_state = persistence.save_current_state()
    
    if current_state:
        print("✅ Current state saved successfully!")
        print("   📈 Scan Count: {current_state['scan_count']}")
        print("   🎯 Signals: {current_state['signals_today']}")
        print("   💰 Balance: ${current_state['paper_balance']:.2f}")
        print("   📁 State File: {persistence.state_file}")
        print("   📅 Daily File: {persistence.daily_file}")
        print()
        print("🔄 On restart, this data can be restored!")
    else:
        print("❌ Failed to save current state")
    
    # Show how to restore
    print("🚀 TO RESTORE DATA ON RESTART:")
    print("   1. Load state from:", persistence.state_file)
    print("   2. Resume scan count from saved value")
    print("   3. Restore paper balance and signals")
    print("   4. Continue ML training data collection")