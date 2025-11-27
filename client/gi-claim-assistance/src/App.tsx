/**
 * Main App component
 */
import { useState, useEffect, useRef } from 'react';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { ApiService } from './services/api';
import type { Message, SessionStatus, InputType, ChatOption } from './types';
import './App.css';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<SessionStatus>('awaiting_policy');
  const [inputType, setInputType] = useState<InputType>('file');
  const [options, setOptions] = useState<ChatOption[]>([]);
  const chatboxRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatboxRef.current) {
      chatboxRef.current.scrollTop = chatboxRef.current.scrollHeight;
    }
  }, [messages]);

  const getStatusMessage = (): string => {
    switch (status) {
      case 'awaiting_policy':
        return '📄 Step 1: Upload your Insurance Policy Bond';
      case 'awaiting_document_choice':
        return '📋 Step 2: Choose document type (bill / prescription / both)';
      case 'awaiting_bill':
        return '🧾 Upload your Hospital Bill';
      case 'awaiting_prescription':
        return '💊 Upload your Prescription';
      case 'awaiting_both_bill':
        return '🧾 Upload your Hospital Bill (1/2)';
      case 'awaiting_both_prescription':
        return '💊 Upload your Prescription (2/2)';
      case 'completed':
        return '✅ Assessment Complete! Type "reset" to start new.';
      default:
        return '';
    }
  };

  const handleSend = async (userInput: string, file?: File) => {
    // Add user message
    const userMessage: Message = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: file ? `Uploaded: ${file.name}` : userInput,
      timestamp: new Date(),
      fileName: file?.name,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await ApiService.sendMessage(sessionId, userInput, file);

      // Update session state from response
      if (response.session_id) {
        setSessionId(response.session_id);
      }
      if (response.status) {
        setStatus(response.status);
      }
      if (response.input_type) {
        setInputType(response.input_type);
      }
      setOptions(response.options || []);

      // Add bot response
      const botMessage: Message = {
        id: `bot_${Date.now()}`,
        role: 'bot',
        content: response.reply,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        role: 'bot',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    if (confirm('Are you sure you want to start a new session? This will clear all messages.')) {
      setSessionId(null);
      setStatus('awaiting_policy');
      setMessages([]);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>GI Claim Assistance</h1>
        <button className="reset-button" onClick={handleReset}>
          New Session
        </button>
      </header>

      {/* Status Banner */}
      <div className={`status-banner status-${status}`}>
        {getStatusMessage()}
      </div>

      <div className="chatbox" ref={chatboxRef}>
        {messages.length === 0 && (
          <div className="welcome-message">
            <h2>Welcome to GI Claim Assistance</h2>
            <p>Upload your documents to process your insurance claim:</p>
            <ol>
              <li><strong>Step 1:</strong> Upload your Insurance Policy Bond</li>
              <li><strong>Step 2:</strong> Choose: Bill, Prescription, or Both</li>
              <li><strong>Step 3:</strong> Upload selected documents</li>
            </ol>
            <p>
              <strong>Bill:</strong> Full claim calculation<br />
              <strong>Prescription:</strong> Price lookup from ABHA/Internal DB/AI
            </p>
          </div>
        )}

        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {isLoading && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>Processing...</span>
          </div>
        )}
      </div>

      <div className="input-container">
        <ChatInput
          onSend={handleSend}
          disabled={isLoading}
          inputType={inputType}
          options={options}
        />
      </div>
    </div>
  );
}

export default App;
