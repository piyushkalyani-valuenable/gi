/**
 * Chat message component
 */
import React from 'react';
import { Message } from '../types';
import './ChatMessage.css';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`message ${isUser ? 'message-user' : 'message-bot'}`}>
      <div className="message-header">
        <strong>{isUser ? 'You' : 'Bot'}</strong>
        {message.fileName && (
          <span className="message-file"> (File: {message.fileName})</span>
        )}
      </div>
      <div className="message-content">
        {message.content}
      </div>
    </div>
  );
};
