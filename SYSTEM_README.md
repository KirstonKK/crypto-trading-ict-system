# 🚀 ICT Trading System - Professional Dashboard

A production-ready algorithmic trading system featuring:

- **Real-time Dashboard** with professional charts and analytics
- **JWT Authentication** for secure access
- **Multi-channel Notifications** (Email, SMS, Push)
- **Paper Trading** with live Bybit Demo Trading integration
- **ICT (Inner Circle Trader) Strategy** implementation

---

## 📊 Features

### Dashboard

- **Real-time Equity Curve** - Track your account balance over time
- **Active Trades Panel** - Monitor open positions with live P&L
- **Performance Metrics** - Win rate, profit factor, Sharpe ratio, max drawdown
- **Trade History** - Paginated table with all closed trades
- **Signal Distribution** - Visualize buy/sell signals and win/loss ratio

### Authentication

- Secure JWT-based login system
- Password hashing with bcrypt
- Protected API routes
- Session management

### Notifications

- **Email** - HTML formatted trade alerts via SMTP
- **SMS** - Trade signals via Twilio
- **Push** - Real-time notifications (Firebase/OneSignal ready)
- Configurable notification preferences per user

### Trading Engine

- ICT strategy with confluence analysis
- Risk management (1% per trade default)
- Real-time price updates from Bybit
- Automatic TP/SL execution
- WebSocket integration for live updates

---

## 🛠️ Tech Stack

### Frontend

- **React 18** with hooks
- **Vite** for blazing fast dev/build
- **Recharts** for professional charts
- **TailwindCSS** for styling
- **Socket.IO** for real-time updates

### Backend

- **Python 3.10+**
- **Flask** REST API
- **Flask-SocketIO** for WebSocket
- **SQLite** database
- **JWT** authentication
- **bcrypt** password hashing

### Services

- **Bybit API** for live price data
- **SMTP** for email notifications
- **Twilio** for SMS notifications

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- npm or yarn

### Quick Start (Development)

1. **Clone and setup**

```bash
cd "/Users/kirstonkwasi-kumah/Desktop/Trading Algoithm"
cp .env.example .env
# Edit .env with your configuration
```

2. **Install Python dependencies**

```bash
pip3 install -r requirements.txt
```

3. **Install frontend dependencies**

```bash
cd frontend
npm install
cd ..
```

4. **Start the system**

```bash
./start_dev.sh
```

The system will start:

- Frontend: http://localhost:3000
- API: http://localhost:5001
- Monitor: Running in background

### Production Deployment

For production deployment with optimized builds:

```bash
./deploy.sh
```

---

## 🔑 Default Credentials

After first run, use these demo credentials:

```
Email: demo@ict.com
Password: demo123
```

**⚠️ Change these immediately in production!**

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```env
# API Configuration
SECRET_KEY=your-secure-random-key-here
FLASK_ENV=production

# Email Notifications (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
FROM_EMAIL=your-email@gmail.com

# SMS Notifications (Twilio)
TWILIO_ACCOUNT_SID=ACxxxx...
TWILIO_AUTH_TOKEN=your-token
TWILIO_FROM_NUMBER=+1234567890

# Trading Configuration
INITIAL_BALANCE=1000.0
RISK_PER_TRADE=0.01
MAX_POSITIONS=3

# Bybit API
BYBIT_API_KEY=your-api-key
BYBIT_API_SECRET=your-api-secret
BYBIT_TESTNET=true
```

### Email Setup (Gmail)

1. Enable 2-factor authentication on your Gmail account
2. Generate an **App Password**: https://myaccount.google.com/apppasswords
3. Use the app password in your `.env` file

### SMS Setup (Twilio)

1. Create account at https://www.twilio.com
2. Get your Account SID and Auth Token
3. Purchase a phone number
4. Add credentials to `.env`

---

## 📡 API Documentation

### Authentication Endpoints

#### POST /api/auth/register

Register a new user

```json
{
  "email": "trader@example.com",
  "password": "securepassword"
}
```

Response:

```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "trader@example.com"
  }
}
```

#### POST /api/auth/login

Login and get JWT token

```json
{
  "email": "trader@example.com",
  "password": "securepassword"
}
```

#### GET /api/auth/me

Get current user (requires JWT token)

Headers:

```
Authorization: Bearer <your-token>
```

### Dashboard Endpoints (Protected)

All dashboard endpoints require `Authorization: Bearer <token>` header.

#### GET /api/dashboard/stats

Get key trading statistics

Response:

```json
{
  "totalTrades": 45,
  "winRate": 62.5,
  "totalPnL": 234.5,
  "activeTrades": 2,
  "avgWin": 12.3,
  "avgLoss": -8.5,
  "profitFactor": 1.85,
  "maxDrawdown": 5.2
}
```

#### GET /api/dashboard/equity

Get equity curve data

#### GET /api/dashboard/trades

Get trade history (paginated)

Query params:

- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50)

#### GET /api/dashboard/signals

Get signal distribution statistics

#### GET /api/dashboard/active-trades

Get currently open trades

---

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   React     │◄───────►│  Flask API   │◄───────►│  Database   │
│  Dashboard  │ SocketIO│  + Auth      │         │  (SQLite)   │
└─────────────┘         └──────────────┘         └─────────────┘
                              │
                              │
                    ┌─────────▼──────────┐
                    │  Trading Monitor   │
                    │  (ICT Strategy)    │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Bybit API        │
                    │   (Price Feed)     │
                    └────────────────────┘
