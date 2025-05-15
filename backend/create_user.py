import json
import os
import secrets
import hashlib
from datetime import datetime

# Constants
AUTH_DIR = "auth_data"
USERS_FILE = os.path.join(AUTH_DIR, "users.json")

def hash_password(password, salt=None):
    """Hash a password with a salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Combine password and salt, then hash
    password_hash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100000  # Number of iterations
    ).hex()
    
    return password_hash, salt

def get_users():
    """Load users from file or return empty dict if file doesn't exist"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                users_data = json.load(f)
                return users_data
        except Exception as e:
            print(f"Error loading users: {str(e)}")
            return {}
    return {}

def save_users(users):
    """Save users to file"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        print("Users saved successfully")
    except Exception as e:
        print(f"Error saving users: {str(e)}")

def create_user(username, email, password, full_name=None, company=None, is_admin=False, subscription_tier="free"):
    """Create a new user"""
    users = get_users()
    
    # Check if username already exists
    if username in users:
        print(f"Username '{username}' already exists")
        return False
    
    # Hash password
    password_hash, salt = hash_password(password)
    
    # Create new user
    new_user = {
        "email": email,
        "username": username,
        "full_name": full_name,
        "company": company,
        "created_at": datetime.now().isoformat(),
        "is_active": True,
        "is_admin": is_admin,
        "subscription_tier": subscription_tier,
        "subscription_expires": None,
        "password_hash": password_hash,
        "salt": salt
    }
    
    # Add to users dict
    users[username] = new_user
    
    # Save users
    save_users(users)
    
    print(f"User '{username}' created successfully")
    return True

if __name__ == "__main__":
    # Create a regular user
    create_user(
        username="user",
        email="user@example.com",
        password="password123",
        full_name="Regular User",
        company="Example Inc",
        is_admin=False,
        subscription_tier="basic"
    )
    
    # Create another user
    create_user(
        username="abdullah",
        email="abdullah@example.com",
        password="password123",
        full_name="Abdullah",
        company="Ebsar",
        is_admin=False,
        subscription_tier="premium"
    )
    
    print("Users created successfully")
