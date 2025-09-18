// frontend/src/hooks/useChat.js
import { useState, useCallback } from 'react';
import { chatAPI } from '../services/api';

export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = useCallback(async (content) => {
    const userMessage = {
      id: Date.now() + '_user',
      type: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

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
      return aiMessage;
    } catch (err) {
      const errorMessage = {
        id: Date.now() + '_error',
        type: 'error',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const history = await chatAPI.getHistory();
      const formattedHistory = history.map(msg => ({
        id: msg.id,
        type: msg.message_type,
        content: msg.content,
        timestamp: new Date(msg.timestamp),
      }));
      setMessages(formattedHistory);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const clearHistory = useCallback(async () => {
    try {
      await chatAPI.clearHistory();
      setMessages([]);
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    loadHistory,
    clearHistory,
  };
};