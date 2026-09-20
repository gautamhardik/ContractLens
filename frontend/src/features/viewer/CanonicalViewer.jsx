import React, { useState } from 'react';
import { GitCommit, FileText as FileTextIcon } from 'lucide-react';
import AmendmentsView from '../amendments/AmendmentsView';

export default function CanonicalViewer({
  contractDetail,
  highlightedBlockId,
  amendmentData,
  onCompareAmendment
}) {
  const [showAmendmentDiff, setShowAmendmentDiff] = useState(false);

  if (!contractDetail) {
    return (
      <div className="glass-panel" style={{ padding: '36px', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-secondary)' }}>Select a contract to view canonical pages and bounding box provenance.</p>
      </div>
    );
  }

  const { document: doc, intelligence: intel } = contractDetail;
  const isAmendment = doc.filename.toLowerCase().includes('access'); // using same naive check as before, ideally use contract_type

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Contract Header Card */}
      <div style={{
        maxWidth: '860px',
        margin: '0 auto',
        width: '100%',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-medium)',
        borderRadius: '12px',
        padding: '20px 24px',
        boxShadow: 'var(--shadow-ambient)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', letterSpacing: '-0.015em' }}>
              {doc.filename}
            </h2>
            <span style={{
              fontSize: '0.68rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--accent-terracotta)',
              background: 'var(--accent-terracotta-dim)',
              border: '1px solid var(--accent-terracotta-border)',
              padding: '2px 8px',
              borderRadius: '4px',
              textTransform: 'uppercase'
            }}>
              {intel?.contract_type?.raw_value || 'Agreement'}
            </span>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '5px', display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span>Doc ID: <strong style={{ color: 'var(--text-primary)' }}>{doc.document_id}</strong></span>
            <span>•</span>
            <span>{doc.page_count} Pages</span>
            <span>•</span>
            <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
          </div>
        </div>

        {/* Quick Page Jump Controls */}
        <div style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingTop: '12px',
          borderTop: '1px solid var(--border-subtle)',
          marginTop: '4px'
        }}>
          {!showAmendmentDiff && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginRight: '4px' }}>
                Jump to Page:
              </span>
              {doc.pages.map(p => (
                <button
                  key={p.page_number}
                  onClick={() => {
                    const el = document.getElementById(`page-${p.page_number}`);
                    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  }}
                  style={{
                    padding: '2px 8px',
                    borderRadius: '4px',
                    border: '1px solid var(--border-subtle)',
                    background: 'var(--bg-surface)',
                    color: 'var(--text-primary)',
                    fontSize: '0.72rem',
                    fontWeight: 500,
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)'
                  }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--accent-terracotta)'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-subtle)'}
                >
                  {p.page_number}
                </button>
              ))}
            </div>
          )}
          {showAmendmentDiff && <div />}

          {isAmendment && (
            <button
              onClick={() => {
                if (!showAmendmentDiff) {
                  onCompareAmendment(doc.document_id);
                }
                setShowAmendmentDiff(!showAmendmentDiff);
              }}
              className={showAmendmentDiff ? "btn-secondary" : "btn-primary"}
              style={{ fontSize: '0.8rem', padding: '6px 12px', marginLeft: 'auto' }}
            >
              {showAmendmentDiff ? <><FileTextIcon size={13} /> View Canonical Pages</> : <><GitCommit size={13} /> Compare Amendment Diffs</>}
            </button>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '860px', margin: '0 auto', width: '100%' }}>
        {showAmendmentDiff ? (
          <div style={{ padding: '20px 0' }}>
            <AmendmentsView amendmentData={amendmentData} onLoadDefaultComparison={() => onCompareAmendment(doc.document_id)} />
          </div>
        ) : (
          doc.pages.map(page => (
            <div
              key={page.page_number}
              id={`page-${page.page_number}`}
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-medium)',
                borderRadius: '12px',
                boxShadow: 'var(--shadow-panel)',
                padding: '36px 44px'
              }}
            >
              {/* Page Header Rule */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderBottom: '1px solid var(--border-subtle)',
                paddingBottom: '12px',
                marginBottom: '24px'
              }}>
                <span style={{ fontSize: '0.74rem', fontWeight: 600, letterSpacing: '0.06em', color: 'var(--text-secondary)' }}>
                  PAGE {page.page_number} OF {doc.page_count}
                </span>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                  {page.width} × {page.height} pt
                </span>
              </div>

              {/* Page Text Stream */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {page.blocks.map(b => {
                  const isHighlighted = highlightedBlockId === b.block_id;
                  const isHeader = b.block_type === 'header' || b.block_type === 'sec_noise' || (b.raw_text && b.raw_text.length < 80 && b.raw_text === b.raw_text.toUpperCase());
                  return (
                    <div
                      key={b.block_id}
                      id={`block-${b.block_id}`}
                      data-highlighted={isHighlighted ? "true" : undefined}
                      style={{
                        padding: isHighlighted ? '12px 16px' : '6px 8px',
                        borderRadius: '8px',
                        background: isHighlighted ? 'rgba(204, 120, 92, 0.08)' : 'transparent',
                        borderLeft: isHighlighted ? '3px solid var(--accent-terracotta)' : '3px solid transparent',
                        transition: 'all 0.2s ease',
                        position: 'relative'
                      }}
                    >
                      {/* Discrete Block Metadata Tag */}
                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '4px'
                      }}>
                        <span style={{
                          fontSize: '0.7rem',
                          fontFamily: 'var(--font-mono)',
                          fontWeight: 500,
                          color: isHighlighted ? 'var(--accent-terracotta)' : 'var(--text-muted)'
                        }}>
                          § {b.block_id}
                          {b.bbox && ` • [${b.bbox.x0.toFixed(0)}, ${b.bbox.y0.toFixed(0)}, ${b.bbox.x1.toFixed(0)}, ${b.bbox.y1.toFixed(0)}]`}
                        </span>
                        {b.section_number && (
                          <span style={{
                            fontSize: '0.68rem',
                            fontFamily: 'var(--font-mono)',
                            color: 'var(--accent-terracotta)',
                            background: 'var(--accent-terracotta-dim)',
                            padding: '1px 6px',
                            borderRadius: '4px'
                          }}>
                            §{b.section_number} {b.section_title}
                          </span>
                        )}
                      </div>

                      {/* Clean High-Legibility Body Text */}
                      <div style={{
                        fontSize: isHeader ? '0.94rem' : '0.95rem',
                        lineHeight: '1.7',
                        color: 'var(--text-primary)',
                        fontWeight: isHeader ? 600 : 400,
                        fontFamily: 'var(--font-sans)',
                        letterSpacing: '-0.005em'
                      }}>
                        {b.raw_text}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
