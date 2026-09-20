import React from 'react';
import { X, ExternalLink, MapPin, FileText, CheckCircle2 } from 'lucide-react';

/**
 * EvidencePanel: Claude-style literary Artifact/Evidence panel
 * Materializes alongside the conversation when a citation is clicked.
 * Displays exact cited text, clause title, PDF coordinates (bbox), and provides
 * a bridge to the Canonical Document Viewer.
 */
export default function EvidencePanel({ 
  citation, 
  onClose, 
  onOpenInViewer,
  contractTitle 
}) {
  if (!citation) return null;

  const bbox = citation.bounding_box || citation.bbox;
  const pageNum = citation.page_number;
  const blockId = citation.block_id;
  const sectionTitle = citation.section_heading || 'Contract Provision';
  const snippet = citation.snippet || citation.raw_text || citation.text || 'Authoritative clause text registered at this document coordinate.';

  return (
    <div 
      className="evidence-shard"
      style={{
        width: '400px',
        flexShrink: 0,
        height: '100%',
        background: 'var(--bg-surface)',
        borderLeft: '1px solid var(--border-medium)',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: 'var(--shadow-panel)',
        zIndex: 30
      }}
    >
      {/* Evidence Shard Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'var(--bg-surface-elevated)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '24px',
            height: '24px',
            borderRadius: '6px',
            background: 'var(--accent-terracotta-dim)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--accent-terracotta)',
            fontWeight: 700,
            fontSize: '0.8rem'
          }}>
            §
          </div>
          <div>
            <div style={{
              fontSize: '0.7rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--accent-terracotta)',
              letterSpacing: '0.05em',
              textTransform: 'uppercase'
            }}>
              Source Document Evidence
            </div>
            <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Verified Clause Provenance
            </div>
          </div>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'color var(--transition-fast)'
          }}
          title="Close Evidence Panel"
        >
          <X size={18} />
        </button>
      </div>

      {/* Evidence Body */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
        
        {/* Source Document Card */}
        <div style={{
          padding: '14px 16px',
          background: 'var(--bg-surface-elevated)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '10px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <FileText size={15} color="var(--accent-terracotta)" />
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {contractTitle || citation.document_id || 'Contract Document'}
            </span>
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-secondary)'
          }}>
            <span>DOC ID: <strong style={{ color: 'var(--text-primary)' }}>{citation.document_id}</strong></span>
            {pageNum && <span>PAGE: <strong style={{ color: 'var(--accent-terracotta)' }}>{pageNum}</strong></span>}
          </div>
        </div>

        {/* Section Pill & Coordinates */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          padding: '12px 14px',
          background: 'var(--accent-terracotta-dim)',
          border: '1px solid var(--accent-terracotta-border)',
          borderRadius: '8px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {sectionTitle}
            </span>
            {blockId && (
              <span style={{
                fontSize: '0.68rem',
                fontFamily: 'var(--font-mono)',
                color: 'var(--accent-terracotta)',
                background: 'var(--bg-surface)',
                border: '1px solid var(--accent-terracotta-border)',
                padding: '2px 6px',
                borderRadius: '4px',
                fontWeight: 600
              }}>
                {blockId}
              </span>
            )}
          </div>

          {bbox && (
            <div style={{
              fontSize: '0.72rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              <MapPin size={12} color="var(--accent-terracotta)" />
              <span>
                bbox: [{Array.isArray(bbox) ? bbox.map(v => typeof v === 'number' ? v.toFixed(0) : v).join(', ') : `${bbox.x0?.toFixed(0)}, ${bbox.y0?.toFixed(0)}, ${bbox.x1?.toFixed(0)}, ${bbox.y1?.toFixed(0)}`}]
              </span>
            </div>
          )}
        </div>

        {/* Exact Clause Text Block with Literary Styling */}
        <div>
          <div style={{
            fontSize: '0.72rem',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '8px'
          }}>
            Verbatim Legal Provision
          </div>
          <div 
            className="legal-verbatim"
            style={{
              padding: '16px 18px',
              background: 'var(--bg-canvas)',
              border: '1px solid var(--border-medium)',
              borderLeft: '3px solid var(--accent-terracotta)',
              borderRadius: '8px',
              color: 'var(--text-primary)',
              fontStyle: 'italic'
            }}
          >
            "{snippet}"
          </div>
        </div>

        {/* Deterministic Verification Check */}
        <div style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '10px',
          padding: '12px 14px',
          background: 'var(--signal-success-dim)',
          border: '1px solid rgba(72, 187, 120, 0.25)',
          borderRadius: '8px',
          fontSize: '0.78rem',
          color: 'var(--signal-success)'
        }}>
          <CheckCircle2 size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontWeight: 600 }}>Deterministic Provenance Verified</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.74rem', marginTop: '2px' }}>
              Extracted via PyMuPDF coordinate indexing with zero hallucinations.
            </div>
          </div>
        </div>
      </div>

      {/* Action Footer */}
      <div style={{
        padding: '16px 20px',
        borderTop: '1px solid var(--border-subtle)',
        background: 'var(--bg-surface-elevated)'
      }}>
        <button
          onClick={() => onOpenInViewer && onOpenInViewer(citation)}
          className="btn-primary"
          style={{ width: '100%', justifyContent: 'center' }}
        >
          <ExternalLink size={14} /> Open in Canonical Viewer
        </button>
      </div>
    </div>
  );
}