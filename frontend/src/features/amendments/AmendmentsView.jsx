import React from 'react';
import { ArrowRight } from 'lucide-react';

export default function AmendmentsView({ amendmentData, onLoadDefaultComparison }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h1 className="editorial-title" style={{ fontSize: '1.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px', letterSpacing: '-0.025em', fontFamily: 'var(--font-sans)' }}>
          Structured Amendment & Version Intelligence
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.94rem', lineHeight: '1.6' }}>
          Clause-by-clause version alignment showing exact modifications and explicit full force confirmation.
        </p>
      </div>

      {amendmentData ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="glass-panel" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>VERSION RELATIONSHIP</div>
                <div style={{ fontSize: '1.05rem', fontWeight: 600, marginTop: '2px', fontFamily: 'var(--font-sans)' }}>
                  {amendmentData.amendment_filename} ➔ amends {amendmentData.parent_filename}
                </div>
              </div>
              <span className="badge badge-emerald">Full Force & Effect Confirmed</span>
            </div>

            <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Key Business Impacts</div>
              {amendmentData.business_impact_items?.map((item, idx) => (
                <div key={idx} style={{ fontSize: '0.86rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ArrowRight size={14} color="var(--accent-terracotta)" /> {item}
                </div>
              ))}
            </div>
          </div>

          {/* Section Changes Diff */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Modified Clauses ({amendmentData.changes?.length})</h3>
            {amendmentData.changes?.map((ch, idx) => (
              <div key={idx} className="glass-panel" style={{ padding: '18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.92rem' }}>
                    §{ch.section_number} {ch.section_title}
                  </div>
                  <span className="badge badge-amber">{ch.change_type}</span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div style={{ background: 'rgba(229, 62, 62, 0.05)', border: '1px solid rgba(229, 62, 62, 0.2)', padding: '12px 14px', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--signal-danger)', marginBottom: '4px' }}>PRIOR AGREEMENT TERM</div>
                    <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: '1.65', fontFamily: 'var(--font-sans)' }}>
                      {ch.before_text || 'No preceding clause text explicitly recorded.'}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(72, 187, 120, 0.05)', border: '1px solid rgba(72, 187, 120, 0.2)', padding: '12px 14px', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--signal-success)', marginBottom: '4px' }}>AMENDED TERM</div>
                    <div style={{ fontSize: '0.84rem', color: 'var(--text-primary)', lineHeight: '1.65', fontFamily: 'var(--font-sans)' }}>
                      {ch.after_text}
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '12px', fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                  <strong>Impact:</strong> {ch.impact_summary}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>
          <p style={{ color: 'var(--text-secondary)' }}>
            Select an amendment contract from the sidebar (e.g. <code>Access-E-TRADE Amendment</code>) to view structured version diffs.
          </p>
          <button
            onClick={onLoadDefaultComparison}
            className="btn-primary"
            style={{ marginTop: '16px' }}
          >
            Load Access-E*TRADE Amendment Diff
          </button>
        </div>
      )}
    </div>
  );
}
