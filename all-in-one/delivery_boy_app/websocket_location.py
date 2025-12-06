import asyncio
import json
import logging
from typing import Dict, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class DeliveryBoyConnectionManager:
    """Manager for delivery boy WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.delivery_locations: Dict[str, Dict] = {}
        self.order_connections: Dict[str, Set[str]] = {}  # order_id -> set of connection_ids
        
    async def connect(self, websocket: WebSocket, delivery_boy_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[delivery_boy_id] = websocket
        logger.info(f"Delivery boy connected: {delivery_boy_id}")
    
    def disconnect(self, delivery_boy_id: str):
        """Handle disconnection"""
        if delivery_boy_id in self.active_connections:
            del self.active_connections[delivery_boy_id]
        
        if delivery_boy_id in self.delivery_locations:
            del self.delivery_locations[delivery_boy_id]
        
        # Remove from order connections
        for order_id, connections in self.order_connections.items():
            if delivery_boy_id in connections:
                connections.remove(delivery_boy_id)
                if not connections:
                    del self.order_connections[order_id]
        
        logger.info(f"Delivery boy disconnected: {delivery_boy_id}")
    
    async def send_message(self, message: dict, delivery_boy_id: str):
        """Send message to specific delivery boy"""
        if delivery_boy_id in self.active_connections:
            try:
                await self.active_connections[delivery_boy_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {delivery_boy_id}: {e}")
    
    async def broadcast_to_order(self, message: dict, order_id: str, exclude: Set[str] = None):
        """Broadcast message to all connections related to an order"""
        exclude = exclude or set()
        
        if order_id in self.order_connections:
            for connection_id in self.order_connections[order_id]:
                if connection_id not in exclude and connection_id in self.active_connections:
                    try:
                        await self.active_connections[connection_id].send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to {connection_id}: {e}")
    
    def update_location(self, delivery_boy_id: str, location: dict):
        """Update delivery boy location"""
        self.delivery_locations[delivery_boy_id] = {
            **location,
            "timestamp": datetime.utcnow().isoformat(),
            "delivery_boy_id": delivery_boy_id
        }
    
    def get_location(self, delivery_boy_id: str) -> Dict:
        """Get current location of delivery boy"""
        return self.delivery_locations.get(delivery_boy_id)
    
    def register_order_connection(self, order_id: str, connection_id: str):
        """Register connection for order updates"""
        if order_id not in self.order_connections:
            self.order_connections[order_id] = set()
        self.order_connections[order_id].add(connection_id)
    
    def unregister_order_connection(self, order_id: str, connection_id: str):
        """Unregister connection from order updates"""
        if order_id in self.order_connections and connection_id in self.order_connections[order_id]:
            self.order_connections[order_id].remove(connection_id)
            if not self.order_connections[order_id]:
                del self.order_connections[order_id]

# Global instance
connection_manager = DeliveryBoyConnectionManager()

async def handle_delivery_boy_websocket(
    websocket: WebSocket,
    delivery_boy_id: str,
    token: str,
    db: AsyncSession
):
    """Handle delivery boy WebSocket connection"""
    from app.core.auth import verify_token
    
    try:
        # Verify token
        user_id = await verify_token(token)
        if user_id != delivery_boy_id:
            await websocket.close(code=1008)
            return
        
        # Connect
        await connection_manager.connect(websocket, delivery_boy_id)
        
        # Send welcome message
        await connection_manager.send_message({
            "type": "welcome",
            "message": "Connected to delivery tracking",
            "timestamp": datetime.utcnow().isoformat(),
            "delivery_boy_id": delivery_boy_id
        }, delivery_boy_id)
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == "location_update":
                    # Update location
                    location = data.get("location")
                    order_id = data.get("order_id")
                    
                    if location:
                        connection_manager.update_location(delivery_boy_id, location)
                        
                        # Broadcast to order if specified
                        if order_id:
                            await connection_manager.broadcast_to_order({
                                "type": "delivery_location",
                                "delivery_boy_id": delivery_boy_id,
                                "order_id": order_id,
                                "location": location,
                                "timestamp": datetime.utcnow().isoformat()
                            }, order_id, exclude={delivery_boy_id})
                        
                        # Update in database (async)
                        asyncio.create_task(update_location_in_db(db, delivery_boy_id, location))
                    
                    # Send acknowledgement
                    await connection_manager.send_message({
                        "type": "ack",
                        "message": "Location updated",
                        "timestamp": datetime.utcnow().isoformat()
                    }, delivery_boy_id)
                
                elif message_type == "status_update":
                    # Update delivery status
                    status = data.get("status")
                    order_id = data.get("order_id")
                    
                    if order_id and status:
                        # Broadcast status update
                        await connection_manager.broadcast_to_order({
                            "type": "delivery_status",
                            "delivery_boy_id": delivery_boy_id,
                            "order_id": order_id,
                            "status": status,
                            "timestamp": datetime.utcnow().isoformat()
                        }, order_id)
                        
                        # Update in database (async)
                        asyncio.create_task(update_status_in_db(db, order_id, status))
                    
                    await connection_manager.send_message({
                        "type": "ack",
                        "message": "Status updated",
                        "timestamp": datetime.utcnow().isoformat()
                    }, delivery_boy_id)
                
                elif message_type == "register_order":
                    # Register for order updates
                    order_id = data.get("order_id")
                    if order_id:
                        connection_manager.register_order_connection(order_id, delivery_boy_id)
                        
                        await connection_manager.send_message({
                            "type": "ack",
                            "message": f"Registered for order {order_id} updates",
                            "timestamp": datetime.utcnow().isoformat()
                        }, delivery_boy_id)
                
                elif message_type == "unregister_order":
                    # Unregister from order updates
                    order_id = data.get("order_id")
                    if order_id:
                        connection_manager.unregister_order_connection(order_id, delivery_boy_id)
                        
                        await connection_manager.send_message({
                            "type": "ack",
                            "message": f"Unregistered from order {order_id} updates",
                            "timestamp": datetime.utcnow().isoformat()
                        }, delivery_boy_id)
                
                elif message_type == "heartbeat":
                    # Respond to heartbeat
                    await connection_manager.send_message({
                        "type": "heartbeat_ack",
                        "timestamp": datetime.utcnow().isoformat()
                    }, delivery_boy_id)
                
                else:
                    # Unknown message type
                    await connection_manager.send_message({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                        "timestamp": datetime.utcnow().isoformat()
                    }, delivery_boy_id)
        
        except WebSocketDisconnect:
            connection_manager.disconnect(delivery_boy_id)
            logger.info(f"Delivery boy WebSocket disconnected: {delivery_boy_id}")
        
        except Exception as e:
            logger.error(f"WebSocket error for {delivery_boy_id}: {e}")
            connection_manager.disconnect(delivery_boy_id)
    
    except Exception as e:
        logger.error(f"Connection error: {e}")
        await websocket.close(code=1011)

async def update_location_in_db(db: AsyncSession, delivery_boy_id: str, location: dict):
    """Update delivery boy location in database"""
    try:
        from app.models.global.delivery_boy_model import DeliveryBoy
        from sqlalchemy import update
        
        await db.execute(
            update(DeliveryBoy)
            .where(DeliveryBoy.user_id == delivery_boy_id)
            .values(
                current_location_lat=location.get("lat"),
                current_location_lng=location.get("lng"),
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()
        
    except Exception as e:
        logger.error(f"Error updating location in DB: {e}")

async def update_status_in_db(db: AsyncSession, order_id: str, status: str):
    """Update order status in database"""
    try:
        # This would update the order in the business database
        # For now, just log
        logger.info(f"Order {order_id} status updated to {status}")
        
    except Exception as e:
        logger.error(f"Error updating status in DB: {e}")

async def get_delivery_location(order_id: str) -> Dict:
    """Get delivery location for an order"""
    # Find delivery boy for this order and get their location
    # This is a simplified version
    for delivery_boy_id, location in connection_manager.delivery_locations.items():
        # Check if this delivery boy is assigned to the order
        # In production, check from database
        if order_id in connection_manager.order_connections:
            if delivery_boy_id in connection_manager.order_connections[order_id]:
                return location
    
    return None

async def broadcast_order_assignment(order_id: str, delivery_boy_id: str):
    """Broadcast order assignment to delivery boy"""
    if delivery_boy_id in connection_manager.active_connections:
        await connection_manager.send_message({
            "type": "order_assigned",
            "order_id": order_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"New order assigned: {order_id}"
        }, delivery_boy_id)
        
        # Register delivery boy for order updates
        connection_manager.register_order_connection(order_id, delivery_boy_id)