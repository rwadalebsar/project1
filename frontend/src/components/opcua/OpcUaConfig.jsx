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
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip,
  Tooltip
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import SaveIcon from '@mui/icons-material/Save';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SyncIcon from '@mui/icons-material/Sync';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import LinkIcon from '@mui/icons-material/Link';
import LinkOffIcon from '@mui/icons-material/LinkOff';
import AddIcon from '@mui/icons-material/Add';
import TankSelector from '../tanks/TankSelector';

const OpcUaConfig = () => {
  const { t } = useTranslation();
  const { token } = useAuth();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [selectedConnectionId, setSelectedConnectionId] = useState(null);
  const [selectedTank, setSelectedTank] = useState('tank1');
  const [connections, setConnections] = useState([]);
  const [config, setConfig] = useState({
    id: '',
    name: 'Default OPC UA Connection',
    enabled: false,
    endpoint: 'opc.tcp://localhost:4840/freeopcua/server/',
    security_mode: 'None',
    security_policy: 'None',
    certificate_path: '',
    private_key_path: '',
    username: '',
    password: '',
    namespace: 'http://examples.freeopcua.github.io',
    node_paths: {
      tanks: ['Objects', 'Server', 'Tanks'],
      tank_level: ['Objects', 'Server', 'Tanks', '{tank_id}', 'Level']
    },
    polling_interval: 60,
    tank_id: 'tank1'
  });
  const [status, setStatus] = useState({
    connected: false,
    last_error: null
  });
  const [opcuaData, setOpcuaData] = useState([]);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  const [monitoring, setMonitoring] = useState(false);

  // Load OPC UA connections from localStorage
  useEffect(() => {
    const savedConnections = localStorage.getItem('opcuaConnections');
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
        console.error('Error parsing OPC UA connections from localStorage:', error);
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
      localStorage.setItem('opcuaConnections', JSON.stringify(connections));
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
      id: `opcua-${Date.now()}`,
      name: 'Default OPC UA Connection',
      enabled: false,
      endpoint: 'opc.tcp://localhost:4840/freeopcua/server/',
      security_mode: 'None',
      security_policy: 'None',
      certificate_path: '',
      private_key_path: '',
      username: '',
      password: '',
      namespace: 'http://examples.freeopcua.github.io',
      node_paths: {
        tanks: ['Objects', 'Server', 'Tanks'],
        tank_level: ['Objects', 'Server', 'Tanks', '{tank_id}', 'Level']
      },
      polling_interval: 60,
      tank_id: 'tank1'
    };
    setConnections([defaultConnection]);
    setSelectedConnectionId(defaultConnection.id);
    setConfig(defaultConnection);
    setSelectedTank(defaultConnection.tank_id);
  };

  // Fetch OPC UA configuration
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
      console.error('Error fetching OPC UA configuration:', error);
      showSnackbar('Error fetching OPC UA configuration', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch OPC UA status
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
      console.error('Error fetching OPC UA status:', error);
    }
  };

  // Fetch OPC UA data
  const fetchData = async () => {
    try {
      const response = await fetch('/api/opcua/data', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setOpcuaData(data);
      } else {
        console.error('Failed to fetch OPC UA data');
      }
    } catch (error) {
      console.error('Error fetching OPC UA data:', error);
    }
  };

  // Save OPC UA configuration
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

      showSnackbar('OPC UA configuration saved successfully', 'success');
      fetchStatus();
    } catch (error) {
      console.error('Error saving OPC UA configuration:', error);
      showSnackbar('Error saving OPC UA configuration', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Add a new OPC UA connection
  const addConnection = () => {
    const newConnection = {
      id: `opcua-${Date.now()}`,
      name: `OPC UA Connection ${connections.length + 1}`,
      enabled: false,
      endpoint: 'opc.tcp://localhost:4840/freeopcua/server/',
      security_mode: 'None',
      security_policy: 'None',
      certificate_path: '',
      private_key_path: '',
      username: '',
      password: '',
      namespace: 'http://examples.freeopcua.github.io',
      node_paths: {
        tanks: ['Objects', 'Server', 'Tanks'],
        tank_level: ['Objects', 'Server', 'Tanks', '{tank_id}', 'Level']
      },
      polling_interval: 60,
      tank_id: selectedTank
    };

    const updatedConnections = [...connections, newConnection];
    setConnections(updatedConnections);
    setSelectedConnectionId(newConnection.id);
    setConfig(newConnection);

    showSnackbar('New OPC UA connection added', 'success');
  };

  // Delete an OPC UA connection
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

    showSnackbar('OPC UA connection deleted', 'success');
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

  // Test OPC UA connection
  const testConnection = async () => {
    try {
      setConnecting(true);
      const response = await fetch('/api/opcua/test', {
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
        console.error('Failed to test OPC UA connection:', errorData.detail);
        showSnackbar(`Failed to test connection: ${errorData.detail}`, 'error');
      }
    } catch (error) {
      console.error('Error testing OPC UA connection:', error);
      showSnackbar('Error testing OPC UA connection', 'error');
    } finally {
      setConnecting(false);
    }
  };

  // Connect to OPC UA server
  const connect = async () => {
    try {
      setConnecting(true);
      const response = await fetch('/api/opcua/connect', {
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
        console.error('Failed to connect to OPC UA server:', errorData.detail);
        showSnackbar(`Failed to connect: ${errorData.detail}`, 'error');
      }
    } catch (error) {
      console.error('Error connecting to OPC UA server:', error);
      showSnackbar('Error connecting to OPC UA server', 'error');
    } finally {
      setConnecting(false);
    }
  };

  // Disconnect from OPC UA server
  const disconnect = async () => {
    try {
      setConnecting(true);
      const response = await fetch('/api/opcua/disconnect', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          showSnackbar(data.message, 'success');
          setStatus({ ...status, connected: false, last_error: null });
        } else {
          showSnackbar(data.message, 'error');
        }
      } else {
        const errorData = await response.json();
        console.error('Failed to disconnect from OPC UA server:', errorData.detail);
        showSnackbar(`Failed to disconnect: ${errorData.detail}`, 'error');
      }
    } catch (error) {
      console.error('Error disconnecting from OPC UA server:', error);
      showSnackbar('Error disconnecting from OPC UA server', 'error');
    } finally {
      setConnecting(false);
    }
  };

  // Start monitoring OPC UA server
  const startMonitoring = async () => {
    try {
      setFetching(true);
      const response = await fetch('/api/opcua/start-monitoring', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          showSnackbar(data.message, 'success');
          setMonitoring(true);
        } else {
          showSnackbar(data.message, 'error');
        }
      } else {
        const errorData = await response.json();
        console.error('Failed to start monitoring OPC UA server:', errorData.detail);
        showSnackbar(`Failed to start monitoring: ${errorData.detail}`, 'error');
      }
    } catch (error) {
      console.error('Error starting monitoring OPC UA server:', error);
      showSnackbar('Error starting monitoring OPC UA server', 'error');
    } finally {
      setFetching(false);
    }
  };

  // Stop monitoring OPC UA server
  const stopMonitoring = async () => {
    try {
      setFetching(true);
      const response = await fetch('/api/opcua/stop-monitoring', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          showSnackbar(data.message, 'success');
          setMonitoring(false);
        } else {
          showSnackbar(data.message, 'error');
        }
      } else {
        const errorData = await response.json();
        console.error('Failed to stop monitoring OPC UA server:', errorData.detail);
        showSnackbar(`Failed to stop monitoring: ${errorData.detail}`, 'error');
      }
    } catch (error) {
      console.error('Error stopping monitoring OPC UA server:', error);
      showSnackbar('Error stopping monitoring OPC UA server', 'error');
    } finally {
      setFetching(false);
    }
  };

  // Fetch new data from OPC UA server
  const fetchNewData = async () => {
    try {
      setFetching(true);
      const response = await fetch('/api/opcua/fetch', {
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
        console.error('Failed to fetch new data from OPC UA server');
        showSnackbar('Failed to fetch new data from OPC UA server', 'error');
      }
    } catch (error) {
      console.error('Error fetching new data from OPC UA server:', error);
      showSnackbar('Error fetching new data from OPC UA server', 'error');
    } finally {
      setFetching(false);
    }
  };

  // Clear OPC UA data
  const clearData = async () => {
    try {
      const response = await fetch('/api/opcua/clear-data', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setOpcuaData([]);
        showSnackbar('OPC UA data cleared successfully', 'success');
      } else {
        console.error('Failed to clear OPC UA data');
        showSnackbar('Failed to clear OPC UA data', 'error');
      }
    } catch (error) {
      console.error('Error clearing OPC UA data:', error);
      showSnackbar('Error clearing OPC UA data', 'error');
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

  // Handle node path change
  const handleNodePathChange = (pathType, index, value) => {
    const newPaths = { ...config.node_paths };
    const pathArray = [...newPaths[pathType]];
    pathArray[index] = value;
    newPaths[pathType] = pathArray;

    setConfig({
      ...config,
      node_paths: newPaths
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
          title={t('opcua.connections')}
          action={
            <Tooltip title={t('opcua.addConnection')}>
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
                      <Tooltip title={t('opcua.deleteConnection')}>
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
          title={`${t('opcua.configuration')}: ${config.name}`}
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
                label={t('opcua.enabled')}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('opcua.connectionName')}
                name="name"
                value={config.name}
                onChange={handleChange}
                helperText={t('opcua.connectionNameHelp')}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  {t('opcua.associatedTank')}
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
                label={t('opcua.endpoint')}
                name="endpoint"
                value={config.endpoint}
                onChange={handleChange}
                disabled={!config.enabled}
                helperText={t('opcua.endpointHelp')}
                required
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth disabled={!config.enabled}>
                <InputLabel id="security-mode-label">{t('opcua.securityMode')}</InputLabel>
                <Select
                  labelId="security-mode-label"
                  name="security_mode"
                  value={config.security_mode}
                  onChange={handleChange}
                  label={t('opcua.securityMode')}
                >
                  <MenuItem value="None">{t('opcua.securityModes.none')}</MenuItem>
                  <MenuItem value="Sign">{t('opcua.securityModes.sign')}</MenuItem>
                  <MenuItem value="SignAndEncrypt">{t('opcua.securityModes.signAndEncrypt')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth disabled={!config.enabled || config.security_mode === 'None'}>
                <InputLabel id="security-policy-label">{t('opcua.securityPolicy')}</InputLabel>
                <Select
                  labelId="security-policy-label"
                  name="security_policy"
                  value={config.security_policy}
                  onChange={handleChange}
                  label={t('opcua.securityPolicy')}
                >
                  <MenuItem value="None">{t('opcua.securityPolicies.none')}</MenuItem>
                  <MenuItem value="Basic128Rsa15">{t('opcua.securityPolicies.basic128Rsa15')}</MenuItem>
                  <MenuItem value="Basic256">{t('opcua.securityPolicies.basic256')}</MenuItem>
                  <MenuItem value="Basic256Sha256">{t('opcua.securityPolicies.basic256Sha256')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {(config.security_mode !== 'None' || config.security_policy !== 'None') && (
              <>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label={t('opcua.certificatePath')}
                    name="certificate_path"
                    value={config.certificate_path}
                    onChange={handleChange}
                    disabled={!config.enabled}
                    helperText={t('opcua.certificatePathHelp')}
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label={t('opcua.privateKeyPath')}
                    name="private_key_path"
                    value={config.private_key_path}
                    onChange={handleChange}
                    disabled={!config.enabled}
                    helperText={t('opcua.privateKeyPathHelp')}
                  />
                </Grid>
              </>
            )}

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('opcua.username')}
                name="username"
                value={config.username}
                onChange={handleChange}
                disabled={!config.enabled}
                helperText={t('opcua.usernameHelp')}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('opcua.password')}
                name="password"
                type="password"
                value={config.password}
                onChange={handleChange}
                disabled={!config.enabled}
                helperText={t('opcua.passwordHelp')}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('opcua.namespace')}
                name="namespace"
                value={config.namespace}
                onChange={handleChange}
                disabled={!config.enabled}
                helperText={t('opcua.namespaceHelp')}
              />
            </Grid>

            <Grid item xs={12}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>{t('opcua.nodePaths')}</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" gutterBottom>
                        {t('opcua.tanksNodePath')}
                      </Typography>
                      <Box sx={{ mb: 2 }}>
                        {config.node_paths.tanks.map((path, index) => (
                          <TextField
                            key={`tanks-${index}`}
                            fullWidth
                            value={path}
                            onChange={(e) => handleNodePathChange('tanks', index, e.target.value)}
                            disabled={!config.enabled}
                            margin="dense"
                            size="small"
                            InputProps={{
                              startAdornment: index > 0 ? <Box component="span" sx={{ mr: 1 }}>→</Box> : null
                            }}
                          />
                        ))}
                      </Box>
                    </Grid>

                    <Grid item xs={12}>
                      <Typography variant="subtitle2" gutterBottom>
                        {t('opcua.tankLevelNodePath')}
                      </Typography>
                      <Box>
                        {config.node_paths.tank_level.map((path, index) => (
                          <TextField
                            key={`tank_level-${index}`}
                            fullWidth
                            value={path}
                            onChange={(e) => handleNodePathChange('tank_level', index, e.target.value)}
                            disabled={!config.enabled}
                            margin="dense"
                            size="small"
                            InputProps={{
                              startAdornment: index > 0 ? <Box component="span" sx={{ mr: 1 }}>→</Box> : null
                            }}
                          />
                        ))}
                      </Box>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('opcua.pollingInterval')}
                name="polling_interval"
                type="number"
                value={config.polling_interval}
                onChange={handleChange}
                disabled={!config.enabled}
                helperText={t('opcua.pollingIntervalHelp')}
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
                  disabled={connecting || !config.enabled}
                >
                  {connecting ? <CircularProgress size={24} /> : t('opcua.testConnection')}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Box mt={3}>
        <Card>
          <CardHeader
            title={t('opcua.connection')}
            action={
              <Box>
                {!status.connected ? (
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<LinkIcon />}
                    onClick={connect}
                    disabled={connecting || !config.enabled}
                    size="small"
                    sx={{ mr: 1 }}
                  >
                    {connecting ? <CircularProgress size={24} /> : t('opcua.connect')}
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    color="error"
                    startIcon={<LinkOffIcon />}
                    onClick={disconnect}
                    disabled={connecting}
                    size="small"
                    sx={{ mr: 1 }}
                  >
                    {connecting ? <CircularProgress size={24} /> : t('opcua.disconnect')}
                  </Button>
                )}

                {status.connected && !monitoring ? (
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<PlayArrowIcon />}
                    onClick={startMonitoring}
                    disabled={fetching || !status.connected}
                    size="small"
                  >
                    {fetching ? <CircularProgress size={24} /> : t('opcua.startMonitoring')}
                  </Button>
                ) : status.connected && monitoring ? (
                  <Button
                    variant="contained"
                    color="warning"
                    startIcon={<StopIcon />}
                    onClick={stopMonitoring}
                    disabled={fetching}
                    size="small"
                  >
                    {fetching ? <CircularProgress size={24} /> : t('opcua.stopMonitoring')}
                  </Button>
                ) : null}
              </Box>
            }
          />
          <Divider />
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Alert severity={status.connected ? "success" : "info"}>
                  {status.connected
                    ? t('opcua.connectedTo', { url: config.endpoint })
                    : t('opcua.notConnected')}
                </Alert>
              </Grid>

              {status.last_error && (
                <Grid item xs={12}>
                  <Alert severity="error">
                    {t('opcua.lastError')}: {status.last_error}
                  </Alert>
                </Grid>
              )}

              <Grid item xs={12}>
                <Box display="flex" alignItems="center">
                  <Typography variant="body2" sx={{ mr: 1 }}>
                    {t('opcua.monitoringStatus')}:
                  </Typography>
                  <Chip
                    label={monitoring ? t('opcua.monitoring') : t('opcua.notMonitoring')}
                    color={monitoring ? "success" : "default"}
                    size="small"
                  />
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Box>

      <Box mt={3}>
        <Card>
          <CardHeader
            title={t('opcua.receivedData')}
            action={
              <Box>
                <IconButton
                  onClick={fetchNewData}
                  sx={{ mr: 1 }}
                  disabled={fetching || !status.connected}
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
            {opcuaData.length === 0 ? (
              <Typography variant="body2" color="textSecondary">
                {t('opcua.noData')}
              </Typography>
            ) : (
              <Box sx={{ maxHeight: '300px', overflow: 'auto' }}>
                {opcuaData.map((item, index) => (
                  <Paper key={index} sx={{ p: 2, mb: 2 }}>
                    <Typography variant="subtitle2">
                      {new Date(item.timestamp).toLocaleString()}
                    </Typography>
                    <Typography variant="body2">
                      {t('opcua.tankId')}: {item.tank_id}
                    </Typography>
                    <Typography variant="body2">
                      {t('opcua.tankName')}: {item.name}
                    </Typography>
                    <Typography variant="body2">
                      {t('opcua.level')}: {item.level}
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

export default OpcUaConfig;
