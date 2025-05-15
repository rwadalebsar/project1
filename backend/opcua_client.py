import json
import os
import logging
import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime
from opcua import Client, ua
from opcua.ua import NodeId, QualifiedName
from opcua.crypto import security_policies
from opcua.ua.uaerrors import UaStatusCodeError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
OPCUA_CONFIG_DIR = "opcua_data"
OPCUA_CONFIG_FILE = os.path.join(OPCUA_CONFIG_DIR, "config.json")

# Ensure opcua data directory exists
os.makedirs(OPCUA_CONFIG_DIR, exist_ok=True)

class OpcUaClient:
    """Client for OPC UA integration with tank monitoring"""

    def __init__(self):
        """Initialize the OPC UA client"""
        self.config = self._load_config()
        self.connected = False
        self.last_error = None
        self.tank_data = []
        self.client = None
        self.subscription = None
        self.subscription_handle = None
        self.monitored_items = {}
        self.monitoring_thread = None
        self.stop_monitoring = False

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(OPCUA_CONFIG_FILE):
            try:
                with open(OPCUA_CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error("Invalid OPC UA config file format. Using defaults.")

        # Default configuration
        default_config = {
            "enabled": False,
            "endpoint": "opc.tcp://localhost:4840/freeopcua/server/",
            "security_mode": "None",  # None, Sign, SignAndEncrypt
            "security_policy": "None",  # None, Basic128Rsa15, Basic256, Basic256Sha256
            "certificate_path": "",
            "private_key_path": "",
            "username": "",
            "password": "",
            "namespace": "http://examples.freeopcua.github.io",
            "node_paths": {
                "tanks": ["Objects", "Server", "Tanks"],
                "tank_level": ["Objects", "Server", "Tanks", "{tank_id}", "Level"]
            },
            "polling_interval": 60,  # seconds
            "user_id": None
        }

        # Save default config if none exists
        if not os.path.exists(OPCUA_CONFIG_FILE):
            with open(OPCUA_CONFIG_FILE, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default OPC UA configuration file: {OPCUA_CONFIG_FILE}")

        return default_config

    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(OPCUA_CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Saved OPC UA configuration")
        except Exception as e:
            logger.error(f"Error saving OPC UA configuration: {str(e)}")

    def update_config(self, config: Dict[str, Any]) -> bool:
        """Update OPC UA configuration"""
        try:
            # Update config
            self.config.update(config)

            # Save config
            self._save_config()

            logger.info("Updated OPC UA configuration")
            return True
        except Exception as e:
            logger.error(f"Error updating OPC UA configuration: {str(e)}")
            return False

    def get_config(self) -> Dict[str, Any]:
        """Get current OPC UA configuration"""
        # Return a copy to prevent direct modification
        config = self.config.copy()

        # Add status information
        config["connected"] = self.connected
        config["last_error"] = self.last_error

        return config

    def _get_security_mode(self) -> ua.MessageSecurityMode:
        """Get security mode from config"""
        mode = self.config.get("security_mode", "None")

        if mode == "Sign":
            return ua.MessageSecurityMode.Sign
        elif mode == "SignAndEncrypt":
            return ua.MessageSecurityMode.SignAndEncrypt
        else:
            return ua.MessageSecurityMode.None_

    def _get_security_policy(self):
        """Get security policy from config"""
        policy = self.config.get("security_policy", "None")

        if policy == "Basic128Rsa15":
            return security_policies.SecurityPolicyBasic128Rsa15
        elif policy == "Basic256":
            return security_policies.SecurityPolicyBasic256
        elif policy == "Basic256Sha256":
            return security_policies.SecurityPolicyBasic256Sha256
        else:
            return security_policies.SecurityPolicyNone

    def _get_node_from_path(self, path: List[str]):
        """Get node from path"""
        if not self.client:
            raise Exception("Client not connected")

        # Start from root node
        node = self.client.get_root_node()

        # Traverse path
        for item in path:
            # Check if item contains a placeholder
            if "{" in item and "}" in item:
                # This is a placeholder, skip for now
                continue

            # Find child node
            children = node.get_children()
            found = False

            for child in children:
                try:
                    if child.get_browse_name().Name == item:
                        node = child
                        found = True
                        break
                except Exception as e:
                    logger.warning(f"Error getting browse name for node: {str(e)}")

            if not found:
                raise Exception(f"Node not found: {item}")

        return node

    def _get_node_from_path_with_tank_id(self, path: List[str], tank_id: str):
        """Get node from path with tank_id placeholder"""
        if not self.client:
            raise Exception("Client not connected")

        # Start from root node
        node = self.client.get_root_node()

        # Traverse path
        for item in path:
            # Check if item contains a placeholder
            if "{tank_id}" in item:
                # Replace placeholder with tank_id
                item = item.replace("{tank_id}", tank_id)

            # Find child node
            children = node.get_children()
            found = False

            for child in children:
                try:
                    if child.get_browse_name().Name == item:
                        node = child
                        found = True
                        break
                except Exception as e:
                    logger.warning(f"Error getting browse name for node: {str(e)}")

            if not found:
                raise Exception(f"Node not found: {item}")

        return node

    def connect(self) -> bool:
        """Connect to OPC UA server"""
        if not self.config.get("enabled", False):
            self.last_error = "OPC UA is disabled"
            return False

        try:
            # Disconnect if already connected
            if self.client:
                self.disconnect()

            # Create client
            self.client = Client(self.config.get("endpoint"))

            # Set security if needed
            if self.config.get("security_mode", "None") != "None" or self.config.get("security_policy", "None") != "None":
                security_mode = self._get_security_mode()
                security_policy = self._get_security_policy()

                # Set security settings
                self.client.set_security(
                    security_policy,
                    self.config.get("certificate_path", ""),
                    self.config.get("private_key_path", ""),
                    mode=security_mode
                )

            # Set user credentials if provided
            if self.config.get("username") and self.config.get("password"):
                self.client.set_user(self.config.get("username"), self.config.get("password"))

            # Connect to server
            self.client.connect()

            # Get namespace index
            namespace = self.config.get("namespace", "http://examples.freeopcua.github.io")
            try:
                self.namespace_idx = self.client.get_namespace_index(namespace)
            except Exception as e:
                logger.warning(f"Namespace not found: {namespace}. Using default namespace 0.")
                self.namespace_idx = 0

            self.connected = True
            self.last_error = None
            logger.info(f"Connected to OPC UA server at {self.config.get('endpoint')}")
            return True

        except Exception as e:
            self.client = None
            self.connected = False
            self.last_error = str(e)
            logger.error(f"Error connecting to OPC UA server: {str(e)}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from OPC UA server"""
        try:
            # Stop monitoring if active
            self.stop_monitoring = True
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)

            # Unsubscribe if subscribed
            if self.subscription:
                self.subscription.delete()
                self.subscription = None

            # Disconnect client
            if self.client:
                self.client.disconnect()
                self.client = None

            self.connected = False
            logger.info("Disconnected from OPC UA server")
            return True

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error disconnecting from OPC UA server: {str(e)}")
            return False

    def test_connection(self) -> bool:
        """Test connection to OPC UA server"""
        if not self.config.get("enabled", False):
            self.last_error = "OPC UA is disabled"
            return False

        try:
            # Connect to server
            if not self.connect():
                return False

            # Try to browse root node
            root = self.client.get_root_node()
            children = root.get_children()

            # Disconnect
            self.disconnect()

            self.connected = True
            self.last_error = None
            return True

        except Exception as e:
            self.disconnect()
            self.connected = False
            self.last_error = str(e)
            logger.error(f"Error testing connection to OPC UA server: {str(e)}")
            return False

    def _monitoring_thread_func(self):
        """Thread function for monitoring OPC UA nodes"""
        logger.info("Starting OPC UA monitoring thread")

        while not self.stop_monitoring:
            try:
                # Check if connected
                if not self.connected or not self.client:
                    # Try to reconnect
                    if not self.connect():
                        time.sleep(5)
                        continue

                # Fetch tank data
                self.fetch_tank_data()

                # Sleep for polling interval
                time.sleep(self.config.get("polling_interval", 60))

            except Exception as e:
                logger.error(f"Error in OPC UA monitoring thread: {str(e)}")
                time.sleep(5)

        logger.info("OPC UA monitoring thread stopped")

    def start_monitoring(self) -> bool:
        """Start monitoring OPC UA nodes"""
        if not self.config.get("enabled", False):
            self.last_error = "OPC UA is disabled"
            return False

        try:
            # Stop existing monitoring if any
            self.stop_monitoring = True
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)

            # Reset flag
            self.stop_monitoring = False

            # Start new monitoring thread
            self.monitoring_thread = threading.Thread(target=self._monitoring_thread_func)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()

            logger.info("Started OPC UA monitoring")
            return True

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error starting OPC UA monitoring: {str(e)}")
            return False

    def stop_monitoring(self) -> bool:
        """Stop monitoring OPC UA nodes"""
        try:
            # Set stop flag
            self.stop_monitoring = True

            # Wait for thread to stop
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)

            logger.info("Stopped OPC UA monitoring")
            return True

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error stopping OPC UA monitoring: {str(e)}")
            return False

    def fetch_tank_data(self) -> List[Dict[str, Any]]:
        """Fetch tank data from OPC UA server"""
        if not self.config.get("enabled", False):
            logger.warning("OPC UA is disabled")
            return []

        try:
            # Connect if not connected
            if not self.connected or not self.client:
                if not self.connect():
                    return []

            # Get tanks node
            tanks_path = self.config.get("node_paths", {}).get("tanks", ["Objects", "Server", "Tanks"])

            try:
                tanks_node = self._get_node_from_path(tanks_path)
            except Exception as e:
                logger.error(f"Error getting tanks node: {str(e)}")
                return []

            # Get tank nodes
            tank_nodes = tanks_node.get_children()

            # Get tank level for each tank
            results = []
            for tank_node in tank_nodes:
                try:
                    # Get tank ID
                    tank_id = tank_node.get_browse_name().Name

                    # Get tank level node
                    level_path = self.config.get("node_paths", {}).get("tank_level", ["Objects", "Server", "Tanks", "{tank_id}", "Level"])
                    level_node = self._get_node_from_path_with_tank_id(level_path, tank_id)

                    # Get level value
                    level = level_node.get_value()

                    # Create tank data entry
                    tank_data = {
                        "tank_id": tank_id,
                        "name": tank_id,
                        "level": float(level),
                        "timestamp": datetime.now().isoformat(),
                        "source": "opcua"
                    }

                    results.append(tank_data)
                    self.tank_data.append(tank_data)

                except Exception as e:
                    logger.warning(f"Error getting data for tank {tank_node.get_browse_name().Name}: {str(e)}")

            logger.info(f"Fetched {len(results)} tank readings from OPC UA server")
            return results

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error fetching tank data from OPC UA server: {str(e)}")
            return []

    def get_tank_data(self) -> List[Dict[str, Any]]:
        """Get collected tank data"""
        return self.tank_data.copy()

    def clear_tank_data(self) -> None:
        """Clear collected tank data"""
        self.tank_data = []
        logger.info("Cleared OPC UA tank data")

# Create a singleton instance
opcua_client = OpcUaClient()
