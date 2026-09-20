import React from 'react';

/**
 * Citation: Claude-inspired literary citation pill
 * Displays clause section, semantic label, and exact physical PDF page number with warm terracotta accents.
 */
export default function Citation({ citation, onClick, isActive }) {
  if (!citation) return null;

  let rawSection = citation.section_heading || 'Clause';
  // Strip leading section symbol if already included in backend heading to prevent "§ §"
  const cleanSection = rawSection.replace(/^§+\s*/, '');
  const page = citation.page_number ? 'p.' + citation.page_number : '';
  const doc = citation.document_id || '';

  return (
    <button
      data-testid="citation-pill"
      className="citation-pill-btn"
      onClick={() => onClick && onClick(citation)}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '3px 10px',
        margin: '2px 4px',
        borderRadius: '6px',
        fontSize: '0.76rem',
        fontFamily: 'var(--font-mono)',
        background: isActive ? 'var(--accent-terracotta-dim)' : 'var(--bg-surface)',
        border: isActive ? '1px solid var(--accent-terracotta)' : '1px solid var(--border-medium)',
        color: isActive ? 'var(--accent-terracotta)' : 'var(--text-primary)',
        cursor: 'pointer',
        transition: 'all var(--transition-fast)',
        verticalAlign: 'middle',
        boxShadow: isActive ? 'var(--shadow-terracotta-glow)' : 'var(--shadow-ambient)'
      }}
      title={'Inspect source block ' + (citation.block_id || '') + ' on ' + page}
    >
      <span style={{ color: 'var(--accent-terracotta)', fontWeight: 700 }}>§</span>
      <span style={{ fontWeight: 600 }}>{cleanSection}</span>
      {page && <span style={{ color: isActive ? 'var(--accent-terracotta)' : 'var(--text-muted)', opacity: 0.9 }}>· {page}</span>}
      {doc && <span style={{ color: isActive ? 'var(--accent-terracotta)' : 'var(--text-faint)', fontSize: '0.7rem', opacity: 0.85 }}>[{doc}]</span>}
    </button>
  );
}
