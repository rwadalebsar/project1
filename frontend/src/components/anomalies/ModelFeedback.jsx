import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import './ModelFeedback.css';

const ModelFeedback = ({ apiUrl }) => {
  const { t } = useTranslation();
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchFeedback = async () => {
      setLoading(true);
      setError('');

      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${apiUrl}/api/model-feedback`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        setFeedback(response.data);
      } catch (err) {
        console.error('Error fetching model feedback:', err);
        setError(t('anomalies.modelFeedback.errorFetching'));
      } finally {
        setLoading(false);
      }
    };

    fetchFeedback();
  }, [apiUrl, t]);

  if (loading) {
    return (
      <div className="model-feedback loading">
        <div className="spinner"></div>
        <p>{t('common.loading')}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="model-feedback">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  if (!feedback) {
    return (
      <div className="model-feedback">
        <p>{t('anomalies.modelFeedback.noData')}</p>
      </div>
    );
  }

  // Prepare data for pie chart
  const pieData = [
    { name: t('anomalies.userList.confirmed'), value: feedback.confirmed_anomalies, color: '#10B981' },
    { name: t('anomalies.userList.rejected'), value: feedback.rejected_anomalies, color: '#EF4444' },
    { name: t('anomalies.userList.pending'), value: feedback.pending_anomalies, color: '#F59E0B' }
  ].filter(item => item.value > 0);

  return (
    <div className="model-feedback">
      <h3>{t('anomalies.modelFeedback.title')}</h3>
      
      <div className="feedback-stats">
        <div className="stat-card">
          <div className="stat-value">{feedback.total_reported_anomalies}</div>
          <div className="stat-label">{t('anomalies.modelFeedback.totalReported')}</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-value">{feedback.model_accuracy.toFixed(1)}%</div>
          <div className="stat-label">{t('anomalies.modelFeedback.modelAccuracy')}</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-value">{feedback.false_negatives_rate.toFixed(1)}%</div>
          <div className="stat-label">{t('anomalies.modelFeedback.falseNegativesRate')}</div>
        </div>
      </div>
      
      {feedback.total_reported_anomalies > 0 && (
        <div className="feedback-chart">
          <h4>{t('anomalies.modelFeedback.reportedAnomaliesBreakdown')}</h4>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [value, t('anomalies.modelFeedback.count')]} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
      
      <div className="feedback-explanation">
        <h4>{t('anomalies.modelFeedback.howItWorks')}</h4>
        <p>{t('anomalies.modelFeedback.explanation')}</p>
        <ul>
          <li><strong>{t('anomalies.modelFeedback.confirmedAnomalies')}:</strong> {t('anomalies.modelFeedback.confirmedExplanation')}</li>
          <li><strong>{t('anomalies.modelFeedback.rejectedAnomalies')}:</strong> {t('anomalies.modelFeedback.rejectedExplanation')}</li>
          <li><strong>{t('anomalies.modelFeedback.pendingAnomalies')}:</strong> {t('anomalies.modelFeedback.pendingExplanation')}</li>
        </ul>
      </div>
    </div>
  );
};

export default ModelFeedback;
