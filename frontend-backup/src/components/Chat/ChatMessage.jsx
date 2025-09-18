// frontend/src/components/Chat/ChatMessage.jsx
import React, { useState } from 'react';
import { learningAPI } from '../../services/api';
import './ChatMessage.css';

const ChatMessage = ({ message, onFeedback }) => {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const handleFeedback = async (helpful) => {
    try {
      await learningAPI.submitFeedback(message.id, helpful);
      setFeedbackSubmitted(true);
      setShowFeedback(false);
      if (onFeedback) onFeedback(message.id, helpful);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  return (
    <div className={`chat-message ${message.type}`}>
      <div className="message-content">
        <div className="message-text">{message.content}</div>
        <div className="message-info">
          <span className="message-time">{formatTimestamp(message.timestamp)}</span>
          {message.model && (
            <span className="message-model">
              {message.provider}:{message.model}
            </span>
          )}
          {message.type === 'assistant' && !feedbackSubmitted && (
            <button
              className="feedback-btn"
              onClick={() => setShowFeedback(!showFeedback)}
              title="Provide feedback"
            >
              💭
            </button>
          )}
        </div>
        
        {showFeedback && (
          <div className="feedback-panel">
            <span>Was this response helpful?</span>
            <div className="feedback-buttons">
              <button
                className="feedback-btn helpful"
                onClick={() => handleFeedback(true)}
              >
                👍 Yes
              </button>
              <button
                className="feedback-btn not-helpful"
                onClick={() => handleFeedback(false)}
              >
                👎 No
              </button>
            </div>
          </div>
        )}
        
        {feedbackSubmitted && (
          <div className="feedback-submitted">
            ✅ Feedback recorded
          </div>
        )}
      </div>
    </div>
  );
};