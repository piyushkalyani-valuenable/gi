/**
 * API service for backend communication
 */
import { API_ENDPOINTS } from '../config/api';
import type { ChatResponse } from '../types';

export class ApiService {
  /**
   * Send chat message with optional file upload
   */
  static async sendMessage(
    sessionId: string | null,
    userInput?: string,
    file?: File
  ): Promise<ChatResponse> {
    const formData = new FormData();

    // Only append session_id if we have one
    if (sessionId) {
      formData.append('session_id', sessionId);
    }

    // Always append user_input (even if empty, backend expects it)
    formData.append('user_input', userInput || '');

    if (file) {
      formData.append('file', file);
    }

    const response = await fetch(API_ENDPOINTS.CHAT, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  /**
   * Check API health
   */
  static async checkHealth(): Promise<{ status: string; service: string }> {
    const response = await fetch(API_ENDPOINTS.HEALTH);

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    return response.json();
  }
}
