# Protocol Simulators for Tank Monitoring System

This directory contains comprehensive simulators for all protocols supported by the tank monitoring system. These simulators allow you to test and develop against realistic data sources without needing actual hardware.

## 🚀 Available Simulators

### 1. MQTT Simulator
- **File**: `mqtt_simulator.py`
- **Purpose**: Simulates sending tank level data via MQTT protocol
- **Protocol**: MQTT 3.1.1
- **Usage**: 
  ```bash
  python mqtt_simulator.py --broker localhost --topic-prefix tanks --tank-id tank1 --level 75.5
  ```

### 2. REST API Simulator
- **File**: `rest_simulator.py`
- **Purpose**: Simulates sending tank level data to REST API endpoints
- **Protocol**: HTTP/REST
- **Usage**:
  ```bash
  python rest_simulator.py --url http://localhost:8000/api/tank-levels --tank-id tank1 --level 75.5 --token YOUR_AUTH_TOKEN
  ```

### 3. GraphQL Simulator ⭐ NEW
- **File**: `graphql_simulator.py`
- **Purpose**: Creates a GraphQL server that provides tank data
- **Protocol**: GraphQL over HTTP
- **Features**: 
  - Real-time data updates
  - Multiple tanks with realistic simulation
  - GraphQL schema introspection
- **Usage**:
  ```bash
  python graphql_simulator.py --port 4000
  ```
- **Endpoints**:
  - GraphQL: `http://localhost:4000/graphql`
  - Health: `http://localhost:4000/health`
- **Sample Queries**:
  ```graphql
  # Get all tanks
  { tanks { id name level status } }
  
  # Get specific tank with readings
  { tank(id: "tank1") { id name level lastUpdated readings { timestamp level } } }
  ```

### 4. OPC UA Simulator ⭐ NEW
- **File**: `opcua_simulator.py`
- **Purpose**: Creates an OPC UA server with tank data nodes
- **Protocol**: OPC UA
- **Features**:
  - Standard OPC UA server implementation
  - Hierarchical tank data structure
  - Real-time value updates
  - Device identification
- **Usage**:
  ```bash
  python opcua_simulator.py --port 4840
  ```
- **Endpoint**: `opc.tcp://localhost:4840/freeopcua/server/`
- **Node Structure**:
  ```
  Objects/
  └── Tanks/
      ├── Main Storage Tank/
      │   ├── Level (Float)
      │   ├── Status (String)
      │   ├── Capacity (Float)
      │   └── LastUpdated (String)
      ├── Secondary Tank/
      └── Emergency Reserve/
  ```

### 5. Modbus Simulator ⭐ NEW
- **File**: `modbus_simulator.py`
- **Purpose**: Creates a Modbus TCP server with tank register data
- **Protocol**: Modbus TCP
- **Features**:
  - Standard Modbus TCP implementation
  - Holding registers for tank data
  - Real-time register updates
  - Device identification
- **Usage**:
  ```bash
  python modbus_simulator.py --port 5020  # Use 5020 to avoid root privileges
  ```
- **Register Mapping** (per tank, 8 registers each):
  ```
  Tank 1: Registers 0-7
  Tank 2: Registers 10-17  
  Tank 3: Registers 20-27
  
  Layout per tank:
  Reg +0-1: Level (32-bit float)
  Reg +2-3: Capacity (32-bit float)
  Reg +4:   Status (16-bit int: 0=NORMAL, 1=LOW, 2=HIGH)
  Reg +5:   Tank ID Hash (16-bit int)
  Reg +6-7: Timestamp (32-bit int)
  ```

## 📦 Installation

### Quick Setup
```bash
# Install all dependencies
pip install -r requirements.txt
```

### Individual Dependencies
```bash
# MQTT
pip install paho-mqtt

# REST API
pip install requests

# GraphQL
pip install flask flask-cors

# OPC UA
pip install asyncua

# Modbus
pip install pymodbus
```

## 🧪 Testing

### Test All Simulators
```bash
python test_all_simulators.py
```

### Test Individual Simulators
```bash
# Test REST (requires backend running)
python rest_simulator.py --url http://localhost:8000/api/tank-levels --tank-id test --level 50 --token YOUR_TOKEN

# Test MQTT (requires MQTT broker)
python mqtt_simulator.py --broker localhost --topic-prefix tanks --tank-id test --level 50

# Test GraphQL (starts server)
python graphql_simulator.py --port 4000

# Test OPC UA (starts server)
python opcua_simulator.py --port 4840

# Test Modbus (starts server)
python modbus_simulator.py --port 5020
```

## 🔧 Configuration

### MQTT Broker Setup
For MQTT testing, install Mosquitto:

**Linux/macOS:**
```bash
# Ubuntu/Debian
sudo apt install mosquitto mosquitto-clients

# macOS
brew install mosquitto
brew services start mosquitto
```

**Windows:**
Download from [Mosquitto Downloads](https://mosquitto.org/download/)

### Backend Configuration
Ensure your backend is configured to connect to these simulators:

1. **GraphQL**: Update `backend/graphql_data/config.json`
2. **OPC UA**: Update `backend/opcua_data/config.json`
3. **Modbus**: Update `backend/modbus_data/config.json`
4. **MQTT**: Update `backend/mqtt_data/config.json`

## 🚀 Quick Start Guide

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start a simulator** (choose one):
   ```bash
   # GraphQL Server
   python graphql_simulator.py --port 4000
   
   # OPC UA Server
   python opcua_simulator.py --port 4840
   
   # Modbus Server
   python modbus_simulator.py --port 5020
   ```

3. **Configure backend** to connect to the simulator

4. **Test the connection** using the backend's protocol clients

## 📊 Simulator Features

| Protocol | Real-time Updates | Multiple Tanks | Authentication | Status Codes |
|----------|------------------|----------------|----------------|--------------|
| MQTT     | ✅               | ✅             | Optional       | ✅           |
| REST     | ✅               | ✅             | Required       | ✅           |
| GraphQL  | ✅               | ✅             | None           | ✅           |
| OPC UA   | ✅               | ✅             | None           | ✅           |
| Modbus   | ✅               | ✅             | None           | ✅           |

## 🛠️ Development

To add new simulators or modify existing ones:

1. Follow the existing patterns in the simulator files
2. Add appropriate error handling and logging
3. Update this README with new features
4. Add tests to `test_all_simulators.py`

## 📝 Notes

- **Port Requirements**: Modbus port 502 requires root privileges on Linux
- **Dependencies**: Each simulator has specific Python package requirements
- **Testing**: Use the test script to verify all simulators work correctly
- **Configuration**: Backend must be configured to connect to simulator endpoints
