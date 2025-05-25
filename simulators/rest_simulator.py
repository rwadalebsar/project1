import requests
import argparse
import json

def main():
    parser = argparse.ArgumentParser(description="Simulates sending tank level data to an API.")
    parser.add_argument("--url", required=True, help="The API endpoint URL (e.g., http://localhost:8000/api/tank-levels)")
    parser.add_argument("--tank-id", required=True, help="The ID of the tank (string)")
    parser.add_argument("--level", required=True, type=float, help="The tank level (float)")
    parser.add_argument("--token", required=True, help="The authentication token (string)")

    args = parser.parse_args()

    payload = {
        "level": args.level,
        "tank_id": args.tank_id
    }

    headers = {
        "Authorization": f"Bearer {args.token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(args.url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
