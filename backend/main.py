from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
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
from mqtt_client import mqtt_client
from rest_api_client import rest_api_client
from graphql_client import graphql_client
from opcua_client import opcua_client
from modbus_client import modbus_client

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

class UserReportedAnomaly(BaseModel):
    timestamp: datetime
    level: float
    tank_id: str = "tank1"
    user_id: Optional[str] = None
    notes: Optional[str] = None
    status: str = "pending"  # pending, confirmed, rejected

class UserReportedAnomalyCreate(BaseModel):
    timestamp: datetime
    level: float
    tank_id: str = "tank1"
    notes: Optional[str] = None

class AnomalyFeedback(BaseModel):
    timestamp: datetime
    level: float
    tank_id: str = "tank1"
    is_normal: bool = True
    user_id: Optional[str] = None
    notes: Optional[str] = None

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

# In-memory storage for user-reported anomalies and feedback
# In a production environment, this would be stored in a database
user_reported_anomalies = []
anomaly_feedback = []  # Store user feedback on anomalies (marked as normal)

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
    global anomaly_feedback

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

    # Create result DataFrame
    result_df = pd.DataFrame({
        'timestamp': data['timestamp'],
        'level': data['level'],
        'is_anomaly': is_anomaly,
        'anomaly_score': scores
    })

    # Apply user feedback to override model predictions
    # If a user has marked a reading as normal, override the model's prediction
    if anomaly_feedback:
        # Convert anomaly_feedback to DataFrame for easier processing
        feedback_df = pd.DataFrame(anomaly_feedback)

        # For each feedback entry, find matching timestamp and level in result_df and set is_anomaly to False
        for _, feedback in feedback_df.iterrows():
            # Find matching entries in result_df
            matches = result_df[
                (result_df['timestamp'] == feedback['timestamp']) &
                (result_df['level'] == feedback['level']) &
                (result_df['is_anomaly'] == True)  # Only override actual anomalies
            ]

            # Update is_anomaly to False for matches
            if not matches.empty:
                for idx in matches.index:
                    result_df.at[idx, 'is_anomaly'] = False

    return result_df

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
                if 'user_id' not in df.columns:
                    df['user_id'] = user.username  # Assign all data to this user for mock data
                else:
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
            if 'user_id' not in df.columns:
                df['user_id'] = user.username  # Assign all data to this user for mock data
            else:
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
            if 'user_id' not in df.columns:
                df['user_id'] = user.username  # Assign all data to this user for mock data
            else:
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

# User-reported anomalies endpoints
@app.post("/api/user-anomalies", response_model=UserReportedAnomaly)
async def report_anomaly(
    anomaly: UserReportedAnomalyCreate,
    user: Optional[UserInDB] = Depends(get_user_from_header)
):
    """Report an anomaly that wasn't detected by the system"""
    global user_reported_anomalies

    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to report anomalies",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Create a new user-reported anomaly
        new_anomaly = UserReportedAnomaly(
            timestamp=anomaly.timestamp,
            level=anomaly.level,
            tank_id=anomaly.tank_id,
            user_id=user.username,
            notes=anomaly.notes,
            status="pending"
        )

        # Add to in-memory storage
        user_reported_anomalies.append(new_anomaly.dict())

        # In a real implementation, you would save to a database here

        return new_anomaly
    except Exception as e:
        logger.error(f"Error reporting anomaly: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reporting anomaly: {str(e)}")

@app.get("/api/user-anomalies", response_model=List[UserReportedAnomaly])
async def get_user_reported_anomalies(
    tank_id: Optional[str] = Query(None, description="Tank ID to filter by"),
    status: Optional[str] = Query(None, description="Status to filter by (pending, confirmed, rejected)"),
    user: Optional[UserInDB] = Depends(get_user_from_header)
):
    """Get user-reported anomalies"""
    global user_reported_anomalies

    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to view reported anomalies",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Convert to DataFrame for easier filtering
        if not user_reported_anomalies:
            return []

        df = pd.DataFrame(user_reported_anomalies)

        # Filter by tank_id if provided
        if tank_id and 'tank_id' in df.columns:
            df = df[df['tank_id'] == tank_id]

        # Filter by status if provided
        if status and 'status' in df.columns:
            df = df[df['status'] == status]

        # Filter by user_id if not admin
        if not user.is_admin and 'user_id' in df.columns:
            df = df[df['user_id'] == user.username]

        # Sort by timestamp (newest first)
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp', ascending=False)

        # Convert back to list of dictionaries
        result = df.to_dict('records') if not df.empty else []
        return result
    except Exception as e:
        logger.error(f"Error getting user-reported anomalies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting user-reported anomalies: {str(e)}")

