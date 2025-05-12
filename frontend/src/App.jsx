import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, AreaChart, Area, BarChart, Bar
} from 'recharts'

// Component for displaying tank level charts
const TankLevelChart = ({ data, title, timeFormat, dataKey = "level" }) => {
  return (
    <div className="chart-container">
      <h3>{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart
          data={data}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return date.toLocaleDateString(undefined, timeFormat);
            }}
          />
          <YAxis label={{ value: 'Level (m)', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            labelFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return date.toLocaleString();
            }}
            formatter={(value) => [`${value.toFixed(2)} m`, 'Level']}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke="#8884d8"
            fill="#8884d8"
            fillOpacity={0.3}
            activeDot={{ r: 8 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

// Component for displaying anomalies
const AnomaliesChart = ({ data, anomalies }) => {
  // Combine data with anomalies for visualization
  const combinedData = data.map(item => {
    const matchingAnomaly = anomalies.find(
      anomaly => anomaly.timestamp === item.timestamp
    );
    return {
      ...item,
      isAnomaly: matchingAnomaly ? true : false
    };
  });

  return (
    <div className="chart-container">
      <h3>Tank Level with Anomalies</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={combinedData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return date.toLocaleDateString();
            }}
          />
          <YAxis label={{ value: 'Level (m)', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            labelFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return date.toLocaleString();
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="level"
            stroke="#8884d8"
            dot={false}
          />
          {/* Render anomalies as red dots */}
          {anomalies.map((anomaly, index) => (
            <Line
              key={index}
              dataKey={() => anomaly.level}
              data={[anomaly]}
              stroke="red"
              dot={{ r: 6, fill: 'red' }}
              activeDot={{ r: 8 }}
              isAnimationActive={false}
              name="Anomaly"
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

// Component for displaying tank stats
const TankStats = ({ stats }) => {
  if (!stats) return <div className="stats-container">Loading stats...</div>;

  return (
    <div className="stats-container">
      <h3>Tank Statistics</h3>
      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-value">{stats.current_level?.toFixed(2)} m</div>
          <div className="stat-label">Current Level</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{stats.min_level?.toFixed(2)} m</div>
          <div className="stat-label">Min Level</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{stats.max_level?.toFixed(2)} m</div>
          <div className="stat-label">Max Level</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{stats.avg_level?.toFixed(2)} m</div>
          <div className="stat-label">Avg Level</div>
        </div>
      </div>
      <div className="last-updated">
        Last updated: {new Date(stats.last_updated).toLocaleString()}
      </div>
    </div>
  );
};

// Main App component
function App() {
  const [tankLevels, setTankLevels] = useState([])
  const [recentLevels, setRecentLevels] = useState([])
  const [anomalies, setAnomalies] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [newLevel, setNewLevel] = useState(5.0)
  const [timeRange, setTimeRange] = useState(30) // Default to 30 days

  useEffect(() => {
    fetchData()
  }, [timeRange])

  const fetchData = async () => {
    try {
      setLoading(true)

      // Fetch tank levels for the selected time range
      const levelsResponse = await axios.get(`http://localhost:8000/api/tank-levels?days=${timeRange}`)

      // Sort by timestamp (oldest first for charts)
      const sortedData = [...levelsResponse.data].sort((a, b) =>
        new Date(a.timestamp) - new Date(b.timestamp)
      )
      setTankLevels(sortedData)

      // Get recent data (3 days) for detailed view
      const recentData = [...levelsResponse.data]
        .filter(item => new Date(item.timestamp) > new Date(Date.now() - 3 * 24 * 60 * 60 * 1000))
        .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
      setRecentLevels(recentData)

      // Fetch anomalies
      const anomaliesResponse = await axios.get(`http://localhost:8000/api/anomalies?days=${timeRange}`)
      setAnomalies(anomaliesResponse.data)

      // Fetch stats
      const statsResponse = await axios.get(`http://localhost:8000/api/stats?days=${timeRange}`)
      setStats(statsResponse.data)

      setError(null)
    } catch (err) {
      setError('Error fetching data. Is the backend server running?')
      console.error('Error fetching data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddReading = async () => {
    try {
      await axios.post('http://localhost:8000/api/tank-levels', {
        level: parseFloat(newLevel),
        tank_id: "tank1"
      })

      // Refresh data after adding a new reading
      fetchData()

      // Reset form
      setNewLevel(5.0)
    } catch (err) {
      setError('Error adding tank level reading')
      console.error('Error adding reading:', err)
    }
  }

  const handleTimeRangeChange = (e) => {
    setTimeRange(parseInt(e.target.value))
  }

  return (
    <div className="app-container">
      <header className="dashboard-header">
        <h1>Tank Level Monitoring Dashboard</h1>
        <div className="time-range-selector">
          <label htmlFor="timeRange">Time Range: </label>
          <select
            id="timeRange"
            value={timeRange}
            onChange={handleTimeRangeChange}
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 3 months</option>
            <option value={180}>Last 6 months</option>
            <option value={365}>Last 12 months</option>
          </select>
        </div>
      </header>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">Loading dashboard data...</div>
      ) : (
        <div className="dashboard-content">
          {/* Current stats */}
          <TankStats stats={stats} />

          {/* Manual reading input */}
          <div className="add-reading-container">
            <h3>Add Manual Reading</h3>
            <div className="add-reading-form">
              <label>
                Tank Level (m):
                <input
                  type="number"
                  min="0"
                  max="10"
                  step="0.1"
                  value={newLevel}
                  onChange={(e) => setNewLevel(e.target.value)}
                />
              </label>
              <button onClick={handleAddReading}>Add Reading</button>
            </div>
          </div>

          {/* Recent data (3 days) */}
          <TankLevelChart
            data={recentLevels}
            title="Recent Tank Levels (Last 3 Days)"
            timeFormat={{ month: 'short', day: 'numeric', hour: '2-digit' }}
          />

          {/* Historical data */}
          <TankLevelChart
            data={tankLevels}
            title={`Historical Tank Levels (${timeRange} Days)`}
            timeFormat={{ month: 'short', day: 'numeric' }}
          />

          {/* Anomalies */}
          {anomalies.length > 0 ? (
            <div>
              <AnomaliesChart data={tankLevels} anomalies={anomalies} />
              <div className="anomalies-list">
                <h3>Detected Anomalies</h3>
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Time</th>
                      <th>Level (m)</th>
                      <th>Anomaly Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {anomalies.map((anomaly, index) => (
                      <tr key={index}>
                        <td>{new Date(anomaly.timestamp).toLocaleDateString()}</td>
                        <td>{new Date(anomaly.timestamp).toLocaleTimeString()}</td>
                        <td>{anomaly.level.toFixed(2)}</td>
                        <td>{anomaly.anomaly_score.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="no-anomalies">
              <h3>Anomaly Detection</h3>
              <p>No anomalies detected in the selected time range.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default App
