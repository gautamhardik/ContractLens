import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Activity, Search, FileText, GitCommit, Layers } from 'lucide-react';

export default function AgentTraceTimeline({ trace }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!trace || !trace.steps || trace.steps.length === 0) {
    return null;
  }

  const getToolIcon = (toolName) => {
    switch (toolName) {
      case 'search_contract_evidence':
        return Search;
      case 'get_contract_details':
      case 'get_contract_timeline':
        return FileText;
      case 'compare_contract_amendments':
        return GitCommit;
      case 'get_contract_obligations':
      case 'query_contract_graph':
      default:
        return Layers;
    }
  };

  return (
    <div style={{
      margin: '6px 0 10px',
      fontSize: '0.76rem',
      fontFamily: 'var(--font-sans)',
    }}>
      {/* Subtle Disclosure Pill */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '3px 10px',
          borderRadius: '9999px',
          background: isOpen ? 'var(--accent-terracotta-dim)' : 'var(--bg-surface)',
          border: '1px solid var(--border-medium)',
          color: isOpen ? 'var(--accent-terracotta)' : 'var(--text-secondary)',
          cursor: 'pointer',
          fontWeight: 500,
          transition: 'all var(--transition-fast)'
        }}
        onMouseEnter={e => !isOpen && (e.currentTarget.style.borderColor = 'var(--accent-terracotta)')}
        onMouseLeave={e => !isOpen && (e.currentTarget.style.borderColor = 'var(--border-medium)')}
      >
        <Activity size={12} color="var(--accent-terracotta)" />
        <span>◈ {trace.steps.length} tool{trace.steps.length > 1 ? 's' : ''} executed ({trace.total_latency_ms.toFixed(1)}ms)</span>
        {isOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
      </button>

      {/* Expanded Step Timeline */}
      {isOpen && (
        <div style={{
          marginTop: '8px',
          padding: '10px 14px',
          borderRadius: '8px',
          background: 'var(--bg-surface-elevated)',
          border: '1px solid var(--border-medium)',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          boxShadow: 'var(--shadow-ambient)',
          animation: 'fadeInRise 0.2s ease-out'
        }}>
          {trace.steps.map((step, sIdx) => {
            const Icon = getToolIcon(step.tool_call?.tool_name);
            const label = step.action_summary || step.tool_call?.tool_name;
            return (
              <div key={sIdx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                <div style={{
                  padding: '3px',
                  borderRadius: '4px',
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  marginTop: '1px'
                }}>
                  <Icon size={11} color="var(--accent-terracotta)" />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.74rem' }}>
                      {step.tool_call?.tool_name}
                    </span>
                    <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {step.result?.latency_ms?.toFixed(1) || 0}ms
                    </span>
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    {label}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
