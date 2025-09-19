// frontend/src/components/Chat/ChatInput.jsx
import React, { useState, useRef, useEffect } from 'react';
import { apiUtils } from '../../services/api';
import './ChatInput.css';

const ChatInput = ({ onSendMessage, isLoading, disabled }) => {
  const [message, setMessage] = useState('');
  const [isWarming, setIsWarming] = useState(false);
  const textareaRef = useRef(null);
  const warmupTimeoutRef = useRef(null);
  const hasWarmedUpRef = useRef(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !isLoading && !disabled) {
      onSendMessage(message);
      setMessage('');
      hasWarmedUpRef.current = false; // Reset for next conversation
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Warmup function
  const warmupModel = async () => {
    if (hasWarmedUpRef.current || isWarming) return;
    
    setIsWarming(true);
    hasWarmedUpRef.current = true;
    
    try {
      // Send a minimal warmup request
      await fetch('http://localhost:8000/api/chat/warmup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ warmup: true })
      });
      console.log('🔥 Model warmed up');
    } catch (error) {
      console.log('Warmup failed, but continuing:', error.message);
    } finally {
      setIsWarming(false);
    }
  };

  // Trigger warmup after user starts typing
  const handleInputChange = (e) => {
    const newValue = e.target.value;
    setMessage(newValue);
    
    // If user is typing and hasn't warmed up yet
    if (newValue.length > 2 && !hasWarmedUpRef.current && !isWarming) {
      // Clear any existing timeout
      if (warmupTimeoutRef.current) {
        clearTimeout(warmupTimeoutRef.current);
      }
      
      // Warmup after user pauses typing for 500ms
      warmupTimeoutRef.current = setTimeout(() => {
        warmupModel();
      }, 500);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
    }
  }, [message]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (warmupTimeoutRef.current) {
        clearTimeout(warmupTimeoutRef.current);
      }
    };
  }, []);

  return (
    <form onSubmit={handleSubmit} className="chat-input-form">
      <div className="input-container">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          placeholder={
            isWarming 
              ? "Preparing AI... continue typing" 
              : "Type your message... (Enter to send, Shift+Enter for new line)"
          }
          disabled={isLoading || disabled}
          className={`message-textarea ${isWarming ? 'warming' : ''}`}
          rows="1"
        />
        <button
          type="submit"
          disabled={isLoading || disabled || !message.trim()}
          className="send-button"
        >
          {isLoading ? (
            <div className="loading-spinner">⏳</div>
          ) : isWarming ? (
            <div className="warming-indicator">🔥</div>
          ) : (
            '➤'
          )}
        </button>
      </div>
    </form>
  );
};

export default ChatInput;