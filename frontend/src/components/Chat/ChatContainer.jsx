// frontend/src/components/Chat/ChatContainer.jsx
import React, { useState, useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import TypingIndicator from './TypingIndicator';
import { chatAPI } from '../../services/api';
import './ChatContainer.css';

const ChatContainer = ({ onStatsUpdate, isConnected, onConnectionRequest }) => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStartTime, setLoadingStartTime] = useState(null);
  const [loadingDuration, setLoadingDuration] = useState(0);
  const messagesEndRef = useRef(null);
  const loadingTimerRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadConversationHistory();
  }, []);

  // Update loading duration timer
  useEffect(() => {
    if (isLoading) {
      const startTime = Date.now();
      setLoadingStartTime(startTime);
      
      loadingTimerRef.current = setInterval(() => {
        setLoadingDuration(Date.now() - startTime);
      }, 1000); // Update every second
      
    } else {
      if (loadingTimerRef.current) {
        clearInterval(loadingTimerRef.current);
      }
      setLoadingDuration(0);
    }

    return () => {
      if (loadingTimerRef.current) {
        clearInterval(loadingTimerRef.current);
      }
    };
  }, [isLoading]);

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
    }
  };

  const sendMessage = async (content) => {
    if (!isConnected) {
      onConnectionRequest();
      return;
    }

    const userMessage = {
      id: Date.now() + '_user',
      type: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Create AbortController for timeout management
      const controller = new AbortController();
      
      // Set a very long timeout (5 minutes) with user feedback
      const timeoutId = setTimeout(() => {
        controller.abort();
      }, 5 * 60 * 1000); // 5 minutes

      const response = await fetch('http://localhost:8000/api/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: content,
          user_id: 'default_user'
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const aiMessage = {
        id: data.message_id,
        type: 'assistant',
        content: data.response,
        timestamp: new Date(data.timestamp),
        model: data.model,
        provider: data.provider,
      };

      setMessages(prev => [...prev, aiMessage]);
      
      if (onStatsUpdate) {
        onStatsUpdate();
      }
      
    } catch (error) {
      console.error('Failed to send message:', error);
      
      let errorMessage = 'Sorry, I encountered an error. Please try again.';
      
      if (error.name === 'AbortError') {
        errorMessage = 'The AI took too long to respond (over 5 minutes). This might be due to a complex question or high server load. Please try a simpler question or try again later.';
      } else if (error.message.includes('Failed to fetch') || error.message.includes('ERR_NETWORK')) {
        errorMessage = 'Connection lost. Click the reconnect button to try again.';
      } else if (error.message.includes('500')) {
        errorMessage = 'The AI service is having issues. Please wait a moment and try again.';
      }
      
      const errorMsg = {
        id: Date.now() + '_error',
        type: 'error',
        content: errorMessage,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = (messageId, helpful) => {
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
        <div className="chat-status">
          {isLoading && (
            <div className="processing-status">
              AI is processing your message...
              {loadingDuration > 10000 && (
                <span className="processing-time">
                  ({Math.floor(loadingDuration / 1000)}s)
                </span>
              )}
            </div>
          )}
        </div>
        <button 
          onClick={clearHistory} 
          className="clear-btn" 
          disabled={isLoading}
          title="Clear conversation history"
        >
          Clear History
        </button>
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h2>Welcome to your Personal AI Agent!</h2>
            <p>I'm here to learn from you and adapt to your communication style.</p>
            <p>Start a conversation and I'll gradually learn your preferences.</p>
            {!isConnected && (
              <div className="connection-warning">
                <p>⚠️ Not connected to AI service. Please check your connection.</p>
              </div>
            )}
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
        
        {isLoading && (
          <TypingIndicator duration={loadingDuration} />
        )}
        
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