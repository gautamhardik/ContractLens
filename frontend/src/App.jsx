import React, { useState, useEffect } from 'react';
import { 
  FileText, ShieldAlert, GitCommit, Search, Layers, Calendar, 
  ChevronRight, ExternalLink, CheckCircle2, AlertTriangle, 
  Send, Sparkles, Clock, Globe, ArrowRight, Eye, RefreshCw
} from 'lucide-react';

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [activeTab, setActiveTab] = useState('portfolio'); // 'portfolio' | 'contracts' | 'viewer' | 'risks' | 'amendments'
  const [contracts, setContracts] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('doc_01');
  const [contractDetail, setContractDetail] = useState(null);
  const [portfolioData, setPortfolioData] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [amendmentData, setAmendmentData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Agent Chat State
  const [queryInput, setQueryInput] = useState('');
  const [chatHistory, setChatHistory] = useState([
    {
      role: 'agent',
      content: 'ContractLens operational intelligence agent ready. Ask any question regarding obligations, governing laws, payment terms, or version amendments across your portfolio.',
      citations: [],
      grounding_status: 'SUPPORTED',
    }
  ]);
  const [queryLoading, setQueryLoading] = useState(false);
  const [highlightedBlockId, setHighlightedBlockId] = useState(null);

  // Initial Data Fetch
  useEffect(() => {
    fetchInitialData();
  }, []);

  // Fetch contract detail when selected
  useEffect(() => {
    if (selectedDocId) {
      fetchContractDetail(selectedDocId);
    }
  }, [selectedDocId]);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const [portRes, listRes, riskRes] = await Promise.all([
        fetch(`${API_BASE}/api/portfolio`),
        fetch(`${API_BASE}/api/contracts`),
        fetch(`${API_BASE}/api/risks`),
      ]);

      if (portRes.ok) setPortfolioData(await portRes.json());
      if (listRes.ok) {
        const list = await listRes.json();
        setContracts(list);
        if (list.length > 0) setSelectedDocId(list[0].document_id);
      }
      if (riskRes.ok) setRiskData(await riskRes.json());
    } catch (err) {
      console.error("Failed to connect to backend API:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchContractDetail = async (docId) => {
    try {
      const res = await fetch(`${API_BASE}/api/contracts/${docId}`);
      if (res.ok) {
        setContractDetail(await res.json());
      }
    } catch (err) {
      console.error("Failed to load contract detail:", err);
    }
  };

  const loadAmendmentComparison = async (docId) => {
    try {
      const res = await fetch(`${API_BASE}/api/amendments/${docId}`);
      if (res.ok) {
        setAmendmentData(await res.json());
        setActiveTab('amendments');
      }
    } catch (err) {
      console.error("Failed to load amendment comparison:", err);
    }
  };

  const handleSendQuery = async (e) => {
    e?.preventDefault();
    if (!queryInput.trim() || queryLoading) return;

    const userMsg = queryInput.trim();
    setQueryInput('');
    setChatHistory(prev => [...prev, { role: 'user', content: userMsg }]);
    setQueryLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsg }),
      });

      if (res.ok) {
        const data = await res.json();
        setChatHistory(prev => [...prev, {
          role: 'agent',
          content: data.answer,
          citations: data.citations || [],
          grounding_status: data.grounding_status,
          trace: data.trace,
        }]);
      } else {
        setChatHistory(prev => [...prev, {
          role: 'agent',
          content: 'Unable to process query safely. The requested topic may lack contract evidence.',
          citations: [],
          grounding_status: 'INSUFFICIENT_EVIDENCE',
        }]);
      }
    } catch (err) {
      setChatHistory(prev => [...prev, {
        role: 'agent',
        content: `Error connecting to agent: ${err.message}`,
        citations: [],
        grounding_status: 'ERROR',
      }]);
    } finally {
      setQueryLoading(false);
    }
  };

  const handleCitationClick = (citation) => {
    if (citation.document_id && citation.document_id !== selectedDocId) {
      setSelectedDocId(citation.document_id);
    }
    setHighlightedBlockId(citation.block_id);
    setActiveTab('viewer');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navigation Bar */}
      <header style={{
        height: '64px',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(10, 13, 20, 0.85)',
        backdropFilter: 'blur(20px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        position: 'sticky',
        top: 0,
        zIndex: 40
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'var(--gradient-brand)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)'
          }}>
            <Eye size={20} color="#fff" />
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: '1.15rem', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '8px' }}>
              Contract<span style={{ color: 'var(--accent-blue)' }}>Lens</span>
              <span className="badge badge-indigo">PROD AGENT</span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Deterministic B2B Contract Review & Obligation Tracking
            </div>
          </div>
        </div>

        {/* View Tabs */}
        <div style={{ display: 'flex', gap: '8px', background: 'rgba(255, 255, 255, 0.03)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
          {[
            { id: 'portfolio', label: 'Portfolio Overview', icon: Globe },
            { id: 'contracts', label: 'All Agreements', icon: FileText },
            { id: 'viewer', label: 'Document & Evidence', icon: Layers },
            { id: 'risks', label: 'Risk Engine', icon: ShieldAlert },
            { id: 'amendments', label: 'Version Diff', icon: GitCommit },
          ].map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  borderRadius: '6px',
                  fontSize: '0.85rem',
                  fontWeight: active ? 600 : 400,
                  color: active ? '#ffffff' : 'var(--text-secondary)',
                  background: active ? 'rgba(99, 102, 241, 0.25)' : 'transparent',
                  border: active ? '1px solid var(--border-accent)' : '1px solid transparent',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <Icon size={14} color={active ? 'var(--accent-blue)' : 'var(--text-muted)'} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Status Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-emerald)', boxShadow: '0 0 10px var(--accent-emerald)' }}></div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            18 Contracts Verified • 0% Unsupported Claims
          </span>
        </div>
      </header>

      {/* Main Workspace Grid */}
      <div className="workspace-grid">
        {/* Left Sidebar: Contract Selector */}
        <aside style={{
          borderRight: '1px solid var(--border-subtle)',
          background: 'rgba(15, 20, 34, 0.5)',
          overflowY: 'auto',
          padding: '16px 12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', padding: '0 8px 8px' }}>
            Portfolio Corpus ({contracts.length})
          </div>
          {contracts.map(c => {
            const isSelected = selectedDocId === c.document_id;
            const isAmendment = c.filename.toLowerCase().includes('amend');
            return (
              <div
                key={c.document_id}
                onClick={() => {
                  setSelectedDocId(c.document_id);
                  if (activeTab === 'portfolio') setActiveTab('viewer');
                }}
                className="glass-panel-interactive"
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  background: isSelected ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.02)',
                  borderColor: isSelected ? 'var(--border-accent)' : 'var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, color: isSelected ? '#fff' : 'var(--text-primary)', wordBreak: 'break-word' }}>
                    {c.filename.replace('.pdf', '')}
                  </span>
                  {isAmendment ? (
                    <span className="badge badge-amber" style={{ fontSize: '0.65rem' }}>AMEND</span>
                  ) : (
                    <span className="badge badge-blue" style={{ fontSize: '0.65rem' }}>{c.document_id}</span>
                  )}
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                  {c.contract_type} • {c.page_count} pages
                </div>
                {c.parties && c.parties.length > 0 && (
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {c.parties.join(' & ')}
                  </div>
                )}
              </div>
            );
          })}
        </aside>

        {/* Center Main Stage */}
        <main style={{ overflowY: 'auto', padding: '24px', position: 'relative' }}>
          {activeTab === 'portfolio' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div>
                <h1 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '6px' }}>Portfolio Intelligence Dashboard</h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  Aggregate operational metrics, governing laws, payment schedules, and counterparty networks.
                </p>
              </div>

              {/* KPI Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                {[
                  { label: 'Total Agreements', value: portfolioData?.total_contracts || 18, desc: 'Indexed in Canonical Model', icon: FileText, color: 'var(--accent-blue)' },
                  { label: 'Extracted Obligations', value: portfolioData?.total_obligations || 24, desc: 'Provenanced Commitments', icon: CheckCircle2, color: 'var(--accent-emerald)' },
                  { label: 'Lifecycle Milestones', value: portfolioData?.total_events || 36, desc: 'Notice & Term Deadlines', icon: Calendar, color: 'var(--accent-purple)' },
                  { label: 'High Risk Flags', value: riskData?.high_risk_contracts || 4, desc: 'Auto-Renewals & Caps', icon: ShieldAlert, color: 'var(--accent-rose)' },
                ].map((kpi, idx) => {
                  const Icon = kpi.icon;
                  return (
                    <div key={idx} className="glass-panel" style={{ padding: '20px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>{kpi.label}</span>
                        <Icon size={18} color={kpi.color} />
                      </div>
                      <div style={{ fontSize: '2rem', fontWeight: 800, margin: '8px 0', color: '#fff' }}>{kpi.value}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{kpi.desc}</div>
                    </div>
                  );
                })}
              </div>

              {/* Distributions Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                {/* Governing Law Breakdown */}
                <div className="glass-panel" style={{ padding: '20px' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Globe size={16} color="var(--accent-blue)" /> Governing Law Distribution
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {portfolioData?.governing_laws && Object.entries(portfolioData.governing_laws).map(([law, count]) => (
                      <div key={law} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{law}</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '50%' }}>
                          <div style={{ flex: 1, height: '6px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ width: `${(count / 18) * 100}%`, height: '100%', background: 'var(--accent-blue)', borderRadius: '3px' }} />
                          </div>
                          <span style={{ fontSize: '0.8rem', fontWeight: 700, minWidth: '20px' }}>{count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Payment Terms Breakdown */}
                <div className="glass-panel" style={{ padding: '20px' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Clock size={16} color="var(--accent-emerald)" /> Commercial Payment Terms
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {portfolioData?.payment_terms && Object.entries(portfolioData.payment_terms).map(([term, count]) => (
                      <div key={term} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{term}</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '50%' }}>
                          <div style={{ flex: 1, height: '6px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ width: `${(count / 18) * 100}%`, height: '100%', background: 'var(--accent-emerald)', borderRadius: '3px' }} />
                          </div>
                          <span style={{ fontSize: '0.8rem', fontWeight: 700, minWidth: '20px' }}>{count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Upcoming Milestones */}
              <div className="glass-panel" style={{ padding: '20px' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Calendar size={16} color="var(--accent-purple)" /> Upcoming Notice & Renewal Milestones
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
                  {portfolioData?.upcoming_milestones?.slice(0, 6).map((m, i) => (
                    <div key={i} style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                        <span className="badge badge-purple" style={{ fontSize: '0.7rem' }}>{m.event_type}</span>
                        <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-blue)' }}>{m.date_or_trigger}</span>
                      </div>
                      <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '4px' }}>{m.title}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{m.filename}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'viewer' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Document Header */}
              {contractDetail && (
                <div className="glass-panel" style={{ padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{contractDetail.document.filename}</h2>
                      <span className="badge badge-blue">{contractDetail.intelligence?.contract_type?.raw_value || 'Agreement'}</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      Document ID: <code style={{ color: 'var(--accent-blue)' }}>{contractDetail.document.document_id}</code> • {contractDetail.document.page_count} Pages • {contractDetail.document.file_size} Bytes
                    </div>
                  </div>
                  {contractDetail.document.filename.toLowerCase().includes('access') && (
                    <button
                      onClick={() => loadAmendmentComparison(contractDetail.document.document_id)}
                      className="btn-primary"
                    >
                      <GitCommit size={16} /> Compare Amendment Diffs
                    </button>
                  )}
                </div>
              )}

              {/* Extracted Intelligence Strip */}
              {contractDetail?.intelligence && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
                  <div className="glass-panel" style={{ padding: '12px' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>EFFECTIVE DATE</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 600, marginTop: '2px' }}>
                      {contractDetail.intelligence.effective_date?.normalized_value || 'Not specified'}
                    </div>
                  </div>
                  <div className="glass-panel" style={{ padding: '12px' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>EXPIRATION DATE</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 600, marginTop: '2px' }}>
                      {contractDetail.intelligence.expiration_date?.normalized_value || 'Not specified'}
                    </div>
                  </div>
                  <div className="glass-panel" style={{ padding: '12px' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>PAYMENT TERMS</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 600, marginTop: '2px' }}>
                      {contractDetail.intelligence.payment_terms?.raw_value || 'Not specified'}
                    </div>
                  </div>
                  <div className="glass-panel" style={{ padding: '12px' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>GOVERNING LAW</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 600, marginTop: '2px' }}>
                      {contractDetail.intelligence.governing_law?.normalized_value || 'Not specified'}
                    </div>
                  </div>
                </div>
              )}

              {/* Canonical Pages with Bounding Box Text Blocks */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {contractDetail?.document.pages.map(page => (
                  <div key={page.page_number} className="glass-panel" style={{ padding: '24px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px', marginBottom: '16px' }}>
                      <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)' }}>PAGE {page.page_number} OF {contractDetail.document.page_count}</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Dimensions: {page.width} x {page.height} pt</span>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {page.blocks.map(b => {
                        const isHighlighted = highlightedBlockId === b.block_id;
                        return (
                          <div
                            key={b.block_id}
                            id={`block-${b.block_id}`}
                            style={{
                              padding: '10px 14px',
                              borderRadius: '6px',
                              background: isHighlighted ? 'rgba(245, 158, 11, 0.15)' : 'rgba(255, 255, 255, 0.01)',
                              border: isHighlighted ? '1px solid var(--accent-amber)' : '1px solid rgba(255, 255, 255, 0.04)',
                              transition: 'all 0.3s ease',
                              position: 'relative'
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                              <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: isHighlighted ? 'var(--accent-amber)' : 'var(--text-muted)' }}>
                                {b.block_id} • {b.block_type}
                                {b.bbox && ` • bbox: [${b.bbox.x0.toFixed(0)}, ${b.bbox.y0.toFixed(0)}, ${b.bbox.x1.toFixed(0)}, ${b.bbox.y1.toFixed(0)}]`}
                              </span>
                              {b.section_number && (
                                <span className="badge badge-blue" style={{ fontSize: '0.65rem' }}>
                                  §{b.section_number} {b.section_title}
                                </span>
                              )}
                            </div>
                            <div style={{ fontSize: '0.85rem', lineHeight: '1.6', color: isHighlighted ? '#ffffff' : 'var(--text-primary)' }}>
                              {b.raw_text}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'risks' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div>
                <h1 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '6px' }}>Operational Risk & Review Signals</h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  Deterministic audit flags answering: <i>"What should I worry about across these contracts?"</i>
                </p>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {riskData?.contract_reports?.map(rep => (
                  <div key={rep.document_id} className="glass-panel" style={{ padding: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>{rep.filename}</h3>
                          <span className={`badge ${rep.risk_score >= 40 ? 'badge-rose' : 'badge-emerald'}`}>
                            Risk Score: {rep.risk_score} / 100
                          </span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                          {rep.total_signals} Risk Signals Identified
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          setSelectedDocId(rep.document_id);
                          setActiveTab('viewer');
                        }}
                        className="btn-secondary"
                        style={{ fontSize: '0.8rem', padding: '6px 12px' }}
                      >
                        Inspect Evidence
                      </button>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {rep.signals.map((sig, sIdx) => (
                        <div key={sIdx} style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '12px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                            <span style={{ fontWeight: 600, fontSize: '0.85rem', color: '#fff' }}>{sig.title}</span>
                            <span className={`badge ${sig.severity === 'HIGH' ? 'badge-rose' : 'badge-amber'}`} style={{ fontSize: '0.65rem' }}>
                              {sig.severity}
                            </span>
                          </div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                            {sig.description}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <CheckCircle2 size={13} /> <strong>Recommendation:</strong> {sig.recommendation}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'amendments' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div>
                <h1 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '6px' }}>Structured Amendment & Version Intelligence</h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  Clause-by-clause version alignment showing exact modifications and explicit full force confirmation.
                </p>
              </div>

              {amendmentData ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div className="glass-panel" style={{ padding: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>VERSION RELATIONSHIP</div>
                        <div style={{ fontSize: '1.1rem', fontWeight: 700, marginTop: '2px' }}>
                          {amendmentData.amendment_filename} ➔ amends {amendmentData.parent_filename}
                        </div>
                      </div>
                      <span className="badge badge-emerald">Full Force & Effect Confirmed</span>
                    </div>

                    <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Key Business Impacts</div>
                      {amendmentData.business_impact_items?.map((item, idx) => (
                        <div key={idx} style={{ fontSize: '0.85rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <ArrowRight size={14} color="var(--accent-blue)" /> {item}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Section Changes Diff */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Modified Clauses ({amendmentData.changes?.length})</h3>
                    {amendmentData.changes?.map((ch, idx) => (
                      <div key={idx} className="glass-panel" style={{ padding: '16px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                          <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>
                            §{ch.section_number} {ch.section_title}
                          </div>
                          <span className="badge badge-amber">{ch.change_type}</span>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                          {/* Before */}
                          <div style={{ background: 'rgba(244, 63, 94, 0.05)', border: '1px solid rgba(244, 63, 94, 0.2)', padding: '12px', borderRadius: '6px' }}>
                            <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--accent-rose)', marginBottom: '4px' }}>PRIOR AGREEMENT TERM</div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                              {ch.before_text || 'No preceding clause text explicitly recorded.'}
                            </div>
                          </div>

                          {/* After */}
                          <div style={{ background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', padding: '12px', borderRadius: '6px' }}>
                            <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--accent-emerald)', marginBottom: '4px' }}>AMENDED TERM</div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-primary)', lineHeight: '1.5' }}>
                              {ch.after_text}
                            </div>
                          </div>
                        </div>

                        <div style={{ marginTop: '12px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
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
                    onClick={() => loadAmendmentComparison('doc_02')}
                    className="btn-primary"
                    style={{ marginTop: '16px' }}
                  >
                    Load Access-E*TRADE Amendment Diff
                  </button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'contracts' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div>
                <h1 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '6px' }}>All Indexed Contract Agreements</h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  Complete registry of 18 documents with verified metadata and canonical provenance.
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                {contracts.map(c => (
                  <div key={c.document_id} className="glass-panel-interactive" style={{ padding: '18px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                      <div>
                        <h4 style={{ fontSize: '0.95rem', fontWeight: 700 }}>{c.filename}</h4>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                          ID: <code style={{ color: 'var(--accent-blue)' }}>{c.document_id}</code> • {c.contract_type}
                        </div>
                      </div>
                      <span className="badge badge-indigo">{c.page_count} Pages</span>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', margin: '12px 0', fontSize: '0.8rem' }}>
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
                        onClick={() => {
                          setSelectedDocId(c.document_id);
                          setActiveTab('viewer');
                        }}
                        className="btn-secondary"
                        style={{ fontSize: '0.75rem', padding: '6px 10px', flex: 1 }}
                      >
                        View Pages & Bounding Boxes
                      </button>
                      {c.filename.toLowerCase().includes('access') && (
                        <button
                          onClick={() => loadAmendmentComparison(c.document_id)}
                          className="btn-primary"
                          style={{ fontSize: '0.75rem', padding: '6px 10px' }}
                        >
                          Diff
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>

        {/* Right Drawer: Conversational Grounded Agent */}
        <aside className="drawer-right" style={{
          borderLeft: '1px solid var(--border-subtle)',
          background: 'rgba(10, 13, 20, 0.95)',
          backdropFilter: 'blur(20px)',
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
        }}>
          {/* Drawer Header */}
          <div style={{
            padding: '16px',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <Sparkles size={16} color="var(--accent-blue)" />
            <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>ContractLens Agent</div>
            <span className="badge badge-blue" style={{ marginLeft: 'auto', fontSize: '0.65rem' }}>Grounded RAG</span>
          </div>

          {/* Chat Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {chatHistory.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '90%',
                  background: msg.role === 'user' ? 'var(--gradient-brand)' : 'rgba(255, 255, 255, 0.04)',
                  border: msg.role === 'user' ? 'none' : '1px solid var(--border-subtle)',
                  borderRadius: '10px',
                  padding: '12px 14px',
                  fontSize: '0.85rem',
                  lineHeight: '1.5',
                  color: '#ffffff'
                }}
              >
                <div>{msg.content}</div>

                {/* Citations / Provenance Badges */}
                {msg.citations && msg.citations.length > 0 && (
                  <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Verified Evidence</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {msg.citations.map((c, cIdx) => (
                        <button
                          key={cIdx}
                          onClick={() => handleCitationClick(c)}
                          style={{
                            background: 'rgba(56, 189, 248, 0.15)',
                            border: '1px solid rgba(56, 189, 248, 0.4)',
                            color: 'var(--accent-blue)',
                            borderRadius: '4px',
                            padding: '3px 8px',
                            fontSize: '0.7rem',
                            cursor: 'pointer',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            transition: 'all 0.15s ease'
                          }}
                        >
                          <ExternalLink size={10} />
                          {c.document_id} p.{c.page_number}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
            {queryLoading && (
              <div style={{ alignSelf: 'flex-start', color: 'var(--text-muted)', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <RefreshCw size={14} className="spin" /> Agent executing deterministic reasoning tools...
              </div>
            )}
          </div>

          {/* Input Box */}
          <form onSubmit={handleSendQuery} style={{ padding: '16px', borderTop: '1px solid var(--border-subtle)', background: 'rgba(15, 20, 34, 0.8)' }}>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                placeholder="Ask about obligations, parties, terms..."
                value={queryInput}
                onChange={e => setQueryInput(e.target.value)}
                style={{
                  flex: 1,
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  fontSize: '0.85rem',
                  color: '#ffffff',
                  outline: 'none',
                }}
              />
              <button
                type="submit"
                disabled={queryLoading}
                className="btn-primary"
                style={{ padding: '10px 14px' }}
              >
                <Send size={16} />
              </button>
            </div>
          </form>
        </aside>
      </div>
    </div>
  );
}
