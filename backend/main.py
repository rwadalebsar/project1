from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import json
import os
import logging
from fastapi.responses import JSONResponse
from tank_api_service import TankAPIService
import auth
from auth import get_current_user, UserInDB

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Tank Level Monitoring API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include the authentication router
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# Helper function to get the current user from the Authorization header
async def get_user_from_header(authorization: Optional[str] = Header(None)) -> Optional[UserInDB]:
    if not authorization:
        return None

    # Extract token from header
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1]
    try:
        return get_current_user(token)
    except HTTPException:
        return None

# Data models
class TankLevel(BaseModel):
    timestamp: datetime
    level: float
    tank_id: str = "tank1"
    user_id: Optional[str] = None

class TankLevelCreate(BaseModel):
    level: float
    tank_id: str = "tank1"

class AnomalyResult(BaseModel):
    timestamp: datetime
    level: float
    is_anomaly: bool
    anomaly_score: float

class SubscriptionTier(BaseModel):
    name: str
    max_tanks: int
    max_history_days: int
    anomaly_detection: bool
    price_monthly: float
    price_yearly: float

# Initialize API service
api_service = TankAPIService()

# Load initial data
tank_data = api_service.fetch_tank_levels()

# Anomaly detection model
def detect_anomalies(data, contamination=0.01):
    """
    Detect anomalies in tank level data using Isolation Forest

    Args:
        data: DataFrame with 'level' column
        contamination: Expected proportion of anomalies

    Returns:
        DataFrame with anomaly detection results
    """
    if len(data) < 10:  # Need enough data for meaningful detection
        return pd.DataFrame({
            'timestamp': data['timestamp'],
            'level': data['level'],
            'is_anomaly': [False] * len(data),
            'anomaly_score': [0.0] * len(data)
        })

    # Create and fit the model
    model = IsolationForest(contamination=contamination, random_state=42)

    # Reshape data for scikit-learn
    X = data['level'].values.reshape(-1, 1)

    # Fit the model and predict
    model.fit(X)
    scores = model.decision_function(X)
    predictions = model.predict(X)

    # Convert predictions (-1 for anomalies, 1 for normal) to boolean
    is_anomaly = [pred == -1 for pred in predictions]

    return pd.DataFrame({
        'timestamp': data['timestamp'],
        'level': data['level'],
        'is_anomaly': is_anomaly,
        'anomaly_score': scores
    })

@app.get("/")
def read_root():
    return {"message": "Welcome to the Tank Level Monitoring API"}

@app.get("/api/tank-levels", response_model=List[TankLevel])
async def get_tank_levels(
    days: Optional[int] = Query(None, description="Number of days of data to return"),
    tank_id: Optional[str] = Query(None, description="Tank ID to filter by"),
    user: Optional[UserInDB] = Depends(get_user_from_header)
):
    """Get tank level data, optionally filtered by days and tank ID"""
    global tank_data

    try:
        # Fetch fresh data from API
        tank_data = api_service.fetch_tank_levels(days)

        # Convert to DataFrame for easier filtering
        df = pd.DataFrame(tank_data)

        # Filter by tank_id if provided
        if tank_id:
            df = df[df['tank_id'] == tank_id]

        # Filter by user_id if user is authenticated
        if user:
            # If user is not admin, only show their data
            if not user.is_admin:
                # For mock data, we'll just assign some data to the user
                # In a real implementation, you'd filter by actual user_id
                df['user_id'] = df['user_id'].fillna(user.username)
                df = df[df['user_id'] == user.username]

        # Sort by timestamp (newest first)
        df = df.sort_values('timestamp', ascending=False)

        # Apply subscription tier limits
        if user:
            # Limit history based on subscription tier
            if user.subscription_tier == "free":
                # Free tier: 7 days of history
                cutoff_date = datetime.now() - timedelta(days=7)
                df = df[df['timestamp'] >= cutoff_date]
            elif user.subscription_tier == "basic":
                # Basic tier: 30 days of history
                cutoff_date = datetime.now() - timedelta(days=30)
                df = df[df['timestamp'] >= cutoff_date]
            # Premium tier: unlimited history

        # Convert back to list of dictionaries
        result = df.to_dict('records')
        return result
    except Exception as e:
        logger.error(f"Error getting tank levels: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching tank levels: {str(e)}")

@app.post("/api/tank-levels", response_model=TankLevel)
async def add_tank_level(
    tank_level: TankLevelCreate,
    user: Optional[UserInDB] = Depends(get_user_from_header)
):
    """Add a new tank level reading"""
    global tank_data

    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to add tank level readings",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Add reading via API service
        new_reading = api_service.add_tank_level(tank_level.level)

        # Add user_id to the reading
        new_reading["user_id"] = user.username

        # Refresh in-memory data
        tank_data = api_service.fetch_tank_levels()

        return new_reading
    except Exception as e:
        logger.error(f"Error adding tank level: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding tank level: {str(e)}")

