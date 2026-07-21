import { useState } from 'react'
import { useSafety } from '../context/SafetyContext'
import { useApi } from '../hooks/useApi'

export default function Alerts() {
  const { state } = useSafety()
  const { acknowledgeAlert } = useApi()
  const [filterSeverity, setFilterSeverity] = useState('ALL')
  const [filterAck, setFilterAck] = useState('ALL')

  const getSeverityBadgeClass = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL': return 'badge badge-critical'
      case 'HIGH': return 'badge badge-warning'
      case 'WARNING': return 'badge badge-info'
      default: return 'badge'
    }
  }

  const filteredAlerts = state.alerts.filter(a => {
    if (filterSeverity !== 'ALL' && a.severity !== filterSeverity) return false
    if (filterAck === 'UNACK' && a.acknowledged) return false
    if (filterAck === 'ACK' && !a.acknowledged) return false
    return true
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="card-title">🚨 Facility Safety Alerts Log</span>
        
        {/* Filters */}
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginRight: '0.4rem' }}>Severity:</label>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              style={{
                background: 'var(--bg-card-2)', border: '1px solid var(--border)',
                borderRadius: 4, color: 'var(--text-primary)', padding: '0.25rem 0.5rem', fontSize: '0.8rem'
              }}
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="WARNING">Warning</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginRight: '0.4rem' }}>Status:</label>
            <select
              value={filterAck}
              onChange={(e) => setFilterAck(e.target.value)}
              style={{
                background: 'var(--bg-card-2)', border: '1px solid var(--border)',
                borderRadius: 4, color: 'var(--text-primary)', padding: '0.25rem 0.5rem', fontSize: '0.8rem'
              }}
            >
              <option value="ALL">All Alerts</option>
              <option value="UNACK">Awaiting Acknowledgment</option>
              <option value="ACK">Acknowledged</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card">
        {filteredAlerts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            No alerts match the selected criteria. System status normal.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '0.75rem 0.5rem' }}>Time</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Zone</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Severity</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Rule / Code</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Description</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Risk Score</th>
                <th style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.map(a => (
                <tr key={a.id} style={{ borderBottom: '1px solid var(--border)', background: a.acknowledged ? 'transparent' : 'rgba(239, 68, 68, 0.02)' }}>
                  <td style={{ padding: '0.75rem 0.5rem', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                    {a.created_at ? new Date(a.created_at).toLocaleTimeString() : 'Live'}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', fontWeight: 600 }}>{a.zone}</td>
                  <td style={{ padding: '0.75rem 0.5rem' }}>
                    <span className={getSeverityBadgeClass(a.severity)}>{a.severity}</span>
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>
                    {a.alert_code}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', color: 'var(--text-primary)' }}>{a.message}</td>
                  <td style={{ padding: '0.75rem 0.5rem', fontWeight: 700 }}>{a.risk_score}</td>
                  <td style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>
                    {a.acknowledged ? (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        ✓ Acked by {a.acknowledged_by || 'Operator'}
                      </span>
                    ) : (
                      <button
                        className="btn btn-primary"
                        style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                        onClick={() => acknowledgeAlert(a.id)}
                      >
                        Acknowledge
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
