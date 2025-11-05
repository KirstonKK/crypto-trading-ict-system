#!/bin/bash

# 🛡️ CRITICAL FILES BACKUP SCRIPT
# Backs up all critical system files before any operation

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/critical_${TIMESTAMP}"

echo "🛡️  Creating backup of critical files..."
echo "Backup location: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
echo "📊 Backing up database..."
if [ -f "databases/trading_data.db" ]; then
    cp "databases/trading_data.db" "$BACKUP_DIR/trading_data.db"
    echo "   ✅ Database backed up"
else
    echo "   ⚠️  Database not found!"
fi

# Backup persistence directory
echo "💾 Backing up persistence files..."
if [ -d "data/persistence" ]; then
    cp -r "data/persistence" "$BACKUP_DIR/"
    echo "   ✅ Persistence files backed up"
else
    echo "   ⚠️  Persistence directory not found!"
fi

# Backup config
echo "⚙️  Backing up configuration..."
if [ -d "config" ]; then
    cp -r "config" "$BACKUP_DIR/"
    echo "   ✅ Configuration backed up"
else
    echo "   ⚠️  Config directory not found!"
fi

# Create manifest
echo "📝 Creating backup manifest..."
cat > "$BACKUP_DIR/MANIFEST.txt" << EOF
Backup Created: $TIMESTAMP
System: Trading Algorithm
Type: Critical Files Backup

Contents:
- Database: trading_data.db
- Persistence: data/persistence/
- Configuration: config/

This backup contains all critical system state and should be
preserved indefinitely. DO NOT DELETE without explicit approval.

To restore:
1. Stop all systems
2. Copy files back to original locations
3. Restart systems
EOF

echo ""
echo "✅ Backup complete: $BACKUP_DIR"
echo ""
echo "📋 Backup contains:"
ls -lh "$BACKUP_DIR"

# Keep only last 50 backups
echo ""
echo "🧹 Cleaning old backups (keeping last 50)..."
cd backups
ls -t | grep critical_ | tail -n +51 | xargs -I {} rm -rf {}
cd ..

echo "✅ Backup script complete"
