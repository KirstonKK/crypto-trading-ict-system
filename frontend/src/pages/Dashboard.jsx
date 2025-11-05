import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'
import { io } from 'socket.io-client'
import toast from 'react-hot-toast'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity, 
  Target,
  LogOut,
  RefreshCw,
  Home,
  PieChart as PieChartIcon,
  BarChart3,
  Clock,
  Trophy,
  AlertCircle,
  CheckCircle2,
  XCircle
} from 'lucide-react'
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'

const Dashboard = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [socket, setSocket] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  
  // Raw data states
  const [statsData, setStatsData] = useState(null)
  const [equityData, setEquityData] = useState(null)
  const [tradesData, setTradesData] = useState(null)
  const [signalsData, setSignalsData] = useState(null)
  const [activeTrades, setActiveTrades] = useState([])

  // Chart colors - sophisticated banking palette
  const COLORS = {
    primary: '#6366f1',
    success: '#10b981',
    danger: '#ef4444',
    warning: '#f59e0b',
    purple: '#8b5cf6',
    cyan: '#06b6d4',
    pink: '#ec4899',
    emerald: '#059669'
  }

  const PIE_COLORS = [COLORS.success, COLORS.danger, COLORS.warning, COLORS.primary, COLORS.purple, COLORS.cyan]

  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }

    fetchDashboardData()
    
    // Setup WebSocket connection for real-time updates
    const newSocket = io('http://localhost:5001')
    
    newSocket.on('connect', () => {
      console.log('✅ Connected to trading system')
      toast.success('Connected to live trading system')
    })
    
    newSocket.on('paper_trades_update', (data) => {
      setActiveTrades(data.trades || [])
    })
    
    newSocket.on('new_signal', (signal) => {
      toast.success(`New ${signal.direction} signal: ${signal.symbol} @ $${signal.entry_price}`, {
        duration: 6000
      })
      fetchDashboardData() // Refresh data
    })
    
    newSocket.on('trade_closed', (trade) => {
      const pnl = trade.realized_pnl
      const message = `Trade closed: ${trade.symbol} ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}`
      
      if (pnl >= 0) {
        toast.success(message, { duration: 6000 })
      } else {
        toast.error(message, { duration: 6000 })
      }
      
      fetchDashboardData() // Refresh data
    })
    
    newSocket.on('disconnect', () => {
      console.log('❌ Disconnected from trading system')
      toast.error('Lost connection to trading system')
    })
    
    setSocket(newSocket)
    
    return () => {
      newSocket.close()
    }
  }, [user, navigate])

  const fetchDashboardData = async () => {
    try {
      setRefreshing(true)
      const [statsRes, equityRes, tradesRes, signalsRes] = await Promise.all([
        axios.get('/api/dashboard/stats'),
        axios.get('/api/dashboard/equity'),
        axios.get('/api/dashboard/trades'),
        axios.get('/api/dashboard/signals')
      ])
      
      console.log('📊 Dashboard data loaded:', {
        stats: statsRes.data,
        equity: equityRes.data,
        trades: tradesRes.data,
        signals: signalsRes.data
      })
      
      setStatsData(statsRes.data)
      setEquityData(equityRes.data)
      setTradesData(tradesRes.data)
      setSignalsData(signalsRes.data)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  // Safe data access with defaults
  const stats = statsData || {}
  const equity = equityData || []
  const trades = tradesData || []
  const signals = signalsData || {}

  // Calculate wins and losses from trades
  const winningTrades = trades.filter(t => t.realized_pnl > 0).length
  const losingTrades = trades.filter(t => t.realized_pnl <= 0).length

  // Prepare Win/Loss Pie Chart Data (only show if we have data)
  const winLossData = [
    { name: 'Wins', value: winningTrades, color: COLORS.success },
    { name: 'Losses', value: losingTrades, color: COLORS.danger }
  ].filter(item => item.value > 0) // Remove zero values

  // Prepare Signal Distribution Data (map keys properly and filter zeros)
  const signalDistData = Object.entries(signals)
    .map(([key, value]) => {
      // Clean up the key names for better display
      let displayName = key.replace(/_/g, ' ').replace(/signals?/gi, '').trim().toUpperCase()
      if (displayName === 'BUY') displayName = 'Buy Signals'
      if (displayName === 'SELL') displayName = 'Sell Signals'
      if (displayName === 'WINS') displayName = 'Winning Signals'
      if (displayName === 'LOSSES') displayName = 'Losing Signals'
      
      return {
        name: displayName,
        value: value || 0,
        color: key.toLowerCase().includes('buy') ? COLORS.success :
               key.toLowerCase().includes('sell') ? COLORS.danger :
               key.toLowerCase().includes('win') ? COLORS.success :
               key.toLowerCase().includes('loss') ? COLORS.danger :
               PIE_COLORS[Math.floor(Math.random() * PIE_COLORS.length)]
      }
    })
    .filter(item => item.value > 0) // Remove zero values

  // Prepare Trade Performance by Symbol
  const symbolPerformance = {}
  trades.forEach(trade => {
    if (!symbolPerformance[trade.symbol]) {
      symbolPerformance[trade.symbol] = { wins: 0, losses: 0, totalPnL: 0 }
    }
    if (trade.realized_pnl > 0) {
      symbolPerformance[trade.symbol].wins++
    } else {
      symbolPerformance[trade.symbol].losses++
    }
    symbolPerformance[trade.symbol].totalPnL += trade.realized_pnl || 0
  })

  const symbolPerfData = Object.entries(symbolPerformance).map(([symbol, data]) => ({
    symbol,
    wins: data.wins,
    losses: data.losses,
    pnl: data.totalPnL
  }))

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
      {/* Glassmorphism Header */}
      <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6 mb-6 shadow-2xl">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
              ICT Trading Analytics
            </h1>
            <p className="text-gray-400">
              Welcome back, <span className="text-blue-400 font-semibold">{user?.email || 'Trader'}</span>
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => navigate('/home')}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-white transition-all flex items-center gap-2"
            >
              <Home className="w-4 h-4" />
              Home
            </button>
            <button
              onClick={fetchDashboardData}
              disabled={refreshing}
              className="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/50 rounded-lg text-blue-300 transition-all flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={() => { logout(); navigate('/login') }}
              className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/50 rounded-lg text-red-300 transition-all flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Premium KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {/* Total P&L Card */}
        <div className="backdrop-blur-xl bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 border border-emerald-500/20 rounded-xl p-6 shadow-xl hover:shadow-2xl transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-emerald-500/20 rounded-lg">
              <DollarSign className="w-6 h-6 text-emerald-400" />
            </div>
            <span className="text-xs text-emerald-400 font-semibold px-2 py-1 bg-emerald-500/20 rounded-full">
              Total P&L
            </span>
          </div>
          <div className={`text-3xl font-bold mb-1 ${(stats.total_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {(stats.total_pnl || 0) >= 0 ? '+' : ''}${(stats.total_pnl || 0).toFixed(2)}
          </div>
          <div className="text-sm text-gray-400">
            {stats.total_trades || 0} total trades
          </div>
        </div>

        {/* Win Rate Card */}
        <div className="backdrop-blur-xl bg-gradient-to-br from-blue-500/10 to-blue-600/5 border border-blue-500/20 rounded-xl p-6 shadow-xl hover:shadow-2xl transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-blue-500/20 rounded-lg">
              <Target className="w-6 h-6 text-blue-400" />
            </div>
            <span className="text-xs text-blue-400 font-semibold px-2 py-1 bg-blue-500/20 rounded-full">
              Win Rate
            </span>
          </div>
          <div className="text-3xl font-bold mb-1 text-blue-400">
            {(stats.win_rate || 0).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-400">
            {stats.winning_trades || 0}W / {stats.losing_trades || 0}L
          </div>
        </div>

        {/* Profit Factor Card */}
        <div className="backdrop-blur-xl bg-gradient-to-br from-purple-500/10 to-purple-600/5 border border-purple-500/20 rounded-xl p-6 shadow-xl hover:shadow-2xl transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-purple-500/20 rounded-lg">
              <TrendingUp className="w-6 h-6 text-purple-400" />
            </div>
            <span className="text-xs text-purple-400 font-semibold px-2 py-1 bg-purple-500/20 rounded-full">
              Profit Factor
            </span>
          </div>
          <div className="text-3xl font-bold mb-1 text-purple-400">
            {(stats.profit_factor || 0).toFixed(2)}x
          </div>
          <div className="text-sm text-gray-400">
            Avg Win: ${(stats.avg_win || 0).toFixed(2)}
          </div>
        </div>

        {/* Active Trades Card */}
        <div className="backdrop-blur-xl bg-gradient-to-br from-orange-500/10 to-orange-600/5 border border-orange-500/20 rounded-xl p-6 shadow-xl hover:shadow-2xl transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-orange-500/20 rounded-lg">
              <Activity className="w-6 h-6 text-orange-400" />
            </div>
            <span className="text-xs text-orange-400 font-semibold px-2 py-1 bg-orange-500/20 rounded-full">
              Active Now
            </span>
          </div>
          <div className="text-3xl font-bold mb-1 text-orange-400">
            {stats.active_trades || 0}
          </div>
          <div className="text-sm text-gray-400">
            Max DD: {(stats.max_drawdown || 0).toFixed(2)}%
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Equity Curve Chart */}
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6 shadow-xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <BarChart3 className="w-5 h-5 text-blue-400" />
            </div>
            <h2 className="text-xl font-bold text-white">Equity Curve</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={equity}>
              <defs>
                <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
              <XAxis dataKey="date" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b', 
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Area 
                type="monotone" 
                dataKey="balance" 
                stroke="#6366f1" 
                strokeWidth={3}
                fill="url(#equityGradient)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Win/Loss Donut Chart */}
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6 shadow-xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-emerald-500/20 rounded-lg">
              <PieChartIcon className="w-5 h-5 text-emerald-400" />
            </div>
            <h2 className="text-xl font-bold text-white">Win/Loss Distribution</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={winLossData}
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={110}
                paddingAngle={5}
                dataKey="value"
                label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                labelLine={{ stroke: '#64748b', strokeWidth: 1 }}
              >
                {winLossData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b', 
                  border: '1px solid #334155',
                  borderRadius: '8px'
                }}
              />
              <Legend 
                verticalAlign="bottom" 
                height={36}
                formatter={(value, entry) => (
                  <span style={{ color: '#fff' }}>{value}: {entry.payload.value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Second Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Symbol Performance Bar Chart */}
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6 shadow-xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <BarChart3 className="w-5 h-5 text-purple-400" />
            </div>
            <h2 className="text-xl font-bold text-white">Performance by Symbol</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={symbolPerfData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
              <XAxis dataKey="symbol" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b', 
                  border: '1px solid #334155',
                  borderRadius: '8px'
                }}
              />
              <Legend />
              <Bar dataKey="wins" fill={COLORS.success} radius={[8, 8, 0, 0]} />
              <Bar dataKey="losses" fill={COLORS.danger} radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Signal Distribution Pie Chart */}
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6 shadow-xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cyan-500/20 rounded-lg">
              <Target className="w-5 h-5 text-cyan-400" />
            </div>
            <h2 className="text-xl font-bold text-white">Signal Distribution</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={signalDistData}
                cx="50%"
                cy="50%"
                outerRadius={90}
                paddingAngle={3}
                dataKey="value"
                label={({ name, value, percent }) => `${value}`}
                labelLine={{ stroke: '#64748b', strokeWidth: 1 }}
              >
                {signalDistData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b', 
                  border: '1px solid #334155',
                  borderRadius: '8px'
                }}
              />
              <Legend 
                verticalAlign="bottom" 
                height={36}
                formatter={(value, entry) => (
                  <span style={{ color: '#fff' }}>{value}: {entry.payload.value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Trades Table */}
      <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6 shadow-xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-indigo-500/20 rounded-lg">
            <Clock className="w-5 h-5 text-indigo-400" />
          </div>
          <h2 className="text-xl font-bold text-white">Recent Trades</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-3 px-4 text-gray-400 font-semibold text-sm">Symbol</th>
                <th className="text-left py-3 px-4 text-gray-400 font-semibold text-sm">Side</th>
                <th className="text-left py-3 px-4 text-gray-400 font-semibold text-sm">Entry</th>
                <th className="text-left py-3 px-4 text-gray-400 font-semibold text-sm">Exit</th>
                <th className="text-left py-3 px-4 text-gray-400 font-semibold text-sm">P&L</th>
                <th className="text-left py-3 px-4 text-gray-400 font-semibold text-sm">Status</th>
              </tr>
            </thead>
            <tbody>
              {trades.slice(0, 10).map((trade, idx) => (
                <tr key={idx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                  <td className="py-3 px-4 text-white font-semibold">{trade.symbol}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                      trade.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                    }`}>
                      {trade.direction}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-300">${trade.entry_price?.toFixed(2)}</td>
                  <td className="py-3 px-4 text-gray-300">${trade.exit_price?.toFixed(2)}</td>
                  <td className={`py-3 px-4 font-semibold ${
                    (trade.realized_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                  }`}>
                    {(trade.realized_pnl || 0) >= 0 ? '+' : ''}${(trade.realized_pnl || 0).toFixed(2)}
                  </td>
                  <td className="py-3 px-4">
                    {trade.status === 'TAKE_PROFIT' && (
                      <span className="flex items-center gap-1 text-emerald-400">
                        <CheckCircle2 className="w-4 h-4" />
                        <span className="text-xs">TP</span>
                      </span>
                    )}
                    {trade.status === 'STOP_LOSS' && (
                      <span className="flex items-center gap-1 text-red-400">
                        <XCircle className="w-4 h-4" />
                        <span className="text-xs">SL</span>
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
