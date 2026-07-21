import { useState } from 'react'
import { useSafety } from '../context/SafetyContext'
import { Camera, HardHat, AlertTriangle, ShieldCheck, Video, Settings2 } from 'lucide-react'

export default function PPEDetectionFeed() {
  const { state } = useSafety()
  const [camera, setCamera] = useState('CAM-Zone-D')

  // Find CCTV detections
  const hasViolation = state.triggeredRules.includes('PPE_ZONE')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-4)' }}>
      <div className="card-header" style={{ marginBottom: 0, padding: '0 var(--spacing-2)' }}>
        <span className="card-title" style={{ fontSize: '1.2rem' }}>
          <Camera color="var(--accent)" /> Computer Vision Feed
        </span>
        <span className="badge badge-info" style={{ background: 'var(--accent-bg)', color: 'var(--accent)' }}>
          <Video size={14} style={{ marginRight: '4px' }}/> LIVE
        </span>
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        {/* CCTV Feed Panel */}
        <div className="card fade-in" style={{ padding: 'var(--spacing-4)' }}>
          <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <span style={{ fontSize: '0.95rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Video size={18} color="var(--text-secondary)" /> {camera} Feed
            </span>
            <div style={{ position: 'relative' }}>
              <Settings2 size={16} color="var(--text-muted)" style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)' }} />
              <select
                value={camera}
                onChange={e => setCamera(e.target.value)}
                style={{ 
                  background: 'var(--bg-base)', color: 'var(--text-primary)', border: '1px solid var(--border)', 
                  padding: '0.5rem 1rem 0.5rem 2.2rem', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', outline: 'none'
                }}
              >
                <option value="CAM-Zone-D">Zone D (Hazardous)</option>
                <option value="CAM-Zone-A">Zone A (Processing)</option>
              </select>
            </div>
          </div>

          {/* Interactive CCTV canvas simulation */}
          <div style={{
            position: 'relative', width: '100%', aspectRatio: '16/9',
            background: '#0F172A', borderRadius: 'var(--radius-sm)', overflow: 'hidden',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            border: hasViolation ? '3px solid var(--crit)' : '1px solid var(--border)',
            boxShadow: hasViolation ? '0 0 20px rgba(239, 68, 68, 0.2)' : 'var(--shadow-sm)',
            transition: 'all 0.3s'
          }}>
            {/* Simulated Frame */}
            <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: '1rem', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
              <Camera size={48} strokeWidth={1} />
              AI Object Detection Stream
            </div>

            {/* Bounding box simulation for demo */}
            {hasViolation && camera === 'CAM-Zone-D' && (
              <div className="fade-in" style={{
                position: 'absolute', top: '25%', left: '35%', width: '30%', height: '55%',
                border: '2px solid var(--crit)', borderRadius: 4, pointerEvents: 'none',
                boxShadow: 'inset 0 0 10px rgba(239, 68, 68, 0.4), 0 0 10px rgba(239, 68, 68, 0.4)'
              }}>
                <span style={{
                  position: 'absolute', top: -24, left: -2, background: 'var(--crit)',
                  color: '#fff', fontSize: '0.75rem', padding: '0.1rem 0.5rem', borderRadius: '4px 4px 0 0',
                  fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.3rem'
                }}>
                  <AlertTriangle size={12} /> NO_HARDHAT [94%]
                </span>
              </div>
            )}

            <div style={{ 
              position: 'absolute', top: 12, left: 12, fontSize: '0.7rem', color: '#fff', 
              background: 'rgba(0,0,0,0.6)', padding: '0.3rem 0.6rem', borderRadius: 4, 
              fontFamily: 'var(--font-mono)', display: 'flex', alignItems: 'center', gap: '0.4rem', backdropFilter: 'blur(4px)'
            }}>
              <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--crit)', animation: 'pulse 2s infinite' }} />
              REC
            </div>
          </div>
        </div>

        {/* Analytics Panel */}
        <div className="card fade-in" style={{ padding: 'var(--spacing-4)' }}>
          <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)' }}>
            <HardHat size={18} color="var(--accent)" /> Compliance Analytics
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{ 
              background: hasViolation ? 'var(--crit-bg)' : 'var(--safe-bg)', 
              border: `1px solid ${hasViolation ? 'var(--crit)' : 'var(--safe)'}40`,
              padding: '1.25rem', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              transition: 'all 0.3s'
            }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.2rem' }}>Current Status</div>
                <div style={{ fontWeight: 800, fontSize: '1.1rem', color: hasViolation ? 'var(--crit)' : 'var(--safe)' }}>
                  {hasViolation ? 'VIOLATION DETECTED' : 'FULLY COMPLIANT'}
                </div>
              </div>
              {hasViolation ? (
                <AlertTriangle size={32} color="var(--crit)" style={{ opacity: 0.8 }} />
              ) : (
                <ShieldCheck size={32} color="var(--safe)" style={{ opacity: 0.8 }} />
              )}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Target Detection Class</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.9rem' }}>Hardhat, Vest, Gloves</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Required Zone PPE</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.9rem' }}>Full Gear (Class-3)</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Last Violation Logged</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.9rem' }}>{hasViolation ? 'Just now' : 'None in current shift'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
