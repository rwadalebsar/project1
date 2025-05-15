import json
import os
import logging
import time
import threading
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.exceptions import ModbusException, ConnectionException
from pymodbus.pdu import ExceptionResponse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
MODBUS_CONFIG_DIR = "modbus_data"
MODBUS_CONFIG_FILE = os.path.join(MODBUS_CONFIG_DIR, "config.json")

# Ensure modbus data directory exists
os.makedirs(MODBUS_CONFIG_DIR, exist_ok=True)

class ModbusClient:
    """Client for Modbus integration with tank monitoring"""
    
    def __init__(self):
        """Initialize the Modbus client"""
        self.config = self._load_config()
        self.connected = False
        self.last_error = None
        self.tank_data = []
        self.client = None
        self.monitoring_thread = None
        self.stop_monitoring = False
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(MODBUS_CONFIG_FILE):
            try:
                with open(MODBUS_CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error("Invalid Modbus config file format. Using defaults.")
        
        # Default configuration
        default_config = {
            "enabled": False,
            "mode": "tcp",  # tcp or rtu
            # TCP settings
            "host": "localhost",
            "port": 502,
            # RTU settings
            "port_name": "/dev/ttyUSB0",
            "baudrate": 9600,
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
            # Common settings
            "unit_id": 1,
            "timeout": 3,
            "retries": 3,
            "tank_registers": [
                {
                    "tank_id": "tank1",
                    "name": "Tank 1",
                    "register_type": "holding",  # holding, input, coil, discrete_input
                    "address": 100,
                    "data_type": "float",  # float, int16, int32, uint16, uint32, bool
                    "scaling_factor": 1.0,
                    "offset": 0.0
                }
            ],
            "polling_interval": 60,  # seconds
            "user_id": None
        }
        
        # Save default config if none exists
        if not os.path.exists(MODBUS_CONFIG_FILE):
            with open(MODBUS_CONFIG_FILE, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default Modbus configuration file: {MODBUS_CONFIG_FILE}")
        
        return default_config
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(MODBUS_CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Saved Modbus configuration")
        except Exception as e:
            logger.error(f"Error saving Modbus configuration: {str(e)}")
    
    def update_config(self, config: Dict[str, Any]) -> bool:
        """Update Modbus configuration"""
        try:
            # Update config
            self.config.update(config)
            
            # Save config
            self._save_config()
            
            logger.info("Updated Modbus configuration")
            return True
        except Exception as e:
            logger.error(f"Error updating Modbus configuration: {str(e)}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current Modbus configuration"""
        # Return a copy to prevent direct modification
        config = self.config.copy()
        
        # Add status information
        config["connected"] = self.connected
        config["last_error"] = self.last_error
        
        return config
    
    def _create_client(self):
        """Create Modbus client based on configuration"""
        mode = self.config.get("mode", "tcp")
        
        if mode == "tcp":
            # Create TCP client
            host = self.config.get("host", "localhost")
            port = self.config.get("port", 502)
            timeout = self.config.get("timeout", 3)
            retries = self.config.get("retries", 3)
            
            client = ModbusTcpClient(
                host=host,
                port=port,
                timeout=timeout,
                retries=retries
            )
            
        elif mode == "rtu":
            # Create RTU client
            port_name = self.config.get("port_name", "/dev/ttyUSB0")
            baudrate = self.config.get("baudrate", 9600)
            bytesize = self.config.get("bytesize", 8)
            parity = self.config.get("parity", "N")
            stopbits = self.config.get("stopbits", 1)
            timeout = self.config.get("timeout", 3)
            retries = self.config.get("retries", 3)
            
            client = ModbusSerialClient(
                method="rtu",
                port=port_name,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits,
                timeout=timeout,
                retries=retries
            )
            
        else:
            raise ValueError(f"Unsupported Modbus mode: {mode}")
        
        return client
    
    def connect(self) -> bool:
        """Connect to Modbus device"""
        if not self.config.get("enabled", False):
            self.last_error = "Modbus is disabled"
            return False
            
        try:
            # Disconnect if already connected
            if self.client:
                self.disconnect()
                
            # Create client
            self.client = self._create_client()
            
            # Connect to device
            if not self.client.connect():
                self.last_error = "Failed to connect to Modbus device"
                self.connected = False
                return False
            
            self.connected = True
            self.last_error = None
            logger.info(f"Connected to Modbus device")
            return True
            
        except Exception as e:
            self.client = None
            self.connected = False
            self.last_error = str(e)
            logger.error(f"Error connecting to Modbus device: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from Modbus device"""
        try:
            # Stop monitoring if active
            self.stop_monitoring = True
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            # Disconnect client
            if self.client:
                self.client.close()
                self.client = None
            
            self.connected = False
            logger.info("Disconnected from Modbus device")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error disconnecting from Modbus device: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """Test connection to Modbus device"""
        if not self.config.get("enabled", False):
            self.last_error = "Modbus is disabled"
            return False
            
        try:
            # Connect to device
            if not self.connect():
                return False
            
            # Try to read a register to test connection
            unit_id = self.config.get("unit_id", 1)
            
            # Read first register from configuration or use a default one
            if self.config.get("tank_registers"):
                register = self.config.get("tank_registers")[0]
                register_type = register.get("register_type", "holding")
                address = register.get("address", 0)
                
                if register_type == "holding":
                    result = self.client.read_holding_registers(address, 1, slave=unit_id)
                elif register_type == "input":
                    result = self.client.read_input_registers(address, 1, slave=unit_id)
                elif register_type == "coil":
                    result = self.client.read_coils(address, 1, slave=unit_id)
                elif register_type == "discrete_input":
                    result = self.client.read_discrete_inputs(address, 1, slave=unit_id)
                else:
                    result = self.client.read_holding_registers(0, 1, slave=unit_id)
            else:
                # Default test: read first holding register
                result = self.client.read_holding_registers(0, 1, slave=unit_id)
            
            # Check if result is valid
            if result.isError():
                self.last_error = f"Error reading register: {result}"
                self.connected = False
                return False
            
            # Disconnect
            self.disconnect()
            
            self.connected = True
            self.last_error = None
            return True
            
        except Exception as e:
            self.disconnect()
            self.connected = False
            self.last_error = str(e)
            logger.error(f"Error testing connection to Modbus device: {str(e)}")
            return False
    
    def _read_register_value(self, register: Dict[str, Any]) -> Union[float, int, bool, None]:
        """Read value from register based on configuration"""
        if not self.client or not self.connected:
            return None
            
        try:
            register_type = register.get("register_type", "holding")
            address = register.get("address", 0)
            data_type = register.get("data_type", "float")
            unit_id = self.config.get("unit_id", 1)
            
            # Read register based on type
            if register_type == "holding":
                if data_type in ["float", "int32", "uint32"]:
                    result = self.client.read_holding_registers(address, 2, slave=unit_id)
                else:
                    result = self.client.read_holding_registers(address, 1, slave=unit_id)
            elif register_type == "input":
                if data_type in ["float", "int32", "uint32"]:
                    result = self.client.read_input_registers(address, 2, slave=unit_id)
                else:
                    result = self.client.read_input_registers(address, 1, slave=unit_id)
            elif register_type == "coil":
                result = self.client.read_coils(address, 1, slave=unit_id)
            elif register_type == "discrete_input":
                result = self.client.read_discrete_inputs(address, 1, slave=unit_id)
            else:
                logger.error(f"Unsupported register type: {register_type}")
                return None
            
            # Check if result is valid
            if result.isError():
                logger.error(f"Error reading register: {result}")
                return None
            
            # Process value based on data type
            if register_type in ["coil", "discrete_input"]:
                # Boolean value
                value = result.bits[0]
            else:
                # Numeric value
                if data_type == "float":
                    # Convert two registers to float
                    registers = result.registers
                    if len(registers) < 2:
                        logger.error("Not enough registers for float conversion")
                        return None
                    
                    # Convert two 16-bit registers to 32-bit float
                    import struct
                    value = struct.unpack('>f', struct.pack('>HH', registers[0], registers[1]))[0]
                    
                elif data_type == "int32":
                    # Convert two registers to 32-bit signed integer
                    registers = result.registers
                    if len(registers) < 2:
                        logger.error("Not enough registers for int32 conversion")
                        return None
                    
                    value = (registers[0] << 16) | registers[1]
                    # Handle sign bit
                    if value & 0x80000000:
                        value = -((~value & 0xFFFFFFFF) + 1)
                        
                elif data_type == "uint32":
                    # Convert two registers to 32-bit unsigned integer
                    registers = result.registers
                    if len(registers) < 2:
                        logger.error("Not enough registers for uint32 conversion")
                        return None
                    
                    value = (registers[0] << 16) | registers[1]
                    
                elif data_type == "int16":
                    # Convert register to 16-bit signed integer
                    value = result.registers[0]
                    # Handle sign bit
                    if value & 0x8000:
                        value = -((~value & 0xFFFF) + 1)
                        
                elif data_type == "uint16":
                    # Use register as 16-bit unsigned integer
                    value = result.registers[0]
                    
                else:
                    logger.error(f"Unsupported data type: {data_type}")
                    return None
            
            # Apply scaling and offset
            scaling_factor = register.get("scaling_factor", 1.0)
            offset = register.get("offset", 0.0)
            
            if isinstance(value, bool):
                return value
            else:
                return value * scaling_factor + offset
                
        except Exception as e:
            logger.error(f"Error reading register value: {str(e)}")
            return None
    
    def _monitoring_thread_func(self):
        """Thread function for monitoring Modbus registers"""
        logger.info("Starting Modbus monitoring thread")
        
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
                logger.error(f"Error in Modbus monitoring thread: {str(e)}")
                time.sleep(5)
        
        logger.info("Modbus monitoring thread stopped")
    
    def start_monitoring(self) -> bool:
        """Start monitoring Modbus registers"""
        if not self.config.get("enabled", False):
            self.last_error = "Modbus is disabled"
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
            
            logger.info("Started Modbus monitoring")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error starting Modbus monitoring: {str(e)}")
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop monitoring Modbus registers"""
        try:
            # Set stop flag
            self.stop_monitoring = True
            
            # Wait for thread to stop
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            logger.info("Stopped Modbus monitoring")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error stopping Modbus monitoring: {str(e)}")
            return False
    
    def fetch_tank_data(self) -> List[Dict[str, Any]]:
        """Fetch tank data from Modbus registers"""
        if not self.config.get("enabled", False):
            logger.warning("Modbus is disabled")
            return []
            
        try:
            # Connect if not connected
            if not self.connected or not self.client:
                if not self.connect():
                    return []
            
            # Get tank registers
            tank_registers = self.config.get("tank_registers", [])
            
            # Read values from registers
            results = []
            for register in tank_registers:
                try:
                    # Read register value
                    value = self._read_register_value(register)
                    
                    if value is not None:
                        # Create tank data entry
                        tank_data = {
                            "tank_id": register.get("tank_id", f"tank_{register.get('address')}"),
                            "name": register.get("name", f"Tank {register.get('address')}"),
                            "level": float(value) if not isinstance(value, bool) else (1.0 if value else 0.0),
                            "timestamp": datetime.now().isoformat(),
                            "source": "modbus"
                        }
                        
                        results.append(tank_data)
                        self.tank_data.append(tank_data)
                        
                except Exception as e:
                    logger.warning(f"Error reading register for tank {register.get('tank_id')}: {str(e)}")
            
            logger.info(f"Fetched {len(results)} tank readings from Modbus registers")
            return results
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error fetching tank data from Modbus registers: {str(e)}")
            return []
    
    def get_tank_data(self) -> List[Dict[str, Any]]:
        """Get collected tank data"""
        return self.tank_data.copy()
    
    def clear_tank_data(self) -> None:
        """Clear collected tank data"""
        self.tank_data = []
        logger.info("Cleared Modbus tank data")

# Create a singleton instance
modbus_client = ModbusClient()
