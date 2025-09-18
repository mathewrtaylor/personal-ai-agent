// frontend/src/utils/constants.js
export const API_ENDPOINTS = {
  CHAT: '/api/chat',
  LEARNING: '/api/learning',
  HEALTH: '/api/health',
};

export const MESSAGE_TYPES = {
  USER: 'user',
  ASSISTANT: 'assistant',
  ERROR: 'error',
  SYSTEM: 'system',
};

export const LEARNING_TYPES = {
  PERSONAL_FACT: 'personal_fact',
  COMMUNICATION_PREFERENCE: 'communication_preference',
  TOPIC_INTEREST: 'topic_interest',
  FEEDBACK: 'feedback',
};

export const SYSTEM_STATUS = {
  HEALTHY: 'healthy',
  DEGRADED: 'degraded',
  UNHEALTHY: 'unhealthy',
};

export const DEFAULT_SETTINGS = {
  theme: 'light',
  notifications: true,
  autoSave: true,
  maxHistoryLength: 1000,
  responseTimeout: 30000,
};

export const CONFIDENCE_LEVELS = {
  HIGH: 0.8,
  MEDIUM: 0.5,
  LOW: 0.3,
};