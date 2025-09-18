import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { Message, ChatState } from './types/chat';
import { chatService } from './services/api';

function App() {
  const [chatState, setChatState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
  });
  const [inputMessage, setInputMessage] = useState('');
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatState.messages, chatState.isLoading]);

  // Check backend connection on startup
  useEffect(() => {
    const checkBackend = async () => {
      try {
        await chatService.healthCheck();
        setBackendStatus('connected');
      } catch (error) {
        setBackendStatus('disconnected');
      }
    };
    checkBackend();
  }, []);

  const sendMessage = async () => {
    if (!inputMessage.trim() || chatState.isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      isUser: true,
      timestamp: new Date(),
    };

    setChatState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
      error: null,
    }));

    setInputMessage('');

    try {
      const response = await chatService.sendMessage(inputMessage);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.response,
        isUser: false,
        timestamp: new Date(),
        contextUsed: response.context_used,
        sources: response.sources,
      };

      setChatState(prev => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
        isLoading: false,
      }));
    } catch (error) {
      setChatState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Failed to send message. Please try again.',
      }));
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Personal RAG Chatbot</h1>
        <div className={`status-indicator ${backendStatus}`}>
          Backend: {backendStatus}
        </div>
      </header>
      
      <main className="chat-container">
        <div className="messages-area">
          {chatState.messages.map((message) => (
            <div key={message.id} className={`message ${message.isUser ? 'user' : 'assistant'}`}>
              <div className="message-content">
                {message.content}
                {message.contextUsed && (
                  <div className="context-indicator">
                    🧠 Used RAG context
                  </div>
                )}
              </div>
              <div className="message-timestamp">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          ))}
          
          {chatState.isLoading && (
            <div className="message assistant loading">
              <div className="message-content">Thinking...</div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          {chatState.error && (
            <div className="error-message">{chatState.error}</div>
          )}
          
          <div className="input-container">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask me about my experience and projects..."
              disabled={chatState.isLoading || backendStatus !== 'connected'}
            />
            <button 
              onClick={sendMessage}
              disabled={chatState.isLoading || backendStatus !== 'connected' || !inputMessage.trim()}
            >
              Send
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
