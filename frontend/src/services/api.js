// frontend/src/services/api.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,  // Increase to 120 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth headers if needed
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      // Optionally redirect to login
    }
    return Promise.reject(error);
  }
);

// Chat API endpoints
export const chatAPI = {
  sendMessage: async (content, userId = 'default_user') => {
    const response = await api.post('/api/chat/message', {
      content,
      user_id: userId,
    });
    return response.data;
  },

  getHistory: async (userId = 'default_user', limit = 50, offset = 0) => {
    const response = await api.get('/api/chat/history', {
      params: { user_id: userId, limit, offset },
    });
    return response.data;
  },

  clearHistory: async (userId = 'default_user') => {
    const response = await api.delete('/api/chat/clear', {
      params: { user_id: userId },
    });
    return response.data;
  },

  getStats: async (userId = 'default_user') => {
    const response = await api.get('/api/chat/stats', {
      params: { user_id: userId },
    });
    return response.data;
  },
};

// Learning API endpoints
export const learningAPI = {
  getProfile: async (userId = 'default_user') => {
    const response = await api.get('/api/learning/profile', {
      params: { user_id: userId },
    });
    return response.data;
  },

  submitFeedback: async (messageId, helpful, feedbackText = null, userId = 'default_user') => {
    const response = await api.post('/api/learning/feedback', {
      message_id: messageId,
      helpful,
      feedback_text: feedbackText,
      user_id: userId,
    });
    return response.data;
  },

  getStats: async (userId = 'default_user') => {
    const response = await api.get('/api/learning/stats', {
      params: { user_id: userId },
    });
    return response.data;
  },

  triggerUpdate: async (userId = 'default_user') => {
    const response = await api.post('/api/learning/trigger-update', {
      user_id: userId,
    });
    return response.data;
  },

  createSummary: async (userId = 'default_user', messageCount = 50) => {
    const response = await api.post('/api/learning/create-summary', {
      user_id: userId,
      message_count: messageCount,
    });
    return response.data;
  },

  resetProfile: async (userId = 'default_user') => {
    const response = await api.delete('/api/learning/reset-profile', {
      params: { user_id: userId },
    });
    return response.data;
  },

  getLearningHistory: async (userId = 'default_user', limit = 50, learningType = null) => {
    const response = await api.get('/api/learning/learning-history', {
      params: { 
        user_id: userId, 
        limit, 
        learning_type: learningType 
      },
    });
    return response.data;
  },
};

// Health API endpoints
export const healthAPI = {
  check: async () => {
    const response = await api.get('/api/health');
    return response.data;
  },

  detailed: async () => {
    const response = await api.get('/api/health/detailed');
    return response.data;
  },

  models: async () => {
    const response = await api.get('/api/health/models');
    return response.data;
  },
};

// Utility functions
export const apiUtils = {
  isOnline: async () => {
    try {
      await healthAPI.check();
      return true;
    } catch (error) {
      return false;
    }
  },

  formatError: (error) => {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    if (error.message) {
      return error.message;
    }
    return 'An unexpected error occurred';
  },

  retry: async (fn, retries = 3, delay = 1000) => {
    for (let i = 0; i < retries; i++) {
      try {
        return await fn();
      } catch (error) {
        if (i === retries - 1) throw error;
        await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
      }
    }
  },
};

export default api;