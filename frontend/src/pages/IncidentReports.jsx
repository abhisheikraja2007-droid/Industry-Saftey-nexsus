import { useState } from 'react'
import { useSafety } from '../context/SafetyContext'
import { useApi } from '../hooks/useApi'
import { FileText, Cpu, AlertTriangle, PlayCircle } from 'lucide-react'

export default function IncidentReports() {
  const { state } = useSafety()
  const { generateReport } = useApi()
  const [selectedReport, setSelectedReport] = useState(null)

  const handleManualTrigger = () => {
    generateReport('Zone-D', 85)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-4)' }}>
      <div className="card-header" style={{ marginBottom: 0, padding: '0 var(--spacing-2)' }}>
        <span className="card-title" style={{ fontSize: '1.2rem' }}>
          <FileText color="var(--accent)" /> AI Incident Reports
        </span>
        <button className="btn btn-primary" onClick={handleManualTrigger}>
          <PlayCircle size={16} /> Force Root Cause Analysis
        </button>
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        {/* Report List */}
        <div className="card fade-in" style={{ padding: 'var(--spacing-3)' }}>
          <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            <AlertTriangle size={16} /> Incident Logs
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto', maxHeight: '550px', paddingRight: '0.5rem' }}>
            {state.reports.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center', padding: '3rem 1rem', background: 'var(--bg-base)', borderRadius: 'var(--radius-sm)' }}>
                No incident reports generated.<br/>Facility is operating safely.
              </div>
            ) : (
              state.reports.map(r => (
                <div
                  key={r.id}
                  onClick={() => setSelectedReport(r)}
                  style={{
                    padding: '1rem', border: `1px solid ${selectedReport?.id === r.id ? 'var(--accent)' : 'var(--border)'}`,
                    borderRadius: 'var(--radius-sm)', cursor: 'pointer', background: selectedReport?.id === r.id ? 'var(--accent-bg)' : 'var(--bg-surface)',
                    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                    boxShadow: selectedReport?.id === r.id ? '0 4px 15px rgba(124, 58, 237, 0.1)' : 'none'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.95rem', color: selectedReport?.id === r.id ? 'var(--accent-hover)' : 'var(--text-primary)' }}>
                      {r.title}
                    </span>
                    <span className="badge badge-critical" style={{ fontSize: '0.65rem' }}>Risk: {r.risk_score}</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span>Generated: {r.created_at ? new Date(r.created_at).toLocaleString() : 'Just now'}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Report Details */}
        <div className="card fade-in" style={{ padding: 'var(--spacing-4)', minHeight: '500px' }}>
          {selectedReport ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <h2 style={{ fontSize: '1.4rem', lineHeight: 1.3 }}>{selectedReport.title}</h2>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <span className="badge badge-critical">Critical Severity</span>
                  <span className="badge badge-info"><Cpu size={12} /> AI Analysis</span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>ID: {selectedReport.id.slice(0,8)}</span>
                </div>
              </div>

              <div>
                <h4 style={{ color: 'var(--accent)', marginBottom: '0.5rem', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Executive Summary</h4>
                <p style={{ fontSize: '0.95rem', color: 'var(--text-primary)', background: 'var(--bg-base)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', lineHeight: 1.6 }}>
                  {selectedReport.summary}
                </p>
              </div>

              {selectedReport.ai_explanation && (
                <div>
                  <h4 style={{ color: 'var(--accent)', marginBottom: '0.5rem', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>AI Root Cause Analysis</h4>
                  <pre style={{
                    fontSize: '0.85rem', color: 'var(--text-secondary)', background: 'var(--bg-base)',
                    padding: '1.25rem', borderRadius: 'var(--radius-sm)', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)',
                    border: '1px solid var(--border)', lineHeight: 1.5, overflowX: 'auto'
                  }}>
                    {selectedReport.ai_explanation}
                  </pre>
                </div>
              )}

              {selectedReport.recommended_actions && selectedReport.recommended_actions.length > 0 && (
                <div>
                  <h4 style={{ color: 'var(--accent)', marginBottom: '0.75rem', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Recommended Actions</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {selectedReport.recommended_actions.map((act, i) => (
                      <div key={i} style={{ 
                        fontSize: '0.9rem', display: 'flex', gap: '0.75rem', alignItems: 'flex-start', 
                        background: 'var(--bg-surface)', border: '1px solid var(--border)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)' 
                      }}>
                        <span style={{ 
                          background: 'var(--accent-bg)', color: 'var(--accent)', width: 24, height: 24, flexShrink: 0,
                          borderRadius: '50%', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700 
                        }}>
                          {i + 1}
                        </span>
                        <span style={{ paddingTop: '0.1rem', color: 'var(--text-primary)', lineHeight: 1.5 }}>{act}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: '400px', color: 'var(--text-muted)', gap: '1rem' }}>
              <FileText size={48} color="var(--border-2)" strokeWidth={1} />
              <span style={{ fontSize: '1rem', fontWeight: 500 }}>Select a report to view analysis</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
