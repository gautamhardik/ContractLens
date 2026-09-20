import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import SuggestionChips from '../../components/chat/SuggestionChips';
import Composer from '../../components/chat/Composer';
import Citation from '../../components/evidence/Citation';
import AgentStatus from '../../components/chat/AgentStatus';
import AgentTraceTimeline from '../../components/chat/AgentTraceTimeline';
import EvidencePanel from '../../components/evidence/EvidencePanel';
import AmendmentIntelligenceCard from '../../components/amendments/AmendmentIntelligenceCard';
import ContractUploadZone from '../../components/chat/ContractUploadZone';

/**
 * Lightweight markdown renderer for agent answers.
 * Handles: tables, **bold**, *italic*, bullet lists, plain paragraphs.
 */
function renderMarkdown(text) {
  if (!text) return null;
  const lines = text.split('\n');
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Detect markdown table block (line starts with |)
    if (line.trim().startsWith('|')) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        tableLines.push(lines[i]);
        i++;
      }
      if (tableLines.length >= 2) {
        const headerCells = tableLines[0].split('|').filter((_, ci) => ci > 0 && ci < tableLines[0].split('|').length - 1);
        const bodyRows = tableLines.slice(2); // skip header + separator
        elements.push(
          <div key={`tbl-${i}`} style={{ overflowX: 'auto', margin: '10px 0' }}>
            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '0.8rem',
              fontFamily: 'var(--font-sans)',
            }}>
              <thead>
                <tr>
                  {headerCells.map((h, hi) => (
                    <th key={hi} style={{
                      padding: '7px 12px',
                      background: 'var(--bg-surface-elevated)',
                      border: '1px solid var(--border-medium)',
                      color: 'var(--text-secondary)',
                      fontWeight: 600,
                      fontSize: '0.72rem',
                      textAlign: 'left',
                      whiteSpace: 'nowrap',
                    }}>{h.trim()}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {bodyRows.map((row, ri) => {
                  const cells = row.split('|').filter((_, ci) => ci > 0 && ci < row.split('|').length - 1);
                  const isDiffRow = cells[0] && cells[0].includes('⬅ differs');
                  return (
                    <tr key={ri} style={{ background: isDiffRow ? 'rgba(209, 110, 75, 0.06)' : 'transparent' }}>
                      {cells.map((cell, ci) => (
                        <td key={ci} style={{
                          padding: '6px 12px',
                          border: '1px solid var(--border-subtle)',
                          color: 'var(--text-primary)',
                          verticalAlign: 'top',
                        }} dangerouslySetInnerHTML={{ __html: cell.trim()
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\*(.*?)\*/g, '<em>$1</em>')
                        }} />
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    }

    // Bullet list item
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      const items = [];
      while (i < lines.length && (lines[i].trim().startsWith('- ') || lines[i].trim().startsWith('* '))) {
        items.push(lines[i].trim().slice(2));
        i++;
      }
      elements.push(
        <ul key={`ul-${i}`} style={{ margin: '4px 0 4px 16px', padding: 0, listStyle: 'disc' }}>
          {items.map((item, ii) => (
            <li key={ii} style={{ color: 'var(--text-primary)', fontSize: '0.85rem', marginBottom: '2px' }}
              dangerouslySetInnerHTML={{ __html: item
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
              }}
            />
          ))}
        </ul>
      );
      continue;
    }

    // Empty line → spacer
    if (line.trim() === '') {
      elements.push(<div key={`sp-${i}`} style={{ height: '6px' }} />);
      i++;
      continue;
    }

    // Regular paragraph with inline bold/italic
    elements.push(
      <p key={`p-${i}`} style={{ margin: '2px 0', fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: 1.65 }}
        dangerouslySetInnerHTML={{ __html: line
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.*?)\*/g, '<em>$1</em>')
        }}
      />
    );
    i++;
  }

  return <>{elements}</>;
}

export default function ChatView({
  chatHistory,
  queryInput,
  setQueryInput,
  queryLoading,
  agentActivityState,
  scopedContractIds,
  setScopedContractIds,
  isContractPickerOpen,
  setIsContractPickerOpen,
  contracts,
  onSendQuery,
  activeEvidenceCitation,
  setActiveEvidenceCitation,
  onOpenInViewer,
  onUploadSuccess,
  chatEndRef
}) {
  const [copiedMessageIdx, setCopiedMessageIdx] = useState(null);

  const handleCitationClick = (citation) => {
    setActiveEvidenceCitation(citation);
  };

  const toggleContractScope = (docId) => {
    setScopedContractIds(prev =>
      prev.includes(docId) ? prev.filter(id => id !== docId) : [...prev, docId]
    );
  };

  return (
    <div style={{ flex: 1, display: 'flex', position: 'relative', height: 'calc(100vh - 60px)', overflow: 'hidden' }}>
      {/* Conversation Stream Column */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', position: 'relative', minWidth: 0 }}>
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 24px 8px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ width: '100%', maxWidth: '780px' }}>
            
            {/* Hero Minimal Empty State */}
            {chatHistory.length <= 1 && (
              <div style={{ textAlign: 'center', padding: '16px 0 16px', animation: 'fadeInRise 0.5s ease-out' }}>
                <div style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '4px 12px',
                  borderRadius: '9999px',
                  background: 'var(--accent-terracotta-dim)',
                  border: '1px solid var(--accent-terracotta-border)',
                  fontSize: '0.72rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--accent-terracotta)',
                  marginBottom: '16px'
                }}>
                  ◈ SPATIAL CONTRACT INTELLIGENCE
                </div>
                <h1 className="editorial-title" style={{ fontSize: '2.4rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '12px', letterSpacing: '-0.03em', fontFamily: 'var(--font-sans)', lineHeight: 1.2 }}>
                  Investigate your contracts.
                </h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.98rem', maxWidth: '560px', margin: '0 auto 20px', lineHeight: '1.65', fontFamily: 'var(--font-sans)' }}>
                  Ask questions, compare agreement amendments, track counterparty obligations, and inspect exact physical PDF evidence.
                </p>

                <ContractUploadZone onUploadSuccess={onUploadSuccess} />

                <SuggestionChips contractsCount={contracts.length} onSelectPrompt={(p) => onSendQuery(null, p)} />
              </div>
            )}

            {/* Conversation Message Feed */}
            {chatHistory.length > 1 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '28px', paddingBottom: '24px' }}>
                {chatHistory.map((msg, idx) => {
                  if (msg.role === 'user') {
                    return (
                      <div key={idx} style={{
                        alignSelf: 'flex-end',
                        maxWidth: '85%',
                        background: 'var(--bg-surface-elevated)',
                        border: '1px solid var(--border-medium)',
                        borderRadius: '14px 14px 2px 14px',
                        padding: '14px 18px',
                        color: 'var(--text-primary)',
                        fontSize: '0.94rem',
                        lineHeight: '1.5',
                        boxShadow: 'var(--shadow-ambient)'
                      }}>
                        {msg.scoped_contracts && msg.scoped_contracts.length > 0 && (
                          <div style={{ display: 'flex', gap: '4px', marginBottom: '8px' }}>
                            {msg.scoped_contracts.map(id => (
                              <span key={id} style={{
                                fontSize: '0.68rem',
                                fontFamily: 'var(--font-mono)',
                                background: 'var(--accent-terracotta-dim)',
                                border: '1px solid var(--accent-terracotta-border)',
                                padding: '1px 6px',
                                borderRadius: '4px',
                                color: 'var(--accent-terracotta)'
                              }}>
                                [{id}]
                              </span>
                            ))}
                          </div>
                        )}
                        <div>{msg.content}</div>
                        {msg.timestamp && (
                          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textAlign: 'right', marginTop: '6px' }}>
                            {msg.timestamp}
                          </div>
                        )}
                      </div>
                    );
                  }

                  // Assistant Grounded Response (Claude-style literary prose flow)
                  return (
                    <div key={idx} style={{
                      alignSelf: 'flex-start',
                      width: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '12px'
                    }}>
                      {/* Assistant Header */}
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{
                            width: '22px',
                            height: '22px',
                            borderRadius: '4px',
                            background: 'var(--accent-terracotta)',
                            color: '#ffffff',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '0.75rem',
                            fontFamily: 'var(--font-sans)',
                            fontWeight: 700
                          }}>
                            C
                          </div>
                          <span style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                            ContractLens Intelligence
                          </span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <button
                            onClick={() => {
                              if (navigator.clipboard) {
                                navigator.clipboard.writeText(msg.content);
                                setCopiedMessageIdx(idx);
                                setTimeout(() => setCopiedMessageIdx(null), 2000);
                              }
                            }}
                            title="Copy answer to clipboard"
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                              padding: '3px 8px',
                              borderRadius: '6px',
                              background: copiedMessageIdx === idx ? 'var(--signal-success-dim)' : 'var(--bg-surface)',
                              border: `1px solid ${copiedMessageIdx === idx ? 'rgba(72, 187, 120, 0.3)' : 'var(--border-subtle)'}`,
                              color: copiedMessageIdx === idx ? 'var(--signal-success)' : 'var(--text-secondary)',
                              fontSize: '0.68rem',
                              fontWeight: 500,
                              cursor: 'pointer',
                              transition: 'all var(--transition-fast)'
                            }}
                          >
                            {copiedMessageIdx === idx ? (
                              <>
                                <Check size={12} color="var(--signal-success)" />
                                <span>Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy size={12} color="var(--text-secondary)" />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                          <span style={{
                            fontSize: '0.68rem',
                            fontFamily: 'var(--font-mono)',
                            color: 'var(--signal-success)',
                            background: 'var(--signal-success-dim)',
                            border: '1px solid rgba(72, 187, 120, 0.3)',
                            padding: '2px 8px',
                            borderRadius: '9999px'
                          }}>
                            ◈ {msg.grounding_status || 'SUPPORTED'}
                          </span>
                        </div>
                      </div>

                      {/* Response Text with Literary Spacing */}
                      <div className="claude-prose" style={{
                        padding: '4px 0',
                        whiteSpace: 'pre-wrap'
                      }}>
                        {renderMarkdown(msg.content)}
                      </div>

                      {/* Tool-Level Activity Trace Disclosure Widget */}
                      {msg.trace && msg.trace.steps && msg.trace.steps.length > 0 && (
                        <AgentTraceTimeline trace={msg.trace} />
                      )}

                      {/* In-Conversation Structured Amendment Card */}
                      {msg.structured_diff && (
                        <AmendmentIntelligenceCard diffData={msg.structured_diff} />
                      )}

                      {/* Interactive Citations / Provenance Anchors */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div style={{ marginTop: '8px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
                          <div style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
                            Verified Evidence ({msg.citations.length})
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                            {msg.citations.map((cit, cIdx) => (
                              <Citation
                                key={cIdx}
                                citation={cit}
                                onClick={handleCitationClick}
                                isActive={activeEvidenceCitation && activeEvidenceCitation.block_id === cit.block_id}
                              />
                            ))}
                          </div>
                        </div>
                      )}

                      {/* AXIOM-inspired Dynamic Contextual Follow-up Suggestions */}
                      {idx === chatHistory.length - 1 && !queryLoading && (
                        <div style={{
                          marginTop: '12px',
                          paddingTop: '10px',
                          borderTop: '1px dashed var(--border-subtle)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px'
                        }}>
                          <div style={{
                            fontSize: '0.68rem',
                            fontFamily: 'var(--font-mono)',
                            color: 'var(--text-muted)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '5px'
                          }}>
                            <span>🧭 INVESTIGATION FOLLOW-UPS</span>
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                            {[
                              { label: "Governing Law & Jurisdiction", query: "Which jurisdictions and governing laws are specified across these contracts?" },
                              { label: "Operational Risks & Deadlines", query: "What operational risks, notice windows, and renewal obligations exist?" },
                              { label: "Payment & Financial Terms", query: "Compare payment terms, fee schedules, and net days across the agreements." },
                              { label: "Termination & Renewal Rights", query: "What are the termination rights, convenience clauses, and cure periods?" }
                            ].map((sug, sIdx) => (
                              <button
                                key={sIdx}
                                onClick={() => onSendQuery(null, sug.query)}
                                style={{
                                  padding: '5px 10px',
                                  borderRadius: '16px',
                                  background: 'var(--bg-surface-elevated)',
                                  border: '1px solid var(--border-subtle)',
                                  color: 'var(--text-secondary)',
                                  fontSize: '0.72rem',
                                  cursor: 'pointer',
                                  transition: 'all var(--transition-fast)',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '4px'
                                }}
                                onMouseEnter={e => {
                                  e.currentTarget.style.borderColor = 'var(--accent-terracotta)';
                                  e.currentTarget.style.color = 'var(--text-primary)';
                                }}
                                onMouseLeave={e => {
                                  e.currentTarget.style.borderColor = 'var(--border-subtle)';
                                  e.currentTarget.style.color = 'var(--text-secondary)';
                                }}
                              >
                                <span>{sug.label}</span>
                                <span style={{ opacity: 0.6 }}>→</span>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Real-Time Agent Thought Status Indicator */}
            {agentActivityState !== 'idle' && (
              <div style={{ display: 'flex', justifyContent: 'flex-start', margin: '12px 0' }}>
                <AgentStatus state={agentActivityState} />
              </div>
            )}

            <div ref={chatEndRef} />
          </div>
        </div>

        {/* Floating Composer Deck */}
        <Composer
          queryInput={queryInput}
          setQueryInput={setQueryInput}
          queryLoading={queryLoading}
          scopedContractIds={scopedContractIds}
          onToggleContractScope={toggleContractScope}
          onClearScope={() => setScopedContractIds([])}
          isContractPickerOpen={isContractPickerOpen}
          setIsContractPickerOpen={setIsContractPickerOpen}
          contracts={contracts}
          onSend={onSendQuery}
        />
      </div>

      {/* Spatial Sliding Evidence Panel */}
      <EvidencePanel
        citation={activeEvidenceCitation}
        onClose={() => setActiveEvidenceCitation(null)}
        onOpenInViewer={onOpenInViewer}
      />
    </div>
  );
}
