from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
import asyncio
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.delivery_locations: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, user_type: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"{user_type} connected: {user_id}")
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.delivery_locations:
            del self.delivery_locations[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {e}")
    
    async def broadcast(self, message: dict, exclude: List[str] = None):
        exclude = exclude or []
        for user_id, websocket in self.active_connections.items():
            if user_id not in exclude:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {user_id}: {e}")
    
    def update_location(self, user_id: str, location: dict):
        self.delivery_locations[user_id] = {
            **location,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_location(self, user_id: str) -> Dict:
        return self.delivery_locations.get(user_id)

manager = ConnectionManager()

@router.websocket("/ws/delivery/{delivery_id}")
async def delivery_tracking(
    websocket: WebSocket,
    delivery_id: str
):
    """WebSocket for delivery boy location tracking"""
    await manager.connect(websocket, delivery_id, "delivery_boy")
    
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "location_update":
                # Update delivery boy location
                location = data.get("location")
                manager.update_location(delivery_id, location)
                
                # Broadcast to relevant customers
                order_id = data.get("order_id")
                if order_id:
                    # Get customer ID from order (in production, fetch from DB)
                    # For now, broadcast to all connected customers
                    await manager.broadcast({
                        "type": "delivery_location",
                        "delivery_id": delivery_id,
                        "order_id": order_id,
                        "location": location,
                        "timestamp": datetime.utcnow().isoformat()
                    }, exclude=[delivery_id])
            
            elif message_type == "status_update":
                # Update delivery status
                status = data.get("status")
                order_id = data.get("order_id")
                
                # Broadcast status update
                await manager.broadcast({
                    "type": "delivery_status",
                    "delivery_id": delivery_id,
                    "order_id": order_id,
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        manager.disconnect(delivery_id)
        logger.info(f"Delivery boy disconnected: {delivery_id}")

@router.websocket("/ws/customer/{customer_id}")
async def customer_tracking(
    websocket: WebSocket,
    customer_id: str
):
    """WebSocket for customer order tracking"""
    await manager.connect(websocket, customer_id, "customer")
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(customer_id)
        logger.info(f"Customer disconnected: {customer_id}")

@router.get("/delivery/{delivery_id}/location")
async def get_delivery_location(delivery_id: str):
    """Get current location of delivery boy"""
    location = manager.get_location(delivery_id)
    if location:
        return location
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Delivery boy location not available"
    )