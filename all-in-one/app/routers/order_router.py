from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from app.dependencies import (
    get_business_db, get_current_business, 
    get_current_vendor, get_current_customer,
    get_current_delivery_boy
)
from app.schemas.order_schema import (
    OrderCreate, OrderResponse, OrderUpdate,
    CartUpdate
)
from app.models.business.order_model import Order, Cart, OrderStatus
from app.services.order_service import OrderService
from app.utils.pagination import paginate
import logging

router = APIRouter(prefix="/business/{business_id}/orders", tags=["Orders"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=OrderResponse)
async def create_order(
    business_id: str,
    order_data: OrderCreate,
    customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_business_db)
):
    """Create new order"""
    try:
        order = await OrderService.create_order(
            db=db,
            business_id=business_id,
            customer_id=str(customer.id),
            customer_name=customer.full_name or f"Customer {customer.phone[-4:]}",
            customer_phone=customer.phone,
            order_data=order_data
        )
        return order
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=dict)
async def get_orders(
    business_id: str,
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_business_db),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get orders for business (vendor view)"""
    try:
        orders, total = await OrderService.get_orders(
            db=db,
            business_id=business_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            page=page,
            limit=limit
        )
        
        # Calculate stats
        stats = await OrderService.get_order_stats(db, business_id)
        
        return {
            "orders": paginate(orders, total, page, limit),
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get orders"
        )

@router.get("/customer", response_model=List[OrderResponse])
async def get_customer_orders(
    business_id: str,
    customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_business_db),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get orders for customer"""
    try:
        orders, total = await OrderService.get_customer_orders(
            db=db,
            customer_id=str(customer.id),
            business_id=business_id,
            status=status,
            page=page,
            limit=limit
        )
        
        return paginate(orders, total, page, limit)
        
    except Exception as e:
        logger.error(f"Error getting customer orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get orders"
        )

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    business_id: str,
    order_id: str,
    customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_business_db)
):
    """Get order details"""
    try:
        order = await OrderService.get_order(db, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Verify customer owns this order
        if order.customer_id != str(customer.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order"
        )

@router.put("/{order_id}/status")
async def update_order_status(
    business_id: str,
    order_id: str,
    status_update: OrderUpdate,
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_business_db),
    vendor = Depends(get_current_vendor)
):
    """Update order status (vendor only)"""
    try:
        order = await OrderService.update_order_status(
            db=db,
            order_id=order_id,
            status=status_update.status,
            business_id=business_id
        )
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return {"message": "Order status updated", "order": order}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status"
        )

@router.post("/{order_id}/cancel")
async def cancel_order(
    business_id: str,
    order_id: str,
    customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_business_db)
):
    """Cancel order (customer only)"""
    try:
        success = await OrderService.cancel_order(
            db=db,
            order_id=order_id,
            customer_id=str(customer.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel order"
            )
        
        return {"message": "Order cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order"
        )

@router.get("/{order_id}/track")
async def track_order(
    business_id: str,
    order_id: str,
    customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_business_db)
):
    """Get real-time order tracking info"""
    try:
        tracking_info = await OrderService.get_tracking_info(
            db=db,
            order_id=order_id,
            customer_id=str(customer.id)
        )
        
        if not tracking_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return tracking_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tracking info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tracking info"
        )

@router.post("/cart", response_model=dict)
async def update_cart(
    business_id: str,
    cart_data: CartUpdate,
    customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_business_db)
):
    """Update shopping cart"""
    try:
        cart = await OrderService.update_cart(
            db=db,
            business_id=business_id,
            customer_id=str(customer.id),
            items=cart_data.items
        )
        return cart
    except Exception as e:
        logger.error(f"Error updating cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cart"
        )

@router.get("/cart", response_model=dict)
async def get_cart(
    business_id: str,
    customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_business_db)
):
    """Get shopping cart"""
    try:
        cart = await OrderService.get_cart(
            db=db,
            business_id=business_id,
            customer_id=str(customer.id)
        )
        return cart
    except Exception as e:
        logger.error(f"Error getting cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cart"
        )