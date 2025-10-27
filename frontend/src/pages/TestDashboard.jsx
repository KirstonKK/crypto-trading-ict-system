import { useState, useEffect } from 'react'
import axios from 'axios'

const TestDashboard = () => {
  const [data, setData] = useState({
    stats: null,
    equity: null,
    trades: null,
    signals: null,
    error: null,
    loading: true
  })

  useEffect(() => {
    fetchAllData()
  }, [])

  const fetchAllData = async () => {
    try {
      console.log('🔍 Fetching dashboard data...')
      
      const statsRes = await axios.get('/api/dashboard/stats')
      console.log('✅ Stats:', statsRes.data)
      
      const equityRes = await axios.get('/api/dashboard/equity')
      console.log('✅ Equity:', equityRes.data)
      
      const tradesRes = await axios.get('/api/dashboard/trades')
      console.log('✅ Trades:', tradesRes.data)
      
      const signalsRes = await axios.get('/api/dashboard/signals')
      console.log('✅ Signals:', signalsRes.data)
      
      setData({
        stats: statsRes.data,
        equity: equityRes.data,
        trades: tradesRes.data,
        signals: signalsRes.data,
        error: null,
        loading: false
      })
    } catch (error) {
      console.error('❌ Error fetching data:', error)
      setData(prev => ({
        ...prev,
        error: error.message,
        loading: false
      }))
    }
  }

  if (data.loading) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        background: '#0f172a',
        color: 'white'
      }}>
        <div>
          <h2>Loading dashboard data...</h2>
        </div>
      </div>
    )
  }

  if (data.error) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        padding: '2rem',
        background: '#0f172a',
        color: '#ef4444'
      }}>
        <h1>❌ Error Loading Dashboard</h1>
        <p>{data.error}</p>
        <button 
          onClick={fetchAllData}
          style={{
            marginTop: '1rem',
            padding: '0.5rem 1rem',
            background: '#6366f1',
            color: 'white',
            border: 'none',
            borderRadius: '0.5rem',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      padding: '2rem',
      background: '#0f172a',
      color: 'white'
    }}>
      <h1 style={{ marginBottom: '2rem', fontSize: '2rem', fontWeight: 'bold' }}>
        🧪 Test Dashboard - Data Verification
      </h1>
      
      <button 
        onClick={fetchAllData}
        style={{
          marginBottom: '2rem',
          padding: '0.5rem 1rem',
          background: '#6366f1',
          color: 'white',
          border: 'none',
          borderRadius: '0.5rem',
          cursor: 'pointer'
        }}
      >
        🔄 Refresh Data
      </button>

      {/* Stats Section */}
      <section style={{ 
        marginBottom: '2rem', 
        padding: '1.5rem', 
        background: '#1e293b',
        borderRadius: '0.5rem'
      }}>
        <h2 style={{ marginBottom: '1rem', fontSize: '1.5rem' }}>📊 Stats</h2>
        <pre style={{ 
          background: '#0f172a', 
          padding: '1rem', 
          borderRadius: '0.25rem',
          overflow: 'auto',
          fontSize: '0.875rem'
        }}>
          {JSON.stringify(data.stats, null, 2)}
        </pre>
      </section>

      {/* Equity Section */}
      <section style={{ 
        marginBottom: '2rem', 
        padding: '1.5rem', 
        background: '#1e293b',
        borderRadius: '0.5rem'
      }}>
        <h2 style={{ marginBottom: '1rem', fontSize: '1.5rem' }}>
          💰 Equity Curve ({data.equity?.length || 0} points)
        </h2>
        {data.equity && data.equity.length > 0 ? (
          <div>
            <p>First point: ${data.equity[0]?.balance}</p>
            <p>Last point: ${data.equity[data.equity.length - 1]?.balance}</p>
            <details style={{ marginTop: '1rem' }}>
              <summary style={{ cursor: 'pointer', color: '#6366f1' }}>
                View all data
              </summary>
              <pre style={{ 
                background: '#0f172a', 
                padding: '1rem', 
                borderRadius: '0.25rem',
                overflow: 'auto',
                fontSize: '0.875rem',
                marginTop: '0.5rem'
              }}>
                {JSON.stringify(data.equity, null, 2)}
              </pre>
            </details>
          </div>
        ) : (
          <p style={{ color: '#f59e0b' }}>⚠️ No equity data</p>
        )}
      </section>

      {/* Trades Section */}
      <section style={{ 
        marginBottom: '2rem', 
        padding: '1.5rem', 
        background: '#1e293b',
        borderRadius: '0.5rem'
      }}>
        <h2 style={{ marginBottom: '1rem', fontSize: '1.5rem' }}>
          📈 Trade History ({data.trades?.length || 0} trades)
        </h2>
        {data.trades && data.trades.length > 0 ? (
          <div>
            <p>Total closed trades: {data.trades.length}</p>
            <p>Wins: {data.trades.filter(t => (t.realized_pnl || 0) > 0).length}</p>
            <p>Losses: {data.trades.filter(t => (t.realized_pnl || 0) < 0).length}</p>
            <details style={{ marginTop: '1rem' }}>
              <summary style={{ cursor: 'pointer', color: '#6366f1' }}>
                View first 5 trades
              </summary>
              <pre style={{ 
                background: '#0f172a', 
                padding: '1rem', 
                borderRadius: '0.25rem',
                overflow: 'auto',
                fontSize: '0.875rem',
                marginTop: '0.5rem'
              }}>
                {JSON.stringify(data.trades.slice(0, 5), null, 2)}
              </pre>
            </details>
          </div>
        ) : (
          <p style={{ color: '#f59e0b' }}>⚠️ No trade history</p>
        )}
      </section>

      {/* Signals Section */}
      <section style={{ 
        marginBottom: '2rem', 
        padding: '1.5rem', 
        background: '#1e293b',
        borderRadius: '0.5rem'
      }}>
        <h2 style={{ marginBottom: '1rem', fontSize: '1.5rem' }}>🎯 Signals</h2>
        <pre style={{ 
          background: '#0f172a', 
          padding: '1rem', 
          borderRadius: '0.25rem',
          overflow: 'auto',
          fontSize: '0.875rem'
        }}>
          {JSON.stringify(data.signals, null, 2)}
        </pre>
      </section>

      <div style={{ 
        marginTop: '2rem', 
        padding: '1rem', 
        background: '#10b981',
        color: 'white',
        borderRadius: '0.5rem'
      }}>
        <p>✅ If you see data above, the APIs are working correctly!</p>
        <p>The issue is likely in the React Dashboard component styling or rendering logic.</p>
      </div>
    </div>
  )
}

export default TestDashboard
