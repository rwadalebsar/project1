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
GRAPHQL_CONFIG_DIR = "graphql_data"
GRAPHQL_CONFIG_FILE = os.path.join(GRAPHQL_CONFIG_DIR, "config.json")

# Ensure graphql data directory exists
os.makedirs(GRAPHQL_CONFIG_DIR, exist_ok=True)

class GraphQLClient:
    """Client for GraphQL integration with tank monitoring"""
    
    def __init__(self):
        """Initialize the GraphQL client"""
        self.config = self._load_config()
        self.connected = False
        self.last_error = None
        self.tank_data = []
        self.auth_token = None
        self.token_expiry = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(GRAPHQL_CONFIG_FILE):
            try:
                with open(GRAPHQL_CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error("Invalid GraphQL config file format. Using defaults.")
        
        # Default configuration
        default_config = {
            "enabled": False,
            "endpoint": "https://api.example.com/graphql",
            "api_key": "",
            "username": "",
            "password": "",
            "auth_type": "none",  # none, api_key, basic, oauth2, jwt
            "auth_endpoint": "https://api.example.com/auth",
            "headers": {},
            "queries": {
                "tanks": """
                    query GetTanks {
                        tanks {
                            id
                            name
                            capacity
                        }
                    }
                """,
                "tankLevel": """
                    query GetTankLevel($tankId: ID!) {
                        tank(id: $tankId) {
                            id
                            name
                            level
                            lastUpdated
                        }
                    }
                """
            },
            "polling_interval": 60,  # seconds
            "user_id": None
        }
        
        # Save default config if none exists
        if not os.path.exists(GRAPHQL_CONFIG_FILE):
            with open(GRAPHQL_CONFIG_FILE, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default GraphQL configuration file: {GRAPHQL_CONFIG_FILE}")
        
        return default_config
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(GRAPHQL_CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Saved GraphQL configuration")
        except Exception as e:
            logger.error(f"Error saving GraphQL configuration: {str(e)}")
    
    def update_config(self, config: Dict[str, Any]) -> bool:
        """Update GraphQL configuration"""
        try:
            # Update config
            self.config.update(config)
            
            # Save config
            self._save_config()
            
            logger.info("Updated GraphQL configuration")
            return True
        except Exception as e:
            logger.error(f"Error updating GraphQL configuration: {str(e)}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current GraphQL configuration"""
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
                
        elif auth_type in ["oauth2", "jwt"]:
            # Add token to headers
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # Add content type for GraphQL
        headers["Content-Type"] = "application/json"
                
        return headers
    
    def authenticate(self) -> bool:
        """Authenticate with the GraphQL API if needed"""
        auth_type = self.config.get("auth_type", "none")
        
        if auth_type == "none" or auth_type == "api_key":
            # No authentication needed or handled in headers
            return True
            
        elif auth_type == "basic":
            # Basic auth is handled by the requests library
            return True
            
        elif auth_type in ["oauth2", "jwt"]:
            # Check if we have a valid token
            if self.auth_token and self.token_expiry and datetime.now() < self.token_expiry:
                return True
                
            # Get a new token
            try:
                auth_endpoint = self.config.get("auth_endpoint")
                
                auth_data = {
                    "username": self.config.get("username", ""),
                    "password": self.config.get("password", "")
                }
                
                if auth_type == "jwt":
                    # For JWT, we might use a GraphQL mutation
                    mutation = """
                        mutation Login($username: String!, $password: String!) {
                            login(username: $username, password: $password) {
                                token
                                expiresIn
                            }
                        }
                    """
                    
                    response = requests.post(
                        self.config.get("endpoint"),
                        json={
                            "query": mutation,
                            "variables": auth_data
                        },
                        headers=self.config.get("headers", {})
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "errors" in result:
                            logger.error(f"GraphQL authentication error: {result['errors']}")
                            self.last_error = f"Authentication error: {result['errors']}"
                            return False
                            
                        data = result.get("data", {}).get("login", {})
                        self.auth_token = data.get("token")
                        expires_in = data.get("expiresIn", 3600)
                        
                    else:
                        logger.error(f"Failed to authenticate with GraphQL API: {response.status_code} {response.text}")
                        self.last_error = f"Authentication failed: {response.status_code} {response.text}"
                        return False
                        
                else:  # OAuth2
                    response = requests.post(
                        auth_endpoint,
                        json=auth_data,
                        headers=self.config.get("headers", {})
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.auth_token = data.get("access_token")
                        expires_in = data.get("expires_in", 3600)
                        
                    else:
                        logger.error(f"Failed to authenticate with GraphQL API: {response.status_code} {response.text}")
                        self.last_error = f"Authentication failed: {response.status_code} {response.text}"
                        return False
                
                # Set token expiry
                self.token_expiry = datetime.now() + datetime.timedelta(seconds=expires_in)
                
                logger.info("Successfully authenticated with GraphQL API")
                return True
                    
            except Exception as e:
                logger.error(f"Error authenticating with GraphQL API: {str(e)}")
                self.last_error = f"Authentication error: {str(e)}"
                return False
        
        return False
    
    def _get_auth(self):
        """Get authentication tuple for basic auth"""
        auth_type = self.config.get("auth_type", "none")
        
        if auth_type == "basic":
            return (self.config.get("username", ""), self.config.get("password", ""))
        
        return None
    
    def test_connection(self) -> bool:
        """Test connection to the GraphQL API"""
        if not self.config.get("enabled", False):
            self.last_error = "GraphQL API is disabled"
            return False
            
        try:
            # Authenticate if needed
            if not self.authenticate():
                return False
                
            # Try to execute a simple introspection query
            introspection_query = """
                query {
                    __schema {
                        queryType {
                            name
                        }
                    }
                }
            """
            
            response = requests.post(
                self.config.get("endpoint"),
                json={"query": introspection_query},
                headers=self._get_auth_headers(),
                auth=self._get_auth(),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if "errors" in result:
                    logger.error(f"GraphQL connection error: {result['errors']}")
                    self.last_error = f"Connection error: {result['errors']}"
                    self.connected = False
                    return False
                    
                logger.info("Successfully connected to GraphQL API")
                self.connected = True
                self.last_error = None
                return True
            else:
                logger.error(f"Failed to connect to GraphQL API: {response.status_code} {response.text}")
                self.last_error = f"Connection failed: {response.status_code} {response.text}"
                self.connected = False
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to GraphQL API: {str(e)}")
            self.last_error = f"Connection error: {str(e)}"
            self.connected = False
            return False
    
    def fetch_tank_data(self) -> List[Dict[str, Any]]:
        """Fetch tank data from the GraphQL API"""
        if not self.config.get("enabled", False):
            logger.warning("GraphQL API is disabled")
            return []
            
        try:
            # Authenticate if needed
            if not self.authenticate():
                return []
                
            # Fetch tanks
            tanks_query = self.config.get("queries", {}).get("tanks")
            
            response = requests.post(
                self.config.get("endpoint"),
                json={"query": tanks_query},
                headers=self._get_auth_headers(),
                auth=self._get_auth(),
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch tanks: {response.status_code} {response.text}")
                self.last_error = f"Failed to fetch tanks: {response.status_code} {response.text}"
                return []
                
            result = response.json()
            if "errors" in result:
                logger.error(f"GraphQL error fetching tanks: {result['errors']}")
                self.last_error = f"Error fetching tanks: {result['errors']}"
                return []
                
            tanks = result.get("data", {}).get("tanks", [])
            
            # Fetch level for each tank
            results = []
            tank_level_query = self.config.get("queries", {}).get("tankLevel")
            
            for tank in tanks:
                tank_id = tank.get("id")
                if not tank_id:
                    continue
                    
                response = requests.post(
                    self.config.get("endpoint"),
                    json={
                        "query": tank_level_query,
                        "variables": {"tankId": tank_id}
                    },
                    headers=self._get_auth_headers(),
                    auth=self._get_auth(),
                    timeout=10
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch level for tank {tank_id}: {response.status_code} {response.text}")
                    continue
                    
                result = response.json()
                if "errors" in result:
                    logger.warning(f"GraphQL error fetching tank level: {result['errors']}")
                    continue
                    
                tank_data = result.get("data", {}).get("tank", {})
                
                # Create tank data entry
                tank_entry = {
                    "tank_id": tank_id,
                    "name": tank_data.get("name", f"Tank {tank_id}"),
                    "level": tank_data.get("level", 0),
                    "timestamp": tank_data.get("lastUpdated", datetime.now().isoformat()),
                    "source": "graphql"
                }
                
                results.append(tank_entry)
                self.tank_data.append(tank_entry)
            
            logger.info(f"Fetched {len(results)} tank readings from GraphQL API")
            return results
            
        except Exception as e:
            logger.error(f"Error fetching tank data from GraphQL API: {str(e)}")
            self.last_error = f"Error fetching tank data: {str(e)}"
            return []
    
    def get_tank_data(self) -> List[Dict[str, Any]]:
        """Get collected tank data"""
        return self.tank_data.copy()
    
    def clear_tank_data(self) -> None:
        """Clear collected tank data"""
        self.tank_data = []
        logger.info("Cleared GraphQL tank data")

# Create a singleton instance
graphql_client = GraphQLClient()
