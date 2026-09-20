import React, { useState } from 'react';
import { FileText, CheckCircle2, Calendar, ShieldAlert, Globe, Clock, BarChart3, AlertTriangle, BookOpen } from 'lucide-react';
import ContractsRegistryView from '../contracts/ContractsRegistryView';
import RisksView from '../risks/RisksView';

export default function PortfolioView({ portfolioData, riskData, contracts, onSelectContract, onInspectContract, onCompareAmendment }) {
  const [activeSubTab, setActiveSubTab] = useState('analytics');

  const totalSignals = riskData?.contract_reports?.reduce((sum, r) => sum + (r.total_signals || 0), 0) || 0;
  const totalContracts = contracts?.length || 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h1 className="editorial-title" style={{ fontSize: '1.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px', letterSpacing: '-0.025em', fontFamily: 'var(--font-sans)' }}>
          Portfolio Intelligence Dashboard
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.94rem', lineHeight: '1.6' }}>
          Aggregate operational metrics, governing laws, payment schedules, and counterparty networks.
        </p>
      </div>

      {/* Sub-Navigation Switcher */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px', marginBottom: '8px' }}>
        <button
          onClick={() => setActiveSubTab('analytics')}
          style={{
            background: 'none', border: 'none', padding: '8px 16px', cursor: 'pointer',
            fontSize: '0.9rem', fontWeight: activeSubTab === 'analytics' ? 600 : 400,
            color: activeSubTab === 'analytics' ? 'var(--text-primary)' : 'var(--text-secondary)',
            borderBottom: activeSubTab === 'analytics' ? '2px solid var(--accent-terracotta)' : '2px solid transparent',
            display: 'flex', alignItems: 'center', gap: '8px'
          }}
        >
          <BarChart3 size={16} /> Analytics & Metrics
        </button>
        <button
          onClick={() => setActiveSubTab('risks')}
          style={{
            background: 'none', border: 'none', padding: '8px 16px', cursor: 'pointer',
            fontSize: '0.9rem', fontWeight: activeSubTab === 'risks' ? 600 : 400,
            color: activeSubTab === 'risks' ? 'var(--text-primary)' : 'var(--text-secondary)',
            borderBottom: activeSubTab === 'risks' ? '2px solid var(--accent-terracotta)' : '2px solid transparent',
            display: 'flex', alignItems: 'center', gap: '8px'
          }}
        >
          <AlertTriangle size={16} /> Operational Risks ({totalSignals})
        </button>
        <button
          onClick={() => setActiveSubTab('registry')}
          style={{
            background: 'none', border: 'none', padding: '8px 16px', cursor: 'pointer',
            fontSize: '0.9rem', fontWeight: activeSubTab === 'registry' ? 600 : 400,
            color: activeSubTab === 'registry' ? 'var(--text-primary)' : 'var(--text-secondary)',
            borderBottom: activeSubTab === 'registry' ? '2px solid var(--accent-terracotta)' : '2px solid transparent',
            display: 'flex', alignItems: 'center', gap: '8px'
          }}
        >
          <BookOpen size={16} /> Agreement Registry ({totalContracts})
        </button>
      </div>

      {activeSubTab === 'analytics' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* KPI Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
            {[
              { label: 'Total Agreements', value: portfolioData?.total_contracts || 0, desc: 'Indexed in Canonical Model', icon: FileText, color: 'var(--accent-terracotta)' },
              { label: 'Extracted Obligations', value: portfolioData?.total_obligations || 0, desc: 'Provenanced Commitments', icon: CheckCircle2, color: 'var(--signal-success)' },
              { label: 'Lifecycle Milestones', value: portfolioData?.total_events || 0, desc: 'Notice & Term Deadlines', icon: Calendar, color: 'var(--accent-amber)' },
              { label: 'High Risk Flags', value: riskData?.high_risk_contracts || 0, desc: 'Auto-Renewals & Caps', icon: ShieldAlert, color: 'var(--signal-danger)' },
            ].map((kpi, idx) => {
              const Icon = kpi.icon;
              return (
                <div key={idx} className="glass-panel" style={{ padding: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>{kpi.label}</span>
                    <Icon size={18} color={kpi.color} />
                  </div>
                  <div style={{ fontSize: '2.2rem', fontWeight: 600, margin: '8px 0', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', letterSpacing: '-0.03em' }}>{kpi.value}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{kpi.desc}</div>
                </div>
              );
            })}
          </div>

          {/* Distributions Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div className="glass-panel" style={{ padding: '22px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Globe size={16} color="var(--accent-terracotta)" /> Governing Law Distribution
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {portfolioData?.governing_laws && Object.entries(portfolioData.governing_laws).map(([law, count]) => (
                  <div key={law} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{law}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '50%' }}>
                      <div style={{ flex: 1, height: '6px', background: 'rgba(245, 242, 235, 0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${(count / 18) * 100}%`, height: '100%', background: 'var(--accent-terracotta)', borderRadius: '3px' }} />
                      </div>
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, minWidth: '20px' }}>{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '22px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Clock size={16} color="var(--signal-success)" /> Commercial Payment Terms
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {portfolioData?.payment_terms && Object.entries(portfolioData.payment_terms).map(([term, count]) => (
                  <div key={term} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{term}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '50%' }}>
                      <div style={{ flex: 1, height: '6px', background: 'rgba(245, 242, 235, 0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${(count / 18) * 100}%`, height: '100%', background: 'var(--signal-success)', borderRadius: '3px' }} />
                      </div>
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, minWidth: '20px' }}>{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeSubTab === 'risks' && (
        <div style={{ marginTop: '-20px' }}>
          <RisksView riskData={riskData} onInspectContract={onInspectContract} />
        </div>
      )}

      {activeSubTab === 'registry' && (
        <div style={{ marginTop: '-20px' }}>
          <ContractsRegistryView contracts={contracts} onSelectContract={onSelectContract} onCompareAmendment={onCompareAmendment} />
        </div>
      )}
    </div>
  );
}
