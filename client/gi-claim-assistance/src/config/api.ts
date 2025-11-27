/**
 * API configuration
 * 
 * Uses VITE_API_BASE_URL from .env if set, otherwise defaults to localhost:8000
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  HEALTH: `${API_BASE_URL}/api/health`,
  CHAT: `${API_BASE_URL}/api/chat`,
} as const;