@app.put("/api/user-anomalies/{anomaly_id}", response_model=UserReportedAnomaly)
async def update_anomaly_status(
    anomaly_id: int,
    status: str = Query(..., description="New status (pending, confirmed, rejected)"),
    user: Optional[UserInDB] = Depends(get_user_from_header)
):
    """Update the status of a user-reported anomaly (admin only)"""
    global user_reported_anomalies

    # Check if user is authenticated and is admin
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to update anomaly status",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update anomaly status"
        )

    try:
        # Check if anomaly_id is valid
        if anomaly_id < 0 or anomaly_id >= len(user_reported_anomalies):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Anomaly with ID {anomaly_id} not found"
            )

        # Update the status
        user_reported_anomalies[anomaly_id]['status'] = status

        # In a real implementation, you would update the database here

        return UserReportedAnomaly(**user_reported_anomalies[anomaly_id])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating anomaly status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating anomaly status: {str(e)}")

@app.post("/api/anomalies/mark-normal", response_model=AnomalyFeedback)
async def mark_anomaly_as_normal(
    feedback: AnomalyFeedback,
    user: Optional[UserInDB] = Depends(get_user_from_header)
):
    """Mark an anomaly as normal to improve the model"""
    global anomaly_feedback

    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to provide feedback",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Add user information to the feedback
        feedback_dict = feedback.dict()
        feedback_dict["user_id"] = user.username

        # Check if this feedback already exists
        existing_feedback = next(
            (f for f in anomaly_feedback if
             f["timestamp"] == feedback_dict["timestamp"] and
             f["level"] == feedback_dict["level"] and
             f["tank_id"] == feedback_dict["tank_id"]),
            None
        )

        if existing_feedback:
            # Update existing feedback
            existing_feedback.update(feedback_dict)
            result = existing_feedback
        else:
            # Add new feedback
            anomaly_feedback.append(feedback_dict)
            result = feedback_dict

        # In a real implementation, you would save to a database here

        logger.info(f"Anomaly marked as normal by user {user.username}: {feedback_dict}")

        return AnomalyFeedback(**result)
    except Exception as e:
        logger.error(f"Error marking anomaly as normal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error marking anomaly as normal: {str(e)}")

@app.get("/api/model-feedback")
async def get_model_feedback(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Get feedback on the anomaly detection model performance"""
    global user_reported_anomalies

    # Check if user is authenticated and is admin
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view model feedback",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view model feedback"
        )

    try:
        # Calculate model performance metrics
        if not user_reported_anomalies:
            return {
                "total_reported_anomalies": 0,
                "confirmed_anomalies": 0,
                "rejected_anomalies": 0,
                "pending_anomalies": 0,
                "false_negatives_rate": 0,
                "model_accuracy": 100.0
            }

        df = pd.DataFrame(user_reported_anomalies)

        # Count by status
        total = len(df)
        confirmed = len(df[df['status'] == 'confirmed']) if 'status' in df.columns else 0
        rejected = len(df[df['status'] == 'rejected']) if 'status' in df.columns else 0
        pending = len(df[df['status'] == 'pending']) if 'status' in df.columns else 0

        # Calculate false negatives rate (confirmed anomalies that were missed by the model)
        false_negatives_rate = (confirmed / total) * 100 if total > 0 else 0

        # Calculate model accuracy (assuming confirmed anomalies are false negatives)
        # This is a simplified metric - in a real system you'd use more sophisticated evaluation
        model_accuracy = 100 - false_negatives_rate

        return {
            "total_reported_anomalies": total,
            "confirmed_anomalies": confirmed,
            "rejected_anomalies": rejected,
            "pending_anomalies": pending,
            "false_negatives_rate": false_negatives_rate,
            "model_accuracy": model_accuracy
        }
    except Exception as e:
        logger.error(f"Error getting model feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting model feedback: {str(e)}")

# MQTT API endpoints
class MQTTConfig(BaseModel):
    enabled: bool = False
    broker: str = Field(..., min_length=1)
    port: int = Field(1883, ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    topic_prefix: str = "tanks"
    use_ssl: bool = False

@app.get("/api/mqtt/config")
async def get_mqtt_config(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Get MQTT configuration"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view MQTT configuration",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        config = mqtt_client.get_config()

        # Hide password for security
        if config.get("password"):
            config["password"] = "********"

        return config
    except Exception as e:
        logger.error(f"Error getting MQTT configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting MQTT configuration: {str(e)}"
        )

@app.put("/api/mqtt/config")
async def update_mqtt_config(
    config: MQTTConfig,
    user: Optional[UserInDB] = Depends(get_user_from_header)
):
    """Update MQTT configuration"""
    # Check if user is authenticated and is admin
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to update MQTT configuration",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update MQTT configuration"
        )

    try:
        # Update configuration
        success = mqtt_client.update_config(config.dict())

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update MQTT configuration"
            )

        # Get updated config
        updated_config = mqtt_client.get_config()

        # Hide password for security
        if updated_config.get("password"):
            updated_config["password"] = "********"

        return updated_config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating MQTT configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating MQTT configuration: {str(e)}"
        )

@app.post("/api/mqtt/connect")
async def connect_mqtt(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Connect to MQTT broker"""
    # Check if user is authenticated and is admin
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to connect to MQTT broker",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can connect to MQTT broker"
        )

    try:
        # Connect to broker
        success = mqtt_client.connect()

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to connect to MQTT broker: {mqtt_client.last_error}"
            )

        return {"message": "Connected to MQTT broker successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting to MQTT broker: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error connecting to MQTT broker: {str(e)}"
        )

