import requests
import json
import os
import logging
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CONFIG_FILE = "config.json"
DATA_DIR = "data"
TANK_DATA_FILE = os.path.join(DATA_DIR, "tank_levels.json")

class TankAPIService:
    """Service to interact with external tank level API"""
    
    def __init__(self):
        """Initialize the service with configuration"""
        self.config = self._load_config()
        self.api_url = self.config.get("api_url", "")
        self.api_key = self.config.get("api_key", "")
        self.tank_id = self.config.get("tank_id", "tank1")
        self.use_mock_data = self.config.get("use_mock_data", True)
        
        # Ensure data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error("Invalid config file format. Using defaults.")
        
        # Default configuration
        default_config = {
            "api_url": "https://api.example.com/tank-levels",
            "api_key": "your-api-key",
            "tank_id": "tank1",
            "use_mock_data": True,
            "update_interval_hours": 1
        }
        
        # Save default config if none exists
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default configuration file: {CONFIG_FILE}")
        
        return default_config
    
    def fetch_tank_levels(self, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch tank level data from the API
        
        Args:
            days: Optional number of days to fetch
            
        Returns:
            List of tank level readings
        """
        if self.use_mock_data:
            logger.info("Using mock data (configured in config.json)")
            return self._get_mock_data(days)
        
        # Prepare request parameters
        params = {"tank_id": self.tank_id}
        if days:
            params["days"] = days
            
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            response = requests.get(self.api_url, params=params, headers=headers)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            
            data = response.json()
            logger.info(f"Successfully fetched {len(data)} tank level readings")
            
            # Convert string timestamps to datetime objects
            for item in data:
                if isinstance(item.get("timestamp"), str):
                    item["timestamp"] = datetime.fromisoformat(item["timestamp"])
            
            # Save the fetched data
            self._save_data(data)
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching tank levels: {str(e)}")
            # Fall back to cached data if available
            return self._get_cached_data(days)
    
    def add_tank_level(self, level: float) -> Dict[str, Any]:
        """
        Add a new tank level reading via the API
        
        Args:
            level: The tank level in meters
            
        Returns:
            The created tank level reading
        """
        if self.use_mock_data:
            logger.info("Using mock data - adding to local storage")
            return self._add_to_mock_data(level)
        
        payload = {
            "level": level,
            "tank_id": self.tank_id,
            "timestamp": datetime.now().isoformat()
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully added tank level reading: {level} meters")
            
            # Update cached data
            cached_data = self._get_cached_data()
            if isinstance(data.get("timestamp"), str):
                data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            cached_data.append(data)
            self._save_data(cached_data)
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"Error adding tank level: {str(e)}")
            # Fall back to adding to local cache
            return self._add_to_mock_data(level)
    
    def _get_cached_data(self, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get data from local cache file"""
        if os.path.exists(TANK_DATA_FILE):
            try:
                with open(TANK_DATA_FILE, 'r') as f:
                    data = json.load(f)
                    
                # Convert string timestamps to datetime objects
                for item in data:
                    if isinstance(item.get("timestamp"), str):
                        item["timestamp"] = datetime.fromisoformat(item["timestamp"])
                
                # Filter by days if specified
                if days:
                    cutoff_date = datetime.now() - timedelta(days=days)
                    data = [item for item in data if item["timestamp"] >= cutoff_date]
                    
                logger.info(f"Loaded {len(data)} readings from cache")
                return data
                
            except json.JSONDecodeError:
                logger.error("Invalid cache file format")
        
        logger.warning("No cached data available")
        return []
    
    def _save_data(self, data: List[Dict[str, Any]]) -> None:
        """Save data to local cache file"""
        try:
            # Convert datetime objects to ISO format strings for JSON serialization
            serializable_data = []
            for item in data:
                serializable_item = item.copy()
                if isinstance(item.get("timestamp"), datetime):
                    serializable_item["timestamp"] = item["timestamp"].isoformat()
                serializable_data.append(serializable_item)
                
            with open(TANK_DATA_FILE, 'w') as f:
                json.dump(serializable_data, f, indent=2)
                
            logger.info(f"Saved {len(data)} readings to cache")
            
        except Exception as e:
            logger.error(f"Error saving data to cache: {str(e)}")
    
    def _get_mock_data(self, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generate or load mock data for testing"""
        if os.path.exists(TANK_DATA_FILE):
            return self._get_cached_data(days)
        
        # Generate sample data if no cache exists
        logger.info("Generating sample tank level data")
        tank_data = []
        now = datetime.now()
        
        # Generate 12 months of hourly data
        for i in range(365 * 24):
            timestamp = now - timedelta(hours=i)
            # Base level with some seasonal pattern (higher in summer, lower in winter)
            base_level = 5.0 + 1.0 * pd.np.sin(2 * pd.np.pi * i / (365 * 24))
            # Add some random noise
            noise = pd.np.random.normal(0, 0.2)
            # Add some random anomalies (about 1%)
            anomaly = 0
            if pd.np.random.random() < 0.01:
                anomaly = pd.np.random.choice([-2, 2]) * pd.np.random.random()
            level = max(0, min(10, base_level + noise + anomaly))
            tank_data.append({
                "timestamp": timestamp,
                "level": level,
                "tank_id": self.tank_id
            })
        
        # Save the generated data
        self._save_data(tank_data)
        
        # Filter by days if specified
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            tank_data = [item for item in tank_data if item["timestamp"] >= cutoff_date]
        
        return tank_data
    
    def _add_to_mock_data(self, level: float) -> Dict[str, Any]:
        """Add a new reading to mock data"""
        new_reading = {
            "timestamp": datetime.now(),
            "level": level,
            "tank_id": self.tank_id
        }
        
        # Get existing data
        data = self._get_cached_data()
        data.append(new_reading)
        
        # Save updated data
        self._save_data(data)
        
        return new_reading