```

### Components

1. **Frontend (React)** - User interface with real-time updates
2. **API Server (Flask)** - Authentication, data endpoints, WebSocket
3. **Trading Monitor** - Strategy execution, signal generation
4. **Notification Service** - Multi-channel alerts
5. **Database** - SQLite for data persistence

---

## 📈 Trading Strategy

The system implements ICT (Inner Circle Trader) concepts:

- **Order Blocks** - Institutional buying/selling zones
- **Fair Value Gaps** - Imbalances in price action
- **Liquidity Zones** - Areas where stop losses accumulate
- **Market Structure** - Higher highs/lows for trend identification
- **Confluence Analysis** - Multiple factors for signal strength

### Risk Management

- **Fixed 1% risk** per trade
- **Position sizing** based on stop distance
- **Max positions** configurable (default: 3)
- **Automatic TP/SL** execution

---

## 🔧 Development

### Project Structure

```
├── frontend/                 # React dashboard
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── pages/          # Dashboard, Login pages
│   │   ├── contexts/       # Auth context
│   │   └── App.jsx
│   └── package.json
│
├── src/
│   ├── database/           # Database layer
│   ├── monitors/           # Trading monitor
│   └── strategy/           # ICT strategy implementation
│
├── services/
│   └── notification_service.py  # Email/SMS/Push
│
├── api_server.py           # Flask API + Auth
├── requirements.txt        # Python dependencies
├── deploy.sh              # Production deployment
└── start_dev.sh           # Development startup
```

### Running Tests

```bash
# Backend tests
pytest tests/

# Frontend tests
cd frontend
npm test
```

### Building for Production

```bash
# Build frontend
cd frontend
npm run build

# Start production server
gunicorn -w 4 -b 0.0.0.0:5001 api_server:app
```

---

## 📊 Database Schema

### users

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash BLOB NOT NULL,
    created_at TEXT NOT NULL
)
```

### paper_trades

```sql
CREATE TABLE paper_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_price REAL NOT NULL,
    current_price REAL,
    exit_price REAL,
    position_size REAL NOT NULL,
    stop_loss REAL NOT NULL,
    take_profit REAL NOT NULL,
    status TEXT NOT NULL,
    unrealized_pnl REAL DEFAULT 0,
    realized_pnl REAL DEFAULT 0,
    risk_amount REAL NOT NULL,
    entry_time TEXT NOT NULL,
    exit_time TEXT,
    created_date TEXT NOT NULL
)
```

### signals

```sql
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id TEXT UNIQUE NOT NULL,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_price REAL NOT NULL,
    stop_loss REAL NOT NULL,
    take_profit REAL NOT NULL,
    confluence_score REAL NOT NULL,
    status TEXT NOT NULL,
    -- ... additional fields
)
```

---

## 🚨 Troubleshooting

### Common Issues

**1. Frontend can't connect to API**

- Ensure API is running: `curl http://localhost:5001/api/health`
- Check proxy settings in `frontend/vite.config.js`

**2. Authentication fails**

- Verify SECRET_KEY in `.env`
- Check JWT token in browser DevTools (Network tab)

**3. Notifications not sending**

- Email: Verify SMTP credentials and app password
- SMS: Check Twilio account balance and credentials

**4. Monitor not generating signals**

- Check monitor logs: `tail -f logs/monitor.log`
- Verify Bybit API connection
- Ensure trading pairs are configured

**5. Database errors**

- Delete `data/trading.db` to reset (⚠️ loses all data)
- Run `python3 api_server.py` to recreate tables

---

## 🔒 Security Considerations

### Production Checklist

- [ ] Change default SECRET_KEY
- [ ] Update demo user credentials
- [ ] Use HTTPS in production
- [ ] Enable CORS only for your domain
- [ ] Set up firewall rules
- [ ] Regular database backups
- [ ] Monitor API rate limits
- [ ] Rotate API keys regularly

### Best Practices

1. **Never commit `.env` to Git**
2. **Use environment-specific configs**
3. **Implement rate limiting** on API
4. **Regular security audits**
5. **Keep dependencies updated**

---

## 📝 License

This project is licensed under the MIT License - see LICENSE file.

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📞 Support

For issues, questions, or feature requests:

- **GitHub Issues**: [Create an issue](https://github.com/yourusername/ict-trading-system/issues)
- **Email**: support@ict-trading.com
- **Documentation**: See `/docs` folder

---

## 🎯 Roadmap

### v1.1 (Current)

- [x] Professional dashboard with charts
- [x] JWT authentication
- [x] Multi-channel notifications
- [x] Real-time price updates

### v1.2 (Upcoming)

- [ ] Advanced analytics (Sharpe ratio, Sortino ratio)
- [ ] Multi-timeframe analysis
- [ ] Portfolio allocation optimizer
- [ ] Backtesting UI
- [ ] Trade journal with notes

### v2.0 (Future)

- [ ] Live trading support (not just paper)
- [ ] Multiple exchange integration
- [ ] Mobile app (React Native)
- [ ] Social trading features
- [ ] Machine learning enhancements

---

## 🙏 Acknowledgments

- **ICT Concepts** by Michael J. Huddleston
- **Bybit** for API access
- **React** and **Recharts** communities
- **Flask** ecosystem contributors

---

**Made with ❤️ by the ICT Trading System Team**

_Happy Trading! 📈_
