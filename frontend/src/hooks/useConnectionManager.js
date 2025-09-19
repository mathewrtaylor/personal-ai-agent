// frontend/src/hooks/useConnectionManager.js
import { useState, useEffect, useRef, useCallback } from 'react';
import { healthAPI } from '../services/api';

export const useConnectionManager = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [lastConnected, setLastConnected] = useState(null);
  const [connectionError, setConnectionError] = useState(null);
  
  const reconnectTimeoutRef = useRef(null);
  const checkIntervalRef = useRef(null);
  const isActiveRef = useRef(true);

  // Check if page is visible/active
  const handleVisibilityChange = useCallback(() => {
    isActiveRef.current = !document.hidden;
    if (isActiveRef.current && !isConnected) {
      console.log('Page became active, checking connection...');
      checkConnection();
    }
  }, [isConnected]);

  // Check connection status
  const checkConnection = useCallback(async () => {
    try {
      await healthAPI.check();
      if (!isConnected) {
        console.log('Connection restored');
        setIsConnected(true);
        setLastConnected(new Date());
        setConnectionError(null);
        setIsReconnecting(false);
      }
      return true;
    } catch (error) {
      console.log('Connection check failed:', error.message);
      setIsConnected(false);
      setConnectionError(error.message);
      return false;
    }
  }, [isConnected]);

  // Exponential backoff reconnection
  const attemptReconnect = useCallback(async (attempt = 1) => {
    const maxAttempts = 10;
    const baseDelay = 1000; // 1 second
    
    if (attempt > maxAttempts) {
      console.log('Max reconnection attempts reached');
      setIsReconnecting(false);
      return;
    }

    setIsReconnecting(true);
    console.log(`Reconnection attempt ${attempt}/${maxAttempts}`);

    const connected = await checkConnection();
    
    if (connected) {
      setIsReconnecting(false);
      return;
    }

    // Exponential backoff with jitter
    const delay = Math.min(baseDelay * Math.pow(2, attempt - 1), 30000); // Max 30s
    const jitter = Math.random() * 1000; // Add up to 1s random delay
    
    reconnectTimeoutRef.current = setTimeout(() => {
      attemptReconnect(attempt + 1);
    }, delay + jitter);
    
  }, [checkConnection]);

  // Manual reconnect function
  const reconnect = useCallback(async () => {
    console.log('Manual reconnection triggered');
    setIsReconnecting(true);
    setConnectionError(null);
    
    // Clear any existing reconnection attempts
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    await attemptReconnect(1);
  }, [attemptReconnect]);

  // Auto-reconnect when connection is lost
  useEffect(() => {
    if (!isConnected && !isReconnecting && isActiveRef.current) {
      console.log('Connection lost, starting auto-reconnect...');
      attemptReconnect(1);
    }
  }, [isConnected, isReconnecting, attemptReconnect]);

  // Initial connection check and periodic monitoring
  useEffect(() => {
    // Initial check
    checkConnection();
    
    // Set up periodic health checks (every 30 seconds)
    checkIntervalRef.current = setInterval(checkConnection, 30000);
    
    // Listen for page visibility changes
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Listen for window focus (backup for visibility API)
    window.addEventListener('focus', handleVisibilityChange);
    
    // Listen for online/offline events
    window.addEventListener('online', () => {
      console.log('Browser came online');
      checkConnection();
    });
    
    window.addEventListener('offline', () => {
      console.log('Browser went offline');
      setIsConnected(false);
    });

    return () => {
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleVisibilityChange);
    };
  }, [checkConnection, handleVisibilityChange]);

  return {
    isConnected,
    isReconnecting,
    lastConnected,
    connectionError,
    reconnect,
    checkConnection
  };
};