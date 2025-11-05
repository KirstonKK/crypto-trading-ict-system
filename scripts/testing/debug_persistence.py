#!/usr/bin/env python3

import sqlite3
from datetime import datetime, date
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_load_trading_state():
    """Debug the exact issue in _load_trading_state method"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        today = date.today().isoformat()
        
        logger.info(f"🔄 Debugging trading state restoration for {today}...")
        
        # 1. RESTORE SCAN COUNT
        logger.info("📊 Step 1: Restoring scan count...")
        cursor.execute("SELECT COUNT(*) FROM scan_history WHERE date(timestamp) = ?", (today,))
        scan_count = cursor.fetchone()[0]
        logger.info(f"📊 Restored scan count: {scan_count}")
        
        # 2. RESTORE LIVE SIGNALS
        logger.info("🎯 Step 2: Restoring live signals...")
        cursor.execute("""
            SELECT signal_id, symbol, direction, entry_price, stop_loss, take_profit,
                   confluence_score, timeframes, ict_concepts, session, market_regime,
                   directional_bias, signal_strength, status, entry_time
            FROM signals 
            WHERE date(entry_time) = ? AND status = 'ACTIVE'
            ORDER BY entry_time DESC
        """, (today,))
        
        signals_data = cursor.fetchall()
        logger.info(f"🎯 Found {len(signals_data)} active signals")
        
        # Count today's signals
        cursor.execute("SELECT COUNT(*) FROM signals WHERE date(entry_time) = ?", (today,))
        signals_today = cursor.fetchone()[0]
        logger.info(f"🎯 Total signals today: {signals_today}")
        
        # Count all-time signals
        cursor.execute("SELECT COUNT(*) FROM signals")
        total_signals = cursor.fetchone()[0]
        logger.info(f"🎯 Total all-time signals: {total_signals}")
        
        # 3. RESTORE TODAY'S PAPER TRADES
        logger.info("💰 Step 3: Restoring paper trades...")
        
        # Load open trades from today
        logger.info("💰 Step 3a: Loading open trades...")
        cursor.execute("""
            SELECT id, signal_id, symbol, direction, entry_price, position_size, 
                   stop_loss, take_profit, entry_time, status, current_price, 
                   unrealized_pnl, risk_amount
            FROM paper_trades 
            WHERE date(entry_time) = ? AND status = 'OPEN'
        """, (today,))
        
        open_trades = cursor.fetchall()
        logger.info(f"💰 Found {len(open_trades)} open trades")
        
        # Load completed trades from today  
        logger.info("💰 Step 3b: Loading closed trades...")
        cursor.execute("""
            SELECT id, signal_id, symbol, direction, entry_price, position_size,
                   stop_loss, take_profit, entry_time, exit_time, exit_price,
                   status, realized_pnl, risk_amount
            FROM paper_trades 
            WHERE date(entry_time) = ? AND status = 'CLOSED'
        """, (today,))
        
        closed_trades = cursor.fetchall()
        logger.info(f"💰 Found {len(closed_trades)} closed trades")
        
        # 4. CALCULATE PAPER BALANCE
        logger.info("💰 Step 4: Calculating paper balance...")
        base_balance = 100.0
        
        cursor.execute("""
            SELECT SUM(realized_pnl) FROM paper_trades 
            WHERE status = 'CLOSED' AND realized_pnl IS NOT NULL
        """)
        result = cursor.fetchone()
        total_realized_pnl = float(result[0]) if result and result[0] else 0.0
        
        paper_balance = base_balance + total_realized_pnl
        logger.info(f"💰 Paper balance: ${paper_balance:.2f} (${base_balance:.2f} + ${total_realized_pnl:.2f} PnL)")
        
        # 5. RESTORE TRADING JOURNAL
        logger.info("📝 Step 5: Restoring trading journal...")
        cursor.execute("""
            SELECT entry_type, title, content, signal_id, created_at
            FROM journal_entries 
            WHERE date(created_at) = ?
            ORDER BY created_at DESC
        """, (today,))
        
        journal_entries = cursor.fetchall()
        logger.info(f"📝 Found {len(journal_entries)} journal entries")
        
        conn.close()
        
        logger.info("✅ All steps completed successfully!")
        logger.info(f"📊 Final state: {scan_count} scans, {signals_today} signals, {len(open_trades)} open trades, ${paper_balance:.2f} balance")
        
    except Exception as e:
        logger.error(f"❌ Debug failed at step: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_load_trading_state()