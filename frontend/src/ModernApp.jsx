import { useState, useEffect } from 'react'
import axios from 'axios'
import './modern.css'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, AreaChart, Area, BarChart, Bar
} from 'recharts'

// Icons for the sidebar and UI
const Icons = {
  Dashboard: () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
    </svg>
  ),
  Tank: () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
    </svg>
  ),
  Chart: () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  Alert: () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  Settings: () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  Add: () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
    </svg>
  ),
  Refresh: () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
  Menu: () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  ),
  Close: () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  TrendUp: () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="16" height="16">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ),
  TrendDown: () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="16" height="16">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
    </svg>
  )
};

// Modern Tank Level Chart Component
const ModernTankLevelChart = ({ data, title, timeFormat, dataKey = "level", color = "#4361ee" }) => {
  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{title}</h3>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart
          data={data}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return date.toLocaleDateString(undefined, timeFormat);
            }}
            stroke="#6b7280"
          />
          <YAxis
            label={{ value: 'Level (m)', angle: -90, position: 'insideLeft', style: { fill: '#6b7280' } }}
            stroke="#6b7280"
          />
          <Tooltip
            labelFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return date.toLocaleString();
            }}
            formatter={(value) => [`${value.toFixed(2)} m`, 'Level']}
            contentStyle={{ backgroundColor: 'white', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            fill={color}
            fillOpacity={0.2}
            activeDot={{ r: 8, fill: color, stroke: 'white', strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

// Modern Anomalies Chart Component
const ModernAnomaliesChart = ({ data, anomalies }) => {
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
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Tank Level with Anomalies</h3>
        <div className="card-icon">
          <Icons.Alert />
        </div>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={combinedData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return date.toLocaleDateString();
            }}
            stroke="#6b7280"
          />
          <YAxis
            label={{ value: 'Level (m)', angle: -90, position: 'insideLeft', style: { fill: '#6b7280' } }}
            stroke="#6b7280"
          />
          <Tooltip
            labelFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return date.toLocaleString();
            }}
            contentStyle={{ backgroundColor: 'white', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="level"
            stroke="#4361ee"
            dot={false}
            strokeWidth={2}
          />
          {/* Render anomalies as red dots */}
          {anomalies.map((anomaly, index) => (
            <Line
              key={index}
              dataKey={() => anomaly.level}
              data={[anomaly]}
              stroke="#f43f5e"
              dot={{ r: 6, fill: '#f43f5e', stroke: 'white', strokeWidth: 2 }}
              activeDot={{ r: 8, fill: '#f43f5e', stroke: 'white', strokeWidth: 2 }}
              isAnimationActive={false}
              name="Anomaly"
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

// Modern Stats Component
const ModernStats = ({ stats }) => {
  if (!stats) return <div className="dashboard-grid col-span-12"><div className="card">Loading stats...</div></div>;

  return (
    <div className="dashboard-grid col-span-12">
      <div className="col-span-3">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Current Level</h3>
            <div className="card-icon">
              <Icons.Tank />
            </div>
          </div>
          <div className="stat-value">{stats.current_level?.toFixed(2)} m</div>
          <div className="stat-trend trend-up">
            <Icons.TrendUp /> Updated {new Date(stats.last_updated).toLocaleTimeString()}
          </div>
        </div>
      </div>
      <div className="col-span-3">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Min Level</h3>
          </div>
          <div className="stat-value">{stats.min_level?.toFixed(2)} m</div>
          <div className="stat-label">Last {stats.count} readings</div>
        </div>
      </div>
      <div className="col-span-3">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Max Level</h3>
          </div>
          <div className="stat-value">{stats.max_level?.toFixed(2)} m</div>
          <div className="stat-label">Last {stats.count} readings</div>
        </div>
      </div>
      <div className="col-span-3">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Average Level</h3>
          </div>
          <div className="stat-value">{stats.avg_level?.toFixed(2)} m</div>
          <div className="stat-label">Standard Deviation: {stats.std_dev?.toFixed(2)}</div>
        </div>
      </div>
    </div>
  );
};

// Modern API Configuration Component
const ModernApiConfig = ({ apiConfig, setApiConfig, onSave, showConfig, setShowConfig }) => {
  const [tempConfig, setTempConfig] = useState({ ...apiConfig })

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setTempConfig({
      ...tempConfig,
      [name]: type === 'checkbox' ? checked : value
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave(tempConfig)
    setShowConfig(false)
  }

  if (!showConfig) return null

  return (
    <div className="config-overlay">
      <div className="config-modal">
        <div className="card-header">
          <h3 className="card-title">API Configuration</h3>
          <button className="btn btn-icon" onClick={() => setShowConfig(false)}>
            <Icons.Close />
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="apiUrl">API URL:</label>
            <input
              className="form-control"
              type="text"
              id="apiUrl"
              name="apiUrl"
              value={tempConfig.apiUrl}
              onChange={handleChange}
              placeholder="http://api.example.com/tank-levels"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="apiKey">API Key:</label>
            <input
              className="form-control"
              type="text"
              id="apiKey"
              name="apiKey"
              value={tempConfig.apiKey}
              onChange={handleChange}
              placeholder="your-api-key"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="tankId">Tank ID:</label>
            <input
              className="form-control"
              type="text"
              id="tankId"
              name="tankId"
              value={tempConfig.tankId}
              onChange={handleChange}
              placeholder="tank1"
            />
          </div>

          <div className="form-group">
            <label className="form-label">
              <input
                type="checkbox"
                name="useMockData"
                checked={tempConfig.useMockData}
                onChange={handleChange}
              />
              Use Mock Data (Enable if you don't have a real API endpoint)
            </label>
          </div>

          <div className="config-actions">
            <button type="submit" className="btn btn-success">Save Configuration</button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowConfig(false)}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
};

// Modern Add Reading Component
const ModernAddReading = ({ newLevel, setNewLevel, handleAddReading }) => {
  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Add Manual Reading</h3>
        <div className="card-icon">
          <Icons.Add />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label" htmlFor="tankLevel">Tank Level (m):</label>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            className="form-control"
            type="number"
            id="tankLevel"
            min="0"
            max="10"
            step="0.1"
            value={newLevel}
            onChange={(e) => setNewLevel(e.target.value)}
          />
          <button className="btn btn-primary" onClick={handleAddReading}>Add Reading</button>
        </div>
      </div>
    </div>
  );
};

// Modern Anomalies List Component
const ModernAnomaliesList = ({ anomalies }) => {
  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Detected Anomalies</h3>
        <div className="card-icon">
          <Icons.Alert />
        </div>
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid var(--gray-200)' }}>Date</th>
            <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid var(--gray-200)' }}>Time</th>
            <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid var(--gray-200)' }}>Level (m)</th>
            <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid var(--gray-200)' }}>Anomaly Score</th>
          </tr>
        </thead>
        <tbody>
          {anomalies.map((anomaly, index) => (
            <tr key={index} style={{ backgroundColor: index % 2 === 0 ? 'white' : 'var(--gray-50)' }}>
              <td style={{ padding: '12px', borderBottom: '1px solid var(--gray-200)' }}>{new Date(anomaly.timestamp).toLocaleDateString()}</td>
              <td style={{ padding: '12px', borderBottom: '1px solid var(--gray-200)' }}>{new Date(anomaly.timestamp).toLocaleTimeString()}</td>
              <td style={{ padding: '12px', borderBottom: '1px solid var(--gray-200)' }}>{anomaly.level.toFixed(2)}</td>
              <td style={{ padding: '12px', borderBottom: '1px solid var(--gray-200)' }}>{anomaly.anomaly_score.toFixed(4)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Main App Component
function ModernApp() {
  const [tankLevels, setTankLevels] = useState([])
  const [recentLevels, setRecentLevels] = useState([])
  const [anomalies, setAnomalies] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [newLevel, setNewLevel] = useState(5.0)
  const [timeRange, setTimeRange] = useState(30) // Default to 30 days
  const [showConfig, setShowConfig] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)

  // API configuration state
  const [apiConfig, setApiConfig] = useState(() => {
    // Try to load from localStorage
    const savedConfig = localStorage.getItem('tankApiConfig')
    return savedConfig ? JSON.parse(savedConfig) : {
      apiUrl: 'http://localhost:8000',
      apiKey: '',
      tankId: 'tank1',
      useMockData: true
    }
  })

  // Save API config to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('tankApiConfig', JSON.stringify(apiConfig))
  }, [apiConfig])

  // Fetch data when timeRange or apiConfig changes
  useEffect(() => {
    fetchData()
  }, [timeRange, apiConfig])

  const fetchData = async () => {
    try {
      setLoading(true)

      const headers = apiConfig.apiKey ? {
        'Authorization': `Bearer ${apiConfig.apiKey}`
      } : {}

      // Fetch tank levels for the selected time range
      const levelsResponse = await axios.get(
        `${apiConfig.apiUrl}/api/tank-levels?days=${timeRange}&tank_id=${apiConfig.tankId}`,
        { headers }
      )

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
      const anomaliesResponse = await axios.get(
        `${apiConfig.apiUrl}/api/anomalies?days=${timeRange}&tank_id=${apiConfig.tankId}`,
        { headers }
      )
      setAnomalies(anomaliesResponse.data)

      // Fetch stats
      const statsResponse = await axios.get(
        `${apiConfig.apiUrl}/api/stats?days=${timeRange}&tank_id=${apiConfig.tankId}`,
        { headers }
      )
      setStats(statsResponse.data)

      setError(null)
    } catch (err) {
      setError(`Error fetching data: ${err.message}. Check your API configuration.`)
      console.error('Error fetching data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddReading = async () => {
    try {
      const headers = apiConfig.apiKey ? {
        'Authorization': `Bearer ${apiConfig.apiKey}`
      } : {}

      await axios.post(`${apiConfig.apiUrl}/api/tank-levels`, {
        level: parseFloat(newLevel),
        tank_id: apiConfig.tankId
      }, { headers })

      // Refresh data after adding a new reading
      fetchData()

      // Reset form
      setNewLevel(5.0)
    } catch (err) {
      setError(`Error adding tank level reading: ${err.message}`)
      console.error('Error adding reading:', err)
    }
  }

  const handleSaveConfig = (newConfig) => {
    setApiConfig(newConfig)
    // Fetch data with new config
    fetchData()
  }

  const handleTimeRangeChange = (e) => {
    setTimeRange(parseInt(e.target.value))
  }

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? '' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <Icons.Tank /> <span>TankMonitor</span>
          </div>
        </div>
        <div className="sidebar-nav">
          <div className="nav-item active">
            <Icons.Dashboard /> <span>Dashboard</span>
          </div>
          <div className="nav-item">
            <Icons.Chart /> <span>Analytics</span>
          </div>
          <div className="nav-item">
            <Icons.Alert /> <span>Alerts</span>
          </div>
          <div className="nav-item" onClick={() => setShowConfig(true)}>
            <Icons.Settings /> <span>Settings</span>
          </div>
        </div>
        <div className="sidebar-footer">
          <div className="nav-item" onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? (
              <>
                <Icons.Menu /> <span>Collapse Menu</span>
              </>
            ) : (
              <Icons.Menu />
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {/* Header */}
        <div className="dashboard-header">
          <div className="header-left">
            <button
              className="mobile-menu-toggle btn btn-icon"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              {sidebarOpen ? <Icons.Close /> : <Icons.Menu />}
            </button>
            <h1 className="page-title">Tank Level Monitoring</h1>
          </div>
          <div className="header-actions">
            <div className="form-group" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
              <label className="form-label" style={{ margin: 0 }}>Time Range:</label>
              <select
                className="form-select"
                value={timeRange}
                onChange={handleTimeRangeChange}
                style={{ width: 'auto' }}
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 3 months</option>
                <option value={180}>Last 6 months</option>
                <option value={365}>Last 12 months</option>
              </select>
            </div>
            <button className="btn btn-primary" onClick={fetchData}>
              <Icons.Refresh /> <span className="btn-text">Refresh</span>
            </button>
            <button className="btn btn-secondary" onClick={() => setShowConfig(true)}>
              <Icons.Settings /> <span className="btn-text">API Settings</span>
            </button>
          </div>
        </div>

        {/* API Configuration Modal */}
        <ModernApiConfig
          apiConfig={apiConfig}
          setApiConfig={setApiConfig}
          onSave={handleSaveConfig}
          showConfig={showConfig}
          setShowConfig={setShowConfig}
        />

        {/* Error Message */}
        {error && (
          <div style={{
            padding: '12px',
            backgroundColor: '#FEE2E2',
            color: '#991B1B',
            borderRadius: '8px',
            marginBottom: '20px',
            border: '1px solid #FECACA'
          }}>
            {error}
          </div>
        )}

        {/* Dashboard Content */}
        {loading ? (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '300px',
            fontSize: '1.2rem',
            color: 'var(--gray-500)'
          }}>
            Loading dashboard data...
          </div>
        ) : (
          <>
            {/* Stats Cards */}
            <ModernStats stats={stats} />

            {/* Charts Section */}
            <div className="dashboard-grid col-span-12">
              <div className="col-span-4">
                <ModernAddReading
                  newLevel={newLevel}
                  setNewLevel={setNewLevel}
                  handleAddReading={handleAddReading}
                />
              </div>
              <div className="col-span-8">
                <ModernTankLevelChart
                  data={recentLevels}
                  title="Recent Tank Levels (Last 3 Days)"
                  timeFormat={{ month: 'short', day: 'numeric', hour: '2-digit' }}
                  color="#4cc9f0"
                />
              </div>
            </div>

            <div className="dashboard-grid col-span-12">
              <div className="col-span-12">
                <ModernTankLevelChart
                  data={tankLevels}
                  title={`Historical Tank Levels (${timeRange} Days)`}
                  timeFormat={{ month: 'short', day: 'numeric' }}
                  color="#4361ee"
                />
              </div>
            </div>

            {/* Anomalies Section */}
            <div className="dashboard-grid col-span-12">
              {anomalies.length > 0 ? (
                <>
                  <div className="col-span-6">
                    <ModernAnomaliesChart data={tankLevels} anomalies={anomalies} />
                  </div>
                  <div className="col-span-6">
                    <ModernAnomaliesList anomalies={anomalies} />
                  </div>
                </>
              ) : (
                <div className="col-span-12">
                  <div className="card" style={{ textAlign: 'center', padding: '40px 20px' }}>
                    <div style={{ fontSize: '1.2rem', fontWeight: '600', color: 'var(--gray-700)', marginBottom: '10px' }}>
                      No Anomalies Detected
                    </div>
                    <p style={{ color: 'var(--gray-500)' }}>
                      No anomalies were detected in the selected time range.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default ModernApp;
