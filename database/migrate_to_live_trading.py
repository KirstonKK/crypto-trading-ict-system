#!/usr/bin/env python3
"""
Database Migration Script: Paper Trading → Live Trading
=======================================================

This script migrates the database schema to support live trading:
1. Adds trade_type column to distinguish live vs paper trades
2. Adds order_id for Bybit order tracking
3. Adds order_link_id for custom order tracking
4. Adds execution_price for actual fill price
5. Adds commission and commission_asset for trading fees
6. Backs up existing database before migration

Usage:
    python database/migrate_to_live_trading.py
"""

import sqlite3
import shutil
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backup_database(db_path: str) -> str:
    """Create a backup of the database before migration
    
    Args:
        db_path: Path to database file
        
    Returns:
        Path to backup file
    """
    backup_dir = Path("backups/database_migrations")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"trading_db_backup_{timestamp}.db"
    
    shutil.copy2(db_path, backup_path)
    logger.info(f"✅ Database backed up to: {backup_path}")
    
    return str(backup_path)


def check_column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Check if a column already exists in a table
    
    Args:
        conn: Database connection
        table: Table name
        column: Column name
        
    Returns:
        True if column exists, False otherwise
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def migrate_paper_trades_table(conn: sqlite3.Connection):
    """Add new columns to paper_trades table for live trading
    
    Args:
        conn: Database connection
    """
    cursor = conn.cursor()
    
    # List of new columns to add
    new_columns = [
        ("trade_type", "TEXT DEFAULT 'paper'", "Distinguish between live and paper trades"),
        ("order_id", "TEXT", "Bybit order ID for live trades"),
        ("order_link_id", "TEXT", "Custom order tracking ID"),
        ("execution_price", "REAL", "Actual fill price from exchange"),
        ("commission", "REAL", "Trading fees paid"),
        ("commission_asset", "TEXT", "Asset used for commission (e.g., USDT)")
    ]
    
    for column_name, column_type, description in new_columns:
        if not check_column_exists(conn, "paper_trades", column_name):
            logger.info(f"  Adding column: {column_name} ({description})")
            cursor.execute(f"ALTER TABLE paper_trades ADD COLUMN {column_name} {column_type}")
            conn.commit()
            logger.info(f"  ✅ Added {column_name}")
        else:
            logger.info(f"  ⏭️  Column {column_name} already exists")
    
    # Create index on order_id for faster lookups
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_id ON paper_trades(order_id)")
        conn.commit()
        logger.info("  ✅ Created index on order_id")
    except Exception as e:
        logger.warning(f"  ⚠️  Could not create index: {e}")


def update_existing_trades(conn: sqlite3.Connection):
    """Update existing trades to mark them as 'paper' type
    
    Args:
        conn: Database connection
    """
    cursor = conn.cursor()
    
    # Mark all existing trades as paper trades
    cursor.execute("""
        UPDATE paper_trades 
        SET trade_type = 'paper' 
        WHERE trade_type IS NULL OR trade_type = ''
    """)
    
    rows_updated = cursor.rowcount
    conn.commit()
    
    if rows_updated > 0:
        logger.info(f"  ✅ Marked {rows_updated} existing trades as 'paper' type")
    else:
        logger.info("  ℹ️  No existing trades to update")


def verify_migration(conn: sqlite3.Connection) -> bool:
    """Verify that all columns were added successfully
    
    Args:
        conn: Database connection
        
    Returns:
        True if migration successful, False otherwise
    """
    required_columns = [
        "trade_type",
        "order_id", 
        "order_link_id",
        "execution_price",
        "commission",
        "commission_asset"
    ]
    
    all_present = True
    for column in required_columns:
        if not check_column_exists(conn, "paper_trades", column):
            logger.error(f"  ❌ Column {column} not found after migration!")
            all_present = False
    
    if all_present:
        logger.info("  ✅ All columns verified successfully")
    
    return all_present


def main():
    """Main migration function"""
    logger.info("=" * 60)
    logger.info("DATABASE MIGRATION: Paper Trading → Live Trading")
    logger.info("=" * 60)
    
    # Database path
    db_path = "databases/trading_data.db"
    
    # Check if database exists
    if not Path(db_path).exists():
        logger.error(f"❌ Database not found: {db_path}")
        return False
    
    try:
        # Step 1: Backup database
        logger.info("\n📦 Step 1: Creating backup...")
        backup_path = backup_database(db_path)
        
        # Step 2: Connect to database
        logger.info("\n🔌 Step 2: Connecting to database...")
        conn = sqlite3.connect(db_path)
        logger.info(f"  ✅ Connected to: {db_path}")
        
        # Step 3: Add new columns
        logger.info("\n🔧 Step 3: Adding new columns to paper_trades table...")
        migrate_paper_trades_table(conn)
        
        # Step 4: Update existing trades
        logger.info("\n📝 Step 4: Updating existing trades...")
        update_existing_trades(conn)
        
        # Step 5: Verify migration
        logger.info("\n✓ Step 5: Verifying migration...")
        success = verify_migration(conn)
        
        # Close connection
        conn.close()
        
        # Final status
        logger.info("\n" + "=" * 60)
        if success:
            logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY")
            logger.info(f"📦 Backup saved at: {backup_path}")
            logger.info("🚀 Database ready for live trading!")
        else:
            logger.error("❌ MIGRATION FAILED - Please check errors above")
            logger.info(f"💾 Database backup available at: {backup_path}")
        logger.info("=" * 60)
        
        return success
        
    except Exception as e:
        logger.error(f"\n❌ Migration failed with error: {e}")
        logger.error(f"💾 Restore from backup: {backup_path if 'backup_path' in locals() else 'N/A'}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
