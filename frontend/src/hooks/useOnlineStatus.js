// frontend/src/hooks/useOnlineStatus.js
import { useState, useEffect } from 'react';
import { apiUtils } from '../services/api';

export const useOnlineStatus = (checkInterval = 30000) => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isApiOnline, setIsApiOnline] = useState(false);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const online = await apiUtils.isOnline();
        setIsApiOnline(online);
      } catch (error) {
        setIsApiOnline(false);
      }
    };

    checkApiStatus();
    const interval = setInterval(checkApiStatus, checkInterval);

    return () => clearInterval(interval);
  }, [checkInterval]);

  return { isOnline: isOnline && isApiOnline, networkOnline: isOnline, apiOnline: isApiOnline };
};