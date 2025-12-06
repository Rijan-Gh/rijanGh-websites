from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, and_
from datetime import datetime, timedelta
import uuid
import logging

from app.models.business.order_model import Order, Cart, OrderStatus
from app.models.business.item_model import Item
from app.schemas.order_schema import OrderCreate
from app.utils.geo_distance import calculate_distance, calculate_eta

logger = logging.getLogger(__name__)

class OrderService:
    
    @staticmethod
    async def create_order(
        db: AsyncSession,
        business_id: str,
        customer_id: str,
        customer_name: str,
        customer_phone: str,
        order_data: OrderCreate
    ) -> Order:
        """Create new order"""
        # Calculate totals
        subtotal = 0
        items = []
        
        for order_item in order_data.items:
            # Get item details
            result = await db.execute(
                select(Item).where(Item.id == order_item.item_id)
            )
            item = result.scalar_one_or_none()
            
            if not item or not item.is_active:
                raise ValueError(f"Item not available: {order_item.item_id}")
            
            if item.stock_quantity < order_item.quantity:
                raise ValueError(f"Insufficient stock for: {item.name}")
            
            # Calculate item total
            item_total = order_item.price * order_item.quantity
            subtotal += item_total
            
            # Prepare item data for order
            items.append({
                "item_id": order_item.item_id,
                "name": item.name,
                "quantity": order_item.quantity,
                "price": order_item.price,
                "total": item_total,
                "variants": order_item.variants,
                "special_instructions": order_item.special_instructions
            })
        
        # Calculate delivery fee (simplified)
        delivery_fee = OrderService._calculate_delivery_fee(order_data.delivery_address)
        
        # Calculate taxes (simplified)
        tax_amount = subtotal * 0.18  # 18% GST
        
        # Apply coupon if any
        discount_amount = 0
        if order_data.coupon_code:
            discount_amount = subtotal * 0.1  # 10% discount
        
        # Calculate total
        total_amount = subtotal + tax_amount + delivery_fee - discount_amount
        
        # Generate order number
        order_number = OrderService._generate_order_number()
        
        # Create order
        order = Order(
            order_number=order_number,
            business_id=business_id,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            status=OrderStatus.PENDING.value,
            items=items,
            subtotal=subtotal,
            tax_amount=tax_amount,
            delivery_fee=delivery_fee,
            discount_amount=discount_amount,
            total_amount=total_amount,
            payment_method=order_data.payment_method.value,
            payment_status="pending",
            delivery_address=order_data.delivery_address.dict(),
            delivery_instructions=order_data.delivery_instructions,
            delivery_latitude=order_data.delivery_address.latitude,
            delivery_longitude=order_data.delivery_address.longitude,
            estimated_delivery_time=datetime.utcnow() + timedelta(minutes=45)
        )
        
        db.add(order)
        
        # Update item stock
        for order_item in order_data.items:
            await db.execute(
                update(Item)
                .where(Item.id == order_item.item_id)
                .values(stock_quantity=Item.stock_quantity - order_item.quantity)
            )
        
        # Clear cart
        await db.execute(
            update(Cart)
            .where(Cart.customer_id == customer_id)
            .values(items=[], total_amount=0)
        )
        
        await db.commit()
        await db.refresh(order)
        
        logger.info(f"Created order: {order_number} for customer {customer_id}")
        return order
    
    @staticmethod
    def _generate_order_number() -> str:
        """Generate unique order number"""
        import random
        import string
        
        prefix = "ORD"
        date_part = datetime.utcnow().strftime("%Y%m%d")
        random_part = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}{date_part}{random_part}"
    
    @staticmethod
    def _calculate_delivery_fee(address: Any) -> float:
        """Calculate delivery fee based on distance"""
        # Simplified calculation
        # In production, calculate based on actual distance from business
        
        base_fee = 30.0  # Base delivery fee
        distance_fee = 0  # Additional fee based on distance
        
        return base_fee + distance_fee
    
    @staticmethod
    async def get_order(db: AsyncSession, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_orders(
        db: AsyncSession,
        business_id: str,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Order], int]:
        """Get orders with filters"""
        query = select(Order).where(Order.business_id == business_id)
        
        if status:
            query = query.where(Order.status == status)
        
        if start_date:
            query = query.where(Order.created_at >= start_date)
        
        if end_date:
            query = query.where(Order.created_at <= end_date)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(Order.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await db.execute(query)
        orders = result.scalars().all()
        
        return orders, total
    
    @staticmethod
    async def get_customer_orders(
        db: AsyncSession,
        customer_id: str,
        business_id: str,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Order], int]:
        """Get orders for specific customer"""
        query = select(Order).where(
            and_(
                Order.customer_id == customer_id,
                Order.business_id == business_id
            )
        )
        
        if status:
            query = query.where(Order.status == status)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.order_by(Order.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await db.execute(query)
        orders = result.scalars().all()
        
        return orders, total
    
    @staticmethod
    async def update_order_status(
        db: AsyncSession,
        order_id: str,
        status: str,
        business_id: str
    ) -> Optional[Order]:
        """Update order status"""
        order = await OrderService.get_order(db, order_id)
        
        if not order or order.business_id != business_id:
            return None
        
        order.status = status
        
        # Update timestamps based on status
        now = datetime.utcnow()
        if status == OrderStatus.CONFIRMED.value and not order.confirmed_time:
            order.confirmed_time = now
        elif status == OrderStatus.PREPARING.value and not order.prepared_time:
            order.prepared_time = now
        elif status == OrderStatus.READY.value:
            order.prepared_time = now
        elif status == OrderStatus.PICKED_UP.value and not order.picked_up_time:
            order.picked_up_time = now
        elif status == OrderStatus.DELIVERED.value and not order.delivered_time:
            order.delivered_time = now
        
        await db.commit()
        await db.refresh(order)
        
        logger.info(f"Updated order {order_id} status to {status}")
        return order
    
    @staticmethod
    async def cancel_order(
        db: AsyncSession,
        order_id: str,
        customer_id: str
    ) -> bool:
        """Cancel order"""
        order = await OrderService.get_order(db, order_id)
        
        if not order or order.customer_id != customer_id:
            return False
        
        # Check if order can be cancelled
        if order.status not in [OrderStatus.PENDING.value, OrderStatus.CONFIRMED.value]:
            return False
        
        order.status = OrderStatus.CANCELLED.value
        
        # Restore item stock
        for item in order.items:
            await db.execute(
                update(Item)
                .where(Item.id == item["item_id"])
                .values(stock_quantity=Item.stock_quantity + item["quantity"])
            )
        
        await db.commit()
        
        logger.info(f"Cancelled order {order_id}")
        return True
    
    @staticmethod
    async def get_tracking_info(
        db: AsyncSession,
        order_id: str,
        customer_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get order tracking information"""
        order = await OrderService.get_order(db, order_id)
        
        if not order or order.customer_id != customer_id:
            return None
        
        # Calculate ETA
        eta_minutes = 0
        if order.estimated_delivery_time:
            time_diff = order.estimated_delivery_time - datetime.utcnow()
            eta_minutes = max(0, int(time_diff.total_seconds() / 60))
        
        return {
            "order_id": order_id,
            "order_number": order.order_number,
            "status": order.status,
            "current_location": order.current_location,
            "delivery_boy": {
                "id": order.delivery_boy_id,
                "name": order.delivery_boy_name,
                "phone": order.delivery_boy_phone
            } if order.delivery_boy_id else None,
            "estimated_delivery_time": order.estimated_delivery_time,
            "eta_minutes": eta_minutes,
            "timeline": {
                "order_time": order.order_time,
                "confirmed_time": order.confirmed_time,
                "prepared_time": order.prepared_time,
                "picked_up_time": order.picked_up_time,
                "delivered_time": order.delivered_time
            }
        }
    
    @staticmethod
    async def update_cart(
        db: AsyncSession,
        business_id: str,
        customer_id: str,
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update shopping cart"""
        # Calculate cart total
        total_amount = 0
        cart_items = []
        
        for cart_item in items:
            result = await db.execute(
                select(Item).where(
                    and_(
                        Item.id == cart_item["item_id"],
                        Item.business_id == business_id,
                        Item.is_active == True
                    )
                )
            )
            item = result.scalar_one_or_none()
            
            if item:
                item_total = item.price * cart_item["quantity"]
                total_amount += item_total
                
                cart_items.append({
                    "item_id": cart_item["item_id"],
                    "name": item.name,
                    "quantity": cart_item["quantity"],
                    "price": item.price,
                    "total": item_total,
                    "variants": cart_item.get("variants")
                })
        
        # Update or create cart
        result = await db.execute(
            select(Cart).where(Cart.customer_id == customer_id)
        )
        cart = result.scalar_one_or_none()
        
        if cart:
            cart.items = cart_items
            cart.total_amount = total_amount
            cart.updated_at = datetime.utcnow()
        else:
            cart = Cart(
                customer_id=customer_id,
                items=cart_items,
                total_amount=total_amount
            )
            db.add(cart)
        
        await db.commit()
        
        return {
            "cart_id": str(cart.id),
            "items": cart_items,
            "total_amount": total_amount,
            "item_count": len(cart_items)
        }
    
    @staticmethod
    async def get_cart(
        db: AsyncSession,
        business_id: str,
        customer_id: str
    ) -> Dict[str, Any]:
        """Get shopping cart"""
        result = await db.execute(
            select(Cart).where(Cart.customer_id == customer_id)
        )
        cart = result.scalar_one_or_none()
        
        if not cart or not cart.items:
            return {"items": [], "total_amount": 0, "item_count": 0}
        
        # Filter items for current business
        business_items = [
            item for item in cart.items
            if await OrderService._is_item_from_business(db, item["item_id"], business_id)
        ]
        
        total_amount = sum(item["total"] for item in business_items)
        
        return {
            "cart_id": str(cart.id),
            "items": business_items,
            "total_amount": total_amount,
            "item_count": len(business_items)
        }
    
    @staticmethod
    async def _is_item_from_business(
        db: AsyncSession,
        item_id: str,
        business_id: str
    ) -> bool:
        """Check if item belongs to business"""
        result = await db.execute(
            select(Item).where(
                and_(
                    Item.id == item_id,
                    Item.business_id == business_id
                )
            )
        )
        return result.scalar_one_or_none() is not None
    
    @staticmethod
    async def get_order_stats(
        db: AsyncSession,
        business_id: str
    ) -> Dict[str, Any]:
        """Get order statistics for business"""
        # Today's orders
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        result = await db.execute(
            select(func.count(Order.id), func.sum(Order.total_amount))
            .where(
                and_(
                    Order.business_id == business_id,
                    Order.created_at >= today_start,
                    Order.created_at <= today_end
                )
            )
        )
        today_stats = result.first()
        
        # This week's orders
        week_start = today - timedelta(days=today.weekday())
        result = await db.execute(
            select(func.count(Order.id), func.sum(Order.total_amount))
            .where(
                and_(
                    Order.business_id == business_id,
                    Order.created_at >= week_start
                )
            )
        )
        week_stats = result.first()
        
        # This month's orders
        month_start = datetime(today.year, today.month, 1)
        result = await db.execute(
            select(func.count(Order.id), func.sum(Order.total_amount))
            .where(
                and_(
                    Order.business_id == business_id,
                    Order.created_at >= month_start
                )
            )
        )
        month_stats = result.first()
        
        # Status counts
        result = await db.execute(
            select(Order.status, func.count(Order.id))
            .where(Order.business_id == business_id)
            .group_by(Order.status)
        )
        status_counts = dict(result.all())
        
        return {
            "today": {
                "orders": today_stats[0] or 0,
                "revenue": float(today_stats[1] or 0)
            },
            "this_week": {
                "orders": week_stats[0] or 0,
                "revenue": float(week_stats[1] or 0)
            },
            "this_month": {
                "orders": month_stats[0] or 0,
                "revenue": float(month_stats[1] or 0)
            },
            "status_counts": status_counts
        }