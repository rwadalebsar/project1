import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Container,
  Tab,
  Tabs,
  Typography,
  Paper
} from '@mui/material';
import MQTTConfig from '../mqtt/MQTTConfig';
import RESTConfig from '../rest/RESTConfig';
import GraphQLConfig from '../graphql/GraphQLConfig';
import OpcUaConfig from '../opcua/OpcUaConfig';

// TabPanel component for tab content
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`cloud-tabpanel-${index}`}
      aria-labelledby={`cloud-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

// Helper function for tab accessibility
function a11yProps(index) {
  return {
    id: `cloud-tab-${index}`,
    'aria-controls': `cloud-tabpanel-${index}`,
  };
}

const CloudConnectionsPage = () => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          {t('cloudConnections.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          {t('cloudConnections.description')}
        </Typography>
        <Typography variant="body2" sx={{
          backgroundColor: '#f0f9ff',
          padding: '10px',
          borderRadius: '4px',
          borderLeft: '4px solid #3b82f6'
        }}>
          <strong>Note:</strong> Each connection can now be linked to a specific tank.
          Configure your connections and select the appropriate tank for each one to
          ensure data is properly routed. You can manage your tanks from the dashboard
          or when configuring each connection.
        </Typography>
      </Box>

      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            aria-label="cloud connection tabs"
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab label={t('cloudConnections.mqtt')} {...a11yProps(0)} />
            <Tab label={t('cloudConnections.restApi')} {...a11yProps(1)} />
            <Tab label={t('cloudConnections.graphql')} {...a11yProps(2)} />
            <Tab label={t('cloudConnections.opcua')} {...a11yProps(3)} />
            <Tab label={t('cloudConnections.modbus')} {...a11yProps(4)} />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <MQTTConfig />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <RESTConfig />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <GraphQLConfig />
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <OpcUaConfig />
        </TabPanel>

        <TabPanel value={activeTab} index={4}>
          <Box sx={{ p: 2 }}>
            <Typography variant="h6">
              {t('cloudConnections.modbusConfig')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              {t('cloudConnections.comingSoon')}
            </Typography>
          </Box>
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default CloudConnectionsPage;
