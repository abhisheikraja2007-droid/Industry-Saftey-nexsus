import { useRef } from 'react'
import { useSafety } from '../context/SafetyContext'
import { Activity, ShieldCheck, AlertTriangle } from 'lucide-react'

const SIZE  = 220
const SW    = 18    // stroke width
const R     = 85    // clean radius to fit nicely inside 220px SVG
const CX    = SIZE / 2
const CY    = 100   // center shifted up to allow space below for badge inside the viewbox
const START = 220   // degrees: start of arc
const SWEEP = 280   // total sweep degrees

function polarToCart(cx, cy, r, angleDeg) {
  const rad = ((angleDeg - 90) * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

function describeArc(cx, cy, r, startAngle, endAngle) {
  const s = polarToCart(cx, cy, r, startAngle)
  const e = polarToCart(cx, cy, r, endAngle)
  const lg = endAngle - startAngle > 180 ? 1 : 0
  return `M ${s.x} ${s.y} A ${r} ${r} 0 ${lg} 1 ${e.x} ${e.y}`
}

export default function RiskGauge() {
  const { state } = useSafety()
  const { riskScore, riskLevel, riskColor } = state
  const arcRef    = useRef(null)

  // Arc calculation
  const startAngle = START - SWEEP / 2
  const endAngle   = startAngle + SWEEP
  const angle      = startAngle + (riskScore / 100) * SWEEP

  // Track arc
  const trackPath = describeArc(CX, CY, R, startAngle, endAngle)
  const fillPath  = riskScore > 0 ? describeArc(CX, CY, R, startAngle, angle) : ''

  const isSafe = riskLevel === 'SAFE'
  const Icon = isSafe ? ShieldCheck : AlertTriangle

  return (
    <div className={`card card-${riskLevel.toLowerCase()}`}
      style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: 'var(--spacing-4)', position: 'relative', overflow: 'hidden' }}>
      
      {/* Decorative background blob */}
      <div style={{ position: 'absolute', top: '-20%', left: '-20%', width: '140%', height: '140%', background: `radial-gradient(circle, ${riskColor}10 0%, transparent 60%)`, zIndex: 0, pointerEvents: 'none' }} />

      <div className="card-title" style={{ alignSelf: 'flex-start', marginBottom: '1rem', zIndex: 1, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Activity size={18} color="var(--accent)" />
        Facility Risk Score
      </div>

      <div style={{ position: 'relative', width: SIZE, height: 180, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1 }}>
        <svg width={SIZE} height={180} viewBox={`0 0 ${SIZE} 180`} style={{ overflow: 'visible' }}>
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={riskColor} stopOpacity="0.8" />
              <stop offset="100%" stopColor={riskColor} stopOpacity="1" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          
          {/* Track */}
          <path d={trackPath} fill="none" stroke="var(--border)" strokeWidth={SW} strokeLinecap="round" opacity="0.4" />
          
          {/* Fill arc */}
          {fillPath && (
            <path ref={arcRef} d={fillPath} fill="none" stroke="url(#gaugeGradient)"
              strokeWidth={SW} strokeLinecap="round" filter="url(#glow)"
              style={{ transition: 'd 1s cubic-bezier(0.4, 0, 0.2, 1)' }}
            />
          )}
          
          {/* Score text */}
          <text x={CX} y={CY + 12} textAnchor="middle" fill="var(--text-primary)"
            fontSize="48" fontWeight="800" fontFamily="var(--font-sans)">
            {riskScore}
          </text>
          <text x={CX} y={CY + 35} textAnchor="middle" fill="var(--text-muted)" fontSize="12" fontWeight="600" letterSpacing="0.05em">
            / 100
          </text>
        </svg>
      </div>

      <div style={{ zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', width: '100%', marginTop: '0.5rem' }}>
        <div style={{ 
          display: 'flex', alignItems: 'center', gap: '0.5rem', 
          background: `var(--${riskLevel.toLowerCase()}-bg)`, 
          color: riskColor, 
          padding: '0.5rem 1.5rem', 
          borderRadius: 'var(--radius-full)', 
          fontWeight: 700, 
          fontSize: '1rem',
          letterSpacing: '0.05em',
          border: `1px solid ${riskColor}30`,
          boxShadow: `0 4px 15px ${riskColor}20`
        }}>
          <Icon size={18} strokeWidth={2.5} />
          {riskLevel}
        </div>

        {/* Triggered rules */}
        <div style={{ width: '100%', minHeight: '50px', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '0.4rem' }}>
          {state.triggeredRules.length > 0 ? (
            state.triggeredRules.slice(0, 2).map(rule => (
              <div key={rule} style={{
                fontSize: '0.75rem', color: 'var(--crit)',
                background: 'var(--crit-bg)', padding: '0.4rem 0.8rem',
                borderRadius: 'var(--radius-sm)', textAlign: 'center',
                fontFamily: 'var(--font-mono)', border: '1px solid rgba(239,68,68,0.2)'
              }}>
                ⚡ {rule}
              </div>
            ))
          ) : (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center', background: 'var(--bg-base)', padding: '0.4rem', borderRadius: 'var(--radius-sm)' }}>
              All safety metrics optimal
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
