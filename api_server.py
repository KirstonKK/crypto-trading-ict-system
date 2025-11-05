"""
Enhanced Flask API with Authentication and Dashboard Endpoints
Provides JWT-based authentication and comprehensive trading data APIs
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from functools import wraps
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Database path
DB_PATH = 'data/trading.db'

# ============ AUTHENTICATION ============

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    """Verify a password against a hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def generate_token(user_id):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def token_required(f):
    """Decorator for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# ============ AUTH ROUTES ============

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'message': 'Email and password required'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'message': 'User already exists'}), 400
    
    # Create user
    hashed_pw = hash_password(password)
    cursor.execute(
        'INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)',
        (email, hashed_pw, datetime.now().isoformat())
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    token = generate_token(user_id)
    
    return jsonify({
        'message': 'User created successfully',
        'token': token,
        'user': {'id': user_id, 'email': email}
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login and get JWT token"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'message': 'Email and password required'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, email, password_hash FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not check_password(password, user[2]):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = generate_token(user[0])
    
    return jsonify({
        'token': token,
        'user': {'id': user[0], 'email': user[1]}
    })

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Get current user info"""
    return jsonify({'user': current_user})

# ============ DASHBOARD DATA ROUTES ============

@app.route('/api/dashboard/stats', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    """Get key trading statistics"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get closed trades
    cursor.execute('''
        SELECT 
            COUNT(*) as total_trades,
            SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
            SUM(realized_pnl) as total_pnl,
            AVG(CASE WHEN realized_pnl > 0 THEN realized_pnl END) as avg_win,
            AVG(CASE WHEN realized_pnl < 0 THEN realized_pnl END) as avg_loss,
            MAX(realized_pnl) as best_trade,
            MIN(realized_pnl) as worst_trade
        FROM paper_trades
        WHERE status IN ('TAKE_PROFIT', 'STOP_LOSS', 'CLOSED')
    ''')
    stats = dict(cursor.fetchone())
    
    # Get active trades count
    cursor.execute('SELECT COUNT(*) as active FROM paper_trades WHERE status = "OPEN"')
    stats['activeTrades'] = cursor.fetchone()['active']
    
    # Calculate win rate
    if stats['total_trades'] and stats['total_trades'] > 0:
        stats['winRate'] = (stats['wins'] / stats['total_trades']) * 100
    else:
        stats['winRate'] = 0
    
    # Calculate profit factor
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN realized_pnl > 0 THEN realized_pnl ELSE 0 END) as gross_profit,
            ABS(SUM(CASE WHEN realized_pnl < 0 THEN realized_pnl ELSE 0 END)) as gross_loss
        FROM paper_trades
        WHERE status IN ('TAKE_PROFIT', 'STOP_LOSS', 'CLOSED')
    ''')
    pf_data = dict(cursor.fetchone())
    if pf_data['gross_loss'] and pf_data['gross_loss'] > 0:
        stats['profitFactor'] = pf_data['gross_profit'] / pf_data['gross_loss']
    else:
        stats['profitFactor'] = 0
    
    # Max drawdown calculation (simplified)
    stats['maxDrawdown'] = 0  # TODO: Implement proper drawdown calculation
    
    # Fill in defaults
    stats['totalPnL'] = stats.get('total_pnl') or 0
    stats['avgWin'] = stats.get('avg_win') or 0
    stats['avgLoss'] = stats.get('avg_loss') or 0
    stats['bestTrade'] = stats.get('best_trade') or 0
    stats['worstTrade'] = stats.get('worst_trade') or 0
    
    conn.close()
    
    return jsonify(stats)

@app.route('/api/dashboard/equity', methods=['GET'])
@token_required
def get_equity_curve(current_user):
    """Get equity curve data"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get trade history with cumulative P&L
    cursor.execute('''
        SELECT 
            entry_time as date,
            exit_time,
            realized_pnl as pnl
        FROM paper_trades
        WHERE status IN ('TAKE_PROFIT', 'STOP_LOSS', 'CLOSED')
        ORDER BY entry_time ASC
    ''')
    
    trades = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Build equity curve
    initial_balance = 1000.0  # Starting balance
    balance = initial_balance
    equity_data = [{'date': datetime.now().isoformat(), 'balance': balance, 'pnl': 0}]
    
    for trade in trades:
        balance += trade['pnl']
        equity_data.append({
            'date': trade['exit_time'] or trade['date'],
            'balance': balance,
            'pnl': trade['pnl']
        })
    
    return jsonify(equity_data)

@app.route('/api/dashboard/trades', methods=['GET'])
@token_required
def get_trade_history(current_user):
    """Get paginated trade history"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    offset = (page - 1) * limit
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            id, signal_id, symbol, direction, 
            entry_price, exit_price, position_size,
            stop_loss, take_profit, status,
            realized_pnl, entry_time, exit_time
        FROM paper_trades
        WHERE status IN ('TAKE_PROFIT', 'STOP_LOSS', 'CLOSED')
        ORDER BY entry_time DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    
    trades = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(trades)

@app.route('/api/dashboard/signals', methods=['GET'])
@token_required
def get_signal_stats(current_user):
    """Get signal distribution statistics"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN direction = 'BUY' THEN 1 ELSE 0 END) as buySignals,
            SUM(CASE WHEN direction = 'SELL' THEN 1 ELSE 0 END) as sellSignals,
            SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) as losses
        FROM paper_trades
        WHERE status IN ('TAKE_PROFIT', 'STOP_LOSS', 'CLOSED')
    ''')
    
    stats = dict(cursor.fetchone())
    conn.close()
    
    return jsonify(stats)

@app.route('/api/dashboard/active-trades', methods=['GET'])
@token_required
def get_active_trades(current_user):
    """Get currently active trades"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            id, signal_id, symbol, direction,
            entry_price, current_price, position_size,
            stop_loss, take_profit, status,
            unrealized_pnl, entry_time
        FROM paper_trades
        WHERE status = 'OPEN'
        ORDER BY entry_time DESC
    ''')
    
    trades = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'trades': trades})

# ============ HEALTH CHECK ============

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'ICT Trading System API'
    })

if __name__ == '__main__':
    # Ensure users table exists
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash BLOB NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Create demo user if not exists
    demo_email = 'demo@ict.com'
    cursor.execute('SELECT id FROM users WHERE email = ?', (demo_email,))
    if not cursor.fetchone():
        demo_password = hash_password('demo123')
        cursor.execute(
            'INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)',
            (demo_email, demo_password, datetime.now().isoformat())
        )
        print(f"✅ Created demo user: {demo_email} / demo123")
    
    conn.commit()
    conn.close()
    
    print("🚀 Starting ICT Trading System API...")
    print("   Dashboard: http://localhost:5001")
    print("   API Docs: http://localhost:5001/api/health")
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
