import { useSafety } from '../context/SafetyContext'
import { Map } from 'lucide-react'

/* Zone layout (approximate positions as % of SVG canvas) */
const ZONE_LAYOUT = {
  'Zone-A':       { x: 10,  y: 10,  w: 36, h: 36, label: 'Zone A\nProcessing' },
  'Zone-B':       { x: 54,  y: 10,  w: 36, h: 36, label: 'Zone B\nReaction' },
  'Zone-C':       { x: 10,  y: 54,  w: 36, h: 34, label: 'Zone C\nStorage' },
  'Zone-D':       { x: 54,  y: 54,  w: 36, h: 34, label: 'Zone D\nHazardous' },
  'Control-Room': { x: 35,  y: 42,  w: 30, h: 16, label: 'Control\nCenter' },
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r},${g},${b},${alpha})`
}

export default function FacilityHeatmap() {
  const { state } = useSafety()
  const { zoneBreakdown } = state

  return (
    <div className="card" style={{ padding: 'var(--spacing-4)', display: 'flex', flexDirection: 'column' }}>
      <div className="card-header" style={{ marginBottom: '1rem' }}>
        <span className="card-title"><Map size={18} color="var(--accent)" /> Facility Heatmap</span>
        <span className="badge badge-info" style={{ background: 'var(--accent-bg)', color: 'var(--accent)' }}>Live Map</span>
      </div>

      <div style={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
        <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%', minHeight: '300px', filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.02))' }}>
          <defs>
            {Object.entries(zoneBreakdown).map(([zone, info]) => (
              <linearGradient id={`grad-${zone}`} key={zone} x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor={hexToRgba(info.color, 0.05)} />
                <stop offset="100%" stopColor={hexToRgba(info.color, 0.15)} />
              </linearGradient>
            ))}
          </defs>
          
          {/* Background */}
          <rect width="100" height="100" fill="var(--bg-base)" rx="4" />
          
          {/* Grid lines */}
          {[20, 40, 60, 80].map(v => (
            <g key={v}>
              <line x1={v} y1="0" x2={v} y2="100" stroke="var(--border)" strokeWidth="0.4" strokeDasharray="2 2" />
              <line x1="0" y1={v} x2="100" y2={v} stroke="var(--border)" strokeWidth="0.4" strokeDasharray="2 2" />
            </g>
          ))}

          {/* Zones */}
          {Object.entries(ZONE_LAYOUT).map(([zone, pos]) => {
            const info  = zoneBreakdown[zone]
            const color = info?.color || '#22c55e'
            const score = info?.risk_score || 0
            const [lbl1, lbl2] = pos.label.split('\n')
            const cx = pos.x + pos.w / 2
            const cy = pos.y + pos.h / 2

            return (
              <g key={zone} style={{ cursor: 'pointer', transition: 'all 0.3s ease' }} className="heatmap-zone">
                {/* Zone background */}
                <rect
                  x={pos.x} y={pos.y} width={pos.w} height={pos.h}
                  fill={`url(#grad-${zone})`}
                  stroke={color}
                  strokeWidth={score > 60 ? 1.2 : 0.6}
                  rx="3"
                  style={{ transition: 'all 0.5s ease' }}
                />
                
                {/* Glow effect for high risk */}
                {score > 60 && (
                  <rect
                    x={pos.x} y={pos.y} width={pos.w} height={pos.h}
                    fill="none"
                    stroke={color}
                    strokeWidth="3"
                    rx="3"
                    style={{ opacity: 0.2, filter: `blur(2px)` }}
                  />
                )}
                
                {/* Status indicator dot */}
                {zone !== 'Control-Room' && (
                  <circle cx={pos.x + pos.w - 4} cy={pos.y + 4} r="1.5" fill={color} filter={score > 60 ? 'drop-shadow(0 0 2px ' + color + ')' : ''} />
                )}

                {/* Zone label */}
                <text x={cx} y={cy - 1} textAnchor="middle" fill="var(--text-primary)"
                  fontSize={zone === 'Control-Room' ? '2.5' : '3'} fontWeight="700"
                  fontFamily="var(--font-sans)">
                  {lbl1}
                </text>
                {lbl2 && (
                  <text x={cx} y={cy + 3} textAnchor="middle" fill="var(--text-secondary)"
                    fontSize="2" fontWeight="500" fontFamily="var(--font-sans)">
                    {lbl2}
                  </text>
                )}
                
                {/* Score pill */}
                {zone !== 'Control-Room' && (
                  <g transform={`translate(${cx - 5}, ${pos.y + pos.h - 7})`}>
                    <rect width="10" height="4.5" rx="2" fill="var(--bg-surface)" stroke={color} strokeWidth="0.3" opacity="0.9" />
                    <text x="5" y="3.2" textAnchor="middle"
                      fill={color} fontSize="2.5" fontWeight="700" fontFamily="var(--font-mono)">
                      {score}
                    </text>
                  </g>
                )}
              </g>
            )
          })}

          {/* Legend */}
          <g transform="translate(10, 94)">
            <rect x="-2" y="-2" width="84" height="6" fill="var(--bg-surface)" rx="1" stroke="var(--border)" strokeWidth="0.3" opacity="0.9" />
            {[
              { c: '#22c55e', l: 'Safe (0-20)' },
              { c: '#f59e0b', l: 'Warning (21-60)' },
              { c: '#ea580c', l: 'High (61-80)' },
              { c: '#ef4444', l: 'Critical (81+)' },
            ].map(({ c, l }, i) => (
              <g key={l} transform={`translate(${i * 21}, 1)`}>
                <circle cx="2" cy="0" r="1.5" fill={c} />
                <text x="5" y="0.8" fill="var(--text-secondary)" fontSize="2.2" fontWeight="500" fontFamily="var(--font-sans)">
                  {l}
                </text>
              </g>
            ))}
          </g>
        </svg>
      </div>
    </div>
  )
}
