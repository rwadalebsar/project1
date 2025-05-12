import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import './ReportAnomalyForm.css';

const ReportAnomalyForm = ({ onClose, onSuccess, tankId, apiUrl }) => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    timestamp: new Date().toISOString().slice(0, 16),
    level: '',
    tank_id: tankId || 'tank1',
    notes: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Validate form data
      if (!formData.level) {
        throw new Error(t('anomalies.reportForm.levelRequired'));
      }

      // Convert level to number
      const reportData = {
        ...formData,
        level: parseFloat(formData.level),
        timestamp: new Date(formData.timestamp).toISOString()
      };

      // Send the report to the API
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${apiUrl}/api/user-anomalies`,
        reportData,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      // Show success message
      setSuccess(true);
      setFormData({
        timestamp: new Date().toISOString().slice(0, 16),
        level: '',
        tank_id: tankId || 'tank1',
        notes: ''
      });

      // Call the success callback if provided
      if (onSuccess) {
        onSuccess(response.data);
      }

      // Close the form after 2 seconds
      setTimeout(() => {
        if (onClose) onClose();
      }, 2000);
    } catch (err) {
      console.error('Error reporting anomaly:', err);
      setError(err.message || t('anomalies.reportForm.errorReporting'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="report-anomaly-form">
      <div className="report-form-header">
        <h2>{t('anomalies.reportForm.title')}</h2>
        <button className="close-button" onClick={onClose}>×</button>
      </div>

      {success ? (
        <div className="success-message">
          <div className="success-icon">✓</div>
          <p>{t('anomalies.reportForm.successMessage')}</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="timestamp">{t('anomalies.reportForm.timestamp')}</label>
            <input
              type="datetime-local"
              id="timestamp"
              name="timestamp"
              value={formData.timestamp}
              onChange={handleChange}
              className="form-control"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="level">{t('anomalies.reportForm.level')}</label>
            <input
              type="number"
              id="level"
              name="level"
              value={formData.level}
              onChange={handleChange}
              className="form-control"
              step="0.01"
              required
              placeholder={t('anomalies.reportForm.levelPlaceholder')}
            />
          </div>

          <div className="form-group">
            <label htmlFor="tank_id">{t('anomalies.reportForm.tankId')}</label>
            <input
              type="text"
              id="tank_id"
              name="tank_id"
              value={formData.tank_id}
              onChange={handleChange}
              className="form-control"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="notes">{t('anomalies.reportForm.notes')}</label>
            <textarea
              id="notes"
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              className="form-control"
              rows="3"
              placeholder={t('anomalies.reportForm.notesPlaceholder')}
            ></textarea>
          </div>

          <div className="form-actions">
            <button 
              type="button" 
              className="btn btn-secondary" 
              onClick={onClose}
              disabled={loading}
            >
              {t('common.cancel')}
            </button>
            <button 
              type="submit" 
              className="btn btn-primary" 
              disabled={loading}
            >
              {loading ? t('common.submitting') : t('anomalies.reportForm.submit')}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default ReportAnomalyForm;
