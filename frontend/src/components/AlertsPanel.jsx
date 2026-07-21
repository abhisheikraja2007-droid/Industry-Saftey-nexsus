import { useSafety } from '../context/SafetyContext'
import { useApi } from '../hooks/useApi'
import { formatDistanceToNow } from 'date-fns'
import { AlertCircle, Clock, MapPin, CheckCircle, ShieldAlert } from 'lucide-react'

export default function AlertsPanel() {
  const { state } = useSafety()
  const { acknowledgeAlert } = useApi()
  const { alerts } = state

  const activeAlerts = alerts.filter(a => !a.resolved)

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 'var(--spacing-4)' }}>
      <div className="card-header" style={{ marginBottom: '1rem' }}>
        <span className="card-title"><AlertCircle size={18} color="var(--accent)" /> Active Alerts</span>
        <span className="badge badge-critical">{activeAlerts.length} Active</span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 'var(--spacing-3)', maxHeight: '420px', paddingRight: '0.5rem' }}>
        {activeAlerts.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: '200px', color: 'var(--text-muted)' }}>
            <ShieldAlert size={48} color="var(--border-2)" strokeWidth={1} style={{ marginBottom: '1rem' }} />
            <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>No active alerts</div>
            <div style={{ fontSize: '0.85rem' }}>Facility status is currently nominal.</div>
          </div>
        ) : (
          activeAlerts.map(alert => {
            const isCrit = alert.severity === 'CRITICAL'
            const isHigh = alert.severity === 'HIGH'
            const badgeClass = isCrit ? 'critical' : isHigh ? 'high' : 'warning'
            const color = `var(--${isCrit ? 'crit' : isHigh ? 'high' : 'warn'})`

            return (
              <div key={alert.id} className="fade-in" style={{ 
                background: 'var(--bg-surface)',
                border: '1px solid var(--border)',
                borderLeft: `4px solid ${color}`,
                borderRadius: 'var(--radius-sm)',
                padding: '1rem',
                boxShadow: 'var(--shadow-sm)',
                transition: 'all 0.2s ease',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className={`badge badge-${badgeClass}`} style={{ fontSize: '0.65rem', padding: '0.2rem 0.6rem' }}>
                      {alert.severity}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-sans)' }}>
                      <Clock size={12} />
                      {alert.created_at ? formatDistanceToNow(new Date(alert.created_at), { addSuffix: true }) : ''}
                    </span>
                  </div>
                </div>

                <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.4 }}>
                  {alert.message}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.25rem' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', color: 'var(--text-secondary)', background: 'var(--bg-base)', padding: '0.3rem 0.6rem', borderRadius: 'var(--radius-full)' }}>
                    <MapPin size={12} color="var(--accent)" />
                    {alert.zone}
                  </span>

                  {!alert.acknowledged ? (
                    <button
                      className="btn btn-ghost"
                      style={{ padding: '0.3rem 0.8rem', fontSize: '0.75rem', border: `1px solid ${color}40`, color: color }}
                      onClick={() => acknowledgeAlert(alert.id)}
                    >
                      Acknowledge
                    </button>
                  ) : (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', color: 'var(--safe)', fontWeight: 600 }}>
                      <CheckCircle size={14} />
                      Acknowledged
                    </span>
                  )}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
