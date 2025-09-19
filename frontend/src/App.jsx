// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import ChatContainer from './components/Chat/ChatContainer';
import Settings from './components/Settings/Settings';
import ConnectionStatus from './components/ConnectionStatus';
import { useConnectionManager } from './hooks/useConnectionManager';
import { chatAPI, learningAPI } from './services/api';
import './App.css';

function App() {
  const [showSettings, setShowSettings] = useState(false);
  const [stats, setStats] = useState(null);
  const [profile, setProfile] = useState(null);
  
  // Use the connection manager
  const {
    isConnected,
    isReconnecting,
    lastConnected,
    connectionError,
    reconnect,
    checkConnection
  } = useConnectionManager();

  useEffect(() => {
    if (isConnected) {
      loadInitialData();
    }
  }, [isConnected]);

  const loadInitialData = async () => {
    try {
      const [statsData, profileData] = await Promise.all([
        chatAPI.getStats().catch(() => null),
        learningAPI.getProfile().catch(() => null),
      ]);
      setStats(statsData);
      setProfile(profileData);
    } catch (error) {
      console.error('Failed to load initial data:', error);
    }
  };

  const handleStatsUpdate = () => {
    if (isConnected) {
      loadInitialData();
    }
  };

  return (
    <div className="app">
      {!isConnected && (
        <div className="disconnected-banner">
          AI Agent disconnected - some features may not work properly
          <button 
            className="reconnect-banner-btn" 
            onClick={reconnect}
            disabled={isReconnecting}
          >
            {isReconnecting ? 'Reconnecting...' : 'Reconnect Now'}
          </button>
        </div>
      )}

      <header className="app-header">
        <div className="header-left">
          <h1>Personal AI Agent</h1>
          <ConnectionStatus
            isConnected={isConnected}
            isReconnecting={isReconnecting}
            lastConnected={lastConnected}
            connectionError={connectionError}
            onReconnect={reconnect}
          />
        </div>
        
        <div className="header-right">
          <div className="stats-summary">
            {stats && isConnected && (
              <>
                <span className="stat-item">
                  💬 {stats.total_messages || 0} messages
                </span>
                {profile && profile.total_messages > 10 && (
                  <span className="stat-item">
                    🧠 {Math.round((profile.learning_stats?.profile_completeness || 0) * 100)}% learned
                  </span>
                )}
              </>
            )}
          </div>
          
          <button 
            onClick={() => setShowSettings(true)} 
            className="settings-btn"
            disabled={!isConnected}
            title={!isConnected ? "Connect to AI agent to access settings" : "Settings & Profile"}
          >
            ⚙️ Settings
          </button>
        </div>
      </header>

      <main className="main-content">
        <div className="chat-wrapper">
          <ChatContainer 
            onStatsUpdate={handleStatsUpdate}
            isConnected={isConnected}
            onConnectionRequest={checkConnection}
          />
        </div>
      </main>

      {showSettings && (
        <Settings onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}

export default App;