@app.get("/api/anomalies", response_model=List[AnomalyResult])
async def get_anomalies(
    days: Optional[int] = Query(30, description="Number of days of data to analyze"),
    tank_id: Optional[str] = Query(None, description="Tank ID to filter by"),
    sensitivity: float = Query(0.01, description="Anomaly detection sensitivity (0.01-0.1)"),
    user: Optional[UserInDB] = Depends(get_user_from_header)
):
    """Detect anomalies in tank level data"""
    global tank_data

    # Check if user has access to anomaly detection
    if user and user.subscription_tier == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anomaly detection requires a Basic or Premium subscription"
        )

    try:
        # Ensure we have the latest data
        tank_data = api_service.fetch_tank_levels(days)

        # Convert to DataFrame for analysis
        df = pd.DataFrame(tank_data)

        # Filter by tank_id if provided
        if tank_id:
            df = df[df['tank_id'] == tank_id]

        # Filter by user_id if user is authenticated
        if user and not user.is_admin:
            # For mock data, we'll just assign some data to the user
            df['user_id'] = df['user_id'].fillna(user.username)
            df = df[df['user_id'] == user.username]

        # Sort by timestamp
        df = df.sort_values('timestamp')

        # Detect anomalies
        result_df = detect_anomalies(df, contamination=sensitivity)

        # Filter to only return anomalies
        anomalies_df = result_df[result_df['is_anomaly']]

        # Convert back to list of dictionaries
        result = anomalies_df.to_dict('records')
        return result
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")

@app.get("/api/stats")
async def get_stats(
    days: Optional[int] = Query(30, description="Number of days of data to analyze"),
    tank_id: Optional[str] = Query(None, description="Tank ID to filter by"),
    user: Optional[UserInDB] = Depends(get_user_from_header)
):
    """Get statistics about tank levels"""
    global tank_data

    try:
        # Ensure we have the latest data
        tank_data = api_service.fetch_tank_levels(days)

        # Convert to DataFrame for analysis
        df = pd.DataFrame(tank_data)

        # Filter by tank_id if provided
        if tank_id:
            df = df[df['tank_id'] == tank_id]

        # Filter by user_id if user is authenticated
        if user and not user.is_admin:
            # For mock data, we'll just assign some data to the user
            df['user_id'] = df['user_id'].fillna(user.username)
            df = df[df['user_id'] == user.username]

        # Apply subscription tier limits
        if user:
            if user.subscription_tier == "free":
                # Free tier: 7 days of history
                cutoff_date = datetime.now() - timedelta(days=7)
                df = df[df['timestamp'] >= cutoff_date]
            elif user.subscription_tier == "basic":
                # Basic tier: 30 days of history
                cutoff_date = datetime.now() - timedelta(days=30)
                df = df[df['timestamp'] >= cutoff_date]
            # Premium tier: unlimited history

        # Calculate statistics
        if len(df) == 0:
            return {
                "count": 0,
                "min_level": None,
                "max_level": None,
                "avg_level": None,
                "std_dev": None,
                "current_level": None,
                "last_updated": None
            }

        stats = {
            "count": len(df),
            "min_level": float(df['level'].min()),
            "max_level": float(df['level'].max()),
            "avg_level": float(df['level'].mean()),
            "std_dev": float(df['level'].std()),
            "current_level": float(df.sort_values('timestamp', ascending=False).iloc[0]['level']),
            "last_updated": df.sort_values('timestamp', ascending=False).iloc[0]['timestamp'].isoformat()
        }

        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

# Define subscription tiers
SUBSCRIPTION_TIERS = {
    "free": SubscriptionTier(
        name="Free",
        max_tanks=1,
        max_history_days=7,
        anomaly_detection=False,
        price_monthly=0,
        price_yearly=0
    ),
    "basic": SubscriptionTier(
        name="Basic",
        max_tanks=5,
        max_history_days=30,
        anomaly_detection=True,
        price_monthly=9.99,
        price_yearly=99.99
    ),
    "premium": SubscriptionTier(
        name="Premium",
        max_tanks=100,
        max_history_days=365,
        anomaly_detection=True,
        price_monthly=29.99,
        price_yearly=299.99
    )
}

@app.get("/api/subscription/tiers")
async def get_subscription_tiers():
    """Get available subscription tiers"""
    return SUBSCRIPTION_TIERS

@app.get("/api/subscription/current")
async def get_current_subscription(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Get current user's subscription information"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view subscription information",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tier = user.subscription_tier
    subscription_info = {
        "tier": tier,
        "tier_details": SUBSCRIPTION_TIERS[tier],
        "expires_at": user.subscription_expires.isoformat() if user.subscription_expires else None
    }

    return subscription_info

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
