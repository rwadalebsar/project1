from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import json
import os
from fastapi.responses import JSONResponse

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

# File paths for data storage
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
TANK_DATA_FILE = os.path.join(DATA_DIR, "tank_levels.json")

# Initialize data storage
if os.path.exists(TANK_DATA_FILE):
    with open(TANK_DATA_FILE, 'r') as f:
        try:
            tank_data = json.load(f)
            # Convert string timestamps back to datetime objects
            for item in tank_data:
                item['timestamp'] = datetime.fromisoformat(item['timestamp'])
        except json.JSONDecodeError:
            tank_data = []
else:
    # Generate some sample data if file doesn't exist
    tank_data = []
    now = datetime.now()
    # Generate 12 months of hourly data
    for i in range(365 * 24):
        timestamp = now - timedelta(hours=i)
        # Base level with some seasonal pattern (higher in summer, lower in winter)
        base_level = 5.0 + 1.0 * np.sin(2 * np.pi * i / (365 * 24))
        # Add some random noise
        noise = np.random.normal(0, 0.2)
        # Add some random anomalies (about 1%)
        anomaly = 0
        if np.random.random() < 0.01:
            anomaly = np.random.choice([-2, 2]) * np.random.random()
        level = max(0, min(10, base_level + noise + anomaly))
        tank_data.append({
            "timestamp": timestamp,
            "level": level,
            "tank_id": "tank1"
        })

    # Save the generated data
    with open(TANK_DATA_FILE, 'w') as f:
        # Convert datetime objects to ISO format strings for JSON serialization
        serializable_data = []
        for item in tank_data:
            serializable_item = item.copy()
            serializable_item['timestamp'] = item['timestamp'].isoformat()
            serializable_data.append(serializable_item)
        json.dump(serializable_data, f)

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
    # Convert to DataFrame for easier filtering
    df = pd.DataFrame(tank_data)

    # Filter by tank_id if provided
    if tank_id:
        df = df[df['tank_id'] == tank_id]

    # Filter by days if provided
    if days:
        cutoff_date = datetime.now() - timedelta(days=days)
        df = df[df['timestamp'] >= cutoff_date]

    # Sort by timestamp (newest first)
    df = df.sort_values('timestamp', ascending=False)

    # Convert back to list of dictionaries
    result = df.to_dict('records')
    return result

@app.post("/api/tank-levels", response_model=TankLevel)
def add_tank_level(tank_level: TankLevelCreate):
    """Add a new tank level reading"""
    new_reading = {
        "timestamp": datetime.now(),
        "level": tank_level.level,
        "tank_id": tank_level.tank_id
    }

    # Add to in-memory data
    tank_data.append(new_reading)

    # Save to file
    with open(TANK_DATA_FILE, 'w') as f:
        # Convert datetime objects to ISO format strings for JSON serialization
        serializable_data = []
        for item in tank_data:
            serializable_item = item.copy()
            serializable_item['timestamp'] = item['timestamp'].isoformat()
            serializable_data.append(serializable_item)
        json.dump(serializable_data, f)

    return new_reading

@app.get("/api/anomalies", response_model=List[AnomalyResult])
def get_anomalies(
    days: Optional[int] = Query(30, description="Number of days of data to analyze"),
    tank_id: Optional[str] = Query(None, description="Tank ID to filter by"),
    sensitivity: float = Query(0.01, description="Anomaly detection sensitivity (0.01-0.1)")
):
    """Detect anomalies in tank level data"""
    # Convert to DataFrame for analysis
    df = pd.DataFrame(tank_data)

    # Filter by tank_id if provided
    if tank_id:
        df = df[df['tank_id'] == tank_id]

    # Filter by days
    cutoff_date = datetime.now() - timedelta(days=days)
    df = df[df['timestamp'] >= cutoff_date]

    # Sort by timestamp
    df = df.sort_values('timestamp')

    # Detect anomalies
    result_df = detect_anomalies(df, contamination=sensitivity)

    # Filter to only return anomalies
    anomalies_df = result_df[result_df['is_anomaly']]

    # Convert back to list of dictionaries
    result = anomalies_df.to_dict('records')
    return result

@app.get("/api/stats")
def get_stats(
    days: Optional[int] = Query(30, description="Number of days of data to analyze"),
    tank_id: Optional[str] = Query(None, description="Tank ID to filter by")
):
    """Get statistics about tank levels"""
    # Convert to DataFrame for analysis
    df = pd.DataFrame(tank_data)

    # Filter by tank_id if provided
    if tank_id:
        df = df[df['tank_id'] == tank_id]

    # Filter by days
    cutoff_date = datetime.now() - timedelta(days=days)
    df = df[df['timestamp'] >= cutoff_date]

    # Calculate statistics
    if len(df) == 0:
        return {
            "count": 0,
            "min_level": None,
            "max_level": None,
            "avg_level": None,
            "std_dev": None
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
