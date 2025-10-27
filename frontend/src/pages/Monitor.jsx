import { useEffect } from 'react'

export default function MonitorPage() {
  useEffect(() => {
    // Redirect to the original ICT monitor HTML page
    window.location.href = '/monitor'
  }, [])

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500"></div>
    </div>
  )
}
