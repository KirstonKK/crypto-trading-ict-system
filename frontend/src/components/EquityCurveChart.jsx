import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { format } from 'date-fns'

const EquityCurveChart = ({ data }) => {
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-dark-card border border-dark-border p-3 rounded-lg shadow-lg">
          <p className="text-gray-300 text-sm mb-1">
            {format(new Date(payload[0].payload.date), 'MMM dd, yyyy HH:mm')}
          </p>
          <p className="text-white font-semibold">
            Balance: ${payload[0].value.toFixed(2)}
          </p>
          {payload[0].payload.pnl !== undefined && (
            <p className={`text-sm ${payload[0].payload.pnl >= 0 ? 'text-success' : 'text-danger'}`}>
              P&L: {payload[0].payload.pnl >= 0 ? '+' : ''}${payload[0].payload.pnl.toFixed(2)}
            </p>
          )}
        </div>
      )
    }
    return null
  }

  return (
    <div className="card">
      <h2 className="text-xl font-semibold text-white mb-4">
        Equity Curve
      </h2>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis 
            dataKey="date" 
            stroke="#64748b"
            tick={{ fill: '#94a3b8' }}
            tickFormatter={(value) => format(new Date(value), 'MMM dd')}
          />
          <YAxis 
            stroke="#64748b"
            tick={{ fill: '#94a3b8' }}
            tickFormatter={(value) => `$${value}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area 
            type="monotone" 
            dataKey="balance" 
            stroke="#6366f1" 
            strokeWidth={2}
            fill="url(#equityGradient)" 
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export default EquityCurveChart
