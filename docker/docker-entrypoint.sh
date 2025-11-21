#!/bin/bash
# =============================================================================
# Docker Entrypoint Script for Kirston's Crypto Trading System
# =============================================================================
# This script handles:
#   - Directory initialization
#   - Environment setup
#   - Database initialization
#   - Service startup
# =============================================================================

set -e  # Exit on error

echo "=================================================="
echo "🚀 Kirston's Crypto Trading System - Starting..."
echo "=================================================="

# -----------------------------------------------------------------------------
# Function: Print colored messages
# -----------------------------------------------------------------------------
log_info() {
    echo "ℹ️  [INFO] $1"
}

log_success() {
    echo "✅ [SUCCESS] $1"
}

log_error() {
    echo "❌ [ERROR] $1"
}

log_warn() {
    echo "⚠️  [WARNING] $1"
}

# -----------------------------------------------------------------------------
# Step 1: Verify environment
# -----------------------------------------------------------------------------
log_info "Checking environment configuration..."

# Set defaults if not provided
export ENVIRONMENT="${ENVIRONMENT:-production}"
export DEBUG="${DEBUG:-false}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export ICT_MONITOR_PORT="${ICT_MONITOR_PORT:-5001}"
export DATABASE_PATH="${DATABASE_PATH:-/app/data/trading.db}"

log_success "Environment: $ENVIRONMENT"
log_success "Log Level: $LOG_LEVEL"
log_success "ICT Monitor Port: $ICT_MONITOR_PORT"

# -----------------------------------------------------------------------------
# Step 2: Initialize directories
# -----------------------------------------------------------------------------
log_info "Initializing directories..."

# Create required directories if they don't exist
mkdir -p /app/data/{cache,persistence,processed,raw,trading_sessions}
mkdir -p /app/logs
mkdir -p /app/config/credentials
mkdir -p /app/results

# Set permissions (in case running as non-root)
chmod -R 755 /app/data /app/logs /app/config /app/results 2>/dev/null || true

log_success "Directories initialized"

# -----------------------------------------------------------------------------
# Step 3: Check API credentials
# -----------------------------------------------------------------------------
log_info "Checking API credentials..."

if [ -z "$BYBIT_API_KEY" ] || [ -z "$BYBIT_API_SECRET" ]; then
    log_warn "Bybit API credentials not set!"
    log_warn "Set BYBIT_API_KEY and BYBIT_API_SECRET environment variables"
    log_warn "System will run in demo mode with simulated data"
else
    log_success "Bybit API credentials found"
    
    # Determine Bybit environment
    BYBIT_ENV="${BYBIT_ENVIRONMENT:-demo_mainnet}"
    case "$BYBIT_ENV" in
        testnet)
            log_info "Using Bybit TESTNET (fake money, test environment)"
            ;;
        demo_mainnet)
            log_info "Using Bybit DEMO MAINNET (fake money, real prices)"
            ;;
        live_mainnet)
            log_warn "Using Bybit LIVE MAINNET (REAL MONEY!)"
            log_warn "⚠️  TRADING WITH REAL FUNDS - BE CAREFUL!"
            ;;
        *)
            log_warn "Unknown Bybit environment: $BYBIT_ENV"
            log_info "Defaulting to demo_mainnet"
            ;;
    esac
fi

# -----------------------------------------------------------------------------
# Step 4: Database initialization
# -----------------------------------------------------------------------------
log_info "Checking database..."

if [ ! -f "$DATABASE_PATH" ]; then
    log_info "Database not found. It will be created on first run."
else
    log_success "Database found at $DATABASE_PATH"
    
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
fi

# -----------------------------------------------------------------------------
# Step 5: Python environment check
# -----------------------------------------------------------------------------
log_info "Checking Python environment..."

python3 --version
log_success "Python version verified"

# Verify critical modules
log_info "Verifying critical Python modules..."
python3 -c "import flask, aiohttp, pandas, numpy, sqlite3" 2>/dev/null && \
    log_success "Core Python modules available" || \
    log_error "Some Python modules are missing!"

# -----------------------------------------------------------------------------
# Step 6: Display configuration summary
# -----------------------------------------------------------------------------
echo ""
echo "=================================================="
echo "📊 Configuration Summary"
echo "=================================================="
echo "Environment:        $ENVIRONMENT"
echo "Debug Mode:         $DEBUG"
echo "Log Level:          $LOG_LEVEL"
echo "ICT Monitor Port:   $ICT_MONITOR_PORT"
echo "Database Path:      $DATABASE_PATH"
echo "Bybit Environment:  ${BYBIT_ENVIRONMENT:-demo_mainnet}"
echo "Risk Per Trade:     ${RISK_PER_TRADE:-100.0}"
echo "Max Leverage:       ${MAX_LEVERAGE:-10}x"
echo "=================================================="
echo ""

# -----------------------------------------------------------------------------
# Step 7: Start the application
# -----------------------------------------------------------------------------
log_info "Starting application..."
log_info "Command: $@"

# Handle signals for graceful shutdown
trap 'log_warn "Received shutdown signal..."; exit 0' SIGTERM SIGINT

# Execute the main command
exec "$@"
