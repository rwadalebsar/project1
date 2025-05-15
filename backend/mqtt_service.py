import paho.mqtt.client as mqtt
import json
import os
import logging
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
MQTT_CONFIG_DIR = "mqtt_data"
MQTT_CONFIG_FILE = os.path.join(MQTT_CONFIG_DIR, "connections.json")

# Ensure mqtt data directory exists
os.makedirs(MQTT_CONFIG_DIR, exist_ok=True)

class MQTTConnection:
    """Represents a single MQTT connection configuration"""
    def __init__(self, 
                 id: str,
                 name: str, 
                 broker: str, 
                 port: int = 1883, 
                 username: Optional[str] = None, 
                 password: Optional[str] = None,
                 client_id: Optional[str] = None,
                 topic_prefix: str = "",
                 use_ssl: bool = False,
                 user_id: str = None,
                 enabled: bool = True):
        self.id = id
        self.name = name
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id or f"tank_monitor_{int(time.time())}"
        self.topic_prefix = topic_prefix
        self.use_ssl = use_ssl
        self.user_id = user_id
        self.enabled = enabled
        self.connected = False
        self.last_connected = None
        self.last_error = None
        self.client = None
        self.subscriptions = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "broker": self.broker,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "client_id": self.client_id,
            "topic_prefix": self.topic_prefix,
            "use_ssl": self.use_ssl,
            "user_id": self.user_id,
            "enabled": self.enabled,
            "connected": self.connected,
            "last_connected": self.last_connected.isoformat() if self.last_connected else None,
            "last_error": self.last_error,
            "subscriptions": self.subscriptions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MQTTConnection':
        """Create from dictionary"""
        conn = cls(
            id=data.get("id"),
            name=data.get("name"),
            broker=data.get("broker"),
            port=data.get("port", 1883),
            username=data.get("username"),
            password=data.get("password"),
            client_id=data.get("client_id"),
            topic_prefix=data.get("topic_prefix", ""),
            use_ssl=data.get("use_ssl", False),
            user_id=data.get("user_id"),
            enabled=data.get("enabled", True)
        )
        
        # Set additional properties
        conn.connected = data.get("connected", False)
        if data.get("last_connected"):
            try:
                conn.last_connected = datetime.fromisoformat(data.get("last_connected"))
            except (ValueError, TypeError):
                conn.last_connected = None
        conn.last_error = data.get("last_error")
        conn.subscriptions = data.get("subscriptions", [])
        
        return conn

