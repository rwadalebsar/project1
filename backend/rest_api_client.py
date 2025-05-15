import requests
import json
import os
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
REST_CONFIG_DIR = "rest_api_data"
REST_CONFIG_FILE = os.path.join(REST_CONFIG_DIR, "config.json")

# Ensure rest api data directory exists
os.makedirs(REST_CONFIG_DIR, exist_ok=True)

class RESTAPIClient:
    """Client for REST API integration with tank monitoring"""
    
    def __init__(self):
        """Initialize the REST API client"""
        self.config = self._load_config()
        self.connected = False
        self.last_error = None
        self.tank_data = []
        self.auth_token = None
        self.token_expiry = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(REST_CONFIG_FILE):
            try:
                with open(REST_CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error("Invalid REST API config file format. Using defaults.")
        
        # Default configuration
        default_config = {
            "enabled": False,
            "base_url": "https://api.example.com",
            "api_key": "",
            "username": "",
            "password": "",
            "auth_type": "none",  # none, api_key, basic, oauth2
            "headers": {},
            "endpoints": {
                "tanks": "/tanks",
                "levels": "/tanks/{tank_id}/levels",
                "auth": "/auth/token"
            },
            "polling_interval": 60,  # seconds
            "user_id": None
        }
        
        # Save default config if none exists
        if not os.path.exists(REST_CONFIG_FILE):
            with open(REST_CONFIG_FILE, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default REST API configuration file: {REST_CONFIG_FILE}")
        
        return default_config
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(REST_CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Saved REST API configuration")
        except Exception as e:
            logger.error(f"Error saving REST API configuration: {str(e)}")
    
    def update_config(self, config: Dict[str, Any]) -> bool:
        """Update REST API configuration"""
        try:
            # Update config
            self.config.update(config)
            
            # Save config
            self._save_config()
            
            logger.info("Updated REST API configuration")
            return True
        except Exception as e:
            logger.error(f"Error updating REST API configuration: {str(e)}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current REST API configuration"""
        # Return a copy to prevent direct modification
        config = self.config.copy()
        
        # Add status information
        config["connected"] = self.connected
        config["last_error"] = self.last_error
        
        return config
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers based on config"""
        headers = self.config.get("headers", {}).copy()
        
        auth_type = self.config.get("auth_type", "none")
        
        if auth_type == "api_key":
            # Add API key to headers
            api_key = self.config.get("api_key", "")
            if api_key:
                headers["Authorization"] = f"ApiKey {api_key}"
                
        elif auth_type == "oauth2":
            # Add OAuth2 token to headers
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
                
        # For basic auth, we'll use the auth parameter in the request
        
        return headers
    
    def _get_auth(self):
        """Get authentication tuple for basic auth"""
        auth_type = self.config.get("auth_type", "none")
        
        if auth_type == "basic":
            return (self.config.get("username", ""), self.config.get("password", ""))
        
        return None
    
    def authenticate(self) -> bool:
        """Authenticate with the REST API if needed"""
        auth_type = self.config.get("auth_type", "none")
        
        if auth_type == "none" or auth_type == "api_key" or auth_type == "basic":
            # No authentication needed or handled in headers/auth
            return True
            
        elif auth_type == "oauth2":
            # Check if we have a valid token
            if self.auth_token and self.token_expiry and datetime.now() < self.token_expiry:
                return True
                
            # Get a new token
            try:
                auth_endpoint = self.config.get("endpoints", {}).get("auth", "/auth/token")
                url = f"{self.config.get('base_url')}{auth_endpoint}"
                
                response = requests.post(
                    url,
                    json={
                        "username": self.config.get("username", ""),
                        "password": self.config.get("password", "")
                    },
                    headers=self.config.get("headers", {})
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token")
                    
                    # Set token expiry (default to 1 hour if not provided)
                    expires_in = data.get("expires_in", 3600)
                    self.token_expiry = datetime.now() + datetime.timedelta(seconds=expires_in)
                    
                    logger.info("Successfully authenticated with REST API")
                    return True
                else:
                    logger.error(f"Failed to authenticate with REST API: {response.status_code} {response.text}")
                    self.last_error = f"Authentication failed: {response.status_code} {response.text}"
                    return False
                    
            except Exception as e:
                logger.error(f"Error authenticating with REST API: {str(e)}")
                self.last_error = f"Authentication error: {str(e)}"
                return False
        
        return False
    
    def test_connection(self) -> bool:
        """Test connection to the REST API"""
        if not self.config.get("enabled", False):
            self.last_error = "REST API is disabled"
            return False
            
        try:
            # Authenticate if needed
            if not self.authenticate():
                return False
                
            # Try to access the tanks endpoint
            tanks_endpoint = self.config.get("endpoints", {}).get("tanks", "/tanks")
            url = f"{self.config.get('base_url')}{tanks_endpoint}"
            
            response = requests.get(
                url,
                headers=self._get_auth_headers(),
                auth=self._get_auth(),
                timeout=10
            )
            
            if response.status_code in [200, 201, 202, 203, 204]:
                logger.info("Successfully connected to REST API")
                self.connected = True
                self.last_error = None
                return True
            else:
                logger.error(f"Failed to connect to REST API: {response.status_code} {response.text}")
                self.last_error = f"Connection failed: {response.status_code} {response.text}"
                self.connected = False
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to REST API: {str(e)}")
            self.last_error = f"Connection error: {str(e)}"
            self.connected = False
            return False
    
    def fetch_tank_data(self) -> List[Dict[str, Any]]:
        """Fetch tank data from the REST API"""
        if not self.config.get("enabled", False):
            logger.warning("REST API is disabled")
            return []
            
        try:
            # Authenticate if needed
            if not self.authenticate():
                return []
                
            # Fetch tanks
            tanks_endpoint = self.config.get("endpoints", {}).get("tanks", "/tanks")
            url = f"{self.config.get('base_url')}{tanks_endpoint}"
            
            response = requests.get(
                url,
                headers=self._get_auth_headers(),
                auth=self._get_auth(),
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch tanks: {response.status_code} {response.text}")
                self.last_error = f"Failed to fetch tanks: {response.status_code} {response.text}"
                return []
                
            tanks = response.json()
            
            # Fetch level for each tank
            results = []
            for tank in tanks:
                tank_id = tank.get("id")
                if not tank_id:
                    continue
                    
                levels_endpoint = self.config.get("endpoints", {}).get("levels", "/tanks/{tank_id}/levels")
                levels_endpoint = levels_endpoint.replace("{tank_id}", str(tank_id))
                url = f"{self.config.get('base_url')}{levels_endpoint}"
                
                response = requests.get(
                    url,
                    headers=self._get_auth_headers(),
                    auth=self._get_auth(),
                    timeout=10
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch level for tank {tank_id}: {response.status_code} {response.text}")
                    continue
                    
                level_data = response.json()
                
                # Create tank data entry
                tank_data = {
                    "tank_id": tank_id,
                    "name": tank.get("name", f"Tank {tank_id}"),
                    "level": level_data.get("level", 0),
                    "timestamp": datetime.now().isoformat(),
                    "source": "rest_api"
                }
                
                results.append(tank_data)
                self.tank_data.append(tank_data)
            
            logger.info(f"Fetched {len(results)} tank readings from REST API")
            return results
            
        except Exception as e:
            logger.error(f"Error fetching tank data from REST API: {str(e)}")
            self.last_error = f"Error fetching tank data: {str(e)}"
            return []
    
    def get_tank_data(self) -> List[Dict[str, Any]]:
        """Get collected tank data"""
        return self.tank_data.copy()
    
    def clear_tank_data(self) -> None:
        """Clear collected tank data"""
        self.tank_data = []
        logger.info("Cleared REST API tank data")

# Create a singleton instance
rest_api_client = RESTAPIClient()
