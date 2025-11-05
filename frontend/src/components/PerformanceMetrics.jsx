import { TrendingUp, TrendingDown, Target, BarChart3 } from 'lucide-react'

const PerformanceMetrics = ({ stats }) => {
  const metrics = [
    {
      label: 'Average Win',
      value: `$${stats.avgWin?.toFixed(2) || '0.00'}`,
      icon: TrendingUp,
      color: 'text-success'
    },
    {
      label: 'Average Loss',
      value: `$${Math.abs(stats.avgLoss || 0).toFixed(2)}`,
      icon: TrendingDown,
      color: 'text-danger'
    },
    {
      label: 'Profit Factor',
      value: stats.profitFactor?.toFixed(2) || '0.00',
      icon: Target,
      color: 'text-primary'
    },
    {
      label: 'Max Drawdown',
      value: `${stats.maxDrawdown?.toFixed(2) || '0.00'}%`,
      icon: BarChart3,
      color: 'text-warning'
    },
    {
      label: 'Sharpe Ratio',
      value: stats.sharpeRatio?.toFixed(2) || 'N/A',
      icon: TrendingUp,
      color: 'text-secondary'
    },
    {
      label: 'Best Trade',
      value: `$${stats.bestTrade?.toFixed(2) || '0.00'}`,
      icon: TrendingUp,
      color: 'text-success'
    },
    {
      label: 'Worst Trade',
      value: `$${stats.worstTrade?.toFixed(2) || '0.00'}`,
      icon: TrendingDown,
      color: 'text-danger'
    },
    {
      label: 'Avg Trade Duration',
      value: stats.avgDuration || 'N/A',
      icon: BarChart3,
      color: 'text-gray-400'
    }
  ]

  return (
    <div className="card mb-8">
      <h2 className="text-xl font-semibold text-white mb-4">
        Performance Metrics
      </h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map((metric, index) => {
          const Icon = metric.icon
          return (
            <div key={index} className="bg-dark-bg border border-dark-border rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Icon className={`w-4 h-4 ${metric.color}`} />
                <span className="text-gray-400 text-sm">{metric.label}</span>
              </div>
              <div className={`text-lg font-bold ${metric.color}`}>
                {metric.value}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default PerformanceMetrics
