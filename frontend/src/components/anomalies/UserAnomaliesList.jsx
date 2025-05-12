import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import './UserAnomaliesList.css';

const UserAnomaliesList = ({ apiUrl, tankId, onReportAnomaly }) => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const fetchAnomalies = async () => {
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      let url = `${apiUrl}/api/user-anomalies`;
      
      // Add query parameters if needed
      const params = new URLSearchParams();
      if (tankId) params.append('tank_id', tankId);
      if (statusFilter !== 'all') params.append('status', statusFilter);
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await axios.get(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      setAnomalies(response.data);
    } catch (err) {
      console.error('Error fetching user-reported anomalies:', err);
      setError(t('anomalies.userList.errorFetching'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnomalies();
  }, [apiUrl, tankId, statusFilter]);

  const handleStatusChange = async (anomalyId, newStatus) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${apiUrl}/api/user-anomalies/${anomalyId}?status=${newStatus}`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      // Refresh the list
      fetchAnomalies();
    } catch (err) {
      console.error('Error updating anomaly status:', err);
      setError(t('anomalies.userList.errorUpdating'));
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'pending':
        return 'status-pending';
      case 'confirmed':
        return 'status-confirmed';
      case 'rejected':
        return 'status-rejected';
      default:
        return '';
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <div className="user-anomalies-list">
      <div className="list-header">
        <h3>{t('anomalies.userList.title')}</h3>
        <div className="list-actions">
          <div className="filter-group">
            <label htmlFor="status-filter">{t('anomalies.userList.filterByStatus')}:</label>
            <select
              id="status-filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="form-select"
            >
              <option value="all">{t('anomalies.userList.all')}</option>
              <option value="pending">{t('anomalies.userList.pending')}</option>
              <option value="confirmed">{t('anomalies.userList.confirmed')}</option>
              <option value="rejected">{t('anomalies.userList.rejected')}</option>
            </select>
          </div>
          <button 
            className="btn btn-primary btn-sm" 
            onClick={onReportAnomaly}
          >
            {t('anomalies.userList.reportNew')}
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading-indicator">
          <div className="spinner"></div>
          <p>{t('common.loading')}</p>
        </div>
      ) : anomalies.length === 0 ? (
        <div className="empty-state">
          <p>{t('anomalies.userList.noAnomalies')}</p>
          <button 
            className="btn btn-primary" 
            onClick={onReportAnomaly}
          >
            {t('anomalies.userList.reportFirst')}
          </button>
        </div>
      ) : (
        <div className="anomalies-table-container">
          <table className="anomalies-table">
            <thead>
              <tr>
                <th>{t('anomalies.userList.timestamp')}</th>
                <th>{t('anomalies.userList.level')}</th>
                <th>{t('anomalies.userList.tankId')}</th>
                <th>{t('anomalies.userList.notes')}</th>
                <th>{t('anomalies.userList.status')}</th>
                {user?.is_admin && <th>{t('anomalies.userList.actions')}</th>}
              </tr>
            </thead>
            <tbody>
              {anomalies.map((anomaly, index) => (
                <tr key={index}>
                  <td>{formatDate(anomaly.timestamp)}</td>
                  <td>{anomaly.level.toFixed(2)}</td>
                  <td>{anomaly.tank_id}</td>
                  <td className="notes-cell">{anomaly.notes || '-'}</td>
                  <td>
                    <span className={`status-badge ${getStatusBadgeClass(anomaly.status)}`}>
                      {t(`anomalies.userList.${anomaly.status}`)}
                    </span>
                  </td>
                  {user?.is_admin && (
                    <td className="actions-cell">
                      {anomaly.status === 'pending' && (
                        <>
                          <button
                            className="btn btn-sm btn-success"
                            onClick={() => handleStatusChange(index, 'confirmed')}
                          >
                            {t('anomalies.userList.confirm')}
                          </button>
                          <button
                            className="btn btn-sm btn-danger"
                            onClick={() => handleStatusChange(index, 'rejected')}
                          >
                            {t('anomalies.userList.reject')}
                          </button>
                        </>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default UserAnomaliesList;
