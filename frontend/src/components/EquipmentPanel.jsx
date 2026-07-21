import { useSafety } from '../context/SafetyContext'
import { Settings, Server, AlertTriangle } from 'lucide-react'

export default function EquipmentPanel() {
  const { state } = useSafety()
  const { equipment } = state
  const eqList = Object.values(equipment)

  return (
    <div className="card fade-in" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 'var(--spacing-4)' }}>
      <div className="card-header" style={{ marginBottom: '1rem' }}>
        <span className="card-title"><Settings size={18} color="var(--accent)" /> Equipment Monitor</span>
        <span className="badge badge-info" style={{ background: 'var(--accent-bg)', color: 'var(--accent)' }}>{eqList.length} Online</span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '420px', paddingRight: '0.5rem' }}>
        {eqList.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: '150px', color: 'var(--text-muted)' }}>
            <Server size={32} color="var(--border-2)" style={{ marginBottom: '0.5rem' }} />
            <span style={{ fontSize: '0.9rem' }}>No equipment telemetry detected.</span>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Equipment</th>
                  <th>Status</th>
                  <th>Temp</th>
                  <th>Vibration</th>
                  <th>Zone</th>
                </tr>
              </thead>
              <tbody>
                {eqList.map(eq => {
                  const isFault = eq.status === 'fault'
                  const isOff = eq.status === 'offline'
                  const statusColor = isFault ? 'var(--crit)' : isOff ? 'var(--text-muted)' : 'var(--safe)'

                  return (
                    <tr key={eq.equipment_id}>
                      <td style={{ fontWeight: 600 }}>
                        <div style={{ color: 'var(--text-primary)' }}>{eq.name}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>{eq.equipment_id}</div>
                      </td>
                      <td>
                        <span style={{ 
                          color: statusColor, fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase',
                          display: 'flex', alignItems: 'center', gap: '0.3rem', background: isFault ? 'var(--crit-bg)' : 'transparent',
                          padding: isFault ? '0.2rem 0.5rem' : '0', borderRadius: 'var(--radius-full)', width: 'fit-content'
                        }}>
                          {isFault ? <AlertTriangle size={12} /> : <div style={{ width: 6, height: 6, borderRadius: '50%', background: statusColor }} />}
                          {eq.status}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                        {eq.temperature != null ? `${eq.temperature.toFixed(1)}°C` : '—'}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                        {eq.vibration != null ? `${eq.vibration.toFixed(2)} mm/s` : '—'}
                      </td>
                      <td>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', background: 'var(--bg-base)', padding: '0.2rem 0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                          {eq.zone}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
