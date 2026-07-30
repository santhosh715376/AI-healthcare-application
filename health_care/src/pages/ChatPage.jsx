import React, { useState, useRef, useEffect } from 'react';
import ChatBubble from '../components/ChatBubble.jsx';

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `session-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');

    // Append user message immediately
    setMessages((prev) => [...prev, { role: 'user', content: userText }]);
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8000/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId, message: userText }),
      });
      const data = await res.json();

      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);
    } catch (err) {
      console.error('Chat Error:', err);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Connection error. Please check if the backend server is running.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = async () => {
    try {
      await fetch('http://localhost:8000/api/chat/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId }),
      });
    } catch (err) {
      console.error('Clear error:', err);
    }
    setMessages([]);
  };

  // State 1: Landing (Empty Session)
  if (messages.length === 0) {
    return (
      <div className="chat-landing-container">
        <h1 className="chat-landing-title">Where should we begin?</h1>
        <div className="chat-input-pill-large">
          <input
            type="text"
            className="chat-input-field"
            placeholder="Ask anything"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button className="chat-send-btn-circle" onClick={handleSend} disabled={!input.trim()}>
            ↑
          </button>
        </div>
      </div>
    );
  }

  // State 2: Active Chat Thread
  return (
    <div className="chat-thread-container">
      {/* Header bar with reset option */}
      <div className="chat-thread-header">
        <span>💬 Health AI Conversation</span>
        <button className="chat-reset-btn" onClick={handleClear}>
          🗑️ New Chat
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="chat-messages-area">
        {messages.map((msg, index) => (
          <ChatBubble key={index} role={msg.role} content={msg.content} />
        ))}
        {loading && (
          <div className="chat-message-row assistant">
            <div className="chat-reasoning-tag">Devising response...</div>
            <div className="chat-ai-content" style={{ color: '#9ca3af', fontStyle: 'italic' }}>
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Fixed Bottom Input Bar */}
      <div className="chat-bottom-bar-wrapper">
        <div className="chat-input-pill-bottom">
          <button className="chat-pill-icon">+</button>
          <input
            type="text"
            className="chat-input-field-bottom"
            placeholder="Write a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <div className="chat-input-actions">
            <span className="chat-model-badge">Groq Llama 3.3 70B</span>
            <button className="chat-send-btn-circle" onClick={handleSend} disabled={!input.trim() || loading}>
              ↑
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
