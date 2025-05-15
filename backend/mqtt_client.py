import paho.mqtt.client as mqtt
import json
import os
import logging
import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
MQTT_CONFIG_DIR = "mqtt_data"
MQTT_CONFIG_FILE = os.path.join(MQTT_CONFIG_DIR, "config.json")

# Ensure mqtt data directory exists
os.makedirs(MQTT_CONFIG_DIR, exist_ok=True)

class MQTTClient:
    """Simple MQTT client for tank monitoring"""
    
    def __init__(self):
        """Initialize the MQTT client"""
        self.config = self._load_config()
        self.client = None
        self.connected = False
        self.last_error = None
        self.tank_data = []
        
        # Initialize client if enabled
        if self.config.get("enabled", False):
            self.initialize()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(MQTT_CONFIG_FILE):
            try:
                with open(MQTT_CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error("Invalid MQTT config file format. Using defaults.")
        
        # Default configuration
        default_config = {
            "enabled": False,
            "broker": "localhost",
            "port": 1883,
            "username": "",
            "password": "",
            "client_id": f"tank_monitor_{int(time.time())}",
            "topic_prefix": "tanks",
            "use_ssl": False,
            "user_id": None
        }
        
        # Save default config if none exists
        if not os.path.exists(MQTT_CONFIG_FILE):
            with open(MQTT_CONFIG_FILE, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default MQTT configuration file: {MQTT_CONFIG_FILE}")
        
        return default_config
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(MQTT_CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Saved MQTT configuration")
        except Exception as e:
            logger.error(f"Error saving MQTT configuration: {str(e)}")
    
    def initialize(self) -> None:
        """Initialize the MQTT client"""
        if self.client:
            self.disconnect()
        
        try:
            # Create MQTT client
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, self.config.get("client_id"))
            
            # Set up callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Set username and password if provided
            if self.config.get("username") and self.config.get("password"):
                self.client.username_pw_set(self.config.get("username"), self.config.get("password"))
            
            # Set SSL if enabled
            if self.config.get("use_ssl"):
                self.client.tls_set()
            
            logger.info("MQTT client initialized")
        except Exception as e:
            logger.error(f"Error initializing MQTT client: {str(e)}")
            self.last_error = str(e)
    
    def connect(self) -> bool:
        """Connect to the MQTT broker"""
        if not self.client:
            self.initialize()
        
        if not self.config.get("enabled"):
            logger.warning("MQTT is disabled in configuration")
            return False
        
        try:
            # Connect to broker
            self.client.connect(self.config.get("broker"), self.config.get("port"))
            
            # Start the loop in a separate thread
            self.client.loop_start()
            
            # Subscribe to topics
            topic = f"{self.config.get('topic_prefix')}/#"
            self.client.subscribe(topic)
            logger.info(f"Subscribed to MQTT topic: {topic}")
            
            return True
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {str(e)}")
            self.last_error = str(e)
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the MQTT broker"""
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
                logger.info("Disconnected from MQTT broker")
            except Exception as e:
                logger.error(f"Error disconnecting from MQTT broker: {str(e)}")
            finally:
                self.connected = False
    
    def publish_tank_data(self, tank_data: Dict[str, Any]) -> bool:
        """Publish tank data to MQTT"""
        if not self.client or not self.connected:
            logger.warning("MQTT client not connected")
            return False
        
        try:
            # Create topic
            topic = f"{self.config.get('topic_prefix')}/{tank_data.get('tank_id', 'unknown')}"
            
            # Convert datetime to string if needed
            data = tank_data.copy()
            if isinstance(data.get("timestamp"), datetime):
                data["timestamp"] = data["timestamp"].isoformat()
            
            # Publish data
            payload = json.dumps(data)
            result = self.client.publish(topic, payload)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published tank data to MQTT topic: {topic}")
                return True
            else:
                logger.error(f"Failed to publish tank data to MQTT: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Error publishing tank data to MQTT: {str(e)}")
            return False
    
    def update_config(self, config: Dict[str, Any]) -> bool:
        """Update MQTT configuration"""
        try:
            # Update config
            self.config.update(config)
            
            # Save config
            self._save_config()
            
            # Reinitialize client if needed
            if self.connected:
                self.disconnect()
                self.initialize()
                if self.config.get("enabled"):
                    self.connect()
            elif self.config.get("enabled"):
                self.initialize()
            
            logger.info("Updated MQTT configuration")
            return True
        except Exception as e:
            logger.error(f"Error updating MQTT configuration: {str(e)}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current MQTT configuration"""
        # Return a copy to prevent direct modification
        config = self.config.copy()
        
        # Add status information
        config["connected"] = self.connected
        config["last_error"] = self.last_error
        
        return config
    
    def _on_connect(self, client, userdata, flags, rc, properties) -> None:
        """Callback for when a connection is established"""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self.connected = True
            self.last_error = None
            
            # Subscribe to topics
            topic = f"{self.config.get('topic_prefix')}/#"
            self.client.subscribe(topic)
            logger.info(f"Subscribed to MQTT topic: {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker, rc={rc}")
            self.connected = False
            self.last_error = f"Connection failed with code {rc}"
    
    def _on_disconnect(self, client, userdata, rc, properties) -> None:
        """Callback for when a connection is lost"""
        logger.info(f"Disconnected from MQTT broker, rc={rc}")
        self.connected = False
        
        if rc != 0:
            self.last_error = f"Disconnected with code {rc}"
    
    def _on_message(self, client, userdata, msg) -> None:
        """Callback for when a message is received"""
        try:
            logger.info(f"Received MQTT message on topic: {msg.topic}")
            
            # Try to parse JSON payload
            payload = msg.payload.decode()
            try:
                data = json.loads(payload)
                
                # Check if this is tank data
                if "level" in data and "tank_id" in data:
                    # Convert timestamp string to datetime if needed
                    if isinstance(data.get("timestamp"), str):
                        try:
                            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                        except ValueError:
                            data["timestamp"] = datetime.now()
                    elif not data.get("timestamp"):
                        data["timestamp"] = datetime.now()
                    
                    # Add to tank data
                    self.tank_data.append(data)
                    logger.info(f"Added tank data from MQTT: {data}")
            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON MQTT message: {payload}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {str(e)}")
    
    def get_tank_data(self) -> List[Dict[str, Any]]:
        """Get collected tank data"""
        return self.tank_data.copy()
    
    def clear_tank_data(self) -> None:
        """Clear collected tank data"""
        self.tank_data = []
        logger.info("Cleared MQTT tank data")

# Create a singleton instance
mqtt_client = MQTTClient()
