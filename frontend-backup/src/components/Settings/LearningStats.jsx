// frontend/src/components/Settings/LearningStats.jsx
import React from 'react';

const LearningStats = ({ stats, onRefresh }) => {
  if (!stats) {
    return <div>No statistics available</div>;
  }

  const formatConfidenceDistribution = (dist) => {
    const total = Object.values(dist).reduce((sum, val) => sum + val, 0);
    if (total === 0) return dist;
    
    return Object.entries(dist).map(([level, count]) => ({
      level,
      count,
      percentage: ((count / total) * 100).toFixed(1)
    }));
  };

  return (
    <div className="learning-stats">
      <div className="stats-section">
        <h3>Learning Overview</h3>
        <div className="overview-grid">
          <div className="overview-card">
            <div className="card-value">{stats.total_learning_entries || 0}</div>
            <div className="card-label">Total Learning Entries</div>
          </div>
          <div className="overview-card">
            <div className="card-value">{stats.learning_stats?.high_confidence_learnings || 0}</div>
            <div className="card-label">High Confidence Learnings</div>
          </div>
          <div className="overview-card">
            <div className="card-value">{stats.profile_metrics?.topics_count || 0}</div>
            <div className="card-label">Topics of Interest</div>
          </div>
          <div className="overview-card">
            <div className="card-value">{stats.profile_metrics?.facts_count || 0}</div>
            <div className="card-label">Personal Facts</div>
          </div>
        </div>
      </div>

      <div className="stats-section">
        <h3>Learning Types</h3>
        <div className="learning-types">
          {Object.entries(stats.learning_types || {}).map(([type, count]) => (
            <div key={type} className="learning-type-item">
              <div className="type-name">{type.replace('_', ' ')}</div>
              <div className="type-count">{count}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="stats-section">
        <h3>Confidence Distribution</h3>
        <div className="confidence-chart">
          {formatConfidenceDistribution(stats.confidence_distribution || {}).map(item => (
            <div key={item.level} className="confidence-item">
              <div className="confidence-label">{item.level} confidence</div>
              <div className="confidence-bar">
                <div 
                  className={`confidence-fill ${item.level}`}
                  style={{ width: `${item.percentage}%` }}
                ></div>
              </div>
              <div className="confidence-stats">
                {item.count} ({item.percentage}%)
              </div>
            </div>
          ))}
        </div>
      </div>

      {stats.recent_summaries?.length > 0 && (
        <div className="stats-section">
          <h3>Recent Conversation Summaries</h3>
          <div className="summaries-list">
            {stats.recent_summaries.map((summary, index) => (
              <div key={index} className="summary-item">
                <div className="summary-period">{summary.period}</div>
                <div className="summary-text">{summary.summary}</div>
                <div className="summary-meta">
                  {summary.message_count} messages
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="stats-actions">
        <button className="action-btn primary" onClick={onRefresh}>
          Refresh Statistics
        </button>
      </div>
    </div>
  );
};