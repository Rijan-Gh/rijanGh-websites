from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta
import logging

from app.models.global.user_model import User
import uuid

logger = logging.getLogger(__name__)

class UserService:
    
    @staticmethod
    async def get_user_profile(
        db: AsyncSession,
        user_id: str
    ) -> Dict[str, Any]:
        """Get user profile"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return {}
        
        return {
            "id": str(user.id),
            "phone": user.phone,
            "email": user.email,
            "full_name": user.full_name,
            "profile_picture": user.profile_picture,
            "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
            "gender": user.gender,
            "wallet_balance": user.wallet_balance,
            "reward_points": user.reward_points,
            "addresses": user.addresses or [],
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
    
    @staticmethod
    async def update_user_profile(
        db: AsyncSession,
        user_id: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        date_of_birth: Optional[datetime] = None,
        gender: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update user profile"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return {}
        
        # Check email uniqueness if provided
        if email and email != user.email:
            result = await db.execute(
                select(User).where(User.email == email)
            )
            existing_user = result.scalar_one_or_none()
            if existing_user:
                raise Exception("Email already in use")
        
        # Update fields
        if full_name is not None:
            user.full_name = full_name
        if email is not None:
            user.email = email
        if date_of_birth is not None:
            user.date_of_birth = date_of_birth
        if gender is not None:
            user.gender = gender
        
        await db.commit()
        await db.refresh(user)
        
        return {
            "id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
            "gender": user.gender,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
    
    @staticmethod
    async def get_user_addresses(
        db: AsyncSession,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get user addresses"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.addresses:
            return []
        
        return user.addresses
    
    @staticmethod
    async def add_user_address(
        db: AsyncSession,
        user_id: str,
        address: dict
    ) -> Dict[str, Any]:
        """Add new address"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise Exception("User not found")
        
        # Generate address ID
        address_id = str(uuid.uuid4())
        address["id"] = address_id
        address["created_at"] = datetime.utcnow().isoformat()
        address["is_default"] = False
        
        # If this is the first address, make it default
        if not user.addresses:
            user.addresses = []
            address["is_default"] = True
        
        # Add address
        user.addresses.append(address)
        await db.commit()
        
        return address
    
    @staticmethod
    async def update_user_address(
        db: AsyncSession,
        user_id: str,
        address_id: str,
        address: dict
    ) -> Optional[Dict[str, Any]]:
        """Update address"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.addresses:
            return None
        
        # Find and update address
        for i, addr in enumerate(user.addresses):
            if addr.get("id") == address_id:
                # Keep existing fields not in update
                for key in ["id", "created_at", "is_default"]:
                    if key in addr and key not in address:
                        address[key] = addr[key]
                
                user.addresses[i] = address
                await db.commit()
                return address
        
        return None
    
    @staticmethod
    async def delete_user_address(
        db: AsyncSession,
        user_id: str,
        address_id: str
    ) -> bool:
        """Delete address"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.addresses:
            return False
        
        # Find and remove address
        new_addresses = []
        address_found = False
        
        for addr in user.addresses:
            if addr.get("id") != address_id:
                new_addresses.append(addr)
            else:
                address_found = True
                # If deleting default address and there are other addresses, make first one default
                if addr.get("is_default") and len(user.addresses) > 1:
                    if new_addresses:
                        new_addresses[0]["is_default"] = True
        
        if address_found:
            user.addresses = new_addresses
            await db.commit()
            return True
        
        return False
    
    @staticmethod
    async def get_wallet_info(
        db: AsyncSession,
        user_id: str
    ) -> Dict[str, Any]:
        """Get wallet information"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return {}
        
        # Get recent transactions (in production, from transactions table)
        recent_transactions = [
            {
                "id": f"txn_{i}",
                "type": "credit" if i % 2 == 0 else "debit",
                "amount": 500 + (i * 100),
                "description": "Order payment" if i % 2 == 0 else "Wallet recharge",
                "date": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "status": "completed"
            }
            for i in range(5)
        ]
        
        return {
            "balance": user.wallet_balance,
            "reward_points": user.reward_points,
            "recent_transactions": recent_transactions,
            "can_withdraw": user.wallet_balance >= 100,  # Minimum withdrawal amount
            "withdrawal_fee": 5.0
        }
    
    @staticmethod
    async def get_transactions(
        db: AsyncSession,
        user_id: str,
        transaction_type: Optional[str],
        page: int,
        limit: int
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get wallet transactions"""
        # In production, query transactions table
        # For now, return mock data
        
        mock_transactions = [
            {
                "id": f"txn_{i}",
                "type": "credit" if i % 3 == 0 else "debit",
                "amount": 100 + (i * 50),
                "description": ["Order refund", "Wallet recharge", "Order payment"][i % 3],
                "date": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "status": "completed",
                "reference_id": f"ref_{i}",
                "balance_after": 1000 - (i * 50)
            }
            for i in range(100)
        ]
        
        # Filter by type if specified
        if transaction_type and transaction_type != "all":
            mock_transactions = [t for t in mock_transactions if t["type"] == transaction_type]
        
        total = len(mock_transactions)
        
        # Apply pagination
        start = (page - 1) * limit
        end = start + limit
        paginated = mock_transactions[start:end]
        
        return paginated, total
    
    @staticmethod
    async def get_reward_points(
        db: AsyncSession,
        user_id: str
    ) -> Dict[str, Any]:
        """Get reward points information"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return {}
        
        # Calculate points expiring soon (within 30 days)
        points_expiring_soon = 0
        points_expiry_date = None
        
        if user.reward_points > 0:
            # Mock expiring points (20% of total)
            points_expiring_soon = int(user.reward_points * 0.2)
            points_expiry_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        return {
            "total_points": user.reward_points,
            "points_value": user.reward_points * 0.1,  # 10 points = 1 currency unit
            "points_expiring_soon": points_expiring_soon,
            "points_expiry_date": points_expiry_date,
            "tier": "silver" if user.reward_points < 1000 else "gold" if user.reward_points < 5000 else "platinum",
            "next_tier": {
                "name": "gold" if user.reward_points < 1000 else "platinum",
                "points_needed": 1000 - user.reward_points if user.reward_points < 1000 else 5000 - user.reward_points,
                "benefits": ["Free delivery", "Priority support", "Exclusive offers"]
            }
        }
    
    @staticmethod
    async def get_notifications(
        db: AsyncSession,
        user_id: str,
        unread_only: bool,
        page: int,
        limit: int
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get user notifications"""
        # In production, query notifications table
        # For now, return mock data
        
        mock_notifications = [
            {
                "id": f"user_notif_{i}",
                "title": ["Order Status", "Promotion", "System Alert"][i % 3],
                "message": f"Notification message {i}",
                "type": ["order", "promotion", "system"][i % 3],
                "data": {"order_id": f"order_{i}"} if i % 3 == 0 else {},
                "is_read": i % 4 == 0,
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
        user_id: str,
        notification_id: str
    ) -> bool:
        """Mark notification as read"""
        # In production, update notification in database
        logger.info(f"Notification {notification_id} marked as read by user {user_id}")
        return True
    
    @staticmethod
    async def get_favorites(
        db: AsyncSession,
        user_id: str,
        page: int,
        limit: int
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get user's favorite items"""
        # In production, query favorites table
        # For now, return mock data
        
        mock_favorites = [
            {
                "id": f"fav_{i}",
                "item_id": f"item_{i}",
                "item_name": f"Favorite Item {i}",
                "business_name": f"Business {i % 5}",
                "business_id": f"business_{i % 5}",
                "price": 100 + (i * 50),
                "image_url": f"https://example.com/fav_{i}.jpg",
                "added_at": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "is_available": i % 10 != 0  # 1 in 10 is unavailable
            }
            for i in range(30)
        ]
        
        total = len(mock_favorites)
        
        # Apply pagination
        start = (page - 1) * limit
        end = start + limit
        paginated = mock_favorites[start:end]
        
        return paginated, total
    
    @staticmethod
    async def add_to_favorites(
        db: AsyncSession,
        user_id: str,
        item_id: str,
        business_id: str
    ) -> bool:
        """Add item to favorites"""
        # In production, add to favorites table
        logger.info(f"User {user_id} added item {item_id} from business {business_id} to favorites")
        return True
    
    @staticmethod
    async def remove_from_favorites(
        db: AsyncSession,
        user_id: str,
        item_id: str
    ) -> bool:
        """Remove item from favorites"""
        # In production, remove from favorites table
        logger.info(f"User {user_id} removed item {item_id} from favorites")
        return True
    
    @staticmethod
    async def get_user_reviews(
        db: AsyncSession,
        user_id: str,
        page: int,
        limit: int
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get user's reviews"""
        # In production, query reviews from business databases
        # For now, return mock data
        
        mock_reviews = [
            {
                "id": f"review_{i}",
                "order_id": f"order_{i}",
                "business_name": f"Business {i % 5}",
                "business_id": f"business_{i % 5}",
                "item_name": f"Item {i}",
                "rating": 4 + (i % 2),
                "comment": f"Review comment {i}",
                "created_at": (datetime.utcnow() - timedelta(days=i * 2)).isoformat(),
                "helpful_count": i * 3,
                "business_reply": f"Thank you for your feedback!" if i % 3 == 0 else None
            }
            for i in range(20)
        ]
        
        total = len(mock_reviews)
        
        # Apply pagination
        start = (page - 1) * limit
        end = start + limit
        paginated = mock_reviews[start:end]
        
        return paginated, total
    
    @staticmethod
    async def get_order_history(
        db: AsyncSession,
        user_id: str,
        status: Optional[str],
        page: int,
        limit: int
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get user's order history"""
        # In production, query orders from all business databases
        # For now, return mock data
        
        mock_orders = [
            {
                "id": f"order_{i}",
                "order_number": f"ORD202312{i:03d}",
                "business_name": f"Business {i % 5}",
                "business_id": f"business_{i % 5}",
                "business_type": ["restaurant", "grocery", "pharmacy"][i % 3],
                "total_amount": 300 + (i * 100),
                "status": ["delivered", "cancelled", "pending"][i % 3],
                "order_date": (datetime.utcnow() - timedelta(days=i * 2)).isoformat(),
                "delivery_date": (datetime.utcnow() - timedelta(days=i * 2 - 1)).isoformat() if i % 3 == 0 else None,
                "items_count": 1 + (i % 5),
                "delivery_address": f"Address {i}",
                "can_reorder": i % 3 == 0 and i > 0,
                "can_review": i % 3 == 0 and i > 0 and i % 2 == 0
            }
            for i in range(50)
        ]
        
        # Filter by status if specified
        if status:
            mock_orders = [o for o in mock_orders if o["status"] == status]
        
        total = len(mock_orders)
        
        # Apply pagination
        start = (page - 1) * limit
        end = start + limit
        paginated = mock_orders[start:end]
        
        return paginated, total