import React, { useState } from 'react';
import { 
  GitCommit, FileText as FileTextIcon, ZoomIn, ZoomOut, 
  Search, Bookmark, ShieldCheck, Scale, Calendar, DollarSign,
  Eye, Trash2
} from 'lucide-react';
import AmendmentsView from '../amendments/AmendmentsView';

export default function CanonicalViewer({
  contractDetail,
  highlightedBlockId,
  amendmentData,
  onCompareAmendment,
  onDeleteContract
}) {
  const [showAmendmentDiff, setShowAmendmentDiff] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [searchQuery, setSearchQuery] = useState('');
  const [showMetaDrawer, setShowMetaDrawer] = useState(true);

  if (!contractDetail) {
    return (
      <div style={{
        maxWidth: '800px',
        margin: '60px auto',
        padding: '48px 32px',
        textAlign: 'center',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-medium)',
        borderRadius: '16px',
        boxShadow: 'var(--shadow-elevated)'
      }}>
        <div style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          background: 'var(--accent-terracotta-dim)',
          color: 'var(--accent-terracotta)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 16px'
        }}>
          <FileTextIcon size={26} />
        </div>
        <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
          No Document Selected
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', maxWidth: '420px', margin: '0 auto' }}>
          Select a contract from the sidebar or upload a new PDF to inspect spatial coordinates, typography, and verified clause bounding boxes.
        </p>
      </div>
    );
  }

  const { document: doc, intelligence: intel } = contractDetail;
  const isAmendment = (doc.filename.toLowerCase().includes('amend') || doc.filename.toLowerCase().includes('access')) && !!intel?.amendment_facts;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '1100px', margin: '0 auto', width: '100%' }}>
      {/* ── Top Floating Glass Toolbar & Document Identity Bar ─────────────────── */}
      <div style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-medium)',
        borderRadius: '14px',
        padding: '16px 22px',
        boxShadow: 'var(--shadow-elevated)',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        backdropFilter: 'blur(16px)'
      }}>
        {/* Row 1: Document Identity & Main Actions */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, rgba(204, 120, 92, 0.18) 0%, rgba(204, 120, 92, 0.04) 100%)',
              border: '1px solid var(--accent-terracotta-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-terracotta)',
              flexShrink: 0
            }}>
              <FileTextIcon size={20} />
            </div>

            <div style={{ minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <h2 style={{
                  fontSize: '1.18rem',
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                  letterSpacing: '-0.015em',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}>
                  {doc.filename}
                </h2>

                <span style={{
                  fontSize: '0.68rem',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 600,
                  color: 'var(--accent-terracotta)',
                  background: 'var(--accent-terracotta-dim)',
                  border: '1px solid var(--accent-terracotta-border)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  textTransform: 'uppercase'
                }}>
                  {intel?.contract_type?.raw_value || 'Agreement'}
                </span>

                <span style={{
                  fontSize: '0.68rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-muted)',
                  background: 'var(--bg-canvas)',
                  border: '1px solid var(--border-subtle)',
                  padding: '2px 8px',
                  borderRadius: '4px'
                }}>
                  {doc.document_id}
                </span>
              </div>

              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '3px', display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                <span><strong>{doc.page_count}</strong> {doc.page_count === 1 ? 'Page' : 'Pages'}</span>
                <span>•</span>
                <span>{((doc.file_size || 0) / 1024).toFixed(1)} KB</span>
                <span>•</span>
                <span style={{ color: 'var(--accent-green, #10b981)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                  <ShieldCheck size={13} /> MuPDF Spatial Verified
                </span>
              </div>
            </div>
          </div>

          {/* Right Action Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            {isAmendment && (
              <button
                onClick={() => {
                  if (!showAmendmentDiff) {
                    onCompareAmendment(doc.document_id);
                  }
                  setShowAmendmentDiff(!showAmendmentDiff);
                }}
                className={showAmendmentDiff ? "btn-secondary" : "btn-primary"}
                style={{ fontSize: '0.78rem', padding: '6px 14px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
              >
                {showAmendmentDiff ? <><FileTextIcon size={13} /> View Pages</> : <><GitCommit size={13} /> Amendment Diffs</>}
              </button>
            )}

            <button
              onClick={() => setShowMetaDrawer(!showMetaDrawer)}
              style={{
                fontSize: '0.76rem',
                padding: '6px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border-medium)',
                background: showMetaDrawer ? 'var(--accent-terracotta-dim)' : 'transparent',
                color: showMetaDrawer ? 'var(--accent-terracotta)' : 'var(--text-secondary)',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                transition: 'all var(--transition-fast)'
              }}
            >
              <Eye size={13} /> Metadata Strip
            </button>

            {onDeleteContract && (
              <button
                onClick={() => onDeleteContract(doc.document_id)}
                title="Remove this contract from workspace"
                style={{
                  fontSize: '0.76rem',
                  padding: '6px 12px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-subtle)',
                  background: 'transparent',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px',
                  transition: 'all var(--transition-fast)'
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.color = 'var(--accent-ruby, #ef4444)';
                  e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.4)';
                  e.currentTarget.style.background = 'rgba(239, 68, 68, 0.08)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.color = 'var(--text-muted)';
                  e.currentTarget.style.borderColor = 'var(--border-subtle)';
                  e.currentTarget.style.background = 'transparent';
                }}
              >
                <Trash2 size={13} /> Remove
              </button>
            )}
          </div>
        </div>

        {/* Row 2: Metadata Strip (Governing Law, Payment, Expiration) */}
        {showMetaDrawer && intel && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '10px',
            padding: '12px 14px',
            background: 'var(--bg-canvas)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            fontSize: '0.75rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Scale size={14} color="var(--accent-terracotta)" />
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>Governing Law</div>
                <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{intel.governing_law?.normalized_value || 'Not specified'}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <DollarSign size={14} color="var(--accent-terracotta)" />
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>Payment Terms</div>
                <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{intel.payment_terms?.raw_value || 'Not specified'}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Calendar size={14} color="var(--accent-terracotta)" />
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>Effective Date</div>
                <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{intel.effective_date?.normalized_value || 'Not specified'}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Bookmark size={14} color="var(--accent-terracotta)" />
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>Parties</div>
                <div style={{ fontWeight: 500, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {intel.parties?.map(p => p.name).join(', ') || 'Unresolved'}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Row 3: Viewer Controls (Zoom, Jump to Page, In-Page Text Filter) */}
        {!showAmendmentDiff && (
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingTop: '10px',
            borderTop: '1px solid var(--border-subtle)',
            flexWrap: 'wrap',
            gap: '10px'
          }}>
            {/* Quick Page Jump Chips */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginRight: '4px' }}>
                Page Jump:
              </span>
              {doc.pages.map(p => (
                <button
                  key={p.page_number}
                  onClick={() => {
                    const el = document.getElementById(`page-${p.page_number}`);
                    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  }}
                  style={{
                    padding: '3px 9px',
                    borderRadius: '5px',
                    border: '1px solid var(--border-subtle)',
                    background: 'var(--bg-canvas)',
                    color: 'var(--text-primary)',
                    fontSize: '0.72rem',
                    fontWeight: 500,
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)'
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.borderColor = 'var(--accent-terracotta)';
                    e.currentTarget.style.color = 'var(--accent-terracotta)';
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.borderColor = 'var(--border-subtle)';
                    e.currentTarget.style.color = 'var(--text-primary)';
                  }}
                >
                  P.{p.page_number}
                </button>
              ))}
            </div>

            {/* Filter & Zoom Controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {/* Search text input */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '3px 8px',
                borderRadius: '6px',
                border: '1px solid var(--border-medium)',
                background: 'var(--bg-canvas)'
              }}>
                <Search size={12} color="var(--text-muted)" />
                <input
                  type="text"
                  placeholder="Filter clauses..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    fontSize: '0.72rem',
                    color: 'var(--text-primary)',
                    outline: 'none',
                    width: '110px'
                  }}
                />
              </div>

              {/* Zoom Buttons */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '2px',
                padding: '2px 4px',
                borderRadius: '6px',
                border: '1px solid var(--border-medium)',
                background: 'var(--bg-canvas)'
              }}>
                <button
                  onClick={() => setZoomLevel(prev => Math.max(75, prev - 10))}
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '2px 4px' }}
                  title="Zoom Out"
                >
                  <ZoomOut size={13} />
                </button>
                <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', minWidth: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  {zoomLevel}%
                </span>
                <button
                  onClick={() => setZoomLevel(prev => Math.min(130, prev + 10))}
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '2px 4px' }}
                  title="Zoom In"
                >
                  <ZoomIn size={13} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Document Page Stream ────────────────────────────────────────────── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '28px', width: '100%' }}>
        {showAmendmentDiff ? (
          <div style={{ padding: '10px 0' }}>
            <AmendmentsView amendmentData={amendmentData} onLoadDefaultComparison={() => onCompareAmendment(doc.document_id)} />
          </div>
        ) : (
          doc.pages.map(page => {
            const filteredBlocks = page.blocks.filter(b => {
              if (!searchQuery) return true;
              return b.raw_text.toLowerCase().includes(searchQuery.toLowerCase()) || 
                     (b.section_title && b.section_title.toLowerCase().includes(searchQuery.toLowerCase()));
            });

            return (
              <div
                key={page.page_number}
                id={`page-${page.page_number}`}
                style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: '16px',
                  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.06), 0 1px 3px rgba(0, 0, 0, 0.04)',
                  padding: '40px 52px',
                  position: 'relative',
                  transform: `scale(${zoomLevel / 100})`,
                  transformOrigin: 'top center',
                  transition: 'transform 0.15s ease-out'
                }}
              >
                {/* Visual Sheet Edge Detail */}
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: '48px',
                  right: '48px',
                  height: '2px',
                  background: 'linear-gradient(90deg, transparent 0%, var(--accent-terracotta) 50%, transparent 100%)',
                  opacity: 0.35
                }} />

                {/* Page Header Rule */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderBottom: '1px solid var(--border-subtle)',
                  paddingBottom: '14px',
                  marginBottom: '28px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      fontSize: '0.74rem',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 700,
                      letterSpacing: '0.08em',
                      color: 'var(--text-primary)',
                      textTransform: 'uppercase'
                    }}>
                      Page {page.page_number}
                    </span>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.74rem' }}>of {doc.page_count}</span>
                  </div>

                  <span style={{
                    fontSize: '0.7rem',
                    color: 'var(--text-muted)',
                    fontFamily: 'var(--font-mono)',
                    background: 'var(--bg-canvas)',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    border: '1px solid var(--border-subtle)'
                  }}>
                    {page.width} × {page.height} pt
                  </span>
                </div>

                {/* Page Blocks Stream */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {filteredBlocks.length === 0 ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                      No clauses matching "{searchQuery}" on page {page.page_number}.
                    </div>
                  ) : (
                    filteredBlocks.map(b => {
                      const isHighlighted = highlightedBlockId === b.block_id;
                      const isHeader = b.block_type === 'header' || b.block_type === 'sec_noise' || 
                        (b.raw_text && b.raw_text.length < 90 && b.raw_text === b.raw_text.toUpperCase());

                      return (
                        <div
                          key={b.block_id}
                          id={`block-${b.block_id}`}
                          data-highlighted={isHighlighted ? "true" : undefined}
                          style={{
                            padding: isHighlighted ? '14px 18px' : '8px 12px',
                            borderRadius: '10px',
                            background: isHighlighted 
                              ? 'linear-gradient(135deg, rgba(204, 120, 92, 0.12) 0%, rgba(204, 120, 92, 0.04) 100%)' 
                              : 'transparent',
                            borderLeft: isHighlighted 
                              ? '4px solid var(--accent-terracotta)' 
                              : '4px solid transparent',
                            boxShadow: isHighlighted ? '0 0 0 1px rgba(204, 120, 92, 0.25), 0 4px 12px rgba(204, 120, 92, 0.08)' : 'none',
                            transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                            position: 'relative'
                          }}
                        >
                          {/* Block Provenance Tag */}
                          <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            marginBottom: '6px'
                          }}>
                            <span style={{
                              fontSize: '0.68rem',
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
                                fontWeight: 500,
                                color: 'var(--accent-terracotta)',
                                background: 'var(--accent-terracotta-dim)',
                                padding: '1px 7px',
                                borderRadius: '4px',
                                border: '1px solid var(--accent-terracotta-border)'
                              }}>
                                §{b.section_number} {b.section_title}
                              </span>
                            )}
                          </div>

                          {/* High-Legibility Typography */}
                          <div style={{
                            fontSize: isHeader ? '0.98rem' : '0.94rem',
                            lineHeight: '1.74',
                            color: 'var(--text-primary)',
                            fontWeight: isHeader ? 650 : 400,
                            fontFamily: isHeader ? 'var(--font-sans)' : 'var(--font-sans)',
                            letterSpacing: isHeader ? '-0.015em' : '-0.005em'
                          }}>
                            {b.raw_text}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>

                {/* Page Footer */}
                <div style={{
                  marginTop: '32px',
                  paddingTop: '12px',
                  borderTop: '1px dashed var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'center'
                }}>
                  <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                    — Page {page.page_number} End —
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
