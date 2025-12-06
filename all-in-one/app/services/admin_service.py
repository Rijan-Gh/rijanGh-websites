from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update
from datetime import datetime, timedelta
import logging

from app.models.global.user_model import User
from app.models.global.business_model import Business
from app.models.global.access_key_model import AccessKey
from app.models.global.delivery_boy_model import DeliveryBoy
from app.core.security import generate_access_key
import uuid

logger = logging.getLogger(__name__)

class AdminService:
    
    @staticmethod
    async def get_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get admin dashboard statistics"""
        # Total users
        result = await db.execute(select(func.count(User.id)))
        total_users = result.scalar()
        
        # Total businesses
        result = await db.execute(select(func.count(Business.id)))
        total_businesses = result.scalar()
        
        # Total delivery boys
        result = await db.execute(select(func.count(DeliveryBoy.id)))
        total_delivery_boys = result.scalar()
        
        # New users today
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        result = await db.execute(
            select(func.count(User.id))
            .where(User.created_at >= today_start)
        )
        new_users_today = result.scalar()
        
        # Pending business verifications
        result = await db.execute(
            select(func.count(Business.id))
            .where(Business.is_verified == False)
        )
        pending_verifications = result.scalar()
        
        # Active orders (would require querying business databases)
        # For now, return placeholder
        active_orders = 0
        
        # Revenue (would require aggregating from all business databases)
        total_revenue = 0.0
        
        return {
            "total_users": total_users,
            "total_businesses": total_businesses,
            "total_delivery_boys": total_delivery_boys,
            "new_users_today": new_users_today,
            "pending_verifications": pending_verifications,
            "active_orders": active_orders,
            "total_revenue": total_revenue,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def get_businesses(
        db: AsyncSession,
        status: Optional[str] = None,
        business_type: Optional[str] = None,
        city: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Business], int]:
        """Get all businesses with filters"""
        query = select(Business)
        
        if status == "active":
            query = query.where(Business.is_active == True)
        elif status == "inactive":
            query = query.where(Business.is_active == False)
        elif status == "unverified":
            query = query.where(Business.is_verified == False)
        elif status == "verified":
            query = query.where(Business.is_verified == True)
        
        if business_type:
            query = query.where(Business.business_type == business_type)
        
        if city:
            query = query.where(Business.city.ilike(f"%{city}%"))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.order_by(Business.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await db.execute(query)
        businesses = result.scalars().all()
        
        return businesses, total
    
    @staticmethod
    async def verify_business(
        db: AsyncSession,
        business_id: str,
        verify: bool
    ) -> bool:
        """Verify or unverify business"""
        result = await db.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()
        
        if not business:
            return False
        
        business.is_verified = verify
        await db.commit()
        
        logger.info(f"Business {business_id} verification set to {verify}")
        return True
    
    @staticmethod
    async def block_business(
        db: AsyncSession,
        business_id: str,
        block: bool,
        reason: Optional[str] = None
    ) -> bool:
        """Block or unblock business"""
        result = await db.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()
        
        if not business:
            return False
        
        business.is_active = not block
        if reason:
            # Store block reason (would need a field in model)
            pass
        
        await db.commit()
        
        action = "blocked" if block else "unblocked"
        logger.info(f"Business {business_id} {action}")
        return True
    
    @staticmethod
    async def get_access_keys(
        db: AsyncSession,
        is_active: Optional[bool] = None,
        business_type: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[AccessKey], int]:
        """Get all access keys"""
        query = select(AccessKey)
        
        if is_active is not None:
            query = query.where(AccessKey.is_active == is_active)
        
        if business_type:
            query = query.where(AccessKey.business_type == business_type)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.order_by(AccessKey.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await db.execute(query)
        keys = result.scalars().all()
        
        return keys, total
    
    @staticmethod
    async def create_access_key(
        db: AsyncSession,
        name: str,
        business_type: str,
        max_businesses: int,
        valid_until: Optional[datetime],
        created_by: str
    ) -> AccessKey:
        """Create new access key"""
        key = generate_access_key()
        
        access_key = AccessKey(
            key=key,
            name=name,
            business_type=business_type,
            max_businesses=max_businesses,
            valid_until=valid_until,
            created_by=created_by,
            is_active=True
        )
        
        db.add(access_key)
        await db.commit()
        await db.refresh(access_key)
        
        logger.info(f"Created access key: {key} for {business_type}")
        return access_key
    
    @staticmethod
    async def deactivate_access_key(
        db: AsyncSession,
        key_id: str
    ) -> bool:
        """Deactivate access key"""
        result = await db.execute(
            select(AccessKey).where(AccessKey.id == key_id)
        )
        access_key = result.scalar_one_or_none()
        
        if not access_key:
            return False
        
        access_key.is_active = False
        await db.commit()
        
        logger.info(f"Deactivated access key: {key_id}")
        return True
    
    @staticmethod
    async def get_users(
        db: AsyncSession,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        city: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[User], int]:
        """Get all users"""
        query = select(User)
        
        if role:
            query = query.where(User.role == role)
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        # Note: City would require joining with addresses
        # For simplicity, we'll skip city filtering for now
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.order_by(User.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        return users, total
    
    @staticmethod
    async def block_user(
        db: AsyncSession,
        user_id: str,
        block: bool,
        reason: Optional[str] = None
    ) -> bool:
        """Block or unblock user"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        user.is_blocked = block
        user.is_active = not block
        
        if reason:
            # Store block reason
            pass
        
        await db.commit()
        
        action = "blocked" if block else "unblocked"
        logger.info(f"User {user_id} {action}")
        return True
    
    @staticmethod
    async def get_delivery_boys(
        db: AsyncSession,
        is_verified: Optional[bool] = None,
        is_active: Optional[bool] = None,
        city: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[DeliveryBoy], int]:
        """Get all delivery boys"""
        query = select(DeliveryBoy).join(User)
        
        if is_verified is not None:
            query = query.where(DeliveryBoy.is_verified == is_verified)
        
        if is_active is not None:
            query = query.where(DeliveryBoy.is_active == is_active)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.order_by(DeliveryBoy.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await db.execute(query)
        delivery_boys = result.scalars().all()
        
        return delivery_boys, total
    
    @staticmethod
    async def verify_delivery_boy(
        db: AsyncSession,
        delivery_boy_id: str,
        verify: bool
    ) -> bool:
        """Verify delivery boy"""
        result = await db.execute(
            select(DeliveryBoy).where(DeliveryBoy.id == delivery_boy_id)
        )
        delivery_boy = result.scalar_one_or_none()
        
        if not delivery_boy:
            return False
        
        delivery_boy.is_verified = verify
        await db.commit()
        
        logger.info(f"Delivery boy {delivery_boy_id} verification set to {verify}")
        return True
    
    @staticmethod
    async def get_revenue_analytics(
        db: AsyncSession,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        period: str = "daily"
    ) -> Dict[str, Any]:
        """Get revenue analytics"""
        # In production, this would aggregate revenue from all business databases
        # For now, return mock data
        
        # Mock revenue data
        revenue_data = []
        current = start_date or datetime.utcnow() - timedelta(days=30)
        end = end_date or datetime.utcnow()
        
        while current <= end:
            if period == "daily":
                revenue_data.append({
                    "date": current.date().isoformat(),
                    "revenue": 10000 + (current.day * 1000),
                    "orders": 50 + (current.day * 5)
                })
                current += timedelta(days=1)
            elif period == "weekly":
                revenue_data.append({
                    "week": current.isocalendar()[1],
                    "revenue": 70000 + (current.day * 7000),
                    "orders": 350 + (current.day * 35)
                })
                current += timedelta(weeks=1)
            elif period == "monthly":
                revenue_data.append({
                    "month": current.month,
                    "revenue": 300000 + (current.month * 30000),
                    "orders": 1500 + (current.month * 150)
                })
                current += timedelta(days=30)
        
        return {
            "period": period,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "revenue_data": revenue_data,
            "total_revenue": sum(item["revenue"] for item in revenue_data),
            "total_orders": sum(item["orders"] for item in revenue_data),
            "average_order_value": sum(item["revenue"] for item in revenue_data) / sum(item["orders"] for item in revenue_data) if revenue_data else 0
        }
    
    @staticmethod
    async def get_order_analytics(
        db: AsyncSession,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        business_type: Optional[str]
    ) -> Dict[str, Any]:
        """Get order analytics"""
        # Mock order analytics
        business_types = ["restaurant", "grocery", "pharmacy", "cloud_kitchen"]
        
        if business_type and business_type in business_types:
            business_types = [business_type]
        
        analytics = []
        for bt in business_types:
            analytics.append({
                "business_type": bt,
                "total_orders": 1000 + hash(bt) % 500,
                "completed_orders": 800 + hash(bt) % 400,
                "cancelled_orders": 50 + hash(bt) % 50,
                "avg_order_value": 500 + hash(bt) % 300,
                "popular_categories": ["category1", "category2", "category3"]
            })
        
        return {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "business_type": business_type,
            "analytics": analytics,
            "summary": {
                "total_orders": sum(item["total_orders"] for item in analytics),
                "completed_orders": sum(item["completed_orders"] for item in analytics),
                "cancellation_rate": sum(item["cancelled_orders"] for item in analytics) / sum(item["total_orders"] for item in analytics) if analytics else 0,
                "avg_order_value_all": sum(item["avg_order_value"] * item["total_orders"] for item in analytics) / sum(item["total_orders"] for item in analytics) if analytics else 0
            }
        }
    
    @staticmethod
    async def get_user_analytics(
        db: AsyncSession,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Get user growth analytics"""
        # Mock user analytics
        import random
        
        current = start_date or datetime.utcnow() - timedelta(days=30)
        end = end_date or datetime.utcnow()
        
        user_data = []
        total_users = 0
        
        while current <= end:
            daily_new = random.randint(10, 50)
            total_users += daily_new
            
            user_data.append({
                "date": current.date().isoformat(),
                "new_users": daily_new,
                "total_users": total_users,
                "active_users": random.randint(int(total_users * 0.3), int(total_users * 0.7))
            })
            
            current += timedelta(days=1)
        
        # User segmentation
        user_segments = {
            "customers": int(total_users * 0.7),
            "vendors": int(total_users * 0.2),
            "delivery_boys": int(total_users * 0.08),
            "admins": int(total_users * 0.02)
        }
        
        return {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "user_data": user_data,
            "summary": {
                "total_users": total_users,
                "avg_daily_growth": sum(item["new_users"] for item in user_data) / len(user_data) if user_data else 0,
                "user_segments": user_segments,
                "retention_rate": 0.65  # Mock retention rate
            }
        }