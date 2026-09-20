import React from 'react';
import { ArrowUpRight, GitCommit, ShieldAlert, Clock, Scale } from 'lucide-react';

/**
 * SuggestionChips: Claude-inspired minimal contextual prompt cards
 */
export default function SuggestionChips({ onSelectPrompt, contractsCount = 0 }) {
  const suggestions = contractsCount === 0 ? [
    {
      icon: Scale,
      label: 'Contract Overview',
      prompt: 'What is this contract about and who are the parties?',
      highlight: 'Understand purpose, deal context, and core relationship'
    },
    {
      icon: Clock,
      label: 'Payment Schedules',
      prompt: 'What are the net payment terms, billing cycles, and fee milestones?',
      highlight: 'Extract commercial obligations and late penalties'
    },
    {
      icon: ShieldAlert,
      label: 'Risk & Liabilities',
      prompt: 'Are there unlimited indemnities, uncapped liability, or renewal traps?',
      highlight: 'Scan for asymmetric termination & short cure periods'
    },
    {
      icon: GitCommit,
      label: 'Amendment Diffs',
      prompt: 'What terms were modified or superseded in the latest amendment?',
      highlight: 'Upload agreement & amendments to inspect clause diffs'
    }
  ] : [
    {
      icon: Scale,
      label: 'Contract Overview',
      prompt: 'What is the contract about and what are its key terms?',
      highlight: 'Holistic summary of agreement scope, parties, and deal structure'
    },
    {
      icon: Clock,
      label: 'Payment & Deadlines',
      prompt: 'What are the payment terms, billing terms, and key deadlines?',
      highlight: 'Commercial obligations, billing schedules & penalties'
    },
    {
      icon: ShieldAlert,
      label: 'Operational Risks',
      prompt: 'What operational risks, notice windows, and liabilities should I review?',
      highlight: 'Auto-renewals, notice windows & uncapped liabilities'
    },
    {
      icon: GitCommit,
      label: 'Amendment Diffs',
      prompt: 'What changed in the latest amendment or superseding agreement?',
      highlight: 'Clause-by-clause version alignment & full-force confirmation'
    }
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(2, 1fr)',
      gap: '12px',
      width: '100%',
      maxWidth: '780px',
      marginTop: '16px'
    }}>
      {suggestions.map((s, idx) => {
        const Icon = s.icon;
        return (
          <button
            key={idx}
            onClick={() => onSelectPrompt(s.prompt)}
            style={{
              padding: '16px 18px',
              borderRadius: '12px',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              cursor: 'pointer',
              textAlign: 'left',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              transition: 'all var(--transition-fast)'
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = 'var(--bg-surface-elevated)';
              e.currentTarget.style.borderColor = 'var(--border-medium)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = 'var(--bg-surface)';
              e.currentTarget.style.borderColor = 'var(--border-subtle)';
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '6px',
                  background: 'var(--accent-terracotta-dim)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Icon size={13} color="var(--accent-terracotta)" />
                </div>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {s.label}
                </span>
              </div>
              <ArrowUpRight size={14} color="var(--text-muted)" />
            </div>
            <div style={{ fontSize: '0.86rem', color: 'var(--text-primary)', fontWeight: 500, lineHeight: '1.4' }}>
              "{s.prompt}"
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-sans)' }}>
              {s.highlight}
            </div>
          </button>
        );
      })}
    </div>
  );
}
