# Protocol Simulators

## Purpose
These scripts simulate external devices or services sending tank level data to the main backend application using various supported protocols. They are intended for testing the backend's data ingestion capabilities.

## Supported Simulators
- **REST API Simulator (`rest_simulator.py`)**: Sends data directly to the backend's `/api/tank-levels` POST endpoint.
- **MQTT Simulator (`mqtt_simulator.py`)**: Publishes data to an MQTT broker, which the backend should be configured to subscribe to.

**Note on Other Protocols (GraphQL, OPC UA, Modbus):**
Simulators for direct data ingestion via GraphQL, OPC UA, or Modbus have not been created because the backend application is designed to act as a *client* for these protocols (i.e., it fetches data *from* external GraphQL/OPC UA/Modbus services). The current simulators focus on protocols where the backend actively listens for or accepts incoming data (REST API) or subscribes to messages (MQTT).

## Prerequisites
- Python 3.x
- The `requests` library for `rest_simulator.py`. This is typically included in the main backend's `requirements.txt`.
- The `paho-mqtt` library for `mqtt_simulator.py`. This might need to be installed separately if not part of the main backend's dependencies:
  ```bash
  pip install paho-mqtt
  ```
- Ensure the main backend application is running.
- For the MQTT simulator, ensure an MQTT broker is running and accessible, and that the backend is configured to connect to it and subscribe to the relevant topics.
- For the REST simulator, you will need a valid authentication token for the backend API.

## Running the Simulators

### 1. REST API Simulator (`rest_simulator.py`)

This script sends a single tank level reading to the backend via a POST request.

**Command-line arguments:**
- `--url`: (Required) The full URL of the backend's tank level API endpoint (e.g., `http://localhost:8000/api/tank-levels`).
- `--tank-id`: (Required) The ID of the tank (e.g., `tank001`).
- `--level`: (Required) The tank level to send (e.g., `75.5`).
- `--token`: (Required) The Bearer authentication token for the API.

**Example Usage:**
```bash
python simulators/rest_simulator.py \
  --url http://localhost:8000/api/tank-levels \
  --tank-id "tankAlpha" \
  --level 63.2 \
  --token "your_jwt_token_here"
```

### 2. MQTT Simulator (`mqtt_simulator.py`)

This script publishes a single tank level reading to an MQTT topic. The backend's MQTT client should be configured to listen to this topic.

**Command-line arguments:**
- `--broker`: (Required) MQTT broker address (e.g., `localhost`).
- `--port`: MQTT broker port (default: `1883`).
- `--topic-prefix`: (Required) Topic prefix used by the backend (e.g., `tanks/data`). The message will be published to `<topic-prefix>/<tank-id>`.
- `--tank-id`: (Required) The ID of the tank (e.g., `tankBeta`).
- `--level`: (Required) The tank level to send (e.g., `82.1`).
- `--username`: (Optional) MQTT username.
- `--password`: (Optional) MQTT password.
- `--client-id`: (Optional) MQTT client ID.

**Example Usage:**
```bash
python simulators/mqtt_simulator.py \
  --broker "localhost" \
  --port 1883 \
  --topic-prefix "tanks/telemetry" \
  --tank-id "tankGamma" \
  --level 45.9
```
(Add `--username youruser --password yourpass` if your broker requires authentication)

## Verifying Simulator Operation
After running a simulator:
- **REST Simulator:** Check the script's output for a success status code (e.g., 200 or 201) from the backend. You can then verify in the application's frontend or via its API that the new tank level data for the specified `tank-id` has been recorded.
- **MQTT Simulator:** The script will output a success message if the publish was acknowledged by the broker. Verify in the application's frontend or via its API that the new tank level data (sent via MQTT) for the specified `tank-id` has been processed and recorded by the backend. Check backend logs if data does not appear, ensuring the backend's MQTT client is connected to the same broker and subscribed to the correct topic structure (`<topic-prefix>/<tank-id>`).
