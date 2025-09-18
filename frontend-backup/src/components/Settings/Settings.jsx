// frontend/src/components/Settings/Settings.jsx
import React, { useState, useEffect } from 'react';
import ProfileView from './ProfileView';
import LearningStats from './LearningStats';
import SystemHealth from './SystemHealth';
import { learningAPI, healthAPI } from '../../services/api';
import './Settings.css';

const Settings = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState('profile');
  const [profile, setProfile] = useState(null);
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [profileData, statsData, healthData] = await Promise.all([
        learningAPI.getProfile(),
        learningAPI.getStats(),
        healthAPI.detailed(),
      ]);
      
      setProfile(profileData);
      setStats(statsData);
      setHealth(healthData);
    } catch (error) {
      console.error('Failed to load settings data:', error);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profile & Learning', icon: '👤' },
    { id: 'stats', label: 'Statistics', icon: '📊' },
    { id: 'health', label: 'System Health', icon: '🔧' },
  ];

  return (
    <div className="settings-modal-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-header">
          <h2>Settings & Profile</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="settings-tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="tab-icon">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        <div className="settings-content">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner">Loading...</div>
            </div>
          ) : (
            <>
              {activeTab === 'profile' && (
                <ProfileView profile={profile} onRefresh={loadData} />
              )}
              {activeTab === 'stats' && (
                <LearningStats stats={stats} onRefresh={loadData} />
              )}
              {activeTab === 'health' && (
                <SystemHealth health={health} onRefresh={loadData} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

