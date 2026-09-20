import React from 'react';
import { Sparkles, Search, Layers, ShieldCheck, GitCommit } from 'lucide-react';

export default function AgentStatus({ state = 'investigating' }) {
  const getStatusDetails = () => {
    switch (state) {
      case 'understanding':
        return { text: 'Analyzing contractual intent & party ontology...', icon: Sparkles, color: 'var(--accent-terracotta)' };
      case 'comparing':
        return { text: 'Aligning agreement versions & auditing modifications...', icon: GitCommit, color: 'var(--signal-cyan)' };
      case 'obligations':
        return { text: 'Resolving contractual commitments & temporal anchors...', icon: Layers, color: 'var(--signal-warning)' };
      case 'verifying':
        return { text: 'Verifying evidence boundaries & coordinate bounding boxes...', icon: ShieldCheck, color: 'var(--signal-success)' };
      case 'investigating':
        return { text: 'Investigating canonical contract evidence...', icon: Search, color: 'var(--accent-terracotta)' };
      default:
        // Handle dynamic tool action labels (e.g. "Searching Foxconn agreement evidence...")
        return { text: state, icon: Search, color: 'var(--accent-terracotta)' };
    }
  };

  const { text, icon: Icon, color } = getStatusDetails();

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '10px',
      padding: '8px 16px',
      background: 'var(--bg-surface-elevated)',
      border: '1px solid var(--border-medium)',
      borderRadius: '8px',
      boxShadow: 'var(--shadow-ambient)',
      marginBottom: '16px'
    }}>
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '14px', height: '14px' }}>
        <div
          className="animate-dynamic-circle"
          style={{
            position: 'absolute',
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: color,
          }}
        />
        <div
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: color,
            zIndex: 1
          }}
        />
      </div>
      <Icon size={14} color={color} />
      <span style={{
        fontSize: '0.82rem',
        color: 'var(--text-secondary)',
        fontFamily: 'var(--font-sans)',
        fontWeight: 500
      }}>
        {text}
      </span>
    </div>
  );
}
