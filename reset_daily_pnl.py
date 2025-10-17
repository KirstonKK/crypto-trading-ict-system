#!/usr/bin/env python3
"""
Daily PnL Reset Script
======================
Reset today's PnL to give a clean start for proper trading
"""

import sqlite3
from datetime import date, datetime

DATABASE_PATH = 'databases/trading_data.db'

def reset_daily_pnl():
    print("🔄 DAILY PNL RESET TOOL")
    print("=" * 60)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    today = date.today().isoformat()
    
    # Show current situation
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(realized_pnl), 0)
        FROM paper_trades 
        WHERE date(exit_time) = ? AND status = 'EOD_CLOSE'
    """, (today,))
    
    eod_result = cursor.fetchone()
    
    cursor.execute("""
        SELECT COALESCE(SUM(realized_pnl), 0)
        FROM paper_trades 
        WHERE status IN ('STOP_LOSS', 'TAKE_PROFIT', 'EOD_CLOSE')
        AND realized_pnl IS NOT NULL
    """)
    
    total_pnl = cursor.fetchone()[0]
    current_balance = 100 + total_pnl
    
    print("📊 CURRENT SITUATION:")
    print(f"   EOD Closures Today: {eod_result[0]} trades")
    print(f"   EOD PnL Impact: ${eod_result[1]:.2f}")
    print(f"   Current Balance: ${current_balance:.2f}")
    
    print("\n🎯 RESET OPTIONS:")
    print("1. Mark EOD closures as 'CLEANUP' (exclude from PnL)")
    print("2. Reset balance to $70 (pre-EOD level)")
    print("3. Reset balance to $100 (fresh start)")
    print("4. Cancel (keep current state)")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        print(f"\n🏷️ MARKING {eod_result[0]} EOD CLOSURES AS CLEANUP...")
        
        # Change EOD_CLOSE to CLEANUP status
        cursor.execute("""
            UPDATE paper_trades 
            SET status = 'CLEANUP'
            WHERE date(exit_time) = ? AND status = 'EOD_CLOSE'
        """, (today,))
        
        conn.commit()
        
        # Recalculate balance
        cursor.execute("""
            SELECT COALESCE(SUM(realized_pnl), 0)
            FROM paper_trades 
            WHERE status IN ('STOP_LOSS', 'TAKE_PROFIT')
            AND realized_pnl IS NOT NULL
        """)
        
        new_total_pnl = cursor.fetchone()[0]
        
        print("✅ CLEANUP COMPLETE!")
        print(f"   - {eod_result[0]} trades marked as CLEANUP")
        print(f"   - New balance: ${100 + new_total_pnl:.2f}")
        print("   - Daily PnL calculation will exclude cleanup trades")
        
    elif choice == "2":
        print("\n💰 RESETTING BALANCE TO $70...")
        
        # Add a balance adjustment trade
        now = datetime.now().isoformat()
        adjustment = 70 - current_balance
        
        cursor.execute("""
            INSERT INTO paper_trades 
            (symbol, direction, entry_price, exit_price, position_size,
             entry_time, exit_time, status, realized_pnl)
            VALUES ('BALANCE', 'ADJUSTMENT', 0, 0, 1, ?, ?, 'ADJUSTMENT', ?)
        """, (now, now, adjustment))
        
        conn.commit()
        
        print("✅ BALANCE RESET COMPLETE!")
        print("   - Adjustment: ${adjustment:.2f}")
        print("   - New balance: $70.00")
        
    elif choice == "3":
        print("\n🆕 RESETTING BALANCE TO $100 (FRESH START)...")
        
        # Add a balance adjustment trade
        now = datetime.now().isoformat()
        adjustment = 100 - current_balance
        
        cursor.execute("""
            INSERT INTO paper_trades 
            (symbol, direction, entry_price, exit_price, position_size,
             entry_time, exit_time, status, realized_pnl)
            VALUES ('BALANCE', 'ADJUSTMENT', 0, 0, 1, ?, ?, 'ADJUSTMENT', ?)
        """, (now, now, adjustment))
        
        conn.commit()
        
        print("✅ FRESH START COMPLETE!")
        print("   - Adjustment: ${adjustment:.2f}")
        print("   - New balance: $100.00")
        print("   - Ready for clean trading!")
        
    elif choice == "4":
        print("❌ Reset cancelled")
        
    else:
        print("❌ Invalid choice")
    
    conn.close()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Restart trading systems to reload balance")
    print("2. Monitor stop loss system closely")
    print("3. Verify 1% risk management is working")
    print("4. EOD closure will prevent future accumulation")

if __name__ == "__main__":
    reset_daily_pnl()