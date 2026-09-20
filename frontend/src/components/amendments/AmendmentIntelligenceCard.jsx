import React from 'react';
import { ArrowRight, CheckCircle2, GitCommit } from 'lucide-react';

/**
 * AmendmentIntelligenceCard: Claude-inspired structured comparison card
 * Materializes inside the conversation when user asks about amendments.
 */
export default function AmendmentIntelligenceCard({ diffData }) {
  if (!diffData) return null;

  const changes = diffData.changes || [];
  const parentFile = diffData.parent_filename || 'Preceding Master Services Agreement';
  const amendFile = diffData.amendment_filename || 'Amendment Document';
  const impacts = diffData.business_impact_items || [];

  return (
    <div style={{
      marginTop: '18px',
      marginBottom: '18px',
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-medium)',
      borderRadius: '12px',
      overflow: 'hidden',
      boxShadow: 'var(--shadow-panel)'
    }}>
      {/* Header with Full Force & Effect Confirmation */}
      <div style={{
        padding: '16px 20px',
        background: 'var(--bg-surface-elevated)',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '10px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '6px',
            background: 'var(--accent-terracotta-dim)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <GitCommit size={15} color="var(--accent-terracotta)" />
          </div>
          <div>
            <div style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-terracotta)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Amendment Version Alignment
            </div>
            <div style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {amendFile} <span style={{ color: 'var(--text-muted)', margin: '0 4px' }}>➔</span> {parentFile}
            </div>
          </div>
        </div>

        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '4px 12px',
          background: 'var(--signal-success-dim)',
          border: '1px solid rgba(72, 187, 120, 0.3)',
          borderRadius: '9999px',
          fontSize: '0.74rem',
          fontWeight: 500,
          color: 'var(--signal-success)'
        }}>
          <CheckCircle2 size={13} />
          <span>Full Force & Effect Confirmed</span>
        </div>
      </div>

      {/* Business Impact Bullet Points */}
      {impacts.length > 0 && (
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-surface)' }}>
          <div style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
            Audited Commercial Modifications
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {impacts.map((item, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '0.86rem', color: 'var(--text-secondary)' }}>
                <ArrowRight size={14} color="var(--accent-terracotta)" style={{ flexShrink: 0, marginTop: '3px' }} />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Clause-by-Clause Before & After Diff Grid */}
      <div style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Clause Alignment ({changes.length} Modified Provisions)
        </div>

        {changes.map((ch, idx) => (
          <div key={idx} style={{
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            padding: '16px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                §{ch.section_number} {ch.section_title}
              </span>
              <span style={{
                fontSize: '0.68rem',
                fontFamily: 'var(--font-mono)',
                padding: '2px 8px',
                borderRadius: '4px',
                background: ch.change_type === 'ADDED' ? 'var(--signal-success-dim)' : 'var(--accent-terracotta-dim)',
                color: ch.change_type === 'ADDED' ? 'var(--signal-success)' : 'var(--accent-terracotta)',
                border: '1px solid currentColor'
              }}>
                {ch.change_type}
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              {/* Prior Term */}
              <div style={{
                background: 'rgba(229, 62, 62, 0.05)',
                border: '1px solid rgba(229, 62, 62, 0.2)',
                borderRadius: '8px',
                padding: '12px 14px'
              }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--signal-danger)', marginBottom: '4px', textTransform: 'uppercase' }}>
                  Prior Agreement Term
                </div>
                <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: '1.65', fontFamily: 'var(--font-sans)' }}>
                  {ch.before_text || 'No preceding clause text recorded.'}
                </div>
              </div>

              {/* Amended Term */}
              <div style={{
                background: 'rgba(72, 187, 120, 0.05)',
                border: '1px solid rgba(72, 187, 120, 0.2)',
                borderRadius: '8px',
                padding: '12px 14px'
              }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--signal-success)', marginBottom: '4px', textTransform: 'uppercase' }}>
                  Amended Term
                </div>
                <div style={{ fontSize: '0.84rem', color: 'var(--text-primary)', lineHeight: '1.65', fontFamily: 'var(--font-sans)' }}>
                  {ch.after_text}
                </div>
              </div>
            </div>

            {ch.impact_summary && (
              <div style={{ marginTop: '10px', fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                <strong style={{ color: 'var(--text-secondary)' }}>Impact:</strong> {ch.impact_summary}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
