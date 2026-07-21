import { NavLink } from 'react-router-dom'
import { useSafety } from '../context/SafetyContext'
import { LayoutDashboard, Bell, Camera, ClipboardList, LineChart, FileText } from 'lucide-react'

const NAV = [
  { to: '/',        Icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/alerts',  Icon: Bell, label: 'Alerts' },
  { to: '/cctv',   Icon: Camera, label: 'CCTV / PPE' },
  { to: '/reports', Icon: ClipboardList, label: 'Reports' },
  { to: '/history', Icon: LineChart, label: 'Trends' },
  { to: '/permits', Icon: FileText, label: 'Permits' },
]

export default function Sidebar() {
  const { state } = useSafety()
  const { alerts, riskScore, riskLevel } = state

  const activeAlerts = alerts.filter(a => !a.acknowledged && !a.resolved)
  const critAlerts   = activeAlerts.filter(a => a.severity === 'CRITICAL')

  const levelClass = { SAFE: 'safe', WARNING: 'warning', HIGH: 'high', CRITICAL: 'critical' }[riskLevel] || 'safe'

  return (
    <nav className="sidebar">
      {/* Brand area */}
      <div style={{ padding: 'var(--spacing-3)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{ background: 'var(--accent)', borderRadius: 'var(--radius-sm)', width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800, fontSize: '1.2rem', boxShadow: '0 4px 10px rgba(124, 58, 237, 0.3)' }}>
          S
        </div>
        <div style={{ fontWeight: 800, fontSize: '1.1rem', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
          SafetyAI
        </div>
      </div>

      <div className="section-title">Navigation</div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
        {NAV.map(({ to, Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <div className="icon-wrapper">
              <Icon size={18} strokeWidth={2.5} />
            </div>
            <span>{label}</span>
            {label === 'Alerts' && activeAlerts.length > 0 && (
              <span className="nav-badge" style={{ backgroundColor: 'var(--crit)' }}>{activeAlerts.length}</span>
            )}
            {label === 'Reports' && activeAlerts.length > 0 && (
              <span className="nav-badge">{critAlerts.length || activeAlerts.length}</span>
            )}
          </NavLink>
        ))}
      </div>

      <div style={{ borderTop: '1px solid var(--border)', margin: 'var(--spacing-2)', padding: 'var(--spacing-2) 0 0' }} />
      <div className="section-title">Global Risk Status</div>
      
      {/* Risk Overview */}
      <div style={{ padding: '0 var(--spacing-2)', marginBottom: 'var(--spacing-3)' }}>
        <div style={{ background: 'var(--bg-base)', borderRadius: 'var(--radius-sm)', padding: '0.75rem 1rem', border: '1px solid var(--border)' }}>
          <div style={{ height: 6, background: 'var(--border-2)', borderRadius: 3, overflow: 'hidden', marginBottom: '0.5rem' }}>
            <div style={{
              height: '100%',
              width:  `${riskScore}%`,
              background: `var(--${levelClass === 'safe' ? 'safe' : levelClass === 'warning' ? 'warn' : levelClass === 'high' ? 'high' : 'crit'})`,
              borderRadius: 3,
              transition: 'width 1s ease',
            }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className={`badge badge-${levelClass}`} style={{ fontSize: '0.65rem', padding: '0.2rem 0.5rem' }}>{riskLevel}</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>{riskScore}</span>
          </div>
        </div>
      </div>

      <div className="section-title">Zone Status</div>
      {/* Zone list */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {Object.entries(state.zoneBreakdown).map(([zone, info]) => (
          <div key={zone} style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            padding: '0.3rem var(--spacing-3)', fontSize: '0.8rem',
          }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: info.color, flexShrink: 0 }} />
            <span style={{ color: 'var(--text-secondary)', flex: 1, fontWeight: 500 }}>{zone}</span>
            <span style={{ fontFamily: 'var(--font-mono)', color: info.color, fontWeight: 700 }}>{info.risk_score}</span>
          </div>
        ))}
      </div>

      <div style={{ padding: 'var(--spacing-3)', marginTop: 'auto', borderTop: '1px solid var(--border)' }}>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textAlign: 'center', fontWeight: 500 }}>
          SafetyAI Enterprise v2.0
        </div>
      </div>
    </nav>
  )
}
