// frontend/src/components/Settings/ProfileView.jsx
import React, { useState } from 'react';
import { learningAPI } from '../../services/api';

const ProfileView = ({ profile, onRefresh }) => {
  const [loading, setLoading] = useState(false);

  const handleTriggerUpdate = async () => {
    setLoading(true);
    try {
      await learningAPI.triggerUpdate();
      await onRefresh();
    } catch (error) {
      console.error('Failed to trigger learning update:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResetProfile = async () => {
    if (window.confirm('Are you sure you want to reset your profile? This will delete all learned preferences and facts.')) {
      setLoading(true);
      try {
        await learningAPI.resetProfile();
        await onRefresh();
      } catch (error) {
        console.error('Failed to reset profile:', error);
      } finally {
        setLoading(false);
      }
    }
  };

  if (!profile) {
    return <div>No profile data available</div>;
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="profile-view">
      <div className="profile-section">
        <div className="section-header">
          <h3>Communication Metrics</h3>
          <div className="profile-completeness">
            Profile: {Math.round((profile.communication_metrics?.profile_completeness || 0) * 100)}% complete
          </div>
        </div>
        
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-label">Average Message Length</div>
            <div className="metric-value">
              {profile.communication_metrics?.avg_message_length?.toFixed(1) || 'N/A'} chars
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Formality Score</div>
            <div className="metric-value">
              {profile.communication_metrics?.formality_score?.toFixed(2) || 'N/A'}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Preferred Response Length</div>
            <div className="metric-value">
              {profile.communication_metrics?.preferred_response_length || 'N/A'}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Technical Level</div>
            <div className="metric-value">
              {profile.communication_metrics?.technical_level?.toFixed(2) || 'N/A'}
            </div>
          </div>
        </div>
      </div>

      <div className="profile-section">
        <h3>Personal Facts ({Object.keys(profile.personal_facts || {}).length})</h3>
        {Object.keys(profile.personal_facts || {}).length > 0 ? (
          <div className="facts-list">
            {Object.entries(profile.personal_facts).map(([key, value]) => (
              <div key={key} className="fact-item">
                <strong>{key}:</strong> {value}
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">No personal facts learned yet</div>
        )}
      </div>

      <div className="profile-section">
        <h3>Topics of Interest ({profile.topics_of_interest?.length || 0})</h3>
        {profile.topics_of_interest?.length > 0 ? (
          <div className="topics-list">
            {profile.topics_of_interest.map((topic, index) => (
              <span key={index} className="topic-tag">{topic}</span>
            ))}
          </div>
        ) : (
          <div className="empty-state">No topics identified yet</div>
        )}
      </div>

      <div className="profile-section">
        <h3>Communication Preferences</h3>
        {Object.keys(profile.communication_preferences || {}).length > 0 ? (
          <div className="preferences-list">
            {Object.entries(profile.communication_preferences).map(([key, value]) => (
              <div key={key} className="preference-item">
                <strong>{key}:</strong> {value}
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">No communication preferences learned yet</div>
        )}
      </div>

      <div className="profile-section">
        <h3>Statistics</h3>
        <div className="stats-grid">
          <div className="stat-item">
            <div className="stat-label">Total Messages</div>
            <div className="stat-value">{profile.total_messages || 0}</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">Profile Created</div>
            <div className="stat-value">
              {profile.profile_created ? formatDate(profile.profile_created) : 'N/A'}
            </div>
          </div>
          <div className="stat-item">
            <div className="stat-label">Last Updated</div>
            <div className="stat-value">
              {profile.last_updated ? formatDate(profile.last_updated) : 'N/A'}
            </div>
          </div>
        </div>
      </div>

      <div className="profile-actions">
        <button 
          className="action-btn primary" 
          onClick={handleTriggerUpdate}
          disabled={loading}
        >
          {loading ? 'Updating...' : 'Trigger Learning Update'}
        </button>
        <button 
          className="action-btn danger" 
          onClick={handleResetProfile}
          disabled={loading}
        >
          Reset Profile
        </button>
      </div>
    </div>
  );
};