import { format } from 'date-fns'
import { ArrowUpRight, ArrowDownRight, CheckCircle, XCircle } from 'lucide-react'

const TradeHistoryTable = ({ trades }) => {
  if (!trades || trades.length === 0) {
    return (
      <div className="card">
        <h2 className="text-xl font-semibold text-white mb-4">
          Trade History
        </h2>
        <div className="text-center py-8 text-gray-400">
          No trade history available
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 className="text-xl font-semibold text-white mb-4">
        Trade History
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-dark-border">
              <th className="text-left py-3 px-4 text-gray-400 font-medium text-sm">Symbol</th>
              <th className="text-left py-3 px-4 text-gray-400 font-medium text-sm">Direction</th>
              <th className="text-right py-3 px-4 text-gray-400 font-medium text-sm">Entry</th>
              <th className="text-right py-3 px-4 text-gray-400 font-medium text-sm">Exit</th>
              <th className="text-right py-3 px-4 text-gray-400 font-medium text-sm">Position</th>
              <th className="text-right py-3 px-4 text-gray-400 font-medium text-sm">P&L</th>
              <th className="text-center py-3 px-4 text-gray-400 font-medium text-sm">Status</th>
              <th className="text-left py-3 px-4 text-gray-400 font-medium text-sm">Date</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade) => {
              const pnl = trade.realized_pnl || 0
              const isProfit = pnl >= 0
              
              return (
                <tr 
                  key={trade.id}
                  className="border-b border-dark-border/50 hover:bg-dark-bg/50 transition-colors"
                >
                  <td className="py-3 px-4">
                    <span className="text-white font-medium">
                      {trade.symbol.replace('USDT', '')}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`badge ${trade.direction === 'BUY' ? 'badge-success' : 'badge-danger'}`}>
                      {trade.direction === 'BUY' ? (
                        <ArrowUpRight className="w-3 h-3 inline mr-1" />
                      ) : (
                        <ArrowDownRight className="w-3 h-3 inline mr-1" />
                      )}
                      {trade.direction}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right text-white">
                    ${trade.entry_price.toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-right text-white">
                    {trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : '-'}
                  </td>
                  <td className="py-3 px-4 text-right text-gray-300">
                    {trade.position_size.toFixed(6)}
                  </td>
                  <td className={`py-3 px-4 text-right font-semibold ${isProfit ? 'text-success' : 'text-danger'}`}>
                    {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-center">
                    {trade.status === 'TAKE_PROFIT' ? (
                      <span className="badge-success">
                        <CheckCircle className="w-3 h-3 inline mr-1" />
                        TP
                      </span>
                    ) : trade.status === 'STOP_LOSS' ? (
                      <span className="badge-danger">
                        <XCircle className="w-3 h-3 inline mr-1" />
                        SL
                      </span>
                    ) : (
                      <span className="badge-warning">
                        {trade.status}
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-gray-400 text-sm">
                    {format(new Date(trade.entry_time), 'MMM dd, HH:mm')}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default TradeHistoryTable
