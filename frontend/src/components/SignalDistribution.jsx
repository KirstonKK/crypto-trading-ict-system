import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const SignalDistribution = ({ data }) => {
  const chartData = [
    { name: 'Buy Signals', value: data.buySignals || 0, color: '#10b981' },
    { name: 'Sell Signals', value: data.sellSignals || 0, color: '#ef4444' },
    { name: 'Wins', value: data.wins || 0, color: '#6366f1' },
    { name: 'Losses', value: data.losses || 0, color: '#f59e0b' }
  ]

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-dark-card border border-dark-border p-3 rounded-lg shadow-lg">
          <p className="text-white font-semibold">
            {payload[0].payload.name}: {payload[0].value}
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="card">
      <h2 className="text-xl font-semibold text-white mb-4">
        Signal Distribution
      </h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis 
            dataKey="name" 
            stroke="#64748b"
            tick={{ fill: '#94a3b8' }}
          />
          <YAxis 
            stroke="#64748b"
            tick={{ fill: '#94a3b8' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="value" radius={[8, 8, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default SignalDistribution
