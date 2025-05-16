import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Tooltip
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { useAuth } from '../../context/AuthContext';

const TankSelector = ({ selectedTank, onSelectTank, showAddButton = true }) => {
  const { t } = useTranslation();
  const { token } = useAuth();
  const [tanks, setTanks] = useState([
    { id: 'tank1', name: 'Tank 1 - Main Storage', description: 'Main water storage tank' },
    { id: 'tank2', name: 'Tank 2 - Secondary Storage', description: 'Secondary water storage tank' },
    { id: 'tank3', name: 'Tank 3 - Reserve', description: 'Reserve water storage tank' }
  ]);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingTank, setEditingTank] = useState(null);
  const [tankForm, setTankForm] = useState({
    id: '',
    name: '',
    description: ''
  });
  const [error, setError] = useState('');

  // Load tanks from localStorage on component mount
  useEffect(() => {
    const savedTanks = localStorage.getItem('tanks');
    if (savedTanks) {
      try {
        const parsedTanks = JSON.parse(savedTanks);
        if (Array.isArray(parsedTanks) && parsedTanks.length > 0) {
          setTanks(parsedTanks);
        }
      } catch (error) {
        console.error('Error parsing tanks from localStorage:', error);
      }
    }
  }, []);

  // Save tanks to localStorage when they change
  useEffect(() => {
    localStorage.setItem('tanks', JSON.stringify(tanks));
  }, [tanks]);

  const handleOpenDialog = (tank = null) => {
    if (tank) {
      // Edit existing tank
      setEditingTank(tank);
      setTankForm({
        id: tank.id,
        name: tank.name,
        description: tank.description || ''
      });
    } else {
      // Add new tank
      setEditingTank(null);
      setTankForm({
        id: `tank${tanks.length + 1}`,
        name: '',
        description: ''
      });
    }
    setOpenDialog(true);
    setError('');
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingTank(null);
    setError('');
  };

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setTankForm({
      ...tankForm,
      [name]: value
    });
  };

  const handleSaveTank = () => {
    // Validate form
    if (!tankForm.name.trim()) {
      setError(t('tanks.nameRequired'));
      return;
    }

    if (!tankForm.id.trim()) {
      setError(t('tanks.idRequired'));
      return;
    }

    // Check if ID already exists (for new tanks)
    if (!editingTank && tanks.some(tank => tank.id === tankForm.id)) {
      setError(t('tanks.idExists'));
      return;
    }

    if (editingTank) {
      // Update existing tank
      const updatedTanks = tanks.map(tank => 
        tank.id === editingTank.id ? tankForm : tank
      );
      setTanks(updatedTanks);
    } else {
      // Add new tank
      setTanks([...tanks, tankForm]);
    }

    // Close dialog
    handleCloseDialog();
  };

  const handleDeleteTank = (tankId) => {
    if (tanks.length <= 1) {
      setError(t('tanks.cannotDeleteLast'));
      return;
    }

    const updatedTanks = tanks.filter(tank => tank.id !== tankId);
    setTanks(updatedTanks);
    
    // If the deleted tank was selected, select the first available tank
    if (selectedTank === tankId) {
      onSelectTank(updatedTanks[0].id);
    }
  };

  return (
    <Box sx={{ minWidth: 200 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <FormControl fullWidth size="small">
          <InputLabel id="tank-selector-label">{t('tanks.selectTank')}</InputLabel>
          <Select
            labelId="tank-selector-label"
            id="tank-selector"
            value={selectedTank}
            label={t('tanks.selectTank')}
            onChange={(e) => onSelectTank(e.target.value)}
          >
            {tanks.map((tank) => (
              <MenuItem key={tank.id} value={tank.id}>
                {tank.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        
        {showAddButton && (
          <Box sx={{ display: 'flex', ml: 1 }}>
            <Tooltip title={t('tanks.addTank')}>
              <IconButton 
                color="primary" 
                onClick={() => handleOpenDialog()}
                size="small"
              >
                <AddIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title={t('tanks.editTank')}>
              <IconButton 
                color="secondary" 
                onClick={() => {
                  const tank = tanks.find(t => t.id === selectedTank);
                  if (tank) handleOpenDialog(tank);
                }}
                size="small"
              >
                <EditIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title={t('tanks.deleteTank')}>
              <IconButton 
                color="error" 
                onClick={() => handleDeleteTank(selectedTank)}
                size="small"
              >
                <DeleteIcon />
              </IconButton>
            </Tooltip>
          </Box>
        )}
      </Box>
      
      {/* Tank details */}
      {selectedTank && (
        <Box sx={{ mt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {tanks.find(t => t.id === selectedTank)?.description || ''}
          </Typography>
        </Box>
      )}
      
      {/* Add/Edit Tank Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <DialogTitle>
          {editingTank ? t('tanks.editTank') : t('tanks.addTank')}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Typography color="error" variant="body2" sx={{ mb: 2 }}>
              {error}
            </Typography>
          )}
          
          <TextField
            margin="dense"
            name="id"
            label={t('tanks.tankId')}
            type="text"
            fullWidth
            variant="outlined"
            value={tankForm.id}
            onChange={handleFormChange}
            disabled={!!editingTank} // Disable ID field when editing
            sx={{ mb: 2 }}
          />
          
          <TextField
            margin="dense"
            name="name"
            label={t('tanks.tankName')}
            type="text"
            fullWidth
            variant="outlined"
            value={tankForm.name}
            onChange={handleFormChange}
            sx={{ mb: 2 }}
          />
          
          <TextField
            margin="dense"
            name="description"
            label={t('tanks.tankDescription')}
            type="text"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={tankForm.description}
            onChange={handleFormChange}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>{t('common.cancel')}</Button>
          <Button onClick={handleSaveTank} variant="contained" color="primary">
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TankSelector;
