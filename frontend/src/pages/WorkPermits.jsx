import { useState } from 'react'
import { useSafety } from '../context/SafetyContext'
import { useApi } from '../hooks/useApi'
import { ClipboardCheck, FilePlus, Users, MapPin, CheckCircle, AlertCircle } from 'lucide-react'

export default function WorkPermits() {
  const { state } = useSafety()
  const { createPermit } = useApi()
  const [permitType, setPermitType] = useState('hot_work')
  const [zone, setZone] = useState('Zone-D')
  const [supervisor, setSupervisor] = useState('Ahmed Al-Rashid')
  const [isLoading, setIsLoading] = useState(false)
  const [toast, setToast] = useState(null) // { type: 'success'|'error', message: string }

  const showToast = (type, message) => {
    setToast({ type, message })
    setTimeout(() => setToast(null), 5000)
  }

  const handleIssuePermit = async (e) => {
    e.preventDefault()
    
    // Validation
    if (!supervisor || !supervisor.trim()) {
      showToast('error', 'Safety Supervisor name is required')
      return
    }
    if (supervisor.length < 3) {
      showToast('error', 'Safety Supervisor name must be at least 3 characters')
      return
    }

    setIsLoading(true)
    try {
      await createPermit({
        permit_type: permitType,
        location: `${zone} Sub-station`,
        zone,
        issued_by: supervisor.trim(),
        worker_names: ['Worker-902', 'Worker-113'],
        expires_at: new Date(Date.now() + 4 * 3600000).toISOString(),
        notes: `Routine ${permitType.replace('_', ' ')} maintenance`
      })
      showToast('success', `Permit successfully created and issued to ${zone}!`)
      setSupervisor('Ahmed Al-Rashid')
    } catch (err) {
      showToast('error', err.message || 'API error: failed to create permit')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-4)' }}>
      <div className="card-header" style={{ marginBottom: 0, padding: '0 var(--spacing-2)' }}>
        <span className="card-title" style={{ fontSize: '1.2rem' }}>
          <ClipboardCheck color="var(--accent)" /> Work Permit Administration
        </span>
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        {/* Issue Permit Form */}
        <div className="card fade-in" style={{ padding: 'var(--spacing-4)' }}>
          <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)' }}>
            <FilePlus size={18} color="var(--accent)" /> Issue Safety Permit
          </h3>
          <form onSubmit={handleIssuePermit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Permit Class</label>
              <select
                value={permitType} onChange={e => setPermitType(e.target.value)}
                style={{ 
                  background: 'var(--bg-base)', color: 'var(--text-primary)', border: '1px solid var(--border)', 
                  padding: '0.75rem', borderRadius: 'var(--radius-sm)', fontSize: '0.9rem', outline: 'none',
                  transition: 'border-color 0.2s'
                }}
              >
                <option value="hot_work">🔥 Hot Work Permit (Welding, Cutting)</option>
                <option value="confined_space">🕳️ Confined Space Entry</option>
                <option value="electrical">⚡ Electrical Isolation</option>
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Operational Zone</label>
              <select
                value={zone} onChange={e => setZone(e.target.value)}
                style={{ 
                  background: 'var(--bg-base)', color: 'var(--text-primary)', border: '1px solid var(--border)', 
                  padding: '0.75rem', borderRadius: 'var(--radius-sm)', fontSize: '0.9rem', outline: 'none',
                  transition: 'border-color 0.2s'
                }}
              >
                <option value="Zone-D">Zone D (Hazardous Area)</option>
                <option value="Zone-A">Zone A (Processing Area)</option>
                <option value="Zone-B">Zone B (Reaction Area)</option>
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Safety Supervisor</label>
              <div style={{ position: 'relative' }}>
                <Users size={16} color="var(--text-muted)" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="text" value={supervisor} onChange={e => setSupervisor(e.target.value)}
                  style={{ 
                    width: '100%', background: 'var(--bg-base)', color: 'var(--text-primary)', border: '1px solid var(--border)', 
                    padding: '0.75rem 0.75rem 0.75rem 2.25rem', borderRadius: 'var(--radius-sm)', fontSize: '0.9rem', outline: 'none',
                    transition: 'border-color 0.2s'
                  }}
                />
              </div>
            </div>

            <button 
              type="submit" 
              className="btn btn-primary" 
              disabled={isLoading}
              style={{ width: '100%', padding: '0.75rem', marginTop: '0.5rem', opacity: isLoading ? 0.7 : 1, cursor: isLoading ? 'not-allowed' : 'pointer', display: 'flex', justifyContent: 'center' }}
            >
              {isLoading ? 'Processing Authorization...' : 'Create and Issue Permit'}
            </button>
          </form>
          
          {toast && (
            <div className="fade-in" style={{ 
                marginTop: '1.25rem', padding: '1rem', borderRadius: 'var(--radius-sm)', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem',
                backgroundColor: toast.type === 'success' ? 'var(--safe-bg)' : 'var(--crit-bg)',
                color: toast.type === 'success' ? 'var(--safe)' : 'var(--crit)',
                border: `1px solid ${toast.type === 'success' ? 'var(--safe)' : 'var(--crit)'}40`
              }}
            >
              {toast.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
              {toast.message}
            </div>
          )}
        </div>

        {/* Current active list */}
        <div className="card fade-in" style={{ padding: 'var(--spacing-4)' }}>
          <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-primary)' }}>Active Issued Permits</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {state.permits.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', padding: '2rem 1rem', textAlign: 'center', background: 'var(--bg-base)', borderRadius: 'var(--radius-sm)' }}>
                No active permits currently issued.
              </div>
            ) : (
              state.permits.map(permit => (
                <div key={permit.permit_id} style={{ 
                  background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', 
                  padding: '1rem', transition: 'all 0.2s', boxShadow: 'var(--shadow-sm)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>{permit.permit_id}</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Valid for 4 hours</span>
                    </div>
                    <span className="badge badge-info">{permit.permit_type.replace('_', ' ').toUpperCase()}</span>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', borderTop: '1px solid var(--border)', paddingTop: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      <Users size={14} color="var(--accent)" />
                      {permit.issued_by}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      <MapPin size={14} color="var(--accent)" />
                      {permit.zone}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