@app.post("/api/mqtt/disconnect")
async def disconnect_mqtt(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Disconnect from MQTT broker"""
    # Check if user is authenticated and is admin
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to disconnect from MQTT broker",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can disconnect from MQTT broker"
        )

    try:
        # Disconnect from broker
        mqtt_client.disconnect()

        return {"message": "Disconnected from MQTT broker successfully"}
    except Exception as e:
        logger.error(f"Error disconnecting from MQTT broker: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error disconnecting from MQTT broker: {str(e)}"
        )

@app.get("/api/mqtt/status")
async def get_mqtt_status(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Get MQTT connection status"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view MQTT status",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        config = mqtt_client.get_config()

        return {
            "enabled": config.get("enabled", False),
            "connected": mqtt_client.connected,
            "last_error": mqtt_client.last_error,
            "broker": config.get("broker"),
            "port": config.get("port"),
            "topic_prefix": config.get("topic_prefix")
        }
    except Exception as e:
        logger.error(f"Error getting MQTT status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting MQTT status: {str(e)}"
        )

@app.get("/api/mqtt/data")
async def get_mqtt_data(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Get tank data received from MQTT"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view MQTT data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Get tank data from MQTT
        tank_data = mqtt_client.get_tank_data()

        # Convert datetime objects to ISO format strings
        for item in tank_data:
            if isinstance(item.get("timestamp"), datetime):
                item["timestamp"] = item["timestamp"].isoformat()

        return tank_data
    except Exception as e:
        logger.error(f"Error getting MQTT data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting MQTT data: {str(e)}"
        )

@app.post("/api/mqtt/clear-data")
async def clear_mqtt_data(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Clear tank data received from MQTT"""
    # Check if user is authenticated and is admin
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to clear MQTT data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can clear MQTT data"
        )

    try:
        # Clear tank data
        mqtt_client.clear_tank_data()

        return {"message": "MQTT tank data cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing MQTT data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing MQTT data: {str(e)}"
        )

# REST API endpoints
class RESTAPIConfig(BaseModel):
    enabled: bool = False
    base_url: str = Field(..., min_length=1)
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    auth_type: str = "none"  # none, api_key, basic, oauth2
    headers: Dict[str, str] = {}
    endpoints: Dict[str, str] = {
        "tanks": "/tanks",
        "levels": "/tanks/{tank_id}/levels",
        "auth": "/auth/token"
    }
    polling_interval: int = Field(60, ge=5, le=3600)

