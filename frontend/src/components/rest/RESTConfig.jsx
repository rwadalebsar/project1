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
  FormControl,
  FormControlLabel,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Switch,
  TextField,
  Typography,
  Alert,
  Snackbar,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import SaveIcon from '@mui/icons-material/Save';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SyncIcon from '@mui/icons-material/Sync';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import TankSelector from '../tanks/TankSelector';

const RESTConfig = () => {
  const { t } = useTranslation();
  const { token } = useAuth();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [selectedConnectionId, setSelectedConnectionId] = useState(null);
  const [selectedTank, setSelectedTank] = useState('tank1');
  const [connections, setConnections] = useState([]);
  const [config, setConfig] = useState({
    id: '',
    name: 'Default REST API Connection',
    enabled: false,
    base_url: 'https://api.example.com',
    api_key: '',
    username: '',
    password: '',
    auth_type: 'none',
    headers: {},
    endpoints: {
      tanks: '/tanks',
      levels: '/tanks/{tank_id}/levels',
      auth: '/auth/token'
    },
    polling_interval: 60,
    tank_id: 'tank1'
  });
  const [status, setStatus] = useState({
    connected: false,
    last_error: null
  });
  const [restData, setRestData] = useState([]);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  const [newHeader, setNewHeader] = useState({ key: '', value: '' });

  // Load REST API connections from localStorage
  useEffect(() => {
    const savedConnections = localStorage.getItem('restConnections');
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
        console.error('Error parsing REST connections from localStorage:', error);
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
      localStorage.setItem('restConnections', JSON.stringify(connections));
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
      id: `rest-${Date.now()}`,
      name: 'Default REST API Connection',
      enabled: false,
      base_url: 'https://api.example.com',
      api_key: '',
      username: '',
      password: '',
      auth_type: 'none',
      headers: {},
      endpoints: {
        tanks: '/tanks',
        levels: '/tanks/{tank_id}/levels',
        auth: '/auth/token'
      },
      polling_interval: 60,
      tank_id: 'tank1'
    };
    setConnections([defaultConnection]);
    setSelectedConnectionId(defaultConnection.id);
    setConfig(defaultConnection);
    setSelectedTank(defaultConnection.tank_id);
  };

  // Fetch REST API configuration
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
      console.error('Error fetching REST API configuration:', error);
      showSnackbar('Error fetching REST API configuration', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch REST API status
  const fetchStatus = async () => {
    try {
      // In a real app, you would fetch from the server
      // For now, we're simulating a status check

      // Find the selected connection
      const selectedConnection = connections.find(conn => conn.id === selectedConnectionId);
      if (selectedConnection) {
        setStatus({
          connected: selectedConnection.enabled,
          last_error: null
        });
      }
    } catch (error) {
      console.error('Error fetching REST API status:', error);
    }
  };

  // Fetch REST API data
  const fetchData = async () => {
    try {
      const response = await fetch('/api/rest/data', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setRestData(data);
      } else {
        console.error('Failed to fetch REST API data');
      }
    } catch (error) {
      console.error('Error fetching REST API data:', error);
    }
  };

  // Save REST API configuration
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

      showSnackbar('REST API configuration saved successfully', 'success');
      fetchStatus();
    } catch (error) {
      console.error('Error saving REST API configuration:', error);
      showSnackbar('Error saving REST API configuration', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Add a new REST API connection
  const addConnection = () => {
    const newConnection = {
      id: `rest-${Date.now()}`,
      name: `REST API Connection ${connections.length + 1}`,
      enabled: false,
      base_url: 'https://api.example.com',
      api_key: '',
      username: '',
      password: '',
      auth_type: 'none',
      headers: {},
      endpoints: {
        tanks: '/tanks',
        levels: '/tanks/{tank_id}/levels',
        auth: '/auth/token'
      },
      polling_interval: 60,
      tank_id: selectedTank
    };

    const updatedConnections = [...connections, newConnection];
    setConnections(updatedConnections);
    setSelectedConnectionId(newConnection.id);
    setConfig(newConnection);

    showSnackbar('New REST API connection added', 'success');
  };

  // Delete a REST API connection
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

    showSnackbar('REST API connection deleted', 'success');
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

  // Test REST API connection
  const testConnection = async () => {
    try {
      setFetching(true);
      const response = await fetch('/api/rest/test', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          showSnackbar(data.message, 'success');
          setStatus({ ...status, connected: true, last_error: null });
        } else {
          showSnackbar(data.message, 'error');
          setStatus({ ...status, connected: false, last_error: data.message });
        }
      } else {
        const errorData = await response.json();
        console.error('Failed to test REST API connection:', errorData.detail);
        showSnackbar(`Failed to test connection: ${errorData.detail}`, 'error');
      }
    } catch (error) {
      console.error('Error testing REST API connection:', error);
      showSnackbar('Error testing REST API connection', 'error');
    } finally {
      setFetching(false);
    }
  };

  // Fetch new data from REST API
  const fetchNewData = async () => {
    try {
      setFetching(true);
      const response = await fetch('/api/rest/fetch', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        showSnackbar(result.message, 'success');
        fetchData();
      } else {
        console.error('Failed to fetch new data from REST API');
        showSnackbar('Failed to fetch new data from REST API', 'error');
      }
    } catch (error) {
      console.error('Error fetching new data from REST API:', error);
      showSnackbar('Error fetching new data from REST API', 'error');
    } finally {
      setFetching(false);
    }
  };

  // Clear REST API data
  const clearData = async () => {
    try {
      const response = await fetch('/api/rest/clear-data', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setRestData([]);
        showSnackbar('REST API data cleared successfully', 'success');
      } else {
        console.error('Failed to clear REST API data');
        showSnackbar('Failed to clear REST API data', 'error');
      }
    } catch (error) {
      console.error('Error clearing REST API data:', error);
      showSnackbar('Error clearing REST API data', 'error');
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

  // Handle endpoint change
  const handleEndpointChange = (e) => {
    const { name, value } = e.target;
    setConfig({
      ...config,
      endpoints: {
        ...config.endpoints,
        [name]: value
      }
    });
  };

  // Handle new header change
  const handleNewHeaderChange = (e) => {
    const { name, value } = e.target;
    setNewHeader({
      ...newHeader,
      [name]: value
    });
  };

  // Add new header
  const addHeader = () => {
    if (newHeader.key.trim() === '') return;

    setConfig({
      ...config,
      headers: {
        ...config.headers,
        [newHeader.key]: newHeader.value
      }
    });

    setNewHeader({ key: '', value: '' });
  };

  // Remove header
  const removeHeader = (key) => {
    const newHeaders = { ...config.headers };
    delete newHeaders[key];

    setConfig({
      ...config,
      headers: newHeaders
    });
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
          title={t('rest.connections')}
          action={
            <Tooltip title={t('rest.addConnection')}>
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
                      <Tooltip title={t('rest.deleteConnection')}>
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
          title={`${t('rest.configuration')}: ${config.name}`}
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
                label={t('rest.enabled')}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('rest.connectionName')}
                name="name"
                value={config.name}
                onChange={handleChange}
                helperText={t('rest.connectionNameHelp')}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  {t('rest.associatedTank')}
                </Typography>
                <TankSelector
                  selectedTank={selectedTank}
                  onSelectTank={handleTankChange}
                />
              </Box>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('rest.baseUrl')}
                name="base_url"
                value={config.base_url}
                onChange={handleChange}
                disabled={!config.enabled}
                helperText={t('rest.baseUrlHelp')}
                required
              />
            </Grid>

            <Grid item xs={12}>
              <FormControl fullWidth disabled={!config.enabled}>
                <InputLabel id="auth-type-label">{t('rest.authType')}</InputLabel>
                <Select
                  labelId="auth-type-label"
                  name="auth_type"
                  value={config.auth_type}
                  onChange={handleChange}
                  label={t('rest.authType')}
                >
                  <MenuItem value="none">{t('rest.authTypes.none')}</MenuItem>
                  <MenuItem value="api_key">{t('rest.authTypes.apiKey')}</MenuItem>
                  <MenuItem value="basic">{t('rest.authTypes.basic')}</MenuItem>
                  <MenuItem value="oauth2">{t('rest.authTypes.oauth2')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {config.auth_type === 'api_key' && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label={t('rest.apiKey')}
                  name="api_key"
                  value={config.api_key}
                  onChange={handleChange}
                  disabled={!config.enabled}
                  helperText={t('rest.apiKeyHelp')}
                  type="password"
                />
              </Grid>
            )}

            {(config.auth_type === 'basic' || config.auth_type === 'oauth2') && (
              <>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label={t('rest.username')}
                    name="username"
                    value={config.username}
                    onChange={handleChange}
                    disabled={!config.enabled}
                    helperText={t('rest.usernameHelp')}
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label={t('rest.password')}
                    name="password"
                    type="password"
                    value={config.password}
                    onChange={handleChange}
                    disabled={!config.enabled}
                    helperText={t('rest.passwordHelp')}
                  />
                </Grid>
              </>
            )}

            <Grid item xs={12}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>{t('rest.endpoints')}</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label={t('rest.tanksEndpoint')}
                        name="tanks"
                        value={config.endpoints.tanks}
                        onChange={handleEndpointChange}
                        disabled={!config.enabled}
                        helperText={t('rest.tanksEndpointHelp')}
                      />
                    </Grid>

                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label={t('rest.levelsEndpoint')}
                        name="levels"
                        value={config.endpoints.levels}
                        onChange={handleEndpointChange}
                        disabled={!config.enabled}
                        helperText={t('rest.levelsEndpointHelp')}
                      />
                    </Grid>

                    {config.auth_type === 'oauth2' && (
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          label={t('rest.authEndpoint')}
                          name="auth"
                          value={config.endpoints.auth}
                          onChange={handleEndpointChange}
                          disabled={!config.enabled}
                          helperText={t('rest.authEndpointHelp')}
                        />
                      </Grid>
                    )}
                  </Grid>
                </AccordionDetails>
              </Accordion>
            </Grid>

            <Grid item xs={12}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>{t('rest.headers')}</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    {Object.entries(config.headers).map(([key, value]) => (
                      <Grid item xs={12} key={key} container spacing={1} alignItems="center">
                        <Grid item xs={5}>
                          <TextField
                            fullWidth
                            value={key}
                            disabled
                            label={t('rest.headerKey')}
                          />
                        </Grid>
                        <Grid item xs={5}>
                          <TextField
                            fullWidth
                            value={value}
                            disabled
                            label={t('rest.headerValue')}
                          />
                        </Grid>
                        <Grid item xs={2}>
                          <IconButton
                            color="error"
                            onClick={() => removeHeader(key)}
                            disabled={!config.enabled}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Grid>
                      </Grid>
                    ))}

                    <Grid item xs={12} container spacing={1} alignItems="center">
                      <Grid item xs={5}>
                        <TextField
                          fullWidth
                          value={newHeader.key}
                          onChange={handleNewHeaderChange}
                          name="key"
                          label={t('rest.headerKey')}
                          disabled={!config.enabled}
                        />
                      </Grid>
                      <Grid item xs={5}>
                        <TextField
                          fullWidth
                          value={newHeader.value}
                          onChange={handleNewHeaderChange}
                          name="value"
                          label={t('rest.headerValue')}
                          disabled={!config.enabled}
                        />
                      </Grid>
                      <Grid item xs={2}>
                        <IconButton
                          color="primary"
                          onClick={addHeader}
                          disabled={!config.enabled || !newHeader.key.trim()}
                        >
                          <AddIcon />
                        </IconButton>
                      </Grid>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('rest.pollingInterval')}
                name="polling_interval"
                type="number"
                value={config.polling_interval}
                onChange={handleChange}
                disabled={!config.enabled}
                helperText={t('rest.pollingIntervalHelp')}
                InputProps={{ inputProps: { min: 5, max: 3600 } }}
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

                <Button
                  variant="contained"
                  color="secondary"
                  startIcon={<SyncIcon />}
                  onClick={testConnection}
                  disabled={fetching || !config.enabled}
                >
                  {fetching ? <CircularProgress size={24} /> : t('rest.testConnection')}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Box mt={3}>
        <Card>
          <CardHeader
            title={t('rest.status')}
            action={
              <IconButton onClick={testConnection} disabled={fetching || !config.enabled}>
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
                    ? t('rest.connectedTo', { url: config.base_url })
                    : t('rest.notConnected')}
                </Alert>
              </Grid>

              {status.last_error && (
                <Grid item xs={12}>
                  <Alert severity="error">
                    {t('rest.lastError')}: {status.last_error}
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
            title={t('rest.receivedData')}
            action={
              <Box>
                <IconButton
                  onClick={fetchNewData}
                  sx={{ mr: 1 }}
                  disabled={fetching || !config.enabled}
                >
                  <SyncIcon />
                </IconButton>
                <IconButton onClick={clearData} color="error">
                  <DeleteIcon />
                </IconButton>
              </Box>
            }
          />
          <Divider />
          <CardContent>
            {restData.length === 0 ? (
              <Typography variant="body2" color="textSecondary">
                {t('rest.noData')}
              </Typography>
            ) : (
              <Box sx={{ maxHeight: '300px', overflow: 'auto' }}>
                {restData.map((item, index) => (
                  <Paper key={index} sx={{ p: 2, mb: 2 }}>
                    <Typography variant="subtitle2">
                      {new Date(item.timestamp).toLocaleString()}
                    </Typography>
                    <Typography variant="body2">
                      {t('rest.tankId')}: {item.tank_id}
                    </Typography>
                    <Typography variant="body2">
                      {t('rest.tankName')}: {item.name}
                    </Typography>
                    <Typography variant="body2">
                      {t('rest.level')}: {item.level}
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

export default RESTConfig;
