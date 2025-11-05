import { Link } from 'react-router-dom'
import { TrendingUp, BarChart3, Activity, Zap, Shield, Bell } from 'lucide-react'

const HomePage = () => {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-6xl w-full">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-primary/20 rounded-full mb-6">
            <TrendingUp className="w-10 h-10 text-primary" />
          </div>
          <h1 className="text-5xl font-bold text-white mb-4">
            ICT Trading System
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Professional algorithmic trading platform powered by Inner Circle Trader strategies
          </p>
        </div>

        {/* Main Navigation Cards */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* Dashboard Card */}
          <Link to="/dashboard">
            <div className="card hover:border-primary transition-all duration-300 transform hover:scale-105 cursor-pointer group">
              <div className="flex items-start gap-4 mb-4">
                <div className="p-3 bg-primary/20 rounded-lg group-hover:bg-primary/30 transition-colors">
                  <BarChart3 className="w-8 h-8 text-primary" />
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-white mb-2">
                    Professional Dashboard
                  </h2>
                  <p className="text-gray-400">
                    View comprehensive analytics, equity curves, and performance metrics with beautiful charts
                  </p>
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-dark-border">
                <div>
                  <div className="text-2xl font-bold text-primary mb-1">📊</div>
                  <div className="text-xs text-gray-500">Live Charts</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-success mb-1">📈</div>
                  <div className="text-xs text-gray-500">Analytics</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-secondary mb-1">📉</div>
                  <div className="text-xs text-gray-500">Insights</div>
                </div>
              </div>
              
              <div className="mt-6 flex items-center text-primary font-semibold group-hover:translate-x-2 transition-transform">
                Open Dashboard
                <span className="ml-2">→</span>
              </div>
            </div>
          </Link>

          {/* Monitor Card */}
          <a href="http://localhost:5001" target="_blank" rel="noopener noreferrer">
            <div className="card hover:border-success transition-all duration-300 transform hover:scale-105 cursor-pointer group">
              <div className="flex items-start gap-4 mb-4">
                <div className="p-3 bg-success/20 rounded-lg group-hover:bg-success/30 transition-colors">
                  <Activity className="w-8 h-8 text-success" />
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-white mb-2">
                    Live Trading Monitor
                  </h2>
                  <p className="text-gray-400">
                    Real-time signal generation, active trades monitoring, and system status
                  </p>
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-dark-border">
                <div>
                  <div className="text-2xl font-bold text-success mb-1">🎯</div>
                  <div className="text-xs text-gray-500">Live Signals</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-warning mb-1">⚡</div>
                  <div className="text-xs text-gray-500">Real-time</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-primary mb-1">🔄</div>
                  <div className="text-xs text-gray-500">Auto Trading</div>
                </div>
              </div>
              
              <div className="mt-6 flex items-center text-success font-semibold group-hover:translate-x-2 transition-transform">
                Open Monitor
                <span className="ml-2">→</span>
              </div>
            </div>
          </a>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-6">
          <div className="card text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-primary/20 rounded-full mb-4">
              <Zap className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              ICT Strategy
            </h3>
            <p className="text-sm text-gray-400">
              Advanced Inner Circle Trader concepts with confluence analysis
            </p>
          </div>

          <div className="card text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-success/20 rounded-full mb-4">
              <Shield className="w-6 h-6 text-success" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              Risk Management
            </h3>
            <p className="text-sm text-gray-400">
              1% risk per trade with automatic position sizing and stop loss
            </p>
          </div>

          <div className="card text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-warning/20 rounded-full mb-4">
              <Bell className="w-6 h-6 text-warning" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              Smart Alerts
            </h3>
            <p className="text-sm text-gray-400">
              Email and SMS notifications for signals and trade executions
            </p>
          </div>
        </div>

        {/* Footer Stats */}
        <div className="mt-12 pt-8 border-t border-dark-border">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            <div>
              <div className="text-3xl font-bold text-primary mb-1">24/7</div>
              <div className="text-sm text-gray-500">Monitoring</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-success mb-1">ICT</div>
              <div className="text-sm text-gray-500">Strategy</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-warning mb-1">Real</div>
              <div className="text-sm text-gray-500">Time Data</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-secondary mb-1">Auto</div>
              <div className="text-sm text-gray-500">Trading</div>
            </div>
          </div>
        </div>

        {/* Version Info */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>ICT Trading System v1.0 | Professional Edition</p>
        </div>
      </div>
    </div>
  )
}

export default HomePage
