// frontend/src/hooks/useWebSocket.js
import { useState, useEffect, useRef } from 'react';

export const useWebSocket = (url, options = {}) => {
  const [socket, setSocket] = useState(null);
  const [lastMessage, setLastMessage] = useState(null);
  const [readyState, setReadyState] = useState(0);
  const messageQueue = useRef([]);

  useEffect(() => {
    if (!url) return;

    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      setReadyState(1);
      // Send queued messages
      while (messageQueue.current.length > 0) {
        const message = messageQueue.current.shift();
        ws.send(message);
      }
    };

    ws.onmessage = (event) => {
      setLastMessage(event.data);
      if (options.onMessage) {
        options.onMessage(event.data);
      }
    };

    ws.onclose = () => {
      setReadyState(3);
    };

    ws.onerror = () => {
      setReadyState(3);
    };

    setSocket(ws);

    return () => {
      ws.close();
    };
  }, [url]);

  const sendMessage = (message) => {
    if (readyState === 1) {
      socket.send(message);
    } else {
      messageQueue.current.push(message);
    }
  };

  return { sendMessage, lastMessage, readyState };
};