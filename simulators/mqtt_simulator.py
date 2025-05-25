import paho.mqtt.client as mqtt
import argparse
import json
import datetime
import random
import time

def main():
    parser = argparse.ArgumentParser(description="Simulates sending tank level data via MQTT.")
    parser.add_argument("--broker", required=True, help="The MQTT broker address (string).")
    parser.add_argument("--port", type=int, default=1883, help="The MQTT broker port (integer, default 1883).")
    parser.add_argument("--topic-prefix", required=True, help="The topic prefix (string, e.g., 'tanks').")
    parser.add_argument("--tank-id", required=True, help="The ID of the tank (string).")
    parser.add_argument("--level", required=True, type=float, help="The tank level (float).")
    parser.add_argument("--username", help="Optional, MQTT username (string).")
    parser.add_argument("--password", help="Optional, MQTT password (string).")
    parser.add_argument("--client-id", default=f"mqtt_simulator_{random.randint(1000, 9999)}", help="Optional, MQTT client ID (string, default to a generated one like 'mqtt_simulator_random_number').")

    args = parser.parse_args()

    # Generate ISO timestamp
    timestamp = datetime.datetime.utcnow().isoformat()

    # Prepare JSON payload
    payload = {
        "level": args.level,
        "tank_id": args.tank_id,
        "timestamp": timestamp
    }
    payload_str = json.dumps(payload)

    # Construct full topic
    full_topic = f"{args.topic_prefix}/{args.tank_id}"

    # Create MQTT client instance
    # Using CallbackAPIVersion.VERSION1 for broader compatibility
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=args.client_id)

    # Set username/password if provided
    if args.username:
        client.username_pw_set(args.username, args.password)

    try:
        print(f"Connecting to MQTT broker {args.broker}:{args.port}...")
        client.connect(args.broker, args.port, 60)
        client.loop_start() # Start loop for processing network traffic and dispatching callbacks

        print(f"Publishing message to topic '{full_topic}': {payload_str}")
        message_info = client.publish(full_topic, payload_str)
        
        # Wait for publish to complete
        # For paho-mqtt versions >= 1.6.0, wait_for_publish is available.
        # For older versions, a short sleep might be necessary, but it's less reliable.
        if hasattr(message_info, 'wait_for_publish'):
            message_info.wait_for_publish(timeout=5) # Timeout after 5 seconds
            print("Message published successfully.")
        else:
            # Fallback for older paho-mqtt versions or if wait_for_publish is not behaving as expected
            time.sleep(2) # Wait 2 seconds to allow message to be sent
            print("Message published (using sleep fallback).")

    except ConnectionRefusedError:
        print(f"Error: Connection to MQTT broker {args.broker}:{args.port} refused. Check broker address and port.")
    except mqtt.MQTTException as e:
        print(f"MQTT Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if client.is_connected():
            client.disconnect()
            print("Disconnected from MQTT broker.")
        client.loop_stop() # Stop the network loop

if __name__ == "__main__":
    main()
