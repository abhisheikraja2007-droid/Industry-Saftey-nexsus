import { useSafety } from '../context/SafetyContext'
import { Wind, Cloud, Skull, Thermometer, Droplets, Activity } from 'lucide-react'

const SENSOR_CONFIG = [
  { key: 'gas_ch4',  label: 'Methane (CH₄)', unit: 'ppm', Icon: Wind, warn: 25, crit: 40 },
  { key: 'gas_co',   label: 'Carbon Monoxide',unit: 'ppm', Icon: Cloud, warn: 50, crit: 100 },
  { key: 'gas_h2s',  label: 'Hydrogen Sulfide',unit: 'ppm', Icon: Skull, warn: 10, crit: 20 },
  { key: 'temp',     label: 'Temperature',    unit: '°C',  Icon: Thermometer, warn: 70, crit: 85 },
  { key: 'humidity', label: 'Humidity',       unit: '%',   Icon: Droplets, warn: 80, crit: 90 },
]

function getSeverity(val, warn, crit) {
  if (val >= crit) return 'critical'
  if (val >= warn) return 'high'
  if (val >= warn * 0.7) return 'warning'
  return 'safe'
}

function SensorCard({ config, zones }) {
  const readings = Object.entries(zones)
    .map(([zone, sensors]) => ({ zone, value: sensors[config.key] }))
    .filter(r => r.value != null)

  const maxVal  = readings.length ? Math.max(...readings.map(r => r.value)) : 0
  const sev     = getSeverity(maxVal, config.warn, config.crit)
  const pct     = Math.min(100, (maxVal / (config.crit * 1.2)) * 100)
  const Icon    = config.Icon

  const color = `var(--${sev === 'safe' ? 'safe' : sev === 'warning' ? 'warn' : sev === 'high' ? 'high' : 'crit'})`

  return (
    <div className="card fade-in" style={{ 
      padding: 'var(--spacing-3)', 
      position: 'relative',
      borderLeft: `4px solid ${color}`,
      boxShadow: 'var(--shadow-sm)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ 
            width: 40, height: 40, borderRadius: 'var(--radius-sm)', 
            background: `var(--${sev === 'safe' ? 'safe' : sev === 'warning' ? 'warn' : sev === 'high' ? 'high' : 'crit'}-bg)`,
            color: color, display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Icon size={20} strokeWidth={2.5} />
          </div>
          <div>
            <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 700 }}>
              {config.label}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 500 }}>
              Peak Reading
            </div>
          </div>
        </div>
        <span className={`badge badge-${sev}`} style={{ fontSize: '0.65rem', padding: '0.2rem 0.6rem' }}>
          {sev.toUpperCase()}
        </span>
      </div>

      {/* Max value */}
      <div style={{
        fontFamily: 'var(--font-sans)', fontSize: '2.2rem', fontWeight: 800,
        color: color, lineHeight: 1, marginBottom: '0.75rem', display: 'flex', alignItems: 'baseline', gap: '0.25rem'
      }}>
        {maxVal.toFixed(1)}
        <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)' }}>
          {config.unit}
        </span>
      </div>

      {/* Mini Trend Bar */}
      <div style={{ height: 4, background: 'var(--bg-hover)', borderRadius: 2, margin: '0.5rem 0 0.75rem', overflow: 'hidden' }}>
        <div style={{
          height: '100%', width:  `${pct}%`,
          background: `linear-gradient(90deg, var(--safe), ${color})`,
          borderRadius: 2, transition: 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
        }} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
        <span>Threshold: {config.warn}{config.unit}</span>
        <span style={{ color: 'var(--crit)' }}>Crit: {config.crit}{config.unit}</span>
      </div>

      {/* Zone readings (optional chip view) */}
      {readings.length > 0 && (
        <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-2)', display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
          {readings.map(({ zone, value }) => (
            <span key={zone} style={{
              fontSize: '0.65rem', padding: '0.2rem 0.5rem',
              background: 'var(--bg-base)', borderRadius: 'var(--radius-full)',
              color: 'var(--text-secondary)', fontWeight: 600, border: '1px solid var(--border)'
            }}>
              {zone.replace('Zone-', 'Z')}: <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{value?.toFixed(1)}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export default function SensorPanel() {
  const { state } = useSafety()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-3)' }}>
      <div className="card-header" style={{ marginBottom: 0 }}>
        <span className="card-title"><Activity size={18} color="var(--accent)" /> Live Telemetry</span>
        <span className="badge badge-info" style={{ background: 'var(--accent-bg)', color: 'var(--accent)' }}>Real-time Sensors</span>
      </div>
      <div className="grid-auto">
        {SENSOR_CONFIG.map(cfg => (
          <SensorCard key={cfg.key} config={cfg} zones={state.sensors} />
        ))}
      </div>
    </div>
  )
}
