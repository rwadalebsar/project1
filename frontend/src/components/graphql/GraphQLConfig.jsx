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
  AccordionDetails
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import SaveIcon from '@mui/icons-material/Save';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SyncIcon from '@mui/icons-material/Sync';
import DeleteIcon from '@mui/icons-material/Delete';
import CodeIcon from '@mui/icons-material/Code';

const GraphQLConfig = () => {
  const { t } = useTranslation();
  const { token } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [config, setConfig] = useState({
    enabled: false,
    endpoint: 'https://api.example.com/graphql',
    api_key: '',
    username: '',
    password: '',
    auth_type: 'none',
    auth_endpoint: 'https://api.example.com/auth',
    headers: {},
    queries: {
      tanks: `
        query GetTanks {
          tanks {
            id
            name
            capacity
          }
        }
      `,
      tankLevel: `
        query GetTankLevel($tankId: ID!) {
          tank(id: $tankId) {
            id
            name
            level
            lastUpdated
          }
        }
      `
    },
    polling_interval: 60
  });
  const [status, setStatus] = useState({
    connected: false,
    last_error: null
  });
  const [graphqlData, setGraphqlData] = useState([]);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  const [editingQuery, setEditingQuery] = useState(null);

  // Load GraphQL configuration
  useEffect(() => {
    fetchConfig();
    fetchData();
  }, []);

  // Fetch GraphQL configuration
  const fetchConfig = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/graphql/config', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
        setStatus({
          connected: data.connected || false,
          last_error: data.last_error || null
        });
      } else {
        console.error('Failed to fetch GraphQL configuration');
        showSnackbar('Failed to fetch GraphQL configuration', 'error');
      }
    } catch (error) {
      console.error('Error fetching GraphQL configuration:', error);
      showSnackbar('Error fetching GraphQL configuration', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch GraphQL data
  const fetchData = async () => {
    try {
      const response = await fetch('/api/graphql/data', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setGraphqlData(data);
      } else {
        console.error('Failed to fetch GraphQL data');
      }
    } catch (error) {
      console.error('Error fetching GraphQL data:', error);
    }
  };

  // Save GraphQL configuration
  const saveConfig = async () => {
    try {
      setSaving(true);
      const response = await fetch('/api/graphql/config', {
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
        showSnackbar('GraphQL configuration saved successfully', 'success');
      } else {
        console.error('Failed to save GraphQL configuration');
        showSnackbar('Failed to save GraphQL configuration', 'error');
      }
    } catch (error) {
      console.error('Error saving GraphQL configuration:', error);
      showSnackbar('Error saving GraphQL configuration', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Test GraphQL connection
  const testConnection = async () => {
    try {
      setFetching(true);
      const response = await fetch('/api/graphql/test', {
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
        console.error('Failed to test GraphQL connection:', errorData.detail);
        showSnackbar(`Failed to test connection: ${errorData.detail}`, 'error');
      }
    } catch (error) {
      console.error('Error testing GraphQL connection:', error);
      showSnackbar('Error testing GraphQL connection', 'error');
    } finally {
      setFetching(false);
    }
  };

  // Fetch new data from GraphQL
  const fetchNewData = async () => {
    try {
      setFetching(true);
      const response = await fetch('/api/graphql/fetch', {
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
        console.error('Failed to fetch new data from GraphQL');
        showSnackbar('Failed to fetch new data from GraphQL', 'error');
      }
    } catch (error) {
      console.error('Error fetching new data from GraphQL:', error);
      showSnackbar('Error fetching new data from GraphQL', 'error');
    } finally {
      setFetching(false);
    }
  };

  // Clear GraphQL data
  const clearData = async () => {
    try {
      const response = await fetch('/api/graphql/clear-data', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        setGraphqlData([]);
        showSnackbar('GraphQL data cleared successfully', 'success');
      } else {
        console.error('Failed to clear GraphQL data');
        showSnackbar('Failed to clear GraphQL data', 'error');
      }
    } catch (error) {
      console.error('Error clearing GraphQL data:', error);
      showSnackbar('Error clearing GraphQL data', 'error');
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

  // Handle query change
  const handleQueryChange = (queryName, value) => {
    setConfig({
      ...config,
      queries: {
        ...config.queries,
        [queryName]: value
      }
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
          title={t('graphql.configuration')} 
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
                label={t('graphql.enabled')}
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('graphql.endpoint')}
                name="endpoint"
                value={config.endpoint}
                onChange={handleChange}
                disabled={!config.enabled}
                helperText={t('graphql.endpointHelp')}
                required
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth disabled={!config.enabled}>
                <InputLabel id="auth-type-label">{t('graphql.authType')}</InputLabel>
                <Select
                  labelId="auth-type-label"
                  name="auth_type"
                  value={config.auth_type}
                  onChange={handleChange}
                  label={t('graphql.authType')}
                >
                  <MenuItem value="none">{t('graphql.authTypes.none')}</MenuItem>
                  <MenuItem value="api_key">{t('graphql.authTypes.apiKey')}</MenuItem>
                  <MenuItem value="basic">{t('graphql.authTypes.basic')}</MenuItem>
                  <MenuItem value="oauth2">{t('graphql.authTypes.oauth2')}</MenuItem>
                  <MenuItem value="jwt">{t('graphql.authTypes.jwt')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            {config.auth_type === 'api_key' && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label={t('graphql.apiKey')}
                  name="api_key"
                  value={config.api_key}
                  onChange={handleChange}
                  disabled={!config.enabled}
                  helperText={t('graphql.apiKeyHelp')}
                  type="password"
                />
              </Grid>
            )}
            
            {(config.auth_type === 'basic' || config.auth_type === 'oauth2' || config.auth_type === 'jwt') && (
              <>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label={t('graphql.username')}
                    name="username"
                    value={config.username}
                    onChange={handleChange}
                    disabled={!config.enabled}
                    helperText={t('graphql.usernameHelp')}
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label={t('graphql.password')}
                    name="password"
                    type="password"
                    value={config.password}
                    onChange={handleChange}
                    disabled={!config.enabled}
                    helperText={t('graphql.passwordHelp')}
                  />
                </Grid>
              </>
            )}
            
            {(config.auth_type === 'oauth2') && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label={t('graphql.authEndpoint')}
                  name="auth_endpoint"
                  value={config.auth_endpoint}
                  onChange={handleChange}
                  disabled={!config.enabled}
                  helperText={t('graphql.authEndpointHelp')}
                />
              </Grid>
            )}
            
            <Grid item xs={12}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>{t('graphql.queries')}</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" gutterBottom>
                        {t('graphql.tanksQuery')}
                      </Typography>
                      <Box sx={{ position: 'relative' }}>
                        <TextField
                          fullWidth
                          multiline
                          rows={6}
                          value={config.queries.tanks}
                          onChange={(e) => handleQueryChange('tanks', e.target.value)}
                          disabled={!config.enabled}
                          variant="outlined"
                          InputProps={{
                            style: { fontFamily: 'monospace' }
                          }}
                        />
                      </Box>
                    </Grid>
                    
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" gutterBottom>
                        {t('graphql.tankLevelQuery')}
                      </Typography>
                      <Box sx={{ position: 'relative' }}>
                        <TextField
                          fullWidth
                          multiline
                          rows={6}
                          value={config.queries.tankLevel}
                          onChange={(e) => handleQueryChange('tankLevel', e.target.value)}
                          disabled={!config.enabled}
                          variant="outlined"
                          InputProps={{
                            style: { fontFamily: 'monospace' }
                          }}
                        />
                      </Box>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('graphql.pollingInterval')}
                name="polling_interval"
                type="number"
                value={config.polling_interval}
                onChange={handleChange}
                disabled={!config.enabled}
                helperText={t('graphql.pollingIntervalHelp')}
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
                  {fetching ? <CircularProgress size={24} /> : t('graphql.testConnection')}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
      
      <Box mt={3}>
        <Card>
          <CardHeader 
            title={t('graphql.status')} 
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
                    ? t('graphql.connectedTo', { url: config.endpoint }) 
                    : t('graphql.notConnected')}
                </Alert>
              </Grid>
              
              {status.last_error && (
                <Grid item xs={12}>
                  <Alert severity="error">
                    {t('graphql.lastError')}: {status.last_error}
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
            title={t('graphql.receivedData')} 
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
            {graphqlData.length === 0 ? (
              <Typography variant="body2" color="textSecondary">
                {t('graphql.noData')}
              </Typography>
            ) : (
              <Box sx={{ maxHeight: '300px', overflow: 'auto' }}>
                {graphqlData.map((item, index) => (
                  <Paper key={index} sx={{ p: 2, mb: 2 }}>
                    <Typography variant="subtitle2">
                      {new Date(item.timestamp).toLocaleString()}
                    </Typography>
                    <Typography variant="body2">
                      {t('graphql.tankId')}: {item.tank_id}
                    </Typography>
                    <Typography variant="body2">
                      {t('graphql.tankName')}: {item.name}
                    </Typography>
                    <Typography variant="body2">
                      {t('graphql.level')}: {item.level}
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

export default GraphQLConfig;
