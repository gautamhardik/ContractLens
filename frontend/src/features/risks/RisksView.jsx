import React from 'react';
import { CheckCircle2 } from 'lucide-react';

export default function RisksView({ riskData, onInspectContract }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h1 className="editorial-title" style={{ fontSize: '1.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px', letterSpacing: '-0.025em', fontFamily: 'var(--font-sans)' }}>
          Operational Risk & Review Signals
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.94rem', lineHeight: '1.6' }}>
          Deterministic audit flags answering: <i>"What should I worry about across these contracts?"</i>
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {riskData?.contract_reports && riskData.contract_reports.length > 0 ? (
          riskData.contract_reports.map(rep => (
            <div key={rep.document_id} className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <h3 style={{ fontSize: '1.05rem', fontWeight: 600, fontFamily: 'var(--font-sans)', color: 'var(--text-primary)' }}>{rep.filename}</h3>
                    <span className={`badge ${rep.risk_score >= 40 ? 'badge-rose' : 'badge-emerald'}`}>
                      Risk Score: {rep.risk_score} / 100
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {rep.total_signals} Risk Signals Identified
                  </div>
                </div>
                <button
                  onClick={() => onInspectContract(rep.document_id)}
                  className="btn-secondary"
                >
                  Inspect Evidence
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {rep.signals.map((sig, sIdx) => (
                  <div key={sIdx} style={{ background: 'var(--bg-canvas)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '14px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--text-primary)' }}>{sig.title}</span>
                      <span className={`badge ${sig.severity === 'HIGH' ? 'badge-rose' : 'badge-amber'}`} style={{ fontSize: '0.65rem' }}>
                        {sig.severity}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginBottom: '8px', lineHeight: '1.65' }}>
                      {sig.description}
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--accent-terracotta)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CheckCircle2 size={13} /> <strong>Recommendation:</strong> {sig.recommendation}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))
        ) : (
          <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
              No operational risk signals or high-impact traps detected across the active contract corpus.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
