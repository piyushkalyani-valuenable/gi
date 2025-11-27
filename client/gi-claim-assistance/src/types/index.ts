/**
 * Type definitions for the application
 */

export type SessionStatus =
  | 'awaiting_policy'
  | 'awaiting_document_choice'
  | 'awaiting_bill'
  | 'awaiting_prescription'
  | 'awaiting_both_bill'
  | 'awaiting_both_prescription'
  | 'completed';

export type InputType = 'file' | 'text' | 'options';

export interface ChatOption {
  value: string;
  label: string;
}

export interface Message {
  id: string;
  role: 'user' | 'bot';
  content: string;
  timestamp: Date;
  fileName?: string;
}

export interface ChatResponse {
  reply: string;
  session_id: string;
  status: SessionStatus;
  options?: ChatOption[];
  input_type: InputType;
}
