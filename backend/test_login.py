import requests
import json

def test_login():
    url = "http://localhost:8000/api/auth/login"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(url, json=data)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("Login successful!")
        print(json.dumps(response.json(), indent=2))
    else:
        print("Login failed!")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_login()
