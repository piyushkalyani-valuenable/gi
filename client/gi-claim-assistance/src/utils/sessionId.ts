/**
 * Session ID management utilities
 */

const SESSION_ID_KEY = 'gi_claim_session_id';

/**
 * Generate a unique session ID
 */
export function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Get or create session ID
 */
export function getSessionId(): string {
  let sessionId = sessionStorage.getItem(SESSION_ID_KEY);
  
  if (!sessionId) {
    sessionId = generateSessionId();
    sessionStorage.setItem(SESSION_ID_KEY, sessionId);
  }
  
  return sessionId;
}

/**
 * Clear session ID (start new session)
 */
export function clearSessionId(): void {
  sessionStorage.removeItem(SESSION_ID_KEY);
}
