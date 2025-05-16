import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Checkbox,
  CircularProgress,
  Divider,
  FormControlLabel,
  Grid,
  IconButton,
  Paper,
  Switch,
  TextField,
  Typography,
  Alert,
  Snackbar,
  Tooltip
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import SaveIcon from '@mui/icons-material/Save';
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew';
import PowerOffIcon from '@mui/icons-material/PowerOff';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import TankSelector from '../tanks/TankSelector';

const MQTTConfig = () => {
  const { t } = useTranslation();
  const { token } = useAuth();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [selectedConnectionId, setSelectedConnectionId] = useState(null);
  const [selectedTank, setSelectedTank] = useState('tank1');
  const [showAddForm, setShowAddForm] = useState(false);
  const [connections, setConnections] = useState([]);
  const [config, setConfig] = useState({
    id: '',
    name: 'Default MQTT Connection',
    enabled: false,
    broker: 'localhost',
    port: 1883,
    username: '',
    password: '',
    client_id: '',
    topic_prefix: 'tanks',
    use_ssl: false,
    tank_id: 'tank1'
  });
  const [status, setStatus] = useState({
    connected: false,
    last_error: null
  });
  const [mqttData, setMqttData] = useState([]);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info'
  });

  // Load MQTT connections from localStorage
  useEffect(() => {
    const savedConnections = localStorage.getItem('mqttConnections');
    if (savedConnections) {
      try {
        const parsedConnections = JSON.parse(savedConnections);
        if (Array.isArray(parsedConnections) && parsedConnections.length > 0) {
          setConnections(parsedConnections);
          // Select the first connection by default
          setSelectedConnectionId(parsedConnections[0].id);
          setConfig(parsedConnections[0]);
          setSelectedTank(parsedConnections[0].tank_id || 'tank1');
        } else {
          // Create a default connection if none exists
          createDefaultConnection();
        }
      } catch (error) {
        console.error('Error parsing MQTT connections from localStorage:', error);
        createDefaultConnection();
      }
    } else {
      // Create a default connection if none exists
      createDefaultConnection();
    }
    setLoading(false);
  }, []);

  // Save connections to localStorage when they change
  useEffect(() => {
    if (connections.length > 0) {
      localStorage.setItem('mqttConnections', JSON.stringify(connections));
    }
  }, [connections]);

  // Fetch status and data when selected connection changes
  useEffect(() => {
    if (selectedConnectionId) {
      fetchStatus();
      fetchData();
    }
  }, [selectedConnectionId]);

  // Create a default connection
  const createDefaultConnection = () => {
    const defaultConnection = {
      id: `mqtt-${Date.now()}`,
      name: 'Default MQTT Connection',
      enabled: false,
      broker: 'localhost',
      port: 1883,
      username: '',
      password: '',
      client_id: '',
      topic_prefix: 'tanks',
      use_ssl: false,
      tank_id: 'tank1'
    };
    setConnections([defaultConnection]);
    setSelectedConnectionId(defaultConnection.id);
    setConfig(defaultConnection);
    setSelectedTank(defaultConnection.tank_id);
  };

  // Fetch MQTT configuration
  const fetchConfig = async () => {
    try {
      setLoading(true);
      // In a real app, you would fetch from the server
      // For now, we're using localStorage

      // Find the selected connection
      const selectedConnection = connections.find(conn => conn.id === selectedConnectionId);
      if (selectedConnection) {
        setConfig(selectedConnection);
        setSelectedTank(selectedConnection.tank_id || 'tank1');
      }
    } catch (error) {
      console.error('Error fetching MQTT configuration:', error);
      showSnackbar('Error fetching MQTT configuration', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch MQTT status
  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/mqtt/status', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      } else {
        console.error('Failed to fetch MQTT status');
      }
    } catch (error) {
      console.error('Error fetching MQTT status:', error);
    }
  };

  // Fetch MQTT data
  const fetchData = async () => {
    try {
      const response = await fetch('/api/mqtt/data', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setMqttData(data);
      } else {
        console.error('Failed to fetch MQTT data');
      }
    } catch (error) {
      console.error('Error fetching MQTT data:', error);
    }
  };

  // Save MQTT configuration
  const saveConfig = async () => {
    try {
      setSaving(true);

      // Update the tank_id in the config
      const updatedConfig = {
        ...config,
        tank_id: selectedTank
      };

      // In a real app, you would save to the server
      // For now, we're using localStorage

      // Update the connection in the connections array
      const updatedConnections = connections.map(conn =>
        conn.id === selectedConnectionId ? updatedConfig : conn
      );

      setConnections(updatedConnections);
      setConfig(updatedConfig);

      showSnackbar('MQTT configuration saved successfully', 'success');
      fetchStatus();
    } catch (error) {
      console.error('Error saving MQTT configuration:', error);
      showSnackbar('Error saving MQTT configuration', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Add a new MQTT connection
  const addConnection = () => {
    const newConnection = {
      id: `mqtt-${Date.now()}`,
      name: `MQTT Connection ${connections.length + 1}`,
      enabled: false,
      broker: 'localhost',
      port: 1883,
      username: '',
      password: '',
      client_id: '',
      topic_prefix: 'tanks',
      use_ssl: false,
      tank_id: selectedTank
    };

    const updatedConnections = [...connections, newConnection];
    setConnections(updatedConnections);
    setSelectedConnectionId(newConnection.id);
    setConfig(newConnection);
    setShowAddForm(false);

    showSnackbar('New MQTT connection added', 'success');
  };

  // Delete an MQTT connection
  const deleteConnection = (connectionId) => {
    if (connections.length <= 1) {
      showSnackbar('Cannot delete the only connection', 'error');
      return;
    }

    const updatedConnections = connections.filter(conn => conn.id !== connectionId);
    setConnections(updatedConnections);

    // If the deleted connection was selected, select the first available connection
    if (selectedConnectionId === connectionId) {
      setSelectedConnectionId(updatedConnections[0].id);
      setConfig(updatedConnections[0]);
      setSelectedTank(updatedConnections[0].tank_id || 'tank1');
    }

    showSnackbar('MQTT connection deleted', 'success');
  };

  // Handle connection selection
  const handleConnectionChange = (connectionId) => {
    setSelectedConnectionId(connectionId);
    const selectedConnection = connections.find(conn => conn.id === connectionId);
    if (selectedConnection) {
      setConfig(selectedConnection);
      setSelectedTank(selectedConnection.tank_id || 'tank1');
    }
  };

  // Connect to MQTT broker
  const connectMQTT = async () => {
    try {
      setConnecting(true);
      const response = await fetch('/api/mqtt/connect', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        showSnackbar('Connected to MQTT broker successfully', 'success');
        fetchStatus();
      } else {
        const errorData = await response.json();
        console.error('Failed to connect to MQTT broker:', errorData.detail);
        showSnackbar(`Failed to connect: ${errorData.detail}`, 'error');
      }
    } catch (error) {
      console.error('Error connecting to MQTT broker:', error);
      showSnackbar('Error connecting to MQTT broker', 'error');
    } finally {
      setConnecting(false);
    }
  };

  // Disconnect from MQTT broker
  const disconnectMQTT = async () => {
    try {
      setConnecting(true);
      const response = await fetch('/api/mqtt/disconnect', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        showSnackbar('Disconnected from MQTT broker successfully', 'success');
        fetchStatus();
      } else {
        console.error('Failed to disconnect from MQTT broker');
        showSnackbar('Failed to disconnect from MQTT broker', 'error');
      }
    } catch (error) {
      console.error('Error disconnecting from MQTT broker:', error);
      showSnackbar('Error disconnecting from MQTT broker', 'error');
    } finally {
      setConnecting(false);
    }
  };

  // Clear MQTT data
  const clearData = async () => {
    try {
      const response = await fetch('/api/mqtt/clear-data', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setMqttData([]);
        showSnackbar('MQTT data cleared successfully', 'success');
      } else {
        console.error('Failed to clear MQTT data');
        showSnackbar('Failed to clear MQTT data', 'error');
      }
    } catch (error) {
      console.error('Error clearing MQTT data:', error);
      showSnackbar('Error clearing MQTT data', 'error');
    }
  };

  // Handle input change
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setConfig({
      ...config,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  // Handle tank selection
  const handleTankChange = (tankId) => {
    setSelectedTank(tankId);
  };

  // Show snackbar
  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({
      open: true,
      message,
      severity
    });
  };

  // Handle snackbar close
  const handleSnackbarClose = () => {
    setSnackbar({
      ...snackbar,
      open: false
    });
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Connection Selector */}
      <Card sx={{ mb: 3 }}>
        <CardHeader
          title={t('mqtt.connections')}
          action={
            <Tooltip title={t('mqtt.addConnection')}>
              <IconButton onClick={addConnection} color="primary">
                <AddIcon />
              </IconButton>
            </Tooltip>
          }
        />
        <Divider />
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {connections.map((conn) => (
                  <Button
                    key={conn.id}
                    variant={selectedConnectionId === conn.id ? "contained" : "outlined"}
                    color={selectedConnectionId === conn.id ? "primary" : "inherit"}
                    onClick={() => handleConnectionChange(conn.id)}
                    sx={{ mb: 1, display: 'flex', justifyContent: 'space-between', minWidth: '200px' }}
                  >
                    <span>{conn.name}</span>
                    {connections.length > 1 && (
                      <Tooltip title={t('mqtt.deleteConnection')}>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteConnection(conn.id);
                          }}
                          sx={{ ml: 1 }}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Button>
                ))}
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Configuration Card */}
      <Card>
        <CardHeader
          title={`${t('mqtt.configuration')}: ${config.name}`}
          action={
            <IconButton onClick={fetchConfig}>
              <RefreshIcon />
            </IconButton>
          }
        />
        <Divider />
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.enabled}
                    onChange={handleChange}
                    name="enabled"
                    color="primary"
                  />
                }
                label={t('mqtt.enabled')}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('mqtt.connectionName')}
                name="name"
                value={config.name}
                onChange={handleChange}
                helperText={t('mqtt.connectionNameHelp')}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  {t('mqtt.associatedTank')}
                </Typography>
                <TankSelector
                  selectedTank={selectedTank}
                  onSelectTank={handleTankChange}
                />
              </Box>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('mqtt.broker')}
                name="broker"
                value={config.broker}
                onChange={handleChange}
                disabled={!config.enabled}
                helperText={t('mqtt.brokerHelp')}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('mqtt.port')}
                name="port"
                type="number"
                value={config.port}
                onChange={handleChange}
                disabled={!config.enabled}
                helperText={t('mqtt.portHelp')}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('mqtt.username')}
                name="username"
                value={config.username}
                onChange={handleChange}
                disabled={!config.enabled}
                helperText={t('mqtt.usernameHelp')}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('mqtt.password')}
                name="password"
                type="password"
                value={config.password}
                onChange={handleChange}
                disabled={!config.enabled}
                helperText={t('mqtt.passwordHelp')}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('mqtt.clientId')}
                name="client_id"
                value={config.client_id}
                onChange={handleChange}
                disabled={!config.enabled}
                helperText={t('mqtt.clientIdHelp')}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('mqtt.topicPrefix')}
                name="topic_prefix"
                value={config.topic_prefix}
                onChange={handleChange}
                disabled={!config.enabled}
                helperText={t('mqtt.topicPrefixHelp')}
              />
            </Grid>

            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={config.use_ssl}
                    onChange={handleChange}
                    name="use_ssl"
                    color="primary"
                    disabled={!config.enabled}
                  />
                }
                label={t('mqtt.useSSL')}
              />
            </Grid>

            <Grid item xs={12}>
              <Box display="flex" justifyContent="space-between">
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<SaveIcon />}
                  onClick={saveConfig}
                  disabled={saving || !config.enabled}
                >
                  {saving ? <CircularProgress size={24} /> : t('common.save')}
                </Button>

                {status.connected ? (
                  <Button
                    variant="contained"
                    color="secondary"
                    startIcon={<PowerOffIcon />}
                    onClick={disconnectMQTT}
                    disabled={connecting || !config.enabled}
                  >
                    {connecting ? <CircularProgress size={24} /> : t('mqtt.disconnect')}
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<PowerSettingsNewIcon />}
                    onClick={connectMQTT}
                    disabled={connecting || !config.enabled}
                  >
                    {connecting ? <CircularProgress size={24} /> : t('mqtt.connect')}
                  </Button>
                )}
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Box mt={3}>
        <Card>
          <CardHeader
            title={t('mqtt.status')}
            action={
              <IconButton onClick={fetchStatus}>
                <RefreshIcon />
              </IconButton>
            }
          />
          <Divider />
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Alert severity={status.connected ? "success" : "info"}>
                  {status.connected
                    ? t('mqtt.connectedTo', { broker: status.broker, port: status.port })
                    : t('mqtt.notConnected')}
                </Alert>
              </Grid>

              {status.last_error && (
                <Grid item xs={12}>
                  <Alert severity="error">
                    {t('mqtt.lastError')}: {status.last_error}
                  </Alert>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      </Box>

      <Box mt={3}>
        <Card>
          <CardHeader
            title={t('mqtt.receivedData')}
            action={
              <Box>
                <IconButton onClick={fetchData} sx={{ mr: 1 }}>
                  <RefreshIcon />
                </IconButton>
                <IconButton onClick={clearData} color="error">
                  <DeleteIcon />
                </IconButton>
              </Box>
            }
          />
          <Divider />
          <CardContent>
            {mqttData.length === 0 ? (
              <Typography variant="body2" color="textSecondary">
                {t('mqtt.noData')}
              </Typography>
            ) : (
              <Box sx={{ maxHeight: '300px', overflow: 'auto' }}>
                {mqttData.map((item, index) => (
                  <Paper key={index} sx={{ p: 2, mb: 2 }}>
                    <Typography variant="subtitle2">
                      {new Date(item.timestamp).toLocaleString()}
                    </Typography>
                    <Typography variant="body2">
                      {t('mqtt.tankId')}: {item.tank_id}
                    </Typography>
                    <Typography variant="body2">
                      {t('mqtt.level')}: {item.level}
                    </Typography>
                  </Paper>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
      >
        <Alert onClose={handleSnackbarClose} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MQTTConfig;
