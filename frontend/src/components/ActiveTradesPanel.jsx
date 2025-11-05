import { format } from 'date-fns'
import { ArrowUpRight, ArrowDownRight, Clock } from 'lucide-react'

const ActiveTradesPanel = ({ trades }) => {
  if (!trades || trades.length === 0) {
    return (
      <div className="card mb-8">
        <h2 className="text-xl font-semibold text-white mb-4">
          Active Trades
        </h2>
        <div className="text-center py-8 text-gray-400">
          <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No active trades at the moment</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card mb-8">
      <h2 className="text-xl font-semibold text-white mb-4">
        Active Trades ({trades.length})
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {trades.map((trade) => {
          const pnl = trade.unrealized_pnl || 0
          const pnlPercent = ((pnl / (trade.entry_price * trade.position_size)) * 100) || 0
          
          return (
            <div 
              key={trade.id}
              className="bg-dark-bg border border-dark-border rounded-lg p-4 hover:border-primary/50 transition-colors"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-white font-bold text-lg">
                    {trade.symbol.replace('USDT', '')}
                  </span>
                  <span className={`badge ${trade.direction === 'BUY' ? 'badge-success' : 'badge-danger'}`}>
                    {trade.direction === 'BUY' ? (
                      <ArrowUpRight className="w-3 h-3 inline mr-1" />
                    ) : (
                      <ArrowDownRight className="w-3 h-3 inline mr-1" />
                    )}
                    {trade.direction}
                  </span>
                </div>
                <div className={`text-right ${pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                  <div className="font-semibold">
                    {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
                  </div>
                  <div className="text-xs">
                    {pnl >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%
                  </div>
                </div>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between text-gray-400">
                  <span>Entry:</span>
                  <span className="text-white">${trade.entry_price.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-gray-400">
                  <span>Current:</span>
                  <span className="text-white">${trade.current_price.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-gray-400">
                  <span>Position:</span>
                  <span className="text-white">{trade.position_size.toFixed(6)}</span>
                </div>
                <div className="flex justify-between text-gray-400">
                  <span>Stop Loss:</span>
                  <span className="text-danger">${trade.stop_loss.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-gray-400">
                  <span>Take Profit:</span>
                  <span className="text-success">${trade.take_profit.toFixed(2)}</span>
                </div>
              </div>
              
              <div className="mt-3 pt-3 border-t border-dark-border text-xs text-gray-500">
                Opened {format(new Date(trade.entry_time), 'MMM dd, HH:mm')}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ActiveTradesPanel
