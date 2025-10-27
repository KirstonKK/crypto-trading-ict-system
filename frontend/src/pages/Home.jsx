import { Link } from 'react-router-dom'
import { Activity, BarChart3, TrendingUp, Zap, Shield, Target } from 'lucide-react'

export default function Home(){
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-700 via-gray-800 to-gray-900 relative overflow-hidden">
      {/* Decorative Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Gradient Blobs (lighter for grey background) */}
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-gradient-to-br from-emerald-400/20 to-cyan-400/20 rounded-full opacity-40 blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-tr from-blue-400/20 to-purple-400/20 rounded-full opacity-40 blur-3xl"></div>
        
        {/* Light Geometric Shapes */}
        <div className="absolute top-10 left-0 w-72 h-72 bg-white/5 transform rotate-12 rounded-3xl"></div>
        <div className="absolute bottom-20 right-0 w-80 h-64 bg-white/5 transform -rotate-6 rounded-3xl"></div>
        <div className="absolute top-1/2 left-1/4 w-48 h-48 bg-white/5 transform rotate-45 rounded-2xl"></div>
        
        {/* Light Circles - Various Sizes */}
        <div className="absolute top-1/4 right-20 w-40 h-40 rounded-full bg-white/5"></div>
        <div className="absolute bottom-1/3 left-10 w-56 h-56 rounded-full bg-white/5"></div>
        <div className="absolute top-2/3 right-1/4 w-32 h-32 rounded-full bg-white/8"></div>
        <div className="absolute top-1/3 left-1/3 w-28 h-28 rounded-full bg-white/5"></div>
        
        {/* Light Border Patterns */}
        <div className="absolute top-20 left-10 w-24 h-24 border-4 border-white/10 transform rotate-45"></div>
        <div className="absolute bottom-32 right-20 w-20 h-20 border-4 border-white/10 transform rotate-12"></div>
        <div className="absolute top-1/3 right-1/4 w-16 h-16 rounded-full border-4 border-white/10"></div>
        <div className="absolute bottom-1/4 left-1/3 w-18 h-18 rounded-full border-4 border-white/10"></div>
        <div className="absolute top-3/4 right-10 w-20 h-20 border-4 border-white/8 rounded-lg transform -rotate-12"></div>
        
        {/* Crypto Symbols in Light */}
        <div className="absolute top-40 right-32 text-white opacity-10 text-7xl font-bold transform rotate-12">₿</div>
        <div className="absolute bottom-40 left-24 text-white opacity-10 text-7xl font-bold transform -rotate-12">Ξ</div>
        <div className="absolute top-1/2 right-1/3 text-white opacity-5 text-6xl font-bold">$</div>
        <div className="absolute bottom-1/4 right-1/4 text-white opacity-8 text-5xl font-bold">€</div>
        
        {/* Diagonal Lines */}
        <div className="absolute top-0 left-1/4 w-1 h-full bg-white/5 transform -rotate-12"></div>
        <div className="absolute top-0 right-1/3 w-1 h-full bg-white/5 transform rotate-12"></div>
        
        {/* Grid Pattern */}
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.2) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.2) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px'
        }}></div>
      </div>

      {/* Content */}
      <div className="relative z-10 p-8">
        <div className="max-w-5xl mx-auto">
          {/* Header Card */}
          <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 p-10 mb-8 text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-emerald-400 to-cyan-400 rounded-2xl mb-6 shadow-lg">
              <TrendingUp className="w-10 h-10 text-white" strokeWidth={2.5} />
            </div>
            <h1 className="text-5xl font-black text-gray-900 mb-3 tracking-tight">
              ICT Trading System
            </h1>
            <p className="text-gray-600 text-lg mb-8 font-medium">
              Choose where you want to go — Monitor or Dashboard
            </p>
            
            {/* Main Action Buttons */}
            <div className="flex flex-col md:flex-row gap-4 justify-center max-w-2xl mx-auto">
              <Link 
                to="/monitor" 
                className="flex-1 group relative overflow-hidden bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white font-bold py-5 px-8 rounded-xl text-lg shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-200 flex items-center justify-center gap-3"
              >
                <Activity className="w-6 h-6" />
                <span>Go to Monitor</span>
              </Link>
              <Link 
                to="/dashboard" 
                className="flex-1 group relative overflow-hidden bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white font-bold py-5 px-8 rounded-xl text-lg shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-200 flex items-center justify-center gap-3"
              >
                <BarChart3 className="w-6 h-6" />
                <span>Open Dashboard</span>
              </Link>
            </div>
          </div>

          {/* Feature Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Monitor Card */}
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 bg-gradient-to-br from-emerald-100 to-emerald-200 rounded-xl flex items-center justify-center">
                  <Activity className="w-7 h-7 text-emerald-600" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900">Live Monitor</h3>
              </div>
              <p className="text-gray-600 text-base mb-6 leading-relaxed">
                Real-time system monitor with engine logs, active positions, and live market data streaming.
              </p>
              <Link 
                to="/monitor" 
                className="inline-flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white font-semibold px-6 py-3 rounded-lg shadow-md hover:shadow-lg transition-all duration-200"
              >
                <span>Open Monitor</span>
                <Target className="w-4 h-4" />
              </Link>
            </div>

            {/* Dashboard Card */}
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-100 to-purple-200 rounded-xl flex items-center justify-center">
                  <BarChart3 className="w-7 h-7 text-blue-600" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h3>
              </div>
              <p className="text-gray-600 text-base mb-6 leading-relaxed">
                Professional charts, performance metrics, and comprehensive historical trade analysis.
              </p>
              <Link 
                to="/dashboard" 
                className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white font-semibold px-6 py-3 rounded-lg shadow-md hover:shadow-lg transition-all duration-200"
              >
                <span>Open Dashboard</span>
                <Target className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200 shadow-lg text-center">
              <Zap className="w-8 h-8 mx-auto mb-2 text-amber-500" />
              <p className="text-2xl font-bold text-gray-900 mb-1">Real-Time</p>
              <p className="text-sm text-gray-600">Live Market Data</p>
            </div>
            <div className="bg-white/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200 shadow-lg text-center">
              <Shield className="w-8 h-8 mx-auto mb-2 text-blue-500" />
              <p className="text-2xl font-bold text-gray-900 mb-1">Secure</p>
              <p className="text-sm text-gray-600">Demo Trading</p>
            </div>
            <div className="bg-white/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200 shadow-lg text-center">
              <TrendingUp className="w-8 h-8 mx-auto mb-2 text-emerald-500" />
              <p className="text-2xl font-bold text-gray-900 mb-1">68%</p>
              <p className="text-sm text-gray-600">Win Rate</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
