from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from mqtt_service import mqtt_service
from auth import get_current_user, UserInDB

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Models
class MQTTConnectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    broker: str = Field(..., min_length=1, max_length=255)
    port: int = Field(1883, ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    topic_prefix: str = ""
    use_ssl: bool = False
    enabled: bool = True

class MQTTConnectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    broker: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    topic_prefix: Optional[str] = None
    use_ssl: Optional[bool] = None
    enabled: Optional[bool] = None

class MQTTPublishMessage(BaseModel):
    topic: str = Field(..., min_length=1)
    payload: Any
    qos: int = Field(0, ge=0, le=2)
    retain: bool = False

class MQTTSubscribeTopic(BaseModel):
    topic: str = Field(..., min_length=1)
    qos: int = Field(0, ge=0, le=2)

# Create router
router = APIRouter()

@router.get("/connections")
async def get_mqtt_connections(user: UserInDB = Depends(get_current_user)):
    """Get all MQTT connections for the current user"""
    try:
        # Get connections for the current user
        connections = mqtt_service.get_connections(user.username)
        
        # Remove sensitive information
        for conn in connections:
            if conn.get("password"):
                conn["password"] = "********"
        
        return connections
    except Exception as e:
        logger.error(f"Error getting MQTT connections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting MQTT connections: {str(e)}"
        )

@router.get("/connections/{conn_id}")
async def get_mqtt_connection(
    conn_id: str,
    user: UserInDB = Depends(get_current_user)
):
    """Get a specific MQTT connection"""
    try:
        # Get the connection
        connection = mqtt_service.get_connection(conn_id)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MQTT connection with ID {conn_id} not found"
            )
        
        # Check if the user owns this connection
        if connection.get("user_id") != user.username and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this connection"
            )
        
        # Remove sensitive information
        if connection.get("password"):
            connection["password"] = "********"
        
        return connection
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting MQTT connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting MQTT connection: {str(e)}"
        )

@router.post("/connections")
async def create_mqtt_connection(
    connection: MQTTConnectionCreate,
    user: UserInDB = Depends(get_current_user)
):
    """Create a new MQTT connection"""
    try:
        # Convert to dict and add user_id
        connection_data = connection.dict()
        connection_data["user_id"] = user.username
        
        # Add the connection
        new_connection = mqtt_service.add_connection(connection_data)
        
        # Remove sensitive information
        if new_connection.get("password"):
            new_connection["password"] = "********"
        
        return new_connection
    except Exception as e:
        logger.error(f"Error creating MQTT connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating MQTT connection: {str(e)}"
        )

@router.put("/connections/{conn_id}")
async def update_mqtt_connection(
    conn_id: str,
    connection: MQTTConnectionUpdate,
    user: UserInDB = Depends(get_current_user)
):
    """Update an existing MQTT connection"""
    try:
        # Check if the connection exists
        existing_connection = mqtt_service.get_connection(conn_id)
        
        if not existing_connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MQTT connection with ID {conn_id} not found"
            )
        
        # Check if the user owns this connection
        if existing_connection.get("user_id") != user.username and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this connection"
            )
        
        # Update only the provided fields
        connection_data = {k: v for k, v in connection.dict().items() if v is not None}
        
        # Ensure user_id doesn't change
        connection_data["user_id"] = existing_connection.get("user_id")
        
        # Update the connection
        updated_connection = mqtt_service.update_connection(conn_id, connection_data)
        
        if not updated_connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MQTT connection with ID {conn_id} not found"
            )
        
        # Remove sensitive information
        if updated_connection.get("password"):
            updated_connection["password"] = "********"
        
        return updated_connection
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating MQTT connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating MQTT connection: {str(e)}"
        )

@router.delete("/connections/{conn_id}")
async def delete_mqtt_connection(
    conn_id: str,
    user: UserInDB = Depends(get_current_user)
):
    """Delete an MQTT connection"""
    try:
        # Check if the connection exists
        existing_connection = mqtt_service.get_connection(conn_id)
        
        if not existing_connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MQTT connection with ID {conn_id} not found"
            )
        
        # Check if the user owns this connection
        if existing_connection.get("user_id") != user.username and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this connection"
            )
        
        # Delete the connection
        success = mqtt_service.delete_connection(conn_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete MQTT connection with ID {conn_id}"
            )
        
        return {"message": f"MQTT connection with ID {conn_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting MQTT connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting MQTT connection: {str(e)}"
        )

@router.post("/connections/{conn_id}/connect")
async def connect_mqtt(
    conn_id: str,
    user: UserInDB = Depends(get_current_user)
):
    """Connect to an MQTT broker"""
    try:
        # Check if the connection exists
        existing_connection = mqtt_service.get_connection(conn_id)
        
        if not existing_connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MQTT connection with ID {conn_id} not found"
            )
        
        # Check if the user owns this connection
        if existing_connection.get("user_id") != user.username and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to connect to this broker"
            )
        
        # Connect to the broker
        connection = mqtt_service.connect(conn_id)
        
        # Remove sensitive information
        if connection.get("password"):
            connection["password"] = "********"
        
        return connection
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting to MQTT broker: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error connecting to MQTT broker: {str(e)}"
        )

