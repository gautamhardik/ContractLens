/**
 * ContractLens Frontend API Service Client
 * Connects directly to the frozen, high-performance FastAPI backend.
 */

import { API_BASE } from '../config/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error('Backend health check failed');
  return res.json();
}

export async function fetchPortfolio() {
  const res = await fetch(`${API_BASE}/api/portfolio`);
  if (!res.ok) throw new Error('Failed to load portfolio overview');
  return res.json();
}

export async function fetchContracts() {
  const res = await fetch(`${API_BASE}/api/contracts`);
  if (!res.ok) throw new Error('Failed to load contracts list');
  return res.json();
}

export async function fetchContractDetail(documentId) {
  const res = await fetch(`${API_BASE}/api/contracts/${documentId}`);
  if (!res.ok) throw new Error(`Failed to load details for ${documentId}`);
  return res.json();
}

export async function fetchRisks() {
  const res = await fetch(`${API_BASE}/api/risks`);
  if (!res.ok) throw new Error('Failed to load risk analysis');
  return res.json();
}

export async function fetchContractRisks(documentId) {
  const res = await fetch(`${API_BASE}/api/risks/${documentId}`);
  if (!res.ok) throw new Error(`Failed to load risks for ${documentId}`);
  return res.json();
}

export async function fetchAmendmentComparison(documentId) {
  const res = await fetch(`${API_BASE}/api/amendments/${documentId}`);
  if (!res.ok) throw new Error(`Failed to compare amendment for ${documentId}`);
  return res.json();
}

export async function queryAgent(query, documentId = null, conversationId = null) {
  const res = await fetch(`${API_BASE}/api/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, document_id: documentId, conversation_id: conversationId })
  });
  if (!res.ok) throw new Error('Agent investigation service error');
  return res.json();
}
