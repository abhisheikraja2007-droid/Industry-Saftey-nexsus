import { useSafety } from '../context/SafetyContext'
import { format } from 'date-fns'
import { Users, Clock, Shield } from 'lucide-react'

export default function ShiftInfo() {
  const { state } = useSafety()
  const { shift } = state

  return (
    <div className="card fade-in" style={{ padding: 'var(--spacing-4)' }}>
      <div className="card-title" style={{ marginBottom: '1rem' }}>
        <Users size={18} color="var(--accent)" /> Shift Details
      </div>
      {shift ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border)' }}>
            <span style={{ color: 'var(--text-muted)' }}>Current Shift:</span>
            <span style={{ textTransform: 'uppercase', fontWeight: 700, color: 'var(--accent)' }}>{shift.shift_type}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border)' }}>
            <span style={{ color: 'var(--text-muted)' }}>Supervisor:</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <Shield size={12} color="var(--text-muted)" /> {shift.supervisor}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border)' }}>
            <span style={{ color: 'var(--text-muted)' }}>Active Workers:</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{shift.worker_count} Personnel</span>
          </div>
          {shift.start_time && (
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Started At:</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <Clock size={12} />
                {format(new Date(shift.start_time), 'HH:mm')}
              </span>
            </div>
          )}
        </div>
      ) : (
        <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center', padding: '2rem 0' }}>
          No active shift logged.
        </div>
      )}
    </div>
  )
}
