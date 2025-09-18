// frontend/src/components/Settings/SystemHealth.jsx
import React from 'react';

const SystemHealth = ({ health, onRefresh }) => {
  if (!health) {
    return <div>No health data available</div>;
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return '#28a745';
      case 'degraded': return '#ffc107';
      case 'unhealthy': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return '✅';
      case 'degraded': return '⚠️';
      case 'unhealthy': return '❌';
      default: return '❓';
    }
  };

  return (
    <div className="system-health">
      <div className="health-overview">
        <div className="overall-status">
          <div className="status-indicator">
            <span className="status-icon">{getStatusIcon(health.status)}</span>
            <span className="status-text">System Status: {health.status}</span>
          </div>
          <div className="status-timestamp">
            Last checked: {new Date(health.timestamp).toLocaleString()}
          </div>
        </div>
      </div>

      <div className="services-grid">
        {Object.entries(health.services || {}).map(([service, serviceHealth]) => (
          <div key={service} className="service-card">
            <div className="service-header">
              <span className="service-icon">{getStatusIcon(serviceHealth.status)}</span>
              <span className="service-name">{service.replace('_', ' ')}</span>
            </div>
            <div 
              className="service-status"
              style={{ color: getStatusColor(serviceHealth.status) }}
            >
              {serviceHealth.status}
            </div>
            {serviceHealth.error && (
              <div className="service-error">
                Error: {serviceHealth.error}
              </div>
            )}
            {serviceHealth.host && (
              <div className="service-detail">
                Host: {serviceHealth.host}
              </div>
            )}
            {serviceHealth.model && (
              <div className="service-detail">
                Model: {serviceHealth.model}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="health-actions">
        <button className="action-btn primary" onClick={onRefresh}>
          Refresh Health Status
        </button>
      </div>
    </div>
  );
};

export default SystemHealth;