import React from 'react';

export default function ContractsRegistryView({
  contracts,
  onSelectContract,
  onCompareAmendment
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h1 className="editorial-title" style={{ fontSize: '1.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px', letterSpacing: '-0.025em', fontFamily: 'var(--font-sans)' }}>
          All Indexed Contract Agreements
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.94rem', lineHeight: '1.6' }}>
          Complete registry of {contracts?.length || 0} indexed contract agreement{contracts?.length === 1 ? '' : 's'} with verified metadata and canonical provenance.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
        {contracts.map(c => (
          <div key={c.document_id} className="glass-panel-interactive" style={{ padding: '18px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
              <div>
                <h4 style={{ fontSize: '0.98rem', fontWeight: 600, fontFamily: 'var(--font-sans)' }}>{c.filename}</h4>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  ID: <code style={{ color: 'var(--accent-terracotta)' }}>{c.document_id}</code> • {c.contract_type}
                </div>
              </div>
              <span className="badge badge-terracotta">{c.page_count} Pages</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', margin: '12px 0', fontSize: '0.82rem' }}>
              <div style={{ color: 'var(--text-secondary)' }}>
                <strong>Parties:</strong> {c.parties?.join(', ') || 'Not identified'}
              </div>
              <div style={{ color: 'var(--text-secondary)' }}>
                <strong>Governing Law:</strong> {c.governing_law || 'Not specified'}
              </div>
              <div style={{ color: 'var(--text-secondary)' }}>
                <strong>Payment Terms:</strong> {c.payment_terms || 'Not specified'}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              <button
                onClick={() => onSelectContract(c.document_id)}
                className="btn-secondary"
                style={{ flex: 1 }}
              >
                View Pages & Bounding Boxes
              </button>
              {c.filename.toLowerCase().includes('access') && (
                <button
                  onClick={() => onCompareAmendment(c.document_id)}
                  className="btn-primary"
                >
                  Diff
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
