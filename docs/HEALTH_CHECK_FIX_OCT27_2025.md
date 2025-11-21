# Health Check Database Error Fix - October 27, 2025

## Problem
When running the Docker container, the health check endpoint (`/health`) was failing with:
```
Database error: file is not a database
```

This happened because the health check queries the SQLite database without error handling, and if the mounted `./data/trading.db` file is corrupted or empty, it crashes.

## Root Cause
1. **Health Check Endpoint** (`core/monitors/ict_enhanced_monitor.py` line 1489):
   - No try/except block around database queries
   - Crashes if database is corrupted, missing, or incompatible

2. **Docker Volume Mount** (`docker-compose.yml` line 36):
   - Mounts local `./data:/app/data` directory
   - If local `trading.db` is corrupted, container uses corrupted file

3. **No Database Validation**:
   - Docker entrypoint didn't validate database integrity on startup
   - Corrupted databases were not detected or fixed

## Solution Implemented

### 1. Health Check Error Handling
**File**: `core/monitors/ict_enhanced_monitor.py`

Added try/except block to health check endpoint:
```python
@self.app.route('/health')
def health_check():
    """Health check endpoint with database error handling"""
    try:
        # Query database for today's trades
        conn = self.crypto_monitor.db._get_connection()
        cursor.execute("""SELECT COUNT(*) FROM paper_trades...""")
        today_signals = cursor.fetchone()[0]
        
        return jsonify({
            'status': 'operational',
            'database': 'healthy',
            # ... other status info
        })
    except Exception as e:
        logger.error(f"Health check database error: {e}")
        return jsonify({
            'status': 'degraded',
            'database': 'error',
            'error': str(e),
            'message': 'Database error - system may need reinitialization'
        }), 500
```

**Benefits**:
- Health check doesn't crash on database errors
- Returns HTTP 500 with `status: degraded` instead of crashing
- Logs error for debugging
- Container stays running even if database is corrupted

### 2. Database Validation in Docker Entrypoint
**File**: `docker/docker-entrypoint.sh`

Added validation to check if database is valid SQLite file:
```bash
# Check if file is actually a valid SQLite database
if ! file "$DATABASE_PATH" | grep -q "SQLite"; then
    log_error "Database file exists but is not a valid SQLite database!"
    log_warn "This may be a corrupted or empty file."
    log_info "Creating backup and removing corrupted database..."
    mv "$DATABASE_PATH" "${DATABASE_PATH}.corrupted.$(date +%Y%m%d_%H%M%S)"
    log_success "Corrupted database backed up. New database will be created."
else
    # Check database integrity
    if sqlite3 "$DATABASE_PATH" "PRAGMA integrity_check;" > /dev/null 2>&1; then
        log_success "Database integrity check passed"
    else
        log_error "Database integrity check failed!"
        log_info "Creating database backup and removing corrupted database..."
        mv "$DATABASE_PATH" "${DATABASE_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
        log_success "Corrupted database backed up. New database will be created."
    fi
fi
```

**Benefits**:
- Detects corrupted databases on container startup
- Backs up corrupted files with timestamp
- Removes corrupted database so fresh one is created
- Prevents "file is not a database" errors

## How to Deploy Fix

### Option 1: Pull Latest Code from GitHub
```bash
# Pull latest changes
git pull origin main

# Rebuild Docker image
docker build -t kirston/crypto-trading-ict:latest .

# Stop old container
docker-compose down

# Remove corrupted database (optional, entrypoint will handle it)
rm ./data/trading.db

# Start new container
docker-compose up -d

# Check health
curl http://localhost:5001/health
```

### Option 2: Pull Updated Docker Image
Once the image is pushed to Docker Hub:
```bash
# Pull latest image
docker pull kirston/crypto-trading-ict:latest

# Stop old container
docker-compose down

# Remove corrupted database (optional)
rm ./data/trading.db

# Start new container
docker-compose up -d

# Check health
curl http://localhost:5001/health
```

### Option 3: Fix Local Corrupted Database
If you want to keep using the current image:
```bash
# Stop container
docker-compose down

# Check if database is corrupted
file ./data/trading.db
# Should say: "SQLite 3.x database"
# If it says "empty" or "data", it's corrupted

# Remove corrupted database
rm ./data/trading.db

# Start container (will create fresh database)
docker-compose up -d

# Verify health
curl http://localhost:5001/health
```

## Verification

### Healthy Response
When database is working:
```json
{
  "status": "operational",
  "service": "ICT Enhanced Trading Monitor",
  "database": "healthy",
  "signals_today": 0,
  "paper_balance": 10000.0,
  "scan_count": 145,
  ...
}
```

### Degraded Response
When database is corrupted (but container still runs):
```json
{
  "status": "degraded",
  "service": "ICT Enhanced Trading Monitor",
  "database": "error",
  "error": "file is not a database",
  "message": "Database error - system may need reinitialization"
}
```

## Git Commit
**Commit**: `5949996`
**Message**: "fix: Add error handling to health check and database validation"

## Next Steps
1. ✅ **DONE**: Added error handling to health check
2. ✅ **DONE**: Added database validation to entrypoint
3. ✅ **DONE**: Committed and pushed to GitHub
4. 🔄 **TODO**: Build and push new Docker image
5. 🔄 **TODO**: Test with other developer

## Prevention
To prevent this issue in the future:

1. **Don't mount corrupted databases**:
   - Use named volumes instead of bind mounts: `db-data:/app/data`
   - Or ensure local `./data` directory is empty on first run

2. **Monitor health checks**:
   - Set up alerts for `status: degraded`
   - Check logs for database errors

3. **Regular database backups**:
   - Backup `./data/trading.db` before updates
   - Keep timestamped backups

## Files Modified
- `core/monitors/ict_enhanced_monitor.py` - Added error handling to health check
- `docker/docker-entrypoint.sh` - Added database validation on startup
