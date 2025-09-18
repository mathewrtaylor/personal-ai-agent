// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import ChatContainer from './components/Chat/ChatContainer';
import Settings from './components/Settings/Settings';
import { useOnlineStatus } from './hooks/useOnlineStatus';
import { chatAPI, learningAPI } from './services/api';
import './App.css';

function App() {
  const [showSettings, setShowSettings] = useState(false);
  const [stats, setStats] = useState(null);
  const [profile, setProfile] = useState(null);
  const { isOnline, networkOnline, apiOnline } = useOnlineStatus();

  useEffect(() => {
    loadInitialData();
  }, []);

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
    loadInitialData();
  };

  const getConnectionStatus = () => {
    if (!networkOnline) return { status: 'offline', message: 'No internet connection' };
    if (!apiOnline) return { status: 'disconnected', message: 'AI Agent offline' };
    return { status: 'connected', message: 'Connected to AI Agent' };
  };

  const connectionStatus = getConnectionStatus();

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <h1>Personal AI Agent</h1>
          <div className={`connection-status ${connectionStatus.status}`}>
            <div className="status-indicator"></div>
            {connectionStatus.message}
          </div>
        </div>
        
        <div className="header-right">
          <div className="stats-summary">
            {stats && (
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
            title="Settings & Profile"
          >
            ⚙️ Settings
          </button>
        </div>
      </header>

      <main className="main-content">
        <div className="chat-wrapper">
          <ChatContainer onStatsUpdate={handleStatsUpdate} />
        </div>
      </main>

      {showSettings && (
        <Settings onClose={() => setShowSettings(false)} />
      )}
      
      {!isOnline && (
        <div className="offline-banner">
          <span>⚠️ You're currently offline. Some features may not work properly.</span>
        </div>
      )}
    </div>
  );
}

export default App;