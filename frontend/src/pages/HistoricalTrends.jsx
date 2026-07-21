import { useState, useEffect } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js'
import { useSafety } from '../context/SafetyContext'
import { LineChart, Activity } from 'lucide-react'

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler
)

export default function HistoricalTrends() {
  const { state } = useSafety()
  const [history, setHistory] = useState([])

  const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  // Fetch initial history from DB on load
  useEffect(() => {
    async function loadHistory() {
      try {
        const res = await fetch(`${API}/api/sensors/history?zone=Zone-D&hours=24`)
        const data = await res.json()
        if (data.history && data.history.length > 0) {
          const groups = {}
          data.history.forEach(r => {
            const timeStr = new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            if (!groups[timeStr]) {
              groups[timeStr] = { time: timeStr, ch4: 0, co: 0, h2s: 0 }
            }
            if (r.sensor_type === 'gas_ch4') groups[timeStr].ch4 = r.value
            if (r.sensor_type === 'gas_co') groups[timeStr].co = r.value
            if (r.sensor_type === 'gas_h2s') groups[timeStr].h2s = r.value
          })
          const sorted = Object.values(groups).slice(-30)
          setHistory(sorted)
        }
      } catch (e) {
        console.warn('Failed to load sensor history:', e)
      }
    }
    loadHistory()
  }, [])

  // Keep a local window of the last 30 gas readings for the live trend chart
  useEffect(() => {
    const ch4 = state.sensors['Zone-D']?.gas_ch4 || 0
    const co = state.sensors['Zone-D']?.gas_co || 0
    const h2s = state.sensors['Zone-D']?.gas_h2s || 0

    if (ch4 === 0 && co === 0 && h2s === 0) return

    setHistory(prev => {
      const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      if (prev.length > 0 && prev[prev.length - 1].time === timeStr) {
        const next = [...prev]
        next[next.length - 1] = { time: timeStr, ch4, co, h2s }
        return next
      }
      const next = [...prev, {
        time: timeStr,
        ch4, co, h2s
      }]
      if (next.length > 30) next.shift()
      return next
    })
  }, [state.sensors])

  const chartData = {
    labels: history.map(h => h.time),
    datasets: [
      {
        label: 'Methane (CH₄)',
        data: history.map(h => h.ch4),
        borderColor: '#EF4444',
        backgroundColor: 'rgba(239, 68, 68, 0.05)',
        tension: 0.4,
        fill: true,
        pointRadius: 2,
        pointHoverRadius: 5
      },
      {
        label: 'Carbon Monoxide (CO)',
        data: history.map(h => h.co),
        borderColor: '#F59E0B',
        backgroundColor: 'rgba(245, 158, 11, 0.05)',
        tension: 0.4,
        fill: true,
        pointRadius: 2,
        pointHoverRadius: 5
      },
      {
        label: 'Hydrogen Sulphide (H₂S)',
        data: history.map(h => h.h2s),
        borderColor: '#7C3AED',
        backgroundColor: 'rgba(124, 58, 237, 0.05)',
        tension: 0.4,
        fill: true,
        pointRadius: 2,
        pointHoverRadius: 5
      }
    ]
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: { 
        position: 'top',
        labels: { 
          color: '#6B7280', 
          usePointStyle: true, 
          boxWidth: 8,
          font: { family: 'Inter', size: 12, weight: 500 }
        } 
      },
      tooltip: {
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        titleColor: '#111827',
        bodyColor: '#6B7280',
        borderColor: '#ECECEC',
        borderWidth: 1,
        padding: 12,
        boxPadding: 6,
        usePointStyle: true,
        titleFont: { family: 'Inter', size: 13, weight: 600 },
        bodyFont: { family: 'Inter', size: 12 }
      }
    },
    scales: {
      x: { 
        grid: { display: false }, 
        ticks: { color: '#9CA3AF', font: { family: 'Inter', size: 11 } } 
      },
      y: { 
        grid: { color: '#F3F4F6', drawBorder: false }, 
        ticks: { color: '#9CA3AF', font: { family: 'Inter', size: 11 }, padding: 10 } 
      }
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-4)' }}>
      <div className="card-header" style={{ marginBottom: 0, padding: '0 var(--spacing-2)' }}>
        <span className="card-title" style={{ fontSize: '1.2rem' }}>
          <LineChart color="var(--accent)" /> Live Telemetry Trends
        </span>
        <span className="badge badge-info" style={{ background: 'var(--accent-bg)', color: 'var(--accent)' }}>
          <Activity size={14} style={{ marginRight: '4px' }}/> Zone-D Active
        </span>
      </div>

      <div className="card fade-in" style={{ padding: 'var(--spacing-4)' }}>
        <div style={{ height: '500px', width: '100%', position: 'relative' }}>
          {history.length < 2 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', gap: '1rem' }}>
              <div className="spinner" style={{ borderColor: 'var(--border-2)', borderTopColor: 'var(--accent)' }}></div>
              Collecting telemetry points...
            </div>
          ) : (
            <Line data={chartData} options={chartOptions} />
          )}
        </div>
      </div>
    </div>
  )
}
