// frontend/src/components/Chat/TypingIndicator.jsx
import React from 'react';
import './TypingIndicator.css';

const TypingIndicator = () => {
  return (
    <div className="chat-message assistant">
      <div className="message-content">
        <div className="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <div className="typing-text">AI is thinking...</div>
      </div>
    </div>
  );
};

export default TypingIndicator;