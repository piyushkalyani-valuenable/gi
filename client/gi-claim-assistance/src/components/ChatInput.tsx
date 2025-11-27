/**
 * Chat input component - handles file upload, text input, and option buttons
 */
import React, { useState, useRef } from 'react';
import type { InputType, ChatOption } from '../types';
import './ChatInput.css';

interface ChatInputProps {
  onSend: (message: string, file?: File) => void;
  disabled: boolean;
  inputType: InputType;
  options: ChatOption[];
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled,
  inputType,
  options,
}) => {
  const [message, setMessage] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (inputType === 'file' && !selectedFile) {
      alert('Please select a file to upload.');
      return;
    }

    if (inputType === 'text' && !message.trim()) {
      alert('Please enter a message.');
      return;
    }

    onSend(message, selectedFile || undefined);
    setMessage('');
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleOptionClick = (value: string) => {
    onSend(value, undefined);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };

  // Render options as buttons
  if (inputType === 'options' && options.length > 0) {
    return (
      <div className="chat-options-container">
        {options.map((option) => (
          <button
            key={option.value}
            className="chat-option-button"
            onClick={() => handleOptionClick(option.value)}
            disabled={disabled}
          >
            {option.label}
          </button>
        ))}
      </div>
    );
  }

  // Render text input
  if (inputType === 'text') {
    return (
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input-text"
          placeholder="Type your message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          disabled={disabled}
          autoComplete="off"
        />
        <button type="submit" className="chat-input-button" disabled={disabled}>
          {disabled ? 'Processing...' : 'Send'}
        </button>
      </form>
    );
  }

  // Render file upload (default)
  return (
    <form className="chat-input-form" onSubmit={handleSubmit}>
      <div className="file-select-area" onClick={handleFileButtonClick}>
        <input
          ref={fileInputRef}
          type="file"
          className="chat-input-file-hidden"
          accept=".pdf,.png,.jpg,.jpeg"
          onChange={handleFileChange}
          disabled={disabled}
        />
        <span className="file-select-text">
          {selectedFile ? `📎 ${selectedFile.name}` : '📁 Click to select file...'}
        </span>
      </div>
      <button type="submit" className="chat-input-button" disabled={disabled}>
        {disabled ? 'Processing...' : 'Upload'}
      </button>
    </form>
  );
};
