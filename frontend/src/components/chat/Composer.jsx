import React, { useRef, useEffect } from 'react';
import { ArrowUp, Layers, X, ChevronDown, CheckSquare, Square, Trash2, Check } from 'lucide-react';

/**
 * Composer: Claude-inspired spacious, calm input surface
 * Warm rounded card container with terracotta send button and scoped contract context pills.
 */
export default function Composer({
  queryInput,
  setQueryInput,
  onSend,
  queryLoading,
  contracts = [],
  scopedContractIds = [],
  onToggleContractScope,
  onSelectAllScope,
  onClearScope,
  onDeleteContract,
  isContractPickerOpen,
  setIsContractPickerOpen
}) {
  const dropdownRef = useRef(null);

  useEffect(() => {
    if (!isContractPickerOpen) return;
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsContractPickerOpen(false);
      }
    };
    const handleEscape = (e) => {
      if (e.key === 'Escape') setIsContractPickerOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isContractPickerOpen, setIsContractPickerOpen]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend(e);
    }
  };

  return (
    <div style={{
      width: '100%',
      maxWidth: '780px',
      margin: '0 auto',
      position: 'relative'
    }}>
      {/* Contract Scope Picker Dropdown */}
      {isContractPickerOpen && (
        <div 
          ref={dropdownRef}
          style={{
          position: 'absolute',
          bottom: '100%',
          left: 0,
          right: 0,
          marginBottom: '10px',
          background: 'var(--bg-surface-elevated)',
          border: '1px solid var(--border-medium)',
          borderRadius: '12px',
          boxShadow: 'var(--shadow-floating)',
          maxHeight: '260px',
          overflowY: 'auto',
          padding: '14px',
          zIndex: 50
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '12px',
            paddingBottom: '8px',
            borderBottom: '1px solid var(--border-subtle)',
            flexWrap: 'wrap',
            gap: '8px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.74rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Agreement Scope ({scopedContractIds.length === 0 ? `All ${contracts.length} Active` : `${scopedContractIds.length} of ${contracts.length} Selected`})
              </span>
            </div>

            {/* Quick Bulk Actions */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                type="button"
                onClick={() => {
                  if (onClearScope) onClearScope();
                }}
                style={{
                  background: 'transparent',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '4px',
                  padding: '2px 8px',
                  fontSize: '0.68rem',
                  fontFamily: 'var(--font-mono)',
                  color: scopedContractIds.length === 0 ? 'var(--accent-terracotta)' : 'var(--text-muted)',
                  cursor: 'pointer'
                }}
              >
                Select All
              </button>

              <button
                type="button"
                onClick={() => {
                  // Select none (or toggle)
                  if (contracts.length > 0) {
                    contracts.forEach(c => {
                      if (scopedContractIds.includes(c.document_id)) {
                        onToggleContractScope(c.document_id);
                      }
                    });
                  }
                }}
                style={{
                  background: 'transparent',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '4px',
                  padding: '2px 8px',
                  fontSize: '0.68rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-muted)',
                  cursor: 'pointer'
                }}
              >
                Clear Selection
              </button>

              <button
                type="button"
                onClick={() => setIsContractPickerOpen(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', marginLeft: '4px' }}
                title="Close"
              >
                <X size={15} />
              </button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '8px' }}>
            {contracts.map(c => {
              const isSelected = scopedContractIds.includes(c.document_id);
              return (
                <div
                  key={c.document_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    background: isSelected ? 'var(--accent-terracotta-dim)' : 'var(--bg-surface)',
                    border: `1px solid ${isSelected ? 'var(--accent-terracotta-border)' : 'var(--border-subtle)'}`,
                    transition: 'all var(--transition-fast)',
                    gap: '8px'
                  }}
                >
                  {/* Selectable Checkbox + Name Area */}
                  <div
                    onClick={() => onToggleContractScope(c.document_id)}
                    style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0, flex: 1, cursor: 'pointer' }}
                  >
                    <div style={{ color: isSelected ? 'var(--accent-terracotta)' : 'var(--text-muted)', display: 'flex', flexShrink: 0 }}>
                      {isSelected ? <CheckSquare size={16} /> : <Square size={16} />}
                    </div>

                    <div style={{ minWidth: 0 }}>
                      <div style={{
                        fontSize: '0.76rem',
                        fontWeight: 500,
                        color: isSelected ? 'var(--accent-terracotta)' : 'var(--text-primary)',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis'
                      }}>
                        {c.filename.replace('.pdf', '')}
                      </div>
                      <div style={{ fontSize: '0.66rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                        {c.document_id} • {c.contract_type || 'Contract'}
                      </div>
                    </div>
                  </div>

                  {/* Individual Remove / Delete Button */}
                  {onDeleteContract && (
                    <button
                      type="button"
                      title="Remove contract from workspace"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteContract(c.document_id, e);
                      }}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        padding: '4px',
                        borderRadius: '4px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        opacity: 0.65,
                        transition: 'all 0.15s ease'
                      }}
                      onMouseEnter={e => {
                        e.currentTarget.style.opacity = '1';
                        e.currentTarget.style.color = 'var(--accent-ruby, #ef4444)';
                        e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.opacity = '0.65';
                        e.currentTarget.style.color = 'var(--text-muted)';
                        e.currentTarget.style.background = 'transparent';
                      }}
                    >
                      <Trash2 size={13} />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Composer Box */}
      <form
        onSubmit={onSend}
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-medium)',
          borderRadius: '16px',
          boxShadow: 'var(--shadow-elevated)',
          padding: '12px 16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          transition: 'all var(--transition-fast)'
        }}
      >
        {/* Active Context Tokens Bar */}
        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '6px' }}>
          <button
            type="button"
            data-testid="scope-picker-toggle-btn"
            onClick={() => setIsContractPickerOpen(!isContractPickerOpen)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '8px',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-secondary)',
              fontSize: '0.75rem',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)'
            }}
          >
            <Layers size={12} color="var(--accent-terracotta)" />
            <span>Scope ({scopedContractIds.length === 0 ? (contracts.length === 0 ? 'No Contracts' : `All ${contracts.length}`) : scopedContractIds.length})</span>
            <ChevronDown size={12} />
          </button>

          {scopedContractIds.map(id => {
            const contract = contracts.find(c => c.document_id === id);
            const label = contract ? contract.filename.replace('.pdf', '') : id;
            return (
              <span
                key={id}
                data-testid="scoped-token-pill"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px',
                  padding: '3px 10px',
                  borderRadius: '8px',
                  background: 'var(--accent-terracotta-dim)',
                  border: '1px solid var(--accent-terracotta-border)',
                  color: 'var(--text-primary)',
                  fontSize: '0.74rem',
                  fontFamily: 'var(--font-mono)'
                }}
              >
                <span>{label}</span>
                <button
                  type="button"
                  onClick={() => onToggleContractScope(id)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--accent-terracotta)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    padding: 0
                  }}
                >
                  <X size={11} />
                </button>
              </span>
            );
          })}
        </div>

        {/* Text Input Row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <input
            type="text"
            placeholder="Reply to ContractLens or ask about contractual obligations..."
            value={queryInput}
            onChange={e => setQueryInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={queryLoading}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.94rem',
              outline: 'none',
              fontFamily: 'inherit',
              padding: '6px 0'
            }}
          />

          <button
            type="submit"
            data-testid="submit-query-button"
            disabled={queryLoading || !queryInput.trim()}
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '8px',
              background: queryInput.trim() && !queryLoading ? 'var(--accent-terracotta)' : 'var(--bg-surface-elevated)',
              border: '1px solid transparent',
              color: queryInput.trim() && !queryLoading ? '#ffffff' : 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: queryInput.trim() && !queryLoading ? 'pointer' : 'default',
              transition: 'all var(--transition-fast)'
            }}
            title="Send query"
          >
            <ArrowUp size={16} />
          </button>
        </div>
      </form>
    </div>
  );
}
