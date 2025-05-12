from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Data models
class TankLevel(BaseModel):
    timestamp: datetime
    level: float
    tank_id: str = "tank1"

class TankLevelCreate(BaseModel):
    level: float
    tank_id: str = "tank1"

class AnomalyResult(BaseModel):
    timestamp: datetime
    level: float
    is_anomaly: bool
    anomaly_score: float

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
def get_tank_levels(
    days: Optional[int] = Query(None, description="Number of days of data to return"),
    tank_id: Optional[str] = Query(None, description="Tank ID to filter by")
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

        # Sort by timestamp (newest first)
        df = df.sort_values('timestamp', ascending=False)

        # Convert back to list of dictionaries
        result = df.to_dict('records')
        return result
    except Exception as e:
        logger.error(f"Error getting tank levels: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching tank levels: {str(e)}")

@app.post("/api/tank-levels", response_model=TankLevel)
def add_tank_level(tank_level: TankLevelCreate):
    """Add a new tank level reading"""
    global tank_data

    try:
        # Add reading via API service
        new_reading = api_service.add_tank_level(tank_level.level)

        # Refresh in-memory data
        tank_data = api_service.fetch_tank_levels()

        return new_reading
    except Exception as e:
        logger.error(f"Error adding tank level: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding tank level: {str(e)}")

@app.get("/api/anomalies", response_model=List[AnomalyResult])
def get_anomalies(
    days: Optional[int] = Query(30, description="Number of days of data to analyze"),
    tank_id: Optional[str] = Query(None, description="Tank ID to filter by"),
    sensitivity: float = Query(0.01, description="Anomaly detection sensitivity (0.01-0.1)")
):
    """Detect anomalies in tank level data"""
    global tank_data

    try:
        # Ensure we have the latest data
        tank_data = api_service.fetch_tank_levels(days)

        # Convert to DataFrame for analysis
        df = pd.DataFrame(tank_data)

        # Filter by tank_id if provided
        if tank_id:
            df = df[df['tank_id'] == tank_id]

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
def get_stats(
    days: Optional[int] = Query(30, description="Number of days of data to analyze"),
    tank_id: Optional[str] = Query(None, description="Tank ID to filter by")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
