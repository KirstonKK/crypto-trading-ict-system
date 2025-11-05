import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import toast from 'react-hot-toast'
import { TrendingUp, BarChart3, Zap, Shield, Lock, ArrowRight } from 'lucide-react'

const Login = () => {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [loading, setLoading] = useState(false)

  const handleDemoLogin = async () => {
    setLoading(true)

    try {
      // Auto-login with demo credentials
      await login('demo@ict.com', 'demo123')
      toast.success('Welcome to ICT Trading System!')
      navigate('/home')
    } catch (error) {
      console.error('Login failed:', error)
      toast.error('Demo login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-gradient-to-br from-gray-50 via-white to-gray-100">
      {/* Decorative Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Gradient Circles (kept for depth) */}
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-emerald-100 to-cyan-100 rounded-full opacity-30 blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-tr from-blue-100 to-purple-100 rounded-full opacity-30 blur-3xl"></div>
        
        {/* Large Black Geometric Shapes */}
        <div className="absolute top-10 left-0 w-72 h-72 bg-black/5 transform rotate-12 rounded-3xl"></div>
        <div className="absolute bottom-20 right-0 w-80 h-64 bg-black/5 transform -rotate-6 rounded-3xl"></div>
        <div className="absolute top-1/2 left-1/4 w-48 h-48 bg-black/5 transform rotate-45 rounded-2xl"></div>
        
        {/* Black Circles - Various Sizes */}
        <div className="absolute top-1/4 right-20 w-40 h-40 rounded-full bg-black/5"></div>
        <div className="absolute bottom-1/3 left-10 w-56 h-56 rounded-full bg-black/5"></div>
        <div className="absolute top-2/3 right-1/4 w-32 h-32 rounded-full bg-black/10"></div>
        <div className="absolute top-1/3 left-1/3 w-28 h-28 rounded-full bg-black/5"></div>
        
        {/* Black Border Patterns */}
        <div className="absolute top-20 left-10 w-24 h-24 border-4 border-black/10 transform rotate-45"></div>
        <div className="absolute bottom-32 right-20 w-20 h-20 border-4 border-black/10 transform rotate-12"></div>
        <div className="absolute top-1/3 right-1/4 w-16 h-16 rounded-full border-4 border-black/10"></div>
        <div className="absolute bottom-1/4 left-1/3 w-18 h-18 rounded-full border-4 border-black/10"></div>
        <div className="absolute top-3/4 right-10 w-20 h-20 border-4 border-black/8 rounded-lg transform -rotate-12"></div>
        
        {/* Crypto Symbols in Black */}
        <div className="absolute top-40 right-32 text-black opacity-10 text-7xl font-bold transform rotate-12">₿</div>
        <div className="absolute bottom-40 left-24 text-black opacity-10 text-7xl font-bold transform -rotate-12">Ξ</div>
        <div className="absolute top-1/2 right-1/3 text-black opacity-5 text-6xl font-bold">$</div>
        <div className="absolute bottom-1/4 right-1/4 text-black opacity-8 text-5xl font-bold">€</div>
        
        {/* Diagonal Lines */}
        <div className="absolute top-0 left-1/4 w-1 h-full bg-black/5 transform -rotate-12"></div>
        <div className="absolute top-0 right-1/3 w-1 h-full bg-black/5 transform rotate-12"></div>
        
        {/* Grid Pattern */}
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `
            linear-gradient(rgba(0,0,0,0.2) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,0,0,0.2) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px'
        }}></div>
      </div>

      {/* Login Card */}
      <div className="relative z-10 w-full max-w-md">
        <div className="bg-white rounded-3xl shadow-2xl p-8 border border-gray-100">
          {/* Logo/Icon */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-emerald-400 to-cyan-400 rounded-2xl mb-6 shadow-lg transform hover:rotate-6 transition-transform duration-300">
              <TrendingUp className="w-12 h-12 text-white" strokeWidth={2.5} />
            </div>
            <h1 className="text-4xl font-black text-gray-900 mb-2 tracking-tight">
              ICT Trading
            </h1>
            <p className="text-gray-600 font-medium">
              Advanced Crypto Trading Platform
            </p>
          </div>

          {/* Features */}
          <div className="grid grid-cols-3 gap-3 mb-8">
            <div className="text-center p-3 bg-gradient-to-br from-emerald-50 to-emerald-100/50 rounded-xl border border-emerald-200/50">
              <BarChart3 className="w-6 h-6 mx-auto mb-1 text-emerald-600" />
              <p className="text-xs font-semibold text-emerald-800">Live Charts</p>
            </div>
            <div className="text-center p-3 bg-gradient-to-br from-amber-50 to-amber-100/50 rounded-xl border border-amber-200/50">
              <Zap className="w-6 h-6 mx-auto mb-1 text-amber-600" />
              <p className="text-xs font-semibold text-amber-800">Real-Time</p>
            </div>
            <div className="text-center p-3 bg-gradient-to-br from-blue-50 to-blue-100/50 rounded-xl border border-blue-200/50">
              <Shield className="w-6 h-6 mx-auto mb-1 text-blue-600" />
              <p className="text-xs font-semibold text-blue-800">Secure</p>
            </div>
          </div>

          {/* Login Button */}
          <button
            onClick={handleDemoLogin}
            disabled={loading}
            className="w-full bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white font-bold py-4 px-6 rounded-xl text-lg shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-3"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-3 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Signing in...</span>
              </>
            ) : (
              <>
                <Lock className="w-5 h-5" />
                <span>Enter Dashboard</span>
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>

          {/* Info */}
          <div className="mt-6 text-center">
            <div className="inline-block bg-gradient-to-r from-gray-800 to-gray-900 text-white px-4 py-2 rounded-full text-sm font-semibold mb-2 shadow-lg">
              🎯 Demo Mode Active
            </div>
            <p className="text-xs text-gray-500 leading-relaxed">
              Connected to Bybit Demo Trading<br />
              Real market prices • Virtual funds
            </p>
          </div>
        </div>

        {/* Bottom Stats */}
        <div className="mt-6 grid grid-cols-3 gap-4 text-center">
          <div className="bg-white/80 backdrop-blur-sm rounded-xl p-3 border border-gray-200 shadow-lg">
            <p className="text-emerald-600 text-xl font-bold">68%</p>
            <p className="text-gray-600 text-xs font-medium">Win Rate</p>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-xl p-3 border border-gray-200 shadow-lg">
            <p className="text-blue-600 text-xl font-bold">1.78</p>
            <p className="text-gray-600 text-xs font-medium">Sharpe Ratio</p>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-xl p-3 border border-gray-200 shadow-lg">
            <p className="text-purple-600 text-xl font-bold">24/7</p>
            <p className="text-gray-600 text-xs font-medium">Monitoring</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
