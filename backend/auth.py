from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
import json
import logging
import secrets
import hashlib
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
AUTH_DIR = "auth_data"
USERS_FILE = os.path.join(AUTH_DIR, "users.json")
SESSIONS_FILE = os.path.join(AUTH_DIR, "sessions.json")

# Ensure auth data directory exists
os.makedirs(AUTH_DIR, exist_ok=True)

# Models
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    company: Optional[str] = None

class User(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    company: Optional[str] = None
    created_at: datetime
    is_active: bool = True
    is_admin: bool = False
    subscription_tier: str = "free"  # free, basic, premium
    subscription_expires: Optional[datetime] = None

class UserInDB(User):
    password_hash: str
    salt: str

class UserPublic(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    company: Optional[str] = None
    subscription_tier: str
    is_admin: bool

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserPublic

class LoginRequest(BaseModel):
    username: str
    password: str

# Helper functions
def get_users() -> Dict[str, UserInDB]:
    """Load users from file or return empty dict if file doesn't exist"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                users_data = json.load(f)
                users = {}
                for username, user_data in users_data.items():
                    # Convert string dates to datetime objects
                    if user_data.get("created_at"):
                        user_data["created_at"] = datetime.fromisoformat(user_data["created_at"])
                    if user_data.get("subscription_expires"):
                        user_data["subscription_expires"] = datetime.fromisoformat(user_data["subscription_expires"])
                    users[username] = UserInDB(**user_data)
                return users
        except Exception as e:
            logger.error(f"Error loading users: {str(e)}")
            return {}
    return {}

def save_users(users: Dict[str, UserInDB]) -> None:
    """Save users to file"""
    try:
        # Convert users to dict for serialization
        users_dict = {}
        for username, user in users.items():
            user_dict = user.dict()
            # Convert datetime objects to ISO format strings
            if isinstance(user_dict.get("created_at"), datetime):
                user_dict["created_at"] = user_dict["created_at"].isoformat()
            if isinstance(user_dict.get("subscription_expires"), datetime):
                user_dict["subscription_expires"] = user_dict["subscription_expires"].isoformat()
            users_dict[username] = user_dict
            
        with open(USERS_FILE, 'w') as f:
            json.dump(users_dict, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save user data"
        )

def get_sessions() -> Dict[str, Dict[str, Any]]:
    """Load sessions from file or return empty dict if file doesn't exist"""
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, 'r') as f:
                sessions_data = json.load(f)
                sessions = {}
                for token, session_data in sessions_data.items():
                    # Convert string dates to datetime objects
                    if session_data.get("expires_at"):
                        session_data["expires_at"] = datetime.fromisoformat(session_data["expires_at"])
                    sessions[token] = session_data
                return sessions
        except Exception as e:
            logger.error(f"Error loading sessions: {str(e)}")
            return {}
    return {}

def save_sessions(sessions: Dict[str, Dict[str, Any]]) -> None:
    """Save sessions to file"""
    try:
        # Convert sessions for serialization
        sessions_dict = {}
        for token, session in sessions.items():
            session_dict = session.copy()
            # Convert datetime objects to ISO format strings
            if isinstance(session_dict.get("expires_at"), datetime):
                session_dict["expires_at"] = session_dict["expires_at"].isoformat()
            sessions_dict[token] = session_dict
            
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions_dict, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving sessions: {str(e)}")

def hash_password(password: str, salt: Optional[str] = None) -> tuple:
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

def verify_password(plain_password: str, hashed_password: str, salt: str) -> bool:
    """Verify a password against a hash"""
    password_hash, _ = hash_password(plain_password, salt)
    return password_hash == hashed_password

def create_access_token(username: str, expires_delta: timedelta = timedelta(days=7)) -> str:
    """Create a new access token"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + expires_delta
    
    # Save token to sessions
    sessions = get_sessions()
    sessions[token] = {
        "username": username,
        "expires_at": expires_at
    }
    save_sessions(sessions)
    
    return token, expires_at

def get_current_user(token: str) -> UserInDB:
    """Get the current user from a token"""
    sessions = get_sessions()
    if token not in sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    session = sessions[token]
    if datetime.now() > session["expires_at"]:
        # Remove expired token
        del sessions[token]
        save_sessions(sessions)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    users = get_users()
    username = session["username"]
    if username not in users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return users[username]

# Create router
router = APIRouter()

@router.post("/register", response_model=UserPublic)
async def register(user_data: UserCreate):
    users = get_users()
    
    # Check if username already exists
    if user_data.username in users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    for existing_user in users.values():
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Hash password
    password_hash, salt = hash_password(user_data.password)
    
    # Create new user
    new_user = UserInDB(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        company=user_data.company,
        created_at=datetime.now(),
        password_hash=password_hash,
        salt=salt,
        subscription_tier="free",
        is_admin=False
    )
    
    # Save user
    users[user_data.username] = new_user
    save_users(users)
    
    # Return public user data
    return UserPublic(
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        company=new_user.company,
        subscription_tier=new_user.subscription_tier,
        is_admin=new_user.is_admin
    )

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    users = get_users()
    
    # Check if user exists
    if login_data.username not in users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = users[login_data.username]
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash, user.salt):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token, expires_at = create_access_token(user.username)
    
    # Return token and user data
    return Token(
        access_token=access_token,
        expires_at=expires_at,
        user=UserPublic(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            company=user.company,
            subscription_tier=user.subscription_tier,
            is_admin=user.is_admin
        )
    )

@router.get("/me", response_model=UserPublic)
async def get_me(token: str):
    user = get_current_user(token)
    return UserPublic(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        company=user.company,
        subscription_tier=user.subscription_tier,
        is_admin=user.is_admin
    )

# Initialize with admin user if no users exist
def init_admin_user():
    users = get_users()
    if not users:
        # Create admin user
        password_hash, salt = hash_password("admin123")
        admin_user = UserInDB(
            email="admin@example.com",
            username="admin",
            full_name="Admin User",
            created_at=datetime.now(),
            password_hash=password_hash,
            salt=salt,
            is_admin=True,
            subscription_tier="premium"
        )
        users["admin"] = admin_user
        save_users(users)
        logger.info("Created default admin user")

# Initialize admin user
init_admin_user()
