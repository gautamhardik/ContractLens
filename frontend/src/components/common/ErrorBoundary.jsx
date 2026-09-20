import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ContractLens React ErrorBoundary caught an exception:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = window.location.pathname;
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'var(--bg-canvas, #FBF9F5)',
          padding: '24px',
          textAlign: 'center',
          fontFamily: 'var(--font-sans, system-ui, sans-serif)'
        }}>
          <div style={{
            background: 'var(--bg-surface-elevated, #FFFFFF)',
            border: '1px solid var(--border-medium, #E8E2D8)',
            borderRadius: '12px',
            padding: '36px',
            maxWidth: '520px',
            boxShadow: 'var(--shadow-ambient, 0 4px 20px rgba(0,0,0,0.05))'
          }}>
            <div style={{
              display: 'inline-flex',
              padding: '12px',
              borderRadius: '50%',
              background: 'rgba(197, 48, 48, 0.1)',
              marginBottom: '16px'
            }}>
              <AlertTriangle size={32} color="var(--signal-danger, #C53030)" />
            </div>
            <h2 style={{
              fontSize: '1.4rem',
              fontWeight: 600,
              color: 'var(--text-primary, #1A1917)',
              marginBottom: '8px'
            }}>
              Workspace Recovery Triggered
            </h2>
            <p style={{
              fontSize: '0.88rem',
              color: 'var(--text-secondary, #5C5750)',
              lineHeight: '1.5',
              marginBottom: '24px'
            }}>
              ContractLens encountered an unexpected client state. All contract evidence and backend states remain secure.
            </p>
            <button
              onClick={this.handleReset}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 20px',
                borderRadius: '8px',
                background: 'var(--accent-terracotta, #CC785C)',
                color: '#FFFFFF',
                fontSize: '0.88rem',
                fontWeight: 500,
                border: 'none',
                cursor: 'pointer',
                transition: 'opacity 0.2s'
              }}
              onMouseEnter={e => e.currentTarget.style.opacity = '0.9'}
              onMouseLeave={e => e.currentTarget.style.opacity = '1.0'}
            >
              <RefreshCw size={16} />
              <span>Reload Workspace</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
