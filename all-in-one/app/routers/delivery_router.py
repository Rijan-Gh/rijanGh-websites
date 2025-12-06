from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from app.dependencies import (
    get_global_db, get_current_delivery_boy,
    get_current_admin
)
from app.models.global.delivery_boy_model import DeliveryBoy
from app.models.global.user_model import User
from app.services.delivery_service import DeliveryService
from app.utils.pagination import paginate
import logging

router = APIRouter(prefix="/delivery", tags=["Delivery"])
logger = logging.getLogger(__name__)

@router.get("/available-orders")
async def get_available_orders(
    delivery_boy: User = Depends(get_current_delivery_boy),
    db: AsyncSession = Depends(get_global_db),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    radius_km: float = Query(5.0, ge=0.1, le=50)
):
    """Get available orders for delivery"""
    try:
        orders = await DeliveryService.get_available_orders(
            db=db,
            delivery_boy_id=str(delivery_boy.id),
            lat=lat,
            lng=lng,
            radius_km=radius_km
        )
        return orders
    except Exception as e:
        logger.error(f"Error getting available orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get available orders"
        )

@router.post("/accept-order/{order_id}")
async def accept_order(
    order_id: str,
    delivery_boy: User = Depends(get_current_delivery_boy),
    db: AsyncSession = Depends(get_global_db)
):
    """Accept delivery order"""
    try:
        success = await DeliveryService.accept_order(
            db=db,
            order_id=order_id,
            delivery_boy_id=str(delivery_boy.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot accept order"
            )
        
        return {"message": "Order accepted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept order"
        )

@router.post("/update-location")
async def update_location(
    lat: float,
    lng: float,
    delivery_boy: User = Depends(get_current_delivery_boy),
    db: AsyncSession = Depends(get_global_db)
):
    """Update delivery boy location"""
    try:
        await DeliveryService.update_location(
            db=db,
            delivery_boy_id=str(delivery_boy.id),
            lat=lat,
            lng=lng
        )
        
        return {"message": "Location updated"}
        
    except Exception as e:
        logger.error(f"Error updating location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update location"
        )

@router.post("/update-status")
async def update_status(
    status: str,
    delivery_boy: User = Depends(get_current_delivery_boy),
    db: AsyncSession = Depends(get_global_db)
):
    """Update delivery boy status (available/busy/offline)"""
    try:
        await DeliveryService.update_status(
            db=db,
            delivery_boy_id=str(delivery_boy.id),
            status=status
        )
        
        return {"message": "Status updated"}
        
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update status"
        )

@router.get("/my-orders")
async def get_my_orders(
    delivery_boy: User = Depends(get_current_delivery_boy),
    db: AsyncSession = Depends(get_global_db),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get orders assigned to delivery boy"""
    try:
        orders, total = await DeliveryService.get_assigned_orders(
            db=db,
            delivery_boy_id=str(delivery_boy.id),
            status=status,
            page=page,
            limit=limit
        )
        
        return paginate(orders, total, page, limit)
        
    except Exception as e:
        logger.error(f"Error getting assigned orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get orders"
        )

@router.post("/order/{order_id}/pickup")
async def pickup_order(
    order_id: str,
    delivery_boy: User = Depends(get_current_delivery_boy),
    db: AsyncSession = Depends(get_global_db)
):
    """Mark order as picked up"""
    try:
        success = await DeliveryService.pickup_order(
            db=db,
            order_id=order_id,
            delivery_boy_id=str(delivery_boy.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot mark as picked up"
            )
        
        return {"message": "Order picked up successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error picking up order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pickup order"
        )

@router.post("/order/{order_id}/deliver")
async def deliver_order(
    order_id: str,
    otp: Optional[str] = None,
    delivery_boy: User = Depends(get_current_delivery_boy),
    db: AsyncSession = Depends(get_global_db)
):
    """Mark order as delivered"""
    try:
        success = await DeliveryService.deliver_order(
            db=db,
            order_id=order_id,
            delivery_boy_id=str(delivery_boy.id),
            otp=otp
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot mark as delivered"
            )
        
        return {"message": "Order delivered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error delivering order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deliver order"
        )

@router.get("/earnings")
async def get_earnings(
    delivery_boy: User = Depends(get_current_delivery_boy),
    db: AsyncSession = Depends(get_global_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get delivery earnings"""
    try:
        earnings = await DeliveryService.get_earnings(
            db=db,
            delivery_boy_id=str(delivery_boy.id),
            start_date=start_date,
            end_date=end_date
        )
        return earnings
    except Exception as e:
        logger.error(f"Error getting earnings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get earnings"
        )

@router.get("/stats")
async def get_delivery_stats(
    delivery_boy: User = Depends(get_current_delivery_boy),
    db: AsyncSession = Depends(get_global_db)
):
    """Get delivery statistics"""
    try:
        stats = await DeliveryService.get_stats(
            db=db,
            delivery_boy_id=str(delivery_boy.id)
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get stats"
        )

@router.websocket("/ws/live-track/{delivery_boy_id}")
async def live_tracking(
    websocket: WebSocket,
    delivery_boy_id: str,
    token: str
):
    """WebSocket for live delivery tracking"""
    # Verify token
    from app.core.auth import verify_token
    try:
        user_id = await verify_token(token)
        
        if user_id != delivery_boy_id:
            await websocket.close(code=1008)
            return
    except:
        await websocket.close(code=1008)
        return
    
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Update location in database
            if data.get("type") == "location":
                lat = data.get("lat")
                lng = data.get("lng")
                order_id = data.get("order_id")
                
                # Update location
                from app.services.delivery_service import DeliveryService
                from app.dependencies import get_global_db
                import asyncio
                
                # Here you would update the location in database
                # and broadcast to relevant customers
                
                # Send acknowledgement
                await websocket.send_json({
                    "type": "ack",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()