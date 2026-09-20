import React, { useState, useEffect, useRef } from 'react';
import { 
  FileText, Layers, 
  MessageSquare, Plus, Search, Sun, Moon, RotateCcw, Trash2
} from 'lucide-react';

import { API_BASE } from './config/api';
import ErrorBoundary from './components/common/ErrorBoundary';
import AmbientField from './components/spatial/AmbientField';
import ChatView from './features/chat/ChatView';
import CanonicalViewer from './features/viewer/CanonicalViewer';
import PortfolioView from './features/portfolio/PortfolioView';

export default function App() {
  // Synchronize initial state from URL query parameters (Deep Linking)
  const queryParams = new URLSearchParams(window.location.search);
  const initialTab = queryParams.get('tab') || 'chat';
  const initialDoc = queryParams.get('doc') || null;
  const initialBlock = queryParams.get('block') || null;

  const [activeTab, setActiveTab] = useState(initialTab);
  const [contracts, setContracts] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(initialDoc);
  const [contractDetail, setContractDetail] = useState(null);
  const [portfolioData, setPortfolioData] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [amendmentData, setAmendmentData] = useState(null);

  // Scoped Contract Context Tokens in Composer
  const [scopedContractIds, setScopedContractIds] = useState([]);
  const [isContractPickerOpen, setIsContractPickerOpen] = useState(false);
  const [activeEvidenceCitation, setActiveEvidenceCitation] = useState(null);
  const [agentActivityState, setAgentActivityState] = useState('idle');

  // Agent Chat State — persisted to localStorage so conversations survive page refresh
  const CHAT_STORAGE_KEY = 'contractlens_chat_history';
  const MAX_CHAT_BYTES = 200 * 1024; // 200 KB cap

  const [chatHistory, setChatHistory] = useState(() => {
    try {
      const saved = localStorage.getItem(CHAT_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (_) {}
    return [
      {
        role: 'agent',
        content: 'ContractLens operational contract intelligence ready. Ask questions about obligations, governing laws, payment schedules, or version amendments across your portfolio.',
        citations: [],
        grounding_status: 'SUPPORTED',
        timestamp: 'Ready'
      }
    ];
  });
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryInput, setQueryInput] = useState('');
  const [highlightedBlockId, setHighlightedBlockId] = useState(initialBlock);
  const [sidebarFilter, setSidebarFilter] = useState('');
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('contractlens_theme') || 'light';
  });

  const chatEndRef = useRef(null);

  // Synchronize URL query params whenever primary navigation changes (Deep Linking & Shareable URLs)
  useEffect(() => {
    const params = new URLSearchParams();
    params.set('tab', activeTab);
    if (selectedDocId) params.set('doc', selectedDocId);
    if (highlightedBlockId) params.set('block', highlightedBlockId);
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({}, '', newUrl);
  }, [activeTab, selectedDocId, highlightedBlockId]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('contractlens_theme', theme);
  }, [theme]);

  // Persist chat history to localStorage on every update (with size cap)
  useEffect(() => {
    try {
      // Strip bulky trace objects before saving to keep storage lean
      const saveable = chatHistory.map(msg => ({
        role: msg.role,
        content: msg.content,
        citations: msg.citations || [],
        grounding_status: msg.grounding_status,
        timestamp: msg.timestamp,
        // Do NOT persist trace / structured_diff — too large
      }));
      const serialized = JSON.stringify(saveable);
      if (serialized.length < MAX_CHAT_BYTES) {
        localStorage.setItem(CHAT_STORAGE_KEY, serialized);
      } else {
        // Keep only the last 20 messages if over limit
        const trimmed = saveable.slice(-20);
        localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(trimmed));
      }
    } catch (_) { /* localStorage may be full — silently ignore */ }
  }, [chatHistory]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  const fetchInitialData = async () => {
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
        if (list.length > 0 && !queryParams.get('doc')) {
          setSelectedDocId(list[0].document_id);
        }
      }
      if (riskRes.ok) setRiskData(await riskRes.json());
    } catch (err) {
      console.error("Failed to connect to backend API:", err);
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

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (selectedDocId) {
      fetchContractDetail(selectedDocId);
    }
  }, [selectedDocId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, agentActivityState]);

  useEffect(() => {
    if (activeTab === 'amendments' && !amendmentData) {
      const targetId = scopedContractIds[0] || selectedDocId || (contracts.length > 0 ? contracts[0].document_id : null);
      if (targetId) {
        loadAmendmentComparison(targetId);
      }
    }
  }, [activeTab, amendmentData, scopedContractIds, selectedDocId, contracts]);

  const handleSendQuery = async (e, manualPrompt = null) => {
    if (e) e.preventDefault();
    const promptText = (manualPrompt || queryInput).trim();
    if (!promptText || queryLoading) return;

    setQueryInput('');
    setChatHistory(prev => [...prev, {
      role: 'user',
      content: promptText,
      scoped_contracts: [...scopedContractIds],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }]);
    setQueryLoading(true);
    setAgentActivityState('understanding');

    try {
      const scopedDocId = scopedContractIds.length === 1 ? scopedContractIds[0] : null;

      const isAmendmentQuery = promptText.toLowerCase().includes('amend') || promptText.toLowerCase().includes('change') || promptText.toLowerCase().includes('diff');
      let comparisonObj = null;
      if (isAmendmentQuery) {
        const targetAmendDocId = scopedDocId || selectedDocId || (contracts.length > 0 ? contracts[0].document_id : null);
        if (targetAmendDocId) {
          try {
            const compRes = await fetch(`${API_BASE}/api/amendments/${targetAmendDocId}`);
            if (compRes.ok) comparisonObj = await compRes.json();
          } catch (e) {
            // fallback
          }
        }
      }

      const res = await fetch(`${API_BASE}/api/query/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: promptText,
          document_id: scopedDocId,
          document_ids: scopedContractIds.length > 0 ? scopedContractIds : null
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      setChatHistory(prev => [...prev, {
        role: 'agent',
        content: '',
        citations: [],
        grounding_status: 'SUPPORTED',
        structured_diff: comparisonObj,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullAnswer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const block of lines) {
          if (!block.trim()) continue;
          const eventMatch = block.match(/event:\s*([^\n]+)/);
          const dataMatch = block.match(/data:\s*([^\n]+)/);
          
          if (!eventMatch || !dataMatch) continue;
          const eventType = eventMatch[1].trim();
          let dataObj = {};
          try {
            dataObj = JSON.parse(dataMatch[1].trim());
          } catch (e) {
            continue;
          }

          if (eventType === 'status') {
            if (dataObj.step) setAgentActivityState(dataObj.step);
          } else if (eventType === 'trace') {
            if (dataObj.label) {
              setAgentActivityState(dataObj.label);
            }
          } else if (eventType === 'token') {
            fullAnswer += dataObj.token;
            setChatHistory(prev => {
              const updated = [...prev];
              if (updated.length > 0) {
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  content: fullAnswer,
                };
              }
              return updated;
            });
          } else if (eventType === 'complete') {
            setChatHistory(prev => {
              const updated = [...prev];
              if (updated.length > 0) {
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  content: dataObj.answer || fullAnswer,
                  citations: dataObj.citations || [],
                  grounding_status: dataObj.grounding_status,
                  trace: dataObj.trace,
                };
              }
              return updated;
            });

            if (dataObj.citations && dataObj.citations.length > 0) {
              setActiveEvidenceCitation(dataObj.citations[0]);
              if (dataObj.citations[0].document_id) {
                setSelectedDocId(dataObj.citations[0].document_id);
              }
              if (dataObj.citations[0].block_id) {
                setHighlightedBlockId(dataObj.citations[0].block_id);
              }
            }
          }
        }
      }
    } catch (err) {
      setChatHistory(prev => [...prev, {
        role: 'agent',
        content: `Error connecting to agent: ${err.message}`,
        citations: [],
        grounding_status: 'ERROR',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setQueryLoading(false);
      setAgentActivityState('idle');
    }
  };

  const handleStartNewInvestigation = () => {
    setChatHistory([
      {
        role: 'agent',
        content: contracts.length === 0
          ? 'Workspace ready. Upload a contract PDF below to begin dynamic ingestion and investigation.'
          : `New investigation session initialized. Ask a question across your ${contracts.length} loaded contract${contracts.length === 1 ? '' : 's'} or select specific agreement scope tokens.`,
        citations: [],
        grounding_status: 'SUPPORTED',
        timestamp: 'Session Reset'
      }
    ]);
    setScopedContractIds([]);
    setActiveEvidenceCitation(null);
    setActiveTab('chat');
  };

  const handleResetWorkspace = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/contracts/clear`, { method: 'POST' });
      if (res.ok) {
        setContracts([]);
        setSelectedDocId(null);
        setContractDetail(null);
        setPortfolioData(null);
        setRiskData(null);
        setAmendmentData(null);
        setScopedContractIds([]);
        setActiveEvidenceCitation(null);
        // Also clear persisted chat history so reset is truly clean
        localStorage.removeItem(CHAT_STORAGE_KEY);
        setChatHistory([
          {
            role: 'agent',
            content: 'Workspace cleared. Upload your contract PDF below to dynamically ingest and query it with grounded provenance.',
            citations: [],
            grounding_status: 'SUPPORTED',
            timestamp: 'Workspace Reset'
          }
        ]);
        setActiveTab('chat');
      }
    } catch (err) {
      console.error("Failed to reset workspace:", err);
    }
  };

  const handleDeleteContract = async (docId, e) => {
    if (e) e.stopPropagation();
    if (!window.confirm(`Are you sure you want to remove this contract from the workspace?`)) return;

    try {
      const res = await fetch(`${API_BASE}/api/contracts/${docId}`, { method: 'DELETE' });
      if (res.ok) {
        setContracts(prev => prev.filter(c => c.document_id !== docId));
        setScopedContractIds(prev => prev.filter(id => id !== docId));
        if (selectedDocId === docId) {
          const remaining = contracts.filter(c => c.document_id !== docId);
          setSelectedDocId(remaining.length > 0 ? remaining[0].document_id : null);
          setContractDetail(null);
        }
        // Refresh portfolio & risks overview
        fetchInitialData();
      }
    } catch (err) {
      console.error(`Failed to delete contract ${docId}:`, err);
    }
  };

  const handleOpenInViewer = (citation) => {
    if (citation.document_id) setSelectedDocId(citation.document_id);
    if (citation.block_id) setHighlightedBlockId(citation.block_id);
    setActiveTab('viewer');
  };

  return (
    <ErrorBoundary>
      <div style={{ height: '100vh', maxHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-canvas)', overflow: 'hidden' }}>
        {/* Top Claude-Inspired Navigation Header */}
        <header style={{
          height: '46px',
          borderBottom: '1px solid var(--border-medium)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          background: 'var(--bg-surface)',
          zIndex: 40,
          flexShrink: 0
        }}>
          {/* Logo & Brand */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '20px',
              height: '20px',
              borderRadius: '4px',
              background: 'var(--accent-terracotta)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              fontSize: '0.72rem',
              fontWeight: 700,
              fontFamily: 'var(--font-sans)'
            }}>
              ◈
            </div>
            <span style={{
              fontFamily: 'var(--font-serif)',
              fontSize: '1.05rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
              letterSpacing: '-0.01em'
            }}>
              ContractLens
            </span>
          </div>

          {/* Calm Mode Navigation Tabs */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
            {[
              { id: 'chat', label: 'Investigate', icon: MessageSquare },
              { id: 'viewer', label: 'Document Viewer', icon: FileText },
              { id: 'portfolio', label: 'Portfolio Overview', icon: Layers },
            ].map(tab => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  data-testid={`tab-${tab.id}`}
                  onClick={() => setActiveTab(tab.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    border: 'none',
                    background: isActive ? 'var(--accent-terracotta-dim)' : 'transparent',
                    color: isActive ? 'var(--accent-terracotta)' : 'var(--text-secondary)',
                    fontWeight: isActive ? 600 : 500,
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)'
                  }}
                  onMouseEnter={e => !isActive && (e.currentTarget.style.color = 'var(--text-primary)')}
                  onMouseLeave={e => !isActive && (e.currentTarget.style.color = 'var(--text-secondary)')}
                >
                  <Icon size={14} color={isActive ? 'var(--accent-terracotta)' : 'currentColor'} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              data-testid="theme-toggle-btn"
              onClick={toggleTheme}
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '28px',
                height: '28px',
                borderRadius: '6px',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-medium)',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'all var(--transition-fast)'
              }}
            >
              {theme === 'dark' ? (
                <Sun size={14} color="var(--accent-amber)" />
              ) : (
                <Moon size={14} color="var(--text-secondary)" />
              )}
            </button>

            <button
              data-testid="new-investigation-btn"
              onClick={handleStartNewInvestigation}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '4px 10px',
                borderRadius: '6px',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-medium)',
                color: 'var(--text-primary)',
                fontSize: '0.76rem',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all var(--transition-fast)'
              }}
              title="Start a fresh investigation session"
            >
              <Plus size={12} color="var(--accent-terracotta)" />
              <span>New Investigation</span>
            </button>

            {contracts.length > 0 && (
              <button
                data-testid="clear-corpus-btn"
                onClick={handleResetWorkspace}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-medium)',
                  color: 'var(--text-secondary)',
                  fontSize: '0.76rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)'
                }}
                title="Wipe current loaded contracts and start with a fresh workspace"
              >
                <RotateCcw size={11} color="var(--text-muted)" />
                <span>Clear Workspace</span>
              </button>
            )}

            <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              {contracts.length === 0 ? '0 contracts (Clean)' : `${contracts.length} contract${contracts.length === 1 ? '' : 's'}`}
            </span>
          </div>
        </header>

        {/* Ambient Canvas Layer */}
        <AmbientField agentState={agentActivityState} />

        {/* Main Workspace Stage */}
        {activeTab === 'chat' ? (
          <ChatView
            chatHistory={chatHistory}
            queryInput={queryInput}
            setQueryInput={setQueryInput}
            queryLoading={queryLoading}
            agentActivityState={agentActivityState}
            scopedContractIds={scopedContractIds}
            setScopedContractIds={setScopedContractIds}
            isContractPickerOpen={isContractPickerOpen}
            setIsContractPickerOpen={setIsContractPickerOpen}
            contracts={contracts}
            onSendQuery={handleSendQuery}
            activeEvidenceCitation={activeEvidenceCitation}
            setActiveEvidenceCitation={setActiveEvidenceCitation}
            onOpenInViewer={handleOpenInViewer}
            onDeleteContract={handleDeleteContract}
            onUploadSuccess={() => {
              fetchInitialData();
            }}
            chatEndRef={chatEndRef}
          />
        ) : (
          <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '260px 1fr', height: 'calc(100vh - 46px)', overflow: 'hidden' }}>
            {/* Shared Document Navigator Sidebar */}
            <aside style={{
              background: 'var(--bg-surface)',
              borderRight: '1px solid var(--border-medium)',
              overflowY: 'auto',
              padding: '12px 10px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}>
              <div style={{ padding: '0 4px 8px' }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'var(--bg-canvas)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: '6px',
                  padding: '4px 8px'
                }}>
                  <Search size={12} color="var(--text-muted)" />
                  <input
                    type="text"
                    placeholder="Filter contracts..."
                    value={sidebarFilter}
                    onChange={e => setSidebarFilter(e.target.value)}
                    style={{
                      border: 'none',
                      background: 'transparent',
                      color: 'var(--text-primary)',
                      fontSize: '0.75rem',
                      width: '100%',
                      outline: 'none'
                    }}
                  />
                </div>
              </div>

              {contracts
                .filter(c => !sidebarFilter || c.filename.toLowerCase().includes(sidebarFilter.toLowerCase()))
                .map(c => {
                  const isSelected = selectedDocId === c.document_id;
                  const isAmendment = c.filename.toLowerCase().includes('amendment');
                  return (
                    <div
                      key={c.document_id}
                      onClick={() => {
                        setSelectedDocId(c.document_id);
                        if (activeTab !== 'viewer' && activeTab !== 'contracts') {
                          setActiveTab('viewer');
                        }
                      }}
                      style={{
                        padding: '8px 10px',
                        borderRadius: '6px',
                        background: isSelected ? 'var(--accent-terracotta-dim)' : 'transparent',
                        border: isSelected ? '1px solid var(--accent-terracotta-border)' : '1px solid transparent',
                        cursor: 'pointer',
                        transition: 'all var(--transition-fast)'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                        <span style={{ fontSize: '0.8rem', fontWeight: isSelected ? 600 : 500, color: isSelected ? 'var(--accent-terracotta)' : 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, marginRight: '8px' }}>
                          {c.filename}
                        </span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          {isAmendment ? (
                            <span className="badge badge-amber" style={{ fontSize: '0.65rem' }}>AMEND</span>
                          ) : (
                            <span className="badge badge-terracotta" style={{ fontSize: '0.65rem' }}>{c.document_id}</span>
                          )}
                          <button
                            type="button"
                            title="Remove contract"
                            onClick={(e) => handleDeleteContract(c.document_id, e)}
                            style={{
                              background: 'transparent',
                              border: 'none',
                              color: 'var(--text-muted)',
                              cursor: 'pointer',
                              padding: '2px 4px',
                              borderRadius: '4px',
                              display: 'inline-flex',
                              alignItems: 'center',
                              opacity: 0.7,
                              transition: 'all 0.15s ease'
                            }}
                            onMouseEnter={e => {
                              e.currentTarget.style.opacity = '1';
                              e.currentTarget.style.color = 'var(--accent-ruby, #ef4444)';
                            }}
                            onMouseLeave={e => {
                              e.currentTarget.style.opacity = '0.7';
                              e.currentTarget.style.color = 'var(--text-muted)';
                            }}
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                        {c.contract_type} • {c.page_count} pages
                      </div>
                    </div>
                  );
                })}
            </aside>

            {/* Main Stage Outlet */}
            <main style={{ overflowY: 'auto', padding: '28px', position: 'relative' }}>
              {activeTab === 'portfolio' && (
                <PortfolioView
                  portfolioData={portfolioData}
                  riskData={riskData}
                  contracts={contracts}
                  onSelectContract={(docId) => {
                    setSelectedDocId(docId);
                    setActiveTab('viewer');
                  }}
                  onInspectContract={(docId) => {
                    setSelectedDocId(docId);
                    setActiveTab('viewer');
                  }}
                  onCompareAmendment={loadAmendmentComparison}
                />
              )}
              {activeTab === 'viewer' && (
                <CanonicalViewer
                  contractDetail={contractDetail}
                  highlightedBlockId={highlightedBlockId}
                  amendmentData={amendmentData}
                  onCompareAmendment={loadAmendmentComparison}
                  onDeleteContract={handleDeleteContract}
                />
              )}
            </main>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}
