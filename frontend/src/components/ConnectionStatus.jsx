// frontend/src/components/ConnectionStatus.jsx
import React from 'react';
import './ConnectionStatus.css';

const ConnectionStatus = ({ 
  isConnected, 
  isReconnecting, 
  lastConnected, 
  connectionError, 
  onReconnect 
}) => {
  const getStatusInfo = () => {
    if (isReconnecting) {
      return {
        status: 'reconnecting',
        message: 'Reconnecting...',
        icon: '🔄',
        color: '#ffc107'
      };
    }
    
    if (isConnected) {
      return {
        status: 'connected',
        message: 'Connected',
        icon: '✅',
        color: '#28a745'
      };
    }
    
    return {
      status: 'disconnected',
      message: 'Disconnected',
      icon: '❌',
      color: '#dc3545'
    };
  };

  const statusInfo = getStatusInfo();

  const formatLastConnected = (date) => {
    if (!date) return '';
    
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className={`connection-status ${statusInfo.status}`}>
      <div className="status-indicator">
        <span className="status-icon">{statusInfo.icon}</span>
        <span className="status-text">{statusInfo.message}</span>
      </div>
      
      {!isConnected && !isReconnecting && (
        <button 
          className="reconnect-btn" 
          onClick={onReconnect}
          title="Try to reconnect to the AI agent"
        >
          🔄 Reconnect
        </button>
      )}
      
      {connectionError && (
        <div className="connection-error" title={connectionError}>
          Error: {connectionError.substring(0, 50)}...
        </div>
      )}
      
      {lastConnected && (
        <div className="last-connected">
          Last connected: {formatLastConnected(lastConnected)}
        </div>
      )}
    </div>
  );
};

export default ConnectionStatus;