@app.get("/api/rest/config")
async def get_rest_config(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Get REST API configuration"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view REST API configuration",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        config = rest_api_client.get_config()

        # Hide sensitive information
        if config.get("password"):
            config["password"] = "********"
        if config.get("api_key"):
            config["api_key"] = "********"

        return config
    except Exception as e:
        logger.error(f"Error getting REST API configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting REST API configuration: {str(e)}"
        )

@app.put("/api/rest/config")
async def update_rest_config(
    config: RESTAPIConfig,
    user: Optional[UserInDB] = Depends(get_user_from_header)
):
    """Update REST API configuration"""
    # Check if user is authenticated and is admin
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to update REST API configuration",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update REST API configuration"
        )

    try:
        # Update configuration
        success = rest_api_client.update_config(config.dict())

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update REST API configuration"
            )

        # Get updated config
        updated_config = rest_api_client.get_config()

        # Hide sensitive information
        if updated_config.get("password"):
            updated_config["password"] = "********"
        if updated_config.get("api_key"):
            updated_config["api_key"] = "********"

        return updated_config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating REST API configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating REST API configuration: {str(e)}"
        )

@app.post("/api/rest/test")
async def test_rest_connection(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Test connection to REST API"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to test REST API connection",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Test connection
        success = rest_api_client.test_connection()

        if success:
            return {"success": True, "message": "Successfully connected to REST API"}
        else:
            return {"success": False, "message": f"Failed to connect: {rest_api_client.last_error}"}
    except Exception as e:
        logger.error(f"Error testing REST API connection: {str(e)}")
        return {"success": False, "message": f"Error testing connection: {str(e)}"}

@app.get("/api/rest/data")
async def get_rest_data(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Get tank data from REST API"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view REST API data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Get tank data
        tank_data = rest_api_client.get_tank_data()

        return tank_data
    except Exception as e:
        logger.error(f"Error getting REST API data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting REST API data: {str(e)}"
        )

@app.post("/api/rest/fetch")
async def fetch_rest_data(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Fetch new tank data from REST API"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to fetch REST API data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Fetch tank data
        tank_data = rest_api_client.fetch_tank_data()

        return {"message": f"Fetched {len(tank_data)} tank readings from REST API", "data": tank_data}
    except Exception as e:
        logger.error(f"Error fetching REST API data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching REST API data: {str(e)}"
        )

@app.post("/api/rest/clear-data")
async def clear_rest_data(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Clear tank data received from REST API"""
    # Check if user is authenticated and is admin
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to clear REST API data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can clear REST API data"
        )

    try:
        # Clear tank data
        rest_api_client.clear_tank_data()

        return {"message": "REST API tank data cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing REST API data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing REST API data: {str(e)}"
        )

# GraphQL API endpoints
class GraphQLConfig(BaseModel):
    enabled: bool = False
    endpoint: str = Field(..., min_length=1)
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    auth_type: str = "none"  # none, api_key, basic, oauth2, jwt
    auth_endpoint: Optional[str] = None
    headers: Dict[str, str] = {}
    queries: Dict[str, str] = {
        "tanks": """
            query GetTanks {
                tanks {
                    id
                    name
                    capacity
                }
            }
        """,
        "tankLevel": """
            query GetTankLevel($tankId: ID!) {
                tank(id: $tankId) {
                    id
                    name
                    level
                    lastUpdated
                }
            }
        """
    }
    polling_interval: int = Field(60, ge=5, le=3600)

@app.get("/api/graphql/config")
async def get_graphql_config(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Get GraphQL configuration"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view GraphQL configuration",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        config = graphql_client.get_config()

        # Hide sensitive information
        if config.get("password"):
            config["password"] = "********"
        if config.get("api_key"):
            config["api_key"] = "********"

        return config
    except Exception as e:
        logger.error(f"Error getting GraphQL configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting GraphQL configuration: {str(e)}"
        )

@app.put("/api/graphql/config")
async def update_graphql_config(
    config: GraphQLConfig,
    user: Optional[UserInDB] = Depends(get_user_from_header)
):
    """Update GraphQL configuration"""
    # Check if user is authenticated and is admin
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to update GraphQL configuration",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update GraphQL configuration"
        )

    try:
        # Update configuration
        success = graphql_client.update_config(config.dict())

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update GraphQL configuration"
            )

        # Get updated config
        updated_config = graphql_client.get_config()

        # Hide sensitive information
        if updated_config.get("password"):
            updated_config["password"] = "********"
        if updated_config.get("api_key"):
            updated_config["api_key"] = "********"

        return updated_config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating GraphQL configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating GraphQL configuration: {str(e)}"
        )

@app.post("/api/graphql/test")
async def test_graphql_connection(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Test connection to GraphQL API"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to test GraphQL connection",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Test connection
        success = graphql_client.test_connection()

        if success:
            return {"success": True, "message": "Successfully connected to GraphQL API"}
        else:
            return {"success": False, "message": f"Failed to connect: {graphql_client.last_error}"}
    except Exception as e:
        logger.error(f"Error testing GraphQL connection: {str(e)}")
        return {"success": False, "message": f"Error testing connection: {str(e)}"}

@app.get("/api/graphql/data")
async def get_graphql_data(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Get tank data from GraphQL API"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view GraphQL data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Get tank data
        tank_data = graphql_client.get_tank_data()

        return tank_data
    except Exception as e:
        logger.error(f"Error getting GraphQL data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting GraphQL data: {str(e)}"
        )

@app.post("/api/graphql/fetch")
async def fetch_graphql_data(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Fetch new tank data from GraphQL API"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to fetch GraphQL data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Fetch tank data
        tank_data = graphql_client.fetch_tank_data()

        return {"message": f"Fetched {len(tank_data)} tank readings from GraphQL API", "data": tank_data}
    except Exception as e:
        logger.error(f"Error fetching GraphQL data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching GraphQL data: {str(e)}"
        )

@app.post("/api/graphql/clear-data")
async def clear_graphql_data(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Clear tank data received from GraphQL API"""
    # Check if user is authenticated and is admin
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to clear GraphQL data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can clear GraphQL data"
        )

    try:
        # Clear tank data
        graphql_client.clear_tank_data()

        return {"message": "GraphQL tank data cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing GraphQL data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing GraphQL data: {str(e)}"
        )

# OPC UA API endpoints
class OpcUaConfig(BaseModel):
    enabled: bool = False
    endpoint: str = Field(..., min_length=1)
    security_mode: str = "None"  # None, Sign, SignAndEncrypt
    security_policy: str = "None"  # None, Basic128Rsa15, Basic256, Basic256Sha256
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    namespace: str = "http://examples.freeopcua.github.io"
    node_paths: Dict[str, List[str]] = {
        "tanks": ["Objects", "Server", "Tanks"],
        "tank_level": ["Objects", "Server", "Tanks", "{tank_id}", "Level"]
    }
    polling_interval: int = Field(60, ge=5, le=3600)

@app.get("/api/opcua/config")
async def get_opcua_config(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Get OPC UA configuration"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view OPC UA configuration",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        config = opcua_client.get_config()

        # Hide sensitive information
        if config.get("password"):
            config["password"] = "********"

        return config
    except Exception as e:
        logger.error(f"Error getting OPC UA configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting OPC UA configuration: {str(e)}"
        )

@app.put("/api/opcua/config")
async def update_opcua_config(
    config: OpcUaConfig,
    user: Optional[UserInDB] = Depends(get_user_from_header)
):
    """Update OPC UA configuration"""
    # Check if user is authenticated and is admin
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to update OPC UA configuration",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update OPC UA configuration"
        )

    try:
        # Update configuration
        success = opcua_client.update_config(config.dict())

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update OPC UA configuration"
            )

        # Get updated config
        updated_config = opcua_client.get_config()

        # Hide sensitive information
        if updated_config.get("password"):
            updated_config["password"] = "********"

        return updated_config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating OPC UA configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating OPC UA configuration: {str(e)}"
        )

@app.post("/api/opcua/test")
async def test_opcua_connection(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Test connection to OPC UA server"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to test OPC UA connection",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Test connection
        success = opcua_client.test_connection()

        if success:
            return {"success": True, "message": "Successfully connected to OPC UA server"}
        else:
            return {"success": False, "message": f"Failed to connect: {opcua_client.last_error}"}
    except Exception as e:
        logger.error(f"Error testing OPC UA connection: {str(e)}")
        return {"success": False, "message": f"Error testing connection: {str(e)}"}

@app.post("/api/opcua/connect")
async def connect_opcua(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Connect to OPC UA server"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to connect to OPC UA server",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Connect to server
        success = opcua_client.connect()

        if success:
            return {"success": True, "message": "Successfully connected to OPC UA server"}
        else:
            return {"success": False, "message": f"Failed to connect: {opcua_client.last_error}"}
    except Exception as e:
        logger.error(f"Error connecting to OPC UA server: {str(e)}")
        return {"success": False, "message": f"Error connecting to server: {str(e)}"}

@app.post("/api/opcua/disconnect")
async def disconnect_opcua(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Disconnect from OPC UA server"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to disconnect from OPC UA server",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Disconnect from server
        success = opcua_client.disconnect()

        if success:
            return {"success": True, "message": "Successfully disconnected from OPC UA server"}
        else:
            return {"success": False, "message": f"Failed to disconnect: {opcua_client.last_error}"}
    except Exception as e:
        logger.error(f"Error disconnecting from OPC UA server: {str(e)}")
        return {"success": False, "message": f"Error disconnecting from server: {str(e)}"}

@app.post("/api/opcua/start-monitoring")
async def start_opcua_monitoring(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Start monitoring OPC UA server"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to start OPC UA monitoring",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Start monitoring
        success = opcua_client.start_monitoring()

        if success:
            return {"success": True, "message": "Successfully started OPC UA monitoring"}
        else:
            return {"success": False, "message": f"Failed to start monitoring: {opcua_client.last_error}"}
    except Exception as e:
        logger.error(f"Error starting OPC UA monitoring: {str(e)}")
        return {"success": False, "message": f"Error starting monitoring: {str(e)}"}

@app.post("/api/opcua/stop-monitoring")
async def stop_opcua_monitoring(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Stop monitoring OPC UA server"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to stop OPC UA monitoring",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Stop monitoring
        success = opcua_client.stop_monitoring()

        if success:
            return {"success": True, "message": "Successfully stopped OPC UA monitoring"}
        else:
            return {"success": False, "message": f"Failed to stop monitoring: {opcua_client.last_error}"}
    except Exception as e:
        logger.error(f"Error stopping OPC UA monitoring: {str(e)}")
        return {"success": False, "message": f"Error stopping monitoring: {str(e)}"}

@app.get("/api/opcua/data")
async def get_opcua_data(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Get tank data from OPC UA server"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view OPC UA data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Get tank data
        tank_data = opcua_client.get_tank_data()

        return tank_data
    except Exception as e:
        logger.error(f"Error getting OPC UA data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting OPC UA data: {str(e)}"
        )

@app.post("/api/opcua/fetch")
async def fetch_opcua_data(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Fetch new tank data from OPC UA server"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to fetch OPC UA data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Fetch tank data
        tank_data = opcua_client.fetch_tank_data()

        return {"message": f"Fetched {len(tank_data)} tank readings from OPC UA server", "data": tank_data}
    except Exception as e:
        logger.error(f"Error fetching OPC UA data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching OPC UA data: {str(e)}"
        )

@app.post("/api/opcua/clear-data")
async def clear_opcua_data(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Clear tank data received from OPC UA server"""
    # Check if user is authenticated and is admin
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to clear OPC UA data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can clear OPC UA data"
        )

    try:
        # Clear tank data
        opcua_client.clear_tank_data()

        return {"message": "OPC UA tank data cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing OPC UA data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing OPC UA data: {str(e)}"
        )

# Modbus API endpoints
class ModbusRegister(BaseModel):
    tank_id: str
    name: str
    register_type: str = "holding"  # holding, input, coil, discrete_input
    address: int
    data_type: str = "float"  # float, int16, int32, uint16, uint32, bool
    scaling_factor: float = 1.0
    offset: float = 0.0

class ModbusConfig(BaseModel):
    enabled: bool = False
    mode: str = "tcp"  # tcp or rtu
    # TCP settings
    host: Optional[str] = "localhost"
    port: Optional[int] = 502
    # RTU settings
    port_name: Optional[str] = "/dev/ttyUSB0"
    baudrate: Optional[int] = 9600
    bytesize: Optional[int] = 8
    parity: Optional[str] = "N"
    stopbits: Optional[int] = 1
    # Common settings
    unit_id: int = 1
    timeout: int = 3
    retries: int = 3
    tank_registers: List[ModbusRegister] = []
    polling_interval: int = Field(60, ge=5, le=3600)

@app.get("/api/modbus/config")
async def get_modbus_config(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Get Modbus configuration"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view Modbus configuration",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        config = modbus_client.get_config()
        return config
    except Exception as e:
        logger.error(f"Error getting Modbus configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting Modbus configuration: {str(e)}"
        )

@app.put("/api/modbus/config")
async def update_modbus_config(
    config: ModbusConfig,
    user: Optional[UserInDB] = Depends(get_user_from_header)
):
    """Update Modbus configuration"""
    # Check if user is authenticated and is admin
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to update Modbus configuration",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update Modbus configuration"
        )

    try:
        # Update configuration
        success = modbus_client.update_config(config.dict())

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update Modbus configuration"
            )

        # Get updated config
        updated_config = modbus_client.get_config()
        return updated_config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Modbus configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating Modbus configuration: {str(e)}"
        )

@app.post("/api/modbus/test")
async def test_modbus_connection(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Test connection to Modbus device"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to test Modbus connection",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Test connection
        success = modbus_client.test_connection()

        if success:
            return {"success": True, "message": "Successfully connected to Modbus device"}
        else:
            return {"success": False, "message": f"Failed to connect: {modbus_client.last_error}"}
    except Exception as e:
        logger.error(f"Error testing Modbus connection: {str(e)}")
        return {"success": False, "message": f"Error testing connection: {str(e)}"}

@app.post("/api/modbus/connect")
async def connect_modbus(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Connect to Modbus device"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to connect to Modbus device",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Connect to device
        success = modbus_client.connect()

        if success:
            return {"success": True, "message": "Successfully connected to Modbus device"}
        else:
            return {"success": False, "message": f"Failed to connect: {modbus_client.last_error}"}
    except Exception as e:
        logger.error(f"Error connecting to Modbus device: {str(e)}")
        return {"success": False, "message": f"Error connecting to device: {str(e)}"}

@app.post("/api/modbus/disconnect")
async def disconnect_modbus(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Disconnect from Modbus device"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to disconnect from Modbus device",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Disconnect from device
        success = modbus_client.disconnect()

        if success:
            return {"success": True, "message": "Successfully disconnected from Modbus device"}
        else:
            return {"success": False, "message": f"Failed to disconnect: {modbus_client.last_error}"}
    except Exception as e:
        logger.error(f"Error disconnecting from Modbus device: {str(e)}")
        return {"success": False, "message": f"Error disconnecting from device: {str(e)}"}

@app.post("/api/modbus/start-monitoring")
async def start_modbus_monitoring(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Start monitoring Modbus registers"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to start Modbus monitoring",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Start monitoring
        success = modbus_client.start_monitoring()

        if success:
            return {"success": True, "message": "Successfully started Modbus monitoring"}
        else:
            return {"success": False, "message": f"Failed to start monitoring: {modbus_client.last_error}"}
    except Exception as e:
        logger.error(f"Error starting Modbus monitoring: {str(e)}")
        return {"success": False, "message": f"Error starting monitoring: {str(e)}"}

@app.post("/api/modbus/stop-monitoring")
async def stop_modbus_monitoring(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Stop monitoring Modbus registers"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to stop Modbus monitoring",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Stop monitoring
        success = modbus_client.stop_monitoring()

        if success:
            return {"success": True, "message": "Successfully stopped Modbus monitoring"}
        else:
            return {"success": False, "message": f"Failed to stop monitoring: {modbus_client.last_error}"}
    except Exception as e:
        logger.error(f"Error stopping Modbus monitoring: {str(e)}")
        return {"success": False, "message": f"Error stopping monitoring: {str(e)}"}

@app.get("/api/modbus/data")
async def get_modbus_data(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Get tank data from Modbus registers"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view Modbus data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Get tank data
        tank_data = modbus_client.get_tank_data()

        return tank_data
    except Exception as e:
        logger.error(f"Error getting Modbus data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting Modbus data: {str(e)}"
        )

@app.post("/api/modbus/fetch")
async def fetch_modbus_data(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Fetch new tank data from Modbus registers"""
    # Check if user is authenticated
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to fetch Modbus data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Fetch tank data
        tank_data = modbus_client.fetch_tank_data()

        return {"message": f"Fetched {len(tank_data)} tank readings from Modbus registers", "data": tank_data}
    except Exception as e:
        logger.error(f"Error fetching Modbus data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching Modbus data: {str(e)}"
        )

@app.post("/api/modbus/clear-data")
async def clear_modbus_data(user: Optional[UserInDB] = Depends(get_user_from_header)):
    """Clear tank data received from Modbus registers"""
    # Check if user is authenticated and is admin
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to clear Modbus data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can clear Modbus data"
        )

    try:
        # Clear tank data
        modbus_client.clear_tank_data()

        return {"message": "Modbus tank data cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing Modbus data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing Modbus data: {str(e)}"
        )



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