@router.post("/connections/{conn_id}/disconnect")
async def disconnect_mqtt(
    conn_id: str,
    user: UserInDB = Depends(get_current_user)
):
    """Disconnect from an MQTT broker"""
    try:
        # Check if the connection exists
        existing_connection = mqtt_service.get_connection(conn_id)
        
        if not existing_connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MQTT connection with ID {conn_id} not found"
            )
        
        # Check if the user owns this connection
        if existing_connection.get("user_id") != user.username and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to disconnect from this broker"
            )
        
        # Disconnect from the broker
        connection = mqtt_service.disconnect(conn_id)
        
        # Remove sensitive information
        if connection.get("password"):
            connection["password"] = "********"
        
        return connection
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting from MQTT broker: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error disconnecting from MQTT broker: {str(e)}"
        )

@router.post("/connections/{conn_id}/publish")
async def publish_mqtt_message(
    conn_id: str,
    message: MQTTPublishMessage,
    user: UserInDB = Depends(get_current_user)
):
    """Publish a message to an MQTT topic"""
    try:
        # Check if the connection exists
        existing_connection = mqtt_service.get_connection(conn_id)
        
        if not existing_connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MQTT connection with ID {conn_id} not found"
            )
        
        # Check if the user owns this connection
        if existing_connection.get("user_id") != user.username and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to publish to this connection"
            )
        
        # Check if the connection is connected
        if not existing_connection.get("connected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MQTT connection is not connected"
            )
        
        # Publish the message
        success = mqtt_service.publish(
            conn_id, 
            message.topic, 
            message.payload, 
            message.qos, 
            message.retain
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish MQTT message"
            )
        
        return {"message": "MQTT message published successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing MQTT message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error publishing MQTT message: {str(e)}"
        )

@router.post("/connections/{conn_id}/subscribe")
async def subscribe_mqtt_topic(
    conn_id: str,
    subscription: MQTTSubscribeTopic,
    user: UserInDB = Depends(get_current_user)
):
    """Subscribe to an MQTT topic"""
    try:
        # Check if the connection exists
        existing_connection = mqtt_service.get_connection(conn_id)
        
        if not existing_connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MQTT connection with ID {conn_id} not found"
            )
        
        # Check if the user owns this connection
        if existing_connection.get("user_id") != user.username and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to subscribe to this connection"
            )
        
        # Check if the connection is connected
        if not existing_connection.get("connected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MQTT connection is not connected"
            )
        
        # Subscribe to the topic
        success = mqtt_service.subscribe(conn_id, subscription.topic, subscription.qos)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to subscribe to MQTT topic"
            )
        
        return {"message": f"Subscribed to MQTT topic {subscription.topic} successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subscribing to MQTT topic: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subscribing to MQTT topic: {str(e)}"
        )

@router.post("/connections/{conn_id}/unsubscribe")
async def unsubscribe_mqtt_topic(
    conn_id: str,
    topic: str = Query(..., description="The topic to unsubscribe from"),
    user: UserInDB = Depends(get_current_user)
):
    """Unsubscribe from an MQTT topic"""
    try:
        # Check if the connection exists
        existing_connection = mqtt_service.get_connection(conn_id)
        
        if not existing_connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MQTT connection with ID {conn_id} not found"
            )
        
        # Check if the user owns this connection
        if existing_connection.get("user_id") != user.username and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to unsubscribe from this connection"
            )
        
        # Check if the connection is connected
        if not existing_connection.get("connected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MQTT connection is not connected"
            )
        
        # Unsubscribe from the topic
        success = mqtt_service.unsubscribe(conn_id, topic)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to unsubscribe from MQTT topic"
            )
        
        return {"message": f"Unsubscribed from MQTT topic {topic} successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing from MQTT topic: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unsubscribing from MQTT topic: {str(e)}"
        )

@router.post("/connections/{conn_id}/test")
async def test_mqtt_connection(
    conn_id: str,
    user: UserInDB = Depends(get_current_user)
):
    """Test an MQTT connection by connecting and disconnecting"""
    try:
        # Check if the connection exists
        existing_connection = mqtt_service.get_connection(conn_id)
        
        if not existing_connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MQTT connection with ID {conn_id} not found"
            )
        
        # Check if the user owns this connection
        if existing_connection.get("user_id") != user.username and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to test this connection"
            )
        
        # Connect to the broker
        connection = mqtt_service.connect(conn_id)
        
        # Wait a moment to ensure connection is established
        import time
        time.sleep(2)
        
        # Disconnect from the broker
        mqtt_service.disconnect(conn_id)
        
        # Check if connection was successful
        if connection.get("last_error"):
            return {
                "success": False,
                "message": f"Failed to connect: {connection.get('last_error')}"
            }
        
        return {
            "success": True,
            "message": "Successfully connected to MQTT broker"
        }
    except Exception as e:
        logger.error(f"Error testing MQTT connection: {str(e)}")
        return {
            "success": False,
            "message": f"Error testing connection: {str(e)}"
        }
