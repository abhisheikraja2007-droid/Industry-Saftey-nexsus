import { useSafety } from '../context/SafetyContext'
import { ClipboardCheck, MapPin, User, FileText } from 'lucide-react'

export default function WorkPermitPanel() {
  const { state } = useSafety()
  const { permits } = state

  const activePermits = permits.filter(p => p.status === 'active')

  return (
    <div className="card fade-in" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 'var(--spacing-4)' }}>
      <div className="card-header" style={{ marginBottom: '1rem' }}>
        <span className="card-title"><ClipboardCheck size={18} color="var(--accent)" /> Active Permits</span>
        <span className="badge badge-info" style={{ background: 'var(--accent-bg)', color: 'var(--accent)' }}>{activePermits.length} Active</span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 'var(--spacing-3)', maxHeight: '420px', paddingRight: '0.5rem' }}>
        {activePermits.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: '150px', color: 'var(--text-muted)' }}>
            <FileText size={32} color="var(--border-2)" style={{ marginBottom: '0.5rem' }} />
            <span style={{ fontSize: '0.9rem' }}>No active permits issued.</span>
          </div>
        ) : (
          activePermits.map(permit => {
            const isHotWork = permit.permit_type === 'hot_work'
            const color = isHotWork ? 'var(--high)' : 'var(--accent)'

            return (
              <div key={permit.permit_id} style={{ 
                background: 'var(--bg-base)', border: '1px solid var(--border)', borderLeft: `3px solid ${color}`,
                padding: '1rem', borderRadius: 'var(--radius-sm)', display: 'flex', flexDirection: 'column', gap: '0.5rem' 
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="badge" style={{ fontSize: '0.65rem', background: `${color}15`, color: color, padding: '0.2rem 0.5rem' }}>
                    {permit.permit_type.replace('_', ' ').toUpperCase()}
                  </span>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {permit.permit_id}
                  </span>
                </div>

                <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 600 }}>
                  <MapPin size={14} color="var(--text-muted)" /> {permit.location} ({permit.zone})
                </div>

                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  Supervisor: <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{permit.issued_by}</span>
                </div>

                {permit.worker_names && permit.worker_names.length > 0 && (
                  <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.25rem', flexWrap: 'wrap' }}>
                    {permit.worker_names.map(w => (
                      <span key={w} style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', fontSize: '0.7rem', background: 'var(--bg-surface)', border: '1px solid var(--border)', color: 'var(--text-secondary)', padding: '0.2rem 0.5rem', borderRadius: 'var(--radius-full)' }}>
                        <User size={10} /> {w}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
