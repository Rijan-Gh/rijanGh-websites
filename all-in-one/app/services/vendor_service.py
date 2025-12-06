from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta
import logging

from app.models.global.business_model import Business, BusinessStaff
from app.models.global.user_model import User
from app.database_manager import db_manager
import asyncio

logger = logging.getLogger(__name__)

class VendorService:
    
    @staticmethod
    async def get_dashboard_data(
        db: AsyncSession,
        vendor_id: str
    ) -> Dict[str, Any]:
        """Get vendor dashboard data"""
        # Get vendor's business
        result = await db.execute(
            select(Business).where(Business.owner_id == vendor_id)
        )
        business = result.scalar_one_or_none()
        
        if not business:
            return {}
        
        # Get business database session
        business_session = await db_manager.get_business_session(str(business.id))
        
        try:
            from sqlalchemy import text
            
            # Today's stats
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            # Get today's orders
            result = await business_session.execute(
                text("""
                    SELECT 
                        COUNT(*) as total_orders,
                        COALESCE(SUM(total_amount), 0) as total_revenue,
                        AVG(total_amount) as avg_order_value
                    FROM orders 
                    WHERE created_at BETWEEN :start AND :end
                """),
                {"start": today_start, "end": today_end}
            )
            today_stats = result.first()
            
            # Get week stats
            week_start = today - timedelta(days=today.weekday())
            result = await business_session.execute(
                text("""
                    SELECT 
                        COUNT(*) as total_orders,
                        COALESCE(SUM(total_amount), 0) as total_revenue
                    FROM orders 
                    WHERE created_at >= :week_start
                """),
                {"week_start": week_start}
            )
            week_stats = result.first()
            
            # Get recent orders
            result = await business_session.execute(
                text("""
                    SELECT 
                        id, order_number, customer_name, total_amount, status, created_at
                    FROM orders 
                    ORDER BY created_at DESC 
                    LIMIT 10
                """)
            )
            recent_orders = result.fetchall()
            
            # Get top items
            result = await business_session.execute(
                text("""
                    SELECT 
                        name, price, total_orders, total_revenue
                    FROM items 
                    WHERE is_active = true 
                    ORDER BY total_orders DESC 
                    LIMIT 5
                """)
            )
            top_items = result.fetchall()
            
            # Get low stock items
            result = await business_session.execute(
                text("""
                    SELECT 
                        name, stock_quantity, low_stock_threshold
                    FROM items 
                    WHERE is_active = true 
                    AND stock_quantity <= low_stock_threshold 
                    AND is_track_inventory = true
                    ORDER BY stock_quantity ASC 
                    LIMIT 5
                """)
            )
            low_stock_items = result.fetchall()
            
            await business_session.close()
            
            return {
                "business": {
                    "id": str(business.id),
                    "name": business.name,
                    "business_type": business.business_type,
                    "is_verified": business.is_verified,
                    "is_active": business.is_active,
                    "total_orders": business.total_orders,
                    "total_revenue": float(business.total_revenue),
                    "avg_rating": business.avg_rating
                },
                "today_stats": {
                    "total_orders": today_stats[0] or 0,
                    "total_revenue": float(today_stats[1] or 0),
                    "avg_order_value": float(today_stats[2] or 0)
                },
                "week_stats": {
                    "total_orders": week_stats[0] or 0,
                    "total_revenue": float(week_stats[1] or 0)
                },
                "recent_orders": [
                    {
                        "id": str(row[0]),
                        "order_number": row[1],
                        "customer_name": row[2],
                        "total_amount": float(row[3]),
                        "status": row[4],
                        "created_at": row[5].isoformat() if row[5] else None
                    }
                    for row in recent_orders
                ],
                "top_items": [
                    {
                        "name": row[0],
                        "price": float(row[1]),
                        "total_orders": row[2],
                        "total_revenue": float(row[3])
                    }
                    for row in top_items
                ],
                "low_stock_items": [
                    {
                        "name": row[0],
                        "current_stock": row[1],
                        "threshold": row[2],
                        "status": "critical" if row[1] == 0 else "low"
                    }
                    for row in low_stock_items
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting vendor dashboard data: {e}")
            await business_session.close()
            return {}
    
    @staticmethod
    async def get_vendor_business(
        db: AsyncSession,
        vendor_id: str
    ) -> Optional[Business]:
        """Get vendor's business"""
        result = await db.execute(
            select(Business).where(Business.owner_id == vendor_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_orders_summary(
        db: AsyncSession,
        business_id: str,
        period: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Get orders summary for given period"""
        business_session = await db_manager.get_business_session(business_id)
        
        try:
            from sqlalchemy import text
            
            # Determine date range
            today = datetime.utcnow().date()
            
            if period == "today":
                start = datetime.combine(today, datetime.min.time())
                end = datetime.combine(today, datetime.max.time())
            elif period == "week":
                start = datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
                end = datetime.combine(today, datetime.max.time())
            elif period == "month":
                start = datetime.combine(datetime(today.year, today.month, 1), datetime.min.time())
                end = datetime.combine(today, datetime.max.time())
            elif period == "year":
                start = datetime.combine(datetime(today.year, 1, 1), datetime.min.time())
                end = datetime.combine(today, datetime.max.time())
            elif period == "custom" and start_date and end_date:
                start = start_date
                end = end_date
            else:
                start = datetime.combine(today - timedelta(days=30), datetime.min.time())
                end = datetime.combine(today, datetime.max.time())
            
            # Get summary
            result = await business_session.execute(
                text("""
                    SELECT 
                        COUNT(*) as total_orders,
                        SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as completed_orders,
                        SUM(CASE WHEN status IN ('pending', 'confirmed', 'preparing', 'ready') THEN 1 ELSE 0 END) as pending_orders,
                        SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_orders,
                        COALESCE(SUM(total_amount), 0) as total_revenue,
                        AVG(total_amount) as avg_order_value
                    FROM orders 
                    WHERE created_at BETWEEN :start AND :end
                """),
                {"start": start, "end": end}
            )
            summary = result.first()
            
            # Get peak hours
            result = await business_session.execute(
                text("""
                    SELECT 
                        EXTRACT(HOUR FROM created_at) as hour,
                        COUNT(*) as order_count
                    FROM orders 
                    WHERE created_at BETWEEN :start AND :end
                    GROUP BY EXTRACT(HOUR FROM created_at)
                    ORDER BY order_count DESC
                    LIMIT 5
                """),
                {"start": start, "end": end}
            )
            peak_hours = result.fetchall()
            
            await business_session.close()
            
            return {
                "total_orders": summary[0] or 0,
                "completed_orders": summary[1] or 0,
                "pending_orders": summary[2] or 0,
                "cancelled_orders": summary[3] or 0,
                "total_revenue": float(summary[4] or 0),
                "avg_order_value": float(summary[5] or 0),
                "period": {
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "type": period
                },
                "peak_hours": [
                    {
                        "hour": int(row[0]),
                        "order_count": row[1],
                        "time_range": f"{int(row[0]):02d}:00-{int(row[0]):02d}:59"
                    }
                    for row in peak_hours
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting orders summary: {e}")
            await business_session.close()
            return {}
    
    @staticmethod
    async def get_revenue_analytics(
        db: AsyncSession,
        business_id: str,
        period: str
    ) -> Dict[str, Any]:
        """Get revenue analytics"""
        business_session = await db_manager.get_business_session(business_id)
        
        try:
            from sqlalchemy import text
            
            today = datetime.utcnow().date()
            
            if period == "daily":
                # Last 30 days
                start_date = today - timedelta(days=30)
                query = """
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as order_count,
                        COALESCE(SUM(total_amount), 0) as revenue
                    FROM orders 
                    WHERE created_at >= :start_date
                    GROUP BY DATE(created_at)
                    ORDER BY DATE(created_at)
                """
                params = {"start_date": start_date}
                
            elif period == "weekly":
                # Last 12 weeks
                start_date = today - timedelta(weeks=12)
                query = """
                    SELECT 
                        EXTRACT(YEAR FROM created_at) as year,
                        EXTRACT(WEEK FROM created_at) as week,
                        COUNT(*) as order_count,
                        COALESCE(SUM(total_amount), 0) as revenue
                    FROM orders 
                    WHERE created_at >= :start_date
                    GROUP BY EXTRACT(YEAR FROM created_at), EXTRACT(WEEK FROM created_at)
                    ORDER BY year, week
                """
                params = {"start_date": start_date}
                
            elif period == "monthly":
                # Last 12 months
                start_date = today - timedelta(days=365)
                query = """
                    SELECT 
                        EXTRACT(YEAR FROM created_at) as year,
                        EXTRACT(MONTH FROM created_at) as month,
                        COUNT(*) as order_count,
                        COALESCE(SUM(total_amount), 0) as revenue
                    FROM orders 
                    WHERE created_at >= :start_date
                    GROUP BY EXTRACT(YEAR FROM created_at), EXTRACT(MONTH FROM created_at)
                    ORDER BY year, month
                """
                params = {"start_date": start_date}
                
            else:  # yearly
                # Last 5 years
                start_date = today - timedelta(days=5*365)
                query = """
                    SELECT 
                        EXTRACT(YEAR FROM created_at) as year,
                        COUNT(*) as order_count,
                        COALESCE(SUM(total_amount), 0) as revenue
                    FROM orders 
                    WHERE created_at >= :start_date
                    GROUP BY EXTRACT(YEAR FROM created_at)
                    ORDER BY year
                """
                params = {"start_date": start_date}
            
            result = await business_session.execute(text(query), params)
            data = result.fetchall()
            
            # Calculate growth rate
            if len(data) >= 2:
                current = float(data[-1][2]) if data[-1][2] else 0
                previous = float(data[-2][2]) if data[-2][2] else 0
                growth_rate = ((current - previous) / previous * 100) if previous > 0 else 0
            else:
                growth_rate = 0
            
            await business_session.close()
            
            return {
                "period": period,
                "data": [
                    {
                        "period": row[0] if period != "daily" else row[0].isoformat(),
                        "order_count": row[1],
                        "revenue": float(row[2])
                    }
                    for row in data
                ],
                "total_revenue": sum(float(row[2]) for row in data),
                "total_orders": sum(row[1] for row in data),
                "growth_rate": round(growth_rate, 2),
                "avg_order_value": sum(float(row[2]) for row in data) / sum(row[1] for row in data) if data else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting revenue analytics: {e}")
            await business_session.close()
            return {}
    
    @staticmethod
    async def get_top_items(
        db: AsyncSession,
        business_id: str,
        limit: int,
        period: str
    ) -> List[Dict[str, Any]]:
        """Get top selling items"""
        business_session = await db_manager.get_business_session(business_id)
        
        try:
            from sqlalchemy import text
            
            # Determine date filter
            today = datetime.utcnow().date()
            
            if period == "day":
                start_date = today
            elif period == "week":
                start_date = today - timedelta(days=7)
            elif period == "month":
                start_date = today - timedelta(days=30)
            elif period == "year":
                start_date = today - timedelta(days=365)
            else:  # all
                start_date = None
            
            if start_date:
                query = """
                    SELECT 
                        i.name,
                        i.category_id,
                        COUNT(o.id) as order_count,
                        SUM(oi.quantity) as total_quantity,
                        SUM(oi.price * oi.quantity) as total_revenue
                    FROM items i
                    LEFT JOIN orders o ON o.business_id = :business_id
                    LEFT JOIN jsonb_array_elements(o.items) oi ON oi->>'item_id' = i.id::text
                    WHERE i.is_active = true
                    AND o.created_at >= :start_date
                    GROUP BY i.id, i.name, i.category_id
                    ORDER BY total_quantity DESC
                    LIMIT :limit
                """
                params = {"business_id": business_id, "start_date": start_date, "limit": limit}
            else:
                query = """
                    SELECT 
                        name,
                        category_id,
                        total_orders,
                        COALESCE(total_revenue, 0) as total_revenue
                    FROM items 
                    WHERE is_active = true 
                    ORDER BY total_orders DESC 
                    LIMIT :limit
                """
                params = {"limit": limit}
            
            result = await business_session.execute(text(query), params)
            items = result.fetchall()
            
            await business_session.close()
            
            return [
                {
                    "name": row[0],
                    "category": row[1],
                    "order_count": row[2],
                    "total_quantity": row[3] if len(row) > 3 else 0,
                    "total_revenue": float(row[3] if len(row) == 4 else row[2])
                }
                for row in items
            ]
            
        except Exception as e:
            logger.error(f"Error getting top items: {e}")
            await business_session.close()
            return []
    
    @staticmethod
    async def get_customer_insights(
        db: AsyncSession,
        business_id: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get customer insights"""
        business_session = await db_manager.get_business_session(business_id)
        
        try:
            from sqlalchemy import text
            
            query = """
                SELECT 
                    customer_id,
                    customer_name,
                    COUNT(*) as total_orders,
                    SUM(total_amount) as total_spent,
                    MAX(created_at) as last_order_date,
                    AVG(total_amount) as avg_order_value
                FROM orders 
                GROUP BY customer_id, customer_name
                ORDER BY total_spent DESC
                LIMIT :limit
            """
            
            result = await business_session.execute(text(query), {"limit": limit})
            customers = result.fetchall()
            
            # Get favorite items for each customer
            insights = []
            for customer in customers:
                # Get favorite items
                fav_query = """
                    SELECT 
                        i.name,
                        SUM(oi.quantity) as total_quantity
                    FROM orders o
                    LEFT JOIN jsonb_array_elements(o.items) oi ON true
                    LEFT JOIN items i ON i.id::text = oi->>'item_id'
                    WHERE o.customer_id = :customer_id
                    AND i.id IS NOT NULL
                    GROUP BY i.name
                    ORDER BY total_quantity DESC
                    LIMIT 3
                """
                
                fav_result = await business_session.execute(
                    text(fav_query), 
                    {"customer_id": customer[0]}
                )
                favorite_items = fav_result.fetchall()
                
                insights.append({
                    "customer_id": customer[0],
                    "customer_name": customer[1],
                    "total_orders": customer[2],
                    "total_spent": float(customer[3] or 0),
                    "last_order_date": customer[4].isoformat() if customer[4] else None,
                    "avg_order_value": float(customer[5] or 0),
                    "favorite_items": [item[0] for item in favorite_items]
                })
            
            await business_session.close()
            return insights
            
        except Exception as e:
            logger.error(f"Error getting customer insights: {e}")
            await business_session.close()
            return []
    
    @staticmethod
    async def add_staff_member(
        db: AsyncSession,
        business_id: str,
        vendor_id: str,
        phone: str,
        role: str,
        permissions: List[str]
    ) -> Dict[str, Any]:
        """Add staff member to business"""
        # Check if user exists
        result = await db.execute(
            select(User).where(User.phone == phone)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            from app.core.security import get_password_hash
            import uuid
            
            # Generate temporary password
            temp_password = "Temp@123"  # In production, generate random password
            
            user = User(
                id=uuid.uuid4(),
                phone=phone,
                password_hash=get_password_hash(temp_password),
                role="staff",
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        # Check if already staff member
        result = await db.execute(
            select(BusinessStaff).where(
                and_(
                    BusinessStaff.business_id == business_id,
                    BusinessStaff.user_id == user.id
                )
            )
        )
        existing_staff = result.scalar_one_or_none()
        
        if existing_staff:
            raise Exception("User is already a staff member")
        
        # Add as staff member
        staff_member = BusinessStaff(
            business_id=business_id,
            user_id=user.id,
            role=role,
            permissions=permissions,
            is_active=True
        )
        
        db.add(staff_member)
        await db.commit()
        await db.refresh(staff_member)
        
        return {
            "id": str(staff_member.id),
            "user_id": str(user.id),
            "phone": user.phone,
            "full_name": user.full_name,
            "role": role,
            "permissions": permissions,
            "is_active": True
        }
    
    @staticmethod
    async def get_staff_members(
        db: AsyncSession,
        business_id: str
    ) -> List[Dict[str, Any]]:
        """Get all staff members"""
        result = await db.execute(
            select(BusinessStaff, User)
            .join(User, BusinessStaff.user_id == User.id)
            .where(BusinessStaff.business_id == business_id)
            .order_by(BusinessStaff.created_at.desc())
        )
        
        staff_members = []
        for staff, user in result:
            staff_members.append({
                "id": str(staff.id),
                "user_id": str(user.id),
                "phone": user.phone,
                "full_name": user.full_name,
                "role": staff.role,
                "permissions": staff.permissions,
                "is_active": staff.is_active,
                "created_at": staff.created_at.isoformat() if staff.created_at else None
            })
        
        return staff_members
    
    @staticmethod
    async def remove_staff_member(
        db: AsyncSession,
        business_id: str,
        staff_id: str,
        vendor_id: str
    ) -> bool:
        """Remove staff member from business"""
        # Verify vendor owns the business
        result = await db.execute(
            select(Business).where(
                and_(
                    Business.id == business_id,
                    Business.owner_id == vendor_id
                )
            )
        )
        business = result.scalar_one_or_none()
        
        if not business:
            return False
        
        # Find and remove staff member
        result = await db.execute(
            select(BusinessStaff).where(
                and_(
                    BusinessStaff.id == staff_id,
                    BusinessStaff.business_id == business_id
                )
            )
        )
        staff_member = result.scalar_one_or_none()
        
        if not staff_member:
            return False
        
        # Soft delete (deactivate)
        staff_member.is_active = False
        await db.commit()
        
        logger.info(f"Removed staff member {staff_id} from business {business_id}")
        return True
    
    @staticmethod
    async def update_business_settings(
        db: AsyncSession,
        business_id: str,
        settings: dict
    ) -> Dict[str, Any]:
        """Update business settings"""
        result = await db.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()
        
        if not business:
            raise Exception("Business not found")
        
        # Update settings (store in JSON field or specific columns)
        # For now, store in a JSON column called settings
        business.settings = settings
        await db.commit()
        
        return {
            "business_id": business_id,
            "settings": settings,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def get_notifications(
        db: AsyncSession,
        vendor_id: str,
        unread_only: bool,
        page: int,
        limit: int
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get vendor notifications"""
        # Get vendor's business
        result = await db.execute(
            select(Business).where(Business.owner_id == vendor_id)
        )
        business = result.scalar_one_or_none()
        
        if not business:
            return [], 0
        
        # In production, this would query a notifications table
        # For now, return mock notifications
        
        mock_notifications = [
            {
                "id": f"notif_{i}",
                "title": "New Order Received",
                "message": f"New order #{1000 + i} has been received",
                "type": "order",
                "data": {"order_id": f"order_{i}", "amount": 500 + (i * 100)},
                "is_read": i % 3 == 0,
                "created_at": (datetime.utcnow() - timedelta(hours=i)).isoformat()
            }
            for i in range(50)
        ]
        
        # Filter unread if requested
        if unread_only:
            mock_notifications = [n for n in mock_notifications if not n["is_read"]]
        
        total = len(mock_notifications)
        
        # Apply pagination
        start = (page - 1) * limit
        end = start + limit
        paginated = mock_notifications[start:end]
        
        return paginated, total
    
    @staticmethod
    async def mark_notification_read(
        db: AsyncSession,
        notification_id: str,
        vendor_id: str
    ) -> bool:
        """Mark notification as read"""
        # In production, update notification in database
        # For now, return success
        logger.info(f"Notification {notification_id} marked as read by vendor {vendor_id}")
        return True