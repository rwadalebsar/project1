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
  Snackbar
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import SaveIcon from '@mui/icons-material/Save';
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew';
import PowerOffIcon from '@mui/icons-material/PowerOff';
import DeleteIcon from '@mui/icons-material/Delete';

const MQTTConfig = () => {
  const { t } = useTranslation();
  const { token } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [config, setConfig] = useState({
    enabled: false,
    broker: 'localhost',
    port: 1883,
    username: '',
    password: '',
    client_id: '',
    topic_prefix: 'tanks',
    use_ssl: false
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

  // Load MQTT configuration
  useEffect(() => {
    fetchConfig();
    fetchStatus();
    fetchData();
  }, []);

  // Fetch MQTT configuration
  const fetchConfig = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/mqtt/config', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      } else {
        console.error('Failed to fetch MQTT configuration');
        showSnackbar('Failed to fetch MQTT configuration', 'error');
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
      const response = await fetch('/api/mqtt/config', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
        showSnackbar('MQTT configuration saved successfully', 'success');
        fetchStatus();
      } else {
        console.error('Failed to save MQTT configuration');
        showSnackbar('Failed to save MQTT configuration', 'error');
      }
    } catch (error) {
      console.error('Error saving MQTT configuration:', error);
      showSnackbar('Error saving MQTT configuration', 'error');
    } finally {
      setSaving(false);
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
      <Card>
        <CardHeader 
          title={t('mqtt.configuration')} 
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
