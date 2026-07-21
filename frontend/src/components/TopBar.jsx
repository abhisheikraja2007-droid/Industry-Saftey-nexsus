import { useSafety } from '../context/SafetyContext'
import { format } from 'date-fns'
import { Search, Bell, ChevronDown, User, MapPin } from 'lucide-react'

export default function TopBar() {
  const { state } = useSafety()
  const { riskScore, riskLevel, connected, lastUpdate } = state

  const levelClass = {
    SAFE:     'safe',
    WARNING:  'warning',
    HIGH:     'high',
    CRITICAL: 'critical',
  }[riskLevel] || 'safe'

  return (
    <header className="topbar">
      {/* Search Bar */}
      <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
        <div style={{ position: 'relative', width: '300px' }}>
          <Search size={18} color="var(--text-muted)" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
          <input 
            type="text" 
            placeholder="Search alerts, sensors, or reports..." 
            style={{
              width: '100%',
              padding: '0.6rem 1rem 0.6rem 2.5rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border)',
              background: 'var(--bg-base)',
              fontSize: '0.85rem',
              color: 'var(--text-primary)',
              outline: 'none',
              transition: 'border-color 0.2s'
            }}
            onFocus={(e) => e.target.style.borderColor = 'var(--accent)'}
            onBlur={(e) => e.target.style.borderColor = 'var(--border)'}
          />
        </div>
      </div>

      {/* Center — Risk indicator & Facility Selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-3)' }}>
        
        {/* Facility Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--bg-base)', padding: '0.4rem 0.8rem', borderRadius: 'var(--radius-sm)', cursor: 'pointer', border: '1px solid var(--border)' }}>
          <MapPin size={16} color="var(--accent)" />
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>Al-Fajr Facility</span>
          <ChevronDown size={14} color="var(--text-muted)" />
        </div>

        {/* Risk Badge */}
        <div className={`badge badge-${levelClass}`} style={{ padding: '0.4rem 1rem', fontSize: '0.75rem', border: '1px solid var(--border)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.05rem', fontWeight: 800 }}>
            {riskScore}
          </span>
          <span style={{ opacity: 0.7 }}>/ 100</span>
          <span style={{ margin: '0 0.4rem', opacity: 0.5 }}>•</span>
          <span>{riskLevel}</span>
        </div>
      </div>

      {/* Right — Status, Notifications, Profile */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-3)', flex: 1, justifyContent: 'flex-end' }}>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
          <span className={`pulse-dot ${connected ? 'live' : ''}`}
            style={{ background: connected ? 'var(--safe)' : 'var(--text-muted)' }} />
          {connected ? 'Live Data' : 'Reconnecting…'}
        </div>

        <div style={{ width: 1, height: 24, background: 'var(--border)' }} />

        {/* Notifications */}
        <div style={{ position: 'relative', cursor: 'pointer' }}>
          <Bell size={20} color="var(--text-secondary)" />
          {riskLevel === 'CRITICAL' && (
            <div style={{ position: 'absolute', top: -2, right: -2, width: 8, height: 8, background: 'var(--crit)', borderRadius: '50%', border: '2px solid var(--bg-surface)' }} />
          )}
        </div>

        {/* Profile Avatar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
          <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'var(--accent-bg)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.9rem' }}>
            A
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>Admin</span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Safety Officer</span>
          </div>
          <ChevronDown size={14} color="var(--text-muted)" style={{ marginLeft: '0.2rem' }} />
        </div>
      </div>
    </header>
  )
}
