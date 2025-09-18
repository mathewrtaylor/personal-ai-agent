// frontend/src/components/Chat/ChatContainer.jsx
import React, { useState, useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import TypingIndicator from './TypingIndicator';
import { chatAPI } from '../../services/api';
import './ChatContainer.css';

const ChatContainer = ({ onStatsUpdate }) => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadConversationHistory();
  }, []);

  const loadConversationHistory = async () => {
    try {
      const history = await chatAPI.getHistory();
      const formattedHistory = history.map(msg => ({
        id: msg.id,
        type: msg.message_type,
        content: msg.content,
        timestamp: new Date(msg.timestamp),
      }));
      setMessages(formattedHistory);
    } catch (error) {
      console.error('Failed to load conversation history:', error);
      setIsConnected(false);
    }
  };

  const sendMessage = async (content) => {
    const userMessage = {
      id: Date.now() + '_user',
      type: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await chatAPI.sendMessage(content);
      
      const aiMessage = {
        id: response.message_id,
        type: 'assistant',
        content: response.response,
        timestamp: new Date(response.timestamp),
        model: response.model,
        provider: response.provider,
      };

      setMessages(prev => [...prev, aiMessage]);
      setIsConnected(true);
      
      // Update stats
      if (onStatsUpdate) {
        onStatsUpdate();
      }
      
    } catch (error) {
      console.error('Failed to send message:', error);
      setIsConnected(false);
      
      const errorMessage = {
        id: Date.now() + '_error',
        type: 'error',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = (messageId, helpful) => {
    // Optionally update UI to show feedback was recorded
    console.log(`Feedback for ${messageId}: ${helpful ? 'helpful' : 'not helpful'}`);
  };

  const clearHistory = async () => {
    if (window.confirm('Are you sure you want to clear all conversation history?')) {
      try {
        await chatAPI.clearHistory();
        setMessages([]);
        if (onStatsUpdate) {
          onStatsUpdate();
        }
      } catch (error) {
        console.error('Failed to clear history:', error);
      }
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="connection-status">
          <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></div>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
        <button onClick={clearHistory} className="clear-btn" disabled={isLoading}>
          Clear History
        </button>
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h2>Welcome to your Personal AI Agent!</h2>
            <p>I'm here to learn from you and adapt to your communication style.</p>
            <p>Start a conversation and I'll gradually learn your preferences.</p>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              onFeedback={handleFeedback}
            />
          ))
        )}
        
        {isLoading && <TypingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>

      <ChatInput
        onSendMessage={sendMessage}
        isLoading={isLoading}
        disabled={!isConnected}
      />
    </div>
  );
};

export default ChatContainer;