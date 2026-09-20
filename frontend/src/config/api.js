/**
 * Centralized API configuration for ContractLens frontend.
 * Resolves API_BASE dynamically from Vite environment variables or defaults to localhost.
 */

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';
