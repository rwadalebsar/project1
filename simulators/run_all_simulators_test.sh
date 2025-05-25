#!/bin/bash

# Test script for running protocol simulators.
# Note: You may need to adjust parameters (especially tokens, URLs, and broker details)
# before running this script. Ensure the backend and any necessary services (like an MQTT broker)
# are running.

echo "--- Running REST API Simulator Test ---"
# Replace with your actual API URL and a valid JWT token
API_URL="http://localhost:8000/api/tank-levels"
AUTH_TOKEN="YOUR_JWT_TOKEN_HERE" # IMPORTANT: Replace with a real token!

if [ "$AUTH_TOKEN" == "YOUR_JWT_TOKEN_HERE" ]; then
  echo "WARNING: Please replace YOUR_JWT_TOKEN_HERE with a valid JWT token in the script."
fi

python simulators/rest_simulator.py \
  --url "$API_URL" \
  --tank-id "restSimTank001" \
  --level 75.2 \
  --token "$AUTH_TOKEN"

echo ""
echo "--- Running MQTT Simulator Test ---"
# Replace with your MQTT broker details if different
MQTT_BROKER="localhost"
MQTT_PORT="1883"
MQTT_TOPIC_PREFIX="tanks/telemetry" # Ensure this matches your backend's subscription

python simulators/mqtt_simulator.py \
  --broker "$MQTT_BROKER" \
  --port "$MQTT_PORT" \
  --topic-prefix "$MQTT_TOPIC_PREFIX" \
  --tank-id "mqttSimTank001" \
  --level 62.8
  # Add --username and --password if your broker requires them:
  # --username "youruser" \
  # --password "yourpassword"

echo ""
echo "--- Simulator tests complete ---"
echo "Check the output of each script and verify data in the backend/frontend."