class MQTTService:
    """Service to manage MQTT connections"""
    
    def __init__(self):
        """Initialize the MQTT service"""
        self.connections: Dict[str, MQTTConnection] = {}
        self.clients: Dict[str, mqtt.Client] = {}
        self.message_callbacks: List[Callable] = []
        self.load_connections()
        
    def load_connections(self) -> None:
        """Load connections from file"""
        if os.path.exists(MQTT_CONFIG_FILE):
            try:
                with open(MQTT_CONFIG_FILE, 'r') as f:
                    connections_data = json.load(f)
                    for conn_id, conn_data in connections_data.items():
                        self.connections[conn_id] = MQTTConnection.from_dict(conn_data)
                logger.info(f"Loaded {len(self.connections)} MQTT connections")
            except Exception as e:
                logger.error(f"Error loading MQTT connections: {str(e)}")
        else:
            logger.info("No MQTT connections file found")
    
    def save_connections(self) -> None:
        """Save connections to file"""
        try:
            connections_dict = {conn_id: conn.to_dict() for conn_id, conn in self.connections.items()}
            with open(MQTT_CONFIG_FILE, 'w') as f:
                json.dump(connections_dict, f, indent=2)
            logger.info(f"Saved {len(self.connections)} MQTT connections")
        except Exception as e:
            logger.error(f"Error saving MQTT connections: {str(e)}")
    
    def get_connections(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all connections, optionally filtered by user_id"""
        if user_id:
            return [conn.to_dict() for conn_id, conn in self.connections.items() 
                   if conn.user_id == user_id]
        return [conn.to_dict() for conn_id, conn in self.connections.items()]
    
    def get_connection(self, conn_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific connection by ID"""
        if conn_id in self.connections:
            return self.connections[conn_id].to_dict()
        return None
    
    def add_connection(self, connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new connection"""
        # Generate a unique ID if not provided
        if not connection_data.get("id"):
            connection_data["id"] = f"mqtt_{int(time.time())}"
            
        # Create connection object
        connection = MQTTConnection.from_dict(connection_data)
        
        # Add to connections dict
        self.connections[connection.id] = connection
        
        # Save to file
        self.save_connections()
        
        return connection.to_dict()
    
    def update_connection(self, conn_id: str, connection_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing connection"""
        if conn_id not in self.connections:
            return None
        
        # Disconnect if connected
        if self.connections[conn_id].connected:
            self.disconnect(conn_id)
        
        # Update connection data
        connection_data["id"] = conn_id  # Ensure ID doesn't change
        self.connections[conn_id] = MQTTConnection.from_dict(connection_data)
        
        # Save to file
        self.save_connections()
        
        return self.connections[conn_id].to_dict()
    
    def delete_connection(self, conn_id: str) -> bool:
        """Delete a connection"""
        if conn_id not in self.connections:
            return False
        
        # Disconnect if connected
        if self.connections[conn_id].connected:
            self.disconnect(conn_id)
        
        # Remove from connections dict
        del self.connections[conn_id]
        
        # Save to file
        self.save_connections()
        
        return True
    
    def connect(self, conn_id: str) -> Dict[str, Any]:
        """Connect to an MQTT broker"""
        if conn_id not in self.connections:
            raise ValueError(f"Connection {conn_id} not found")
        
        connection = self.connections[conn_id]
        
        if not connection.enabled:
            connection.last_error = "Connection is disabled"
            return connection.to_dict()
        
        try:
            # Create MQTT client
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, connection.client_id)
            
            # Set up callbacks
            client.on_connect = lambda client, userdata, flags, rc, properties: self._on_connect(conn_id, rc)
            client.on_disconnect = lambda client, userdata, rc, properties: self._on_disconnect(conn_id, rc)
            client.on_message = lambda client, userdata, msg: self._on_message(conn_id, msg)
            
            # Set username and password if provided
            if connection.username and connection.password:
                client.username_pw_set(connection.username, connection.password)
            
            # Set SSL if enabled
            if connection.use_ssl:
                client.tls_set()
            
            # Connect to broker
            client.connect_async(connection.broker, connection.port)
            
            # Start the loop in a separate thread
            client.loop_start()
            
            # Store client
            self.clients[conn_id] = client
            
            # Update connection status
            connection.connected = True
            connection.last_connected = datetime.now()
            connection.last_error = None
            
            # Save to file
            self.save_connections()
            
            return connection.to_dict()
            
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {str(e)}")
            connection.connected = False
            connection.last_error = str(e)
            self.save_connections()
            raise
    
    def disconnect(self, conn_id: str) -> Dict[str, Any]:
        """Disconnect from an MQTT broker"""
        if conn_id not in self.connections:
            raise ValueError(f"Connection {conn_id} not found")
        
        connection = self.connections[conn_id]
        
        if conn_id in self.clients:
            try:
                client = self.clients[conn_id]
                client.loop_stop()
                client.disconnect()
                del self.clients[conn_id]
            except Exception as e:
                logger.error(f"Error disconnecting from MQTT broker: {str(e)}")
        
        # Update connection status
        connection.connected = False
        
        # Save to file
        self.save_connections()
        
        return connection.to_dict()
    
    def publish(self, conn_id: str, topic: str, payload: Any, qos: int = 0, retain: bool = False) -> bool:
        """Publish a message to an MQTT topic"""
        if conn_id not in self.connections:
            raise ValueError(f"Connection {conn_id} not found")
        
        if conn_id not in self.clients:
            raise ValueError(f"Connection {conn_id} is not connected")
        
        connection = self.connections[conn_id]
        client = self.clients[conn_id]
        
        # Add topic prefix if configured
        if connection.topic_prefix:
            full_topic = f"{connection.topic_prefix}/{topic}"
        else:
            full_topic = topic
        
        # Convert payload to JSON if it's a dict or list
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload)
        
        try:
            result = client.publish(full_topic, payload, qos, retain)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"Error publishing to MQTT topic: {str(e)}")
            return False
    
    def subscribe(self, conn_id: str, topic: str, qos: int = 0) -> bool:
        """Subscribe to an MQTT topic"""
        if conn_id not in self.connections:
            raise ValueError(f"Connection {conn_id} not found")
        
        if conn_id not in self.clients:
            raise ValueError(f"Connection {conn_id} is not connected")
        
        connection = self.connections[conn_id]
        client = self.clients[conn_id]
        
        # Add topic prefix if configured
        if connection.topic_prefix:
            full_topic = f"{connection.topic_prefix}/{topic}"
        else:
            full_topic = topic
        
        try:
            result = client.subscribe(full_topic, qos)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                # Add to subscriptions list if not already there
                if full_topic not in connection.subscriptions:
                    connection.subscriptions.append(full_topic)
                    self.save_connections()
                return True
            return False
        except Exception as e:
            logger.error(f"Error subscribing to MQTT topic: {str(e)}")
            return False
    
    def unsubscribe(self, conn_id: str, topic: str) -> bool:
        """Unsubscribe from an MQTT topic"""
        if conn_id not in self.connections:
            raise ValueError(f"Connection {conn_id} not found")
        
        if conn_id not in self.clients:
            raise ValueError(f"Connection {conn_id} is not connected")
        
        connection = self.connections[conn_id]
        client = self.clients[conn_id]
        
        # Add topic prefix if configured
        if connection.topic_prefix:
            full_topic = f"{connection.topic_prefix}/{topic}"
        else:
            full_topic = topic
        
        try:
            result = client.unsubscribe(full_topic)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                # Remove from subscriptions list
                if full_topic in connection.subscriptions:
                    connection.subscriptions.remove(full_topic)
                    self.save_connections()
                return True
            return False
        except Exception as e:
            logger.error(f"Error unsubscribing from MQTT topic: {str(e)}")
            return False
    
    def register_message_callback(self, callback: Callable) -> None:
        """Register a callback for received messages"""
        self.message_callbacks.append(callback)
    
    def _on_connect(self, conn_id: str, rc: int) -> None:
        """Callback for when a connection is established"""
        connection = self.connections[conn_id]
        
        if rc == 0:
            logger.info(f"Connected to MQTT broker: {connection.broker}")
            connection.connected = True
            connection.last_connected = datetime.now()
            connection.last_error = None
            
            # Resubscribe to topics
            if conn_id in self.clients and connection.subscriptions:
                client = self.clients[conn_id]
                for topic in connection.subscriptions:
                    client.subscribe(topic)
        else:
            logger.error(f"Failed to connect to MQTT broker: {connection.broker}, rc={rc}")
            connection.connected = False
            connection.last_error = f"Connection failed with code {rc}"
        
        self.save_connections()
    
    def _on_disconnect(self, conn_id: str, rc: int) -> None:
        """Callback for when a connection is lost"""
        if conn_id in self.connections:
            connection = self.connections[conn_id]
            
            logger.info(f"Disconnected from MQTT broker: {connection.broker}, rc={rc}")
            connection.connected = False
            
            if rc != 0:
                connection.last_error = f"Disconnected with code {rc}"
            
            self.save_connections()
    
    def _on_message(self, conn_id: str, msg) -> None:
        """Callback for when a message is received"""
        if conn_id in self.connections:
            connection = self.connections[conn_id]
            
            # Try to parse JSON payload
            try:
                payload = msg.payload.decode()
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    # Keep as string if not valid JSON
                    pass
                
                # Create message object
                message = {
                    "connection_id": conn_id,
                    "connection_name": connection.name,
                    "topic": msg.topic,
                    "payload": payload,
                    "qos": msg.qos,
                    "retain": msg.retain,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Call registered callbacks
                for callback in self.message_callbacks:
                    try:
                        callback(message)
                    except Exception as e:
                        logger.error(f"Error in message callback: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error processing MQTT message: {str(e)}")

# Create a singleton instance
mqtt_service = MQTTService()
