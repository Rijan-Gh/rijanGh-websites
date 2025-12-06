from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, and_
from datetime import datetime, timedelta
import logging

from app.models.global.delivery_boy_model import DeliveryBoy
from app.utils.geo_distance import calculate_distance
import asyncio

logger = logging.getLogger(__name__)

class DeliveryService:
    
    @staticmethod
    async def get_available_orders(
        db: AsyncSession,
        delivery_boy_id: str,
        lat: Optional[float],
        lng: Optional[float],
        radius_km: float
    ) -> List[Dict[str, Any]]:
        """Get available orders for delivery"""
        # In production, this would query all business databases
        # For now, return mock data
        
        mock_orders = []
        
        # Generate mock orders near the location
        if lat and lng:
            for i in range(10):
                # Generate nearby coordinates
                import random
                offset_lat = lat + (random.uniform(-0.01, 0.01))
                offset_lng = lng + (random.uniform(-0.01, 0.01))
                
                distance = calculate_distance(lat, lng, offset_lat, offset_lng)
                
                if distance <= radius_km:
                    mock_orders.append({
                        "order_id": f"order_{i}",
                        "business_id": f"business_{i % 3}",
                        "business_name": f"Business {i % 3}",
                        "customer_address": f"Address {i}",
                        "customer_name": f"Customer {i}",
                        "customer_phone": f"+91123456789{i}",
                        "total_amount": 300 + (i * 50),
                        "delivery_fee": 30 + (i * 5),
                        "distance_km": round(distance, 2),
                        "pickup_lat": offset_lat,
                        "pickup_lng": offset_lng,
                        "delivery_lat": lat + (random.uniform(-0.02, 0.02)),
                        "delivery_lng": lng + (random.uniform(-0.02, 0.02)),
                        "estimated_pickup_time": (datetime.utcnow() + timedelta(minutes=10 + i)).isoformat(),
                        "estimated_delivery_time": (datetime.utcnow() + timedelta(minutes=30 + i)).isoformat(),
                        "items_count": 1 + (i % 5)
                    })
        
        # Sort by distance
        mock_orders.sort(key=lambda x: x["distance_km"])
        
        return mock_orders
    
    @staticmethod
    async def accept_order(
        db: AsyncSession,
        order_id: str,
        delivery_boy_id: str
    ) -> bool:
        """Accept delivery order"""
        # In production, this would update the order in business database
        # and assign delivery boy
        
        # Update delivery boy status
        await db.execute(
            update(DeliveryBoy)
            .where(DeliveryBoy.user_id == delivery_boy_id)
            .values(
                current_status="busy",
                is_available=False
            )
        )
        
        await db.commit()
        
        logger.info(f"Delivery boy {delivery_boy_id} accepted order {order_id}")
        return True
    
    @staticmethod
    async def update_location(
        db: AsyncSession,
        delivery_boy_id: str,
        lat: float,
        lng: float
    ) -> bool:
        """Update delivery boy location"""
        await db.execute(
            update(DeliveryBoy)
            .where(DeliveryBoy.user_id == delivery_boy_id)
            .values(
                current_location_lat=lat,
                current_location_lng=lng,
                updated_at=datetime.utcnow()
            )
        )
        
        await db.commit()
        return True
    
    @staticmethod
    async def update_status(
        db: AsyncSession,
        delivery_boy_id: str,
        status: str
    ) -> bool:
        """Update delivery boy status"""
        valid_statuses = ["offline", "available", "busy"]
        
        if status not in valid_statuses:
            return False
        
        update_data = {"current_status": status}
        
        if status == "available":
            update_data["is_available"] = True
        elif status in ["offline", "busy"]:
            update_data["is_available"] = False
        
        await db.execute(
            update(DeliveryBoy)
            .where(DeliveryBoy.user_id == delivery_boy_id)
            .values(**update_data)
        )
        
        await db.commit()
        
        logger.info(f"Delivery boy {delivery_boy_id} status updated to {status}")
        return True
    
    @staticmethod
    async def get_assigned_orders(
        db: AsyncSession,
        delivery_boy_id: str,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get orders assigned to delivery boy"""
        # In production, this would query all business databases
        # For now, return mock data
        
        mock_orders = []
        
        for i in range(limit):
            order_status = status or (["assigned", "picked_up", "delivered"][i % 3])
            
            mock_orders.append({
                "order_id": f"assigned_order_{i}",
                "order_number": f"ORD202312{i:02d}",
                "business_name": f"Business {i % 5}",
                "customer_name": f"Customer {i}",
                "customer_phone": f"+91123456789{i}",
                "customer_address": f"Address {i}, City",
                "total_amount": 400 + (i * 50),
                "delivery_fee": 35 + (i * 5),
                "status": order_status,
                "assigned_time": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                "pickup_time": (datetime.utcnow() - timedelta(hours=i-1)).isoformat() if i > 0 else None,
                "delivery_time": (datetime.utcnow() - timedelta(hours=i-2)).isoformat() if i > 1 else None,
                "pickup_lat": 28.6139 + (i * 0.001),
                "pickup_lng": 77.2090 + (i * 0.001),
                "delivery_lat": 28.6139 + (i * 0.002),
                "delivery_lng": 77.2090 + (i * 0.002),
                "items_count": 2 + (i % 4)
            })
        
        # Filter by status if specified
        if status:
            mock_orders = [order for order in mock_orders if order["status"] == status]
        
        total = len(mock_orders)
        
        # Apply pagination
        start = (page - 1) * limit
        end = start + limit
        paginated = mock_orders[start:end]
        
        return paginated, total
    
    @staticmethod
    async def pickup_order(
        db: AsyncSession,
        order_id: str,
        delivery_boy_id: str
    ) -> bool:
        """Mark order as picked up"""
        # In production, update order status in business database
        logger.info(f"Delivery boy {delivery_boy_id} picked up order {order_id}")
        return True
    
    @staticmethod
    async def deliver_order(
        db: AsyncSession,
        order_id: str,
        delivery_boy_id: str,
        otp: Optional[str] = None
    ) -> bool:
        """Mark order as delivered"""
        # In production, update order status in business database
        # and process delivery boy payment
        
        # Update delivery boy stats
        result = await db.execute(
            select(DeliveryBoy).where(DeliveryBoy.user_id == delivery_boy_id)
        )
        delivery_boy = result.scalar_one_or_none()
        
        if delivery_boy:
            delivery_fee = 40  # Would be fetched from order
            
            delivery_boy.total_deliveries += 1
            delivery_boy.successful_deliveries += 1
            delivery_boy.total_earnings += delivery_fee
            delivery_boy.wallet_balance += delivery_fee
            delivery_boy.current_status = "available"
            delivery_boy.is_available = True
            
            await db.commit()
        
        logger.info(f"Delivery boy {delivery_boy_id} delivered order {order_id}")
        return True
    
    @staticmethod
    async def get_earnings(
        db: AsyncSession,
        delivery_boy_id: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Get delivery earnings"""
        result = await db.execute(
            select(DeliveryBoy).where(DeliveryBoy.user_id == delivery_boy_id)
        )
        delivery_boy = result.scalar_one_or_none()
        
        if not delivery_boy:
            return {}
        
        # In production, this would calculate earnings from delivered orders
        # For now, use delivery boy stats
        
        # Mock earnings breakdown
        earnings_breakdown = []
        current = start_date or datetime.utcnow() - timedelta(days=7)
        end = end_date or datetime.utcnow()
        
        while current <= end:
            daily_earnings = 400 + (hash(str(current.date())) % 300)
            earnings_breakdown.append({
                "date": current.date().isoformat(),
                "earnings": daily_earnings,
                "deliveries": 5 + (hash(str(current.date())) % 5),
                "hours_worked": 8 + (hash(str(current.date())) % 4)
            })
            current += timedelta(days=1)
        
        return {
            "delivery_boy_id": delivery_boy_id,
            "total_earnings": delivery_boy.total_earnings,
            "wallet_balance": delivery_boy.wallet_balance,
            "pending_balance": delivery_boy.pending_balance,
            "total_deliveries": delivery_boy.total_deliveries,
            "successful_deliveries": delivery_boy.successful_deliveries,
            "cancelled_deliveries": delivery_boy.cancelled_deliveries,
            "earnings_breakdown": earnings_breakdown,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }
    
    @staticmethod
    async def get_stats(
        db: AsyncSession,
        delivery_boy_id: str
    ) -> Dict[str, Any]:
        """Get delivery statistics"""
        result = await db.execute(
            select(DeliveryBoy).where(DeliveryBoy.user_id == delivery_boy_id)
        )
        delivery_boy = result.scalar_one_or_none()
        
        if not delivery_boy:
            return {}
        
        # Calculate additional stats
        success_rate = 0
        if delivery_boy.total_deliveries > 0:
            success_rate = (delivery_boy.successful_deliveries / delivery_boy.total_deliveries) * 100
        
        avg_earnings_per_delivery = 0
        if delivery_boy.successful_deliveries > 0:
            avg_earnings_per_delivery = delivery_boy.total_earnings / delivery_boy.successful_deliveries
        
        # Today's stats (mock)
        today_deliveries = 3
        today_earnings = 120
        
        return {
            "delivery_boy_id": delivery_boy_id,
            "basic_stats": {
                "total_deliveries": delivery_boy.total_deliveries,
                "successful_deliveries": delivery_boy.successful_deliveries,
                "cancelled_deliveries": delivery_boy.cancelled_deliveries,
                "total_earnings": delivery_boy.total_earnings,
                "wallet_balance": delivery_boy.wallet_balance,
                "avg_rating": delivery_boy.avg_rating,
                "rating_count": delivery_boy.rating_count
            },
            "calculated_stats": {
                "success_rate": round(success_rate, 2),
                "avg_earnings_per_delivery": round(avg_earnings_per_delivery, 2),
                "completion_rate": round((delivery_boy.successful_deliveries / max(1, delivery_boy.total_deliveries)) * 100, 2)
            },
            "today_stats": {
                "deliveries": today_deliveries,
                "earnings": today_earnings,
                "hours_worked": 6,
                "avg_delivery_time": "45 minutes"
            },
            "vehicle_info": {
                "vehicle_type": delivery_boy.vehicle_type,
                "vehicle_number": delivery_boy.vehicle_number,
                "is_verified": delivery_boy.is_verified
            }
        }