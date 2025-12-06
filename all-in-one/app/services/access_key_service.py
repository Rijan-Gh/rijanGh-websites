from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta
import logging

from app.models.global.access_key_model import AccessKey
from app.models.global.user_model import User
from app.core.security import generate_access_key
import uuid

logger = logging.getLogger(__name__)

class AccessKeyService:
    
    @staticmethod
    async def generate_access_key(
        db: AsyncSession,
        admin_id: str,
        name: str,
        business_type: str,
        max_businesses: int = 1,
        valid_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate new access key"""
        # Generate unique key
        key = generate_access_key()
        
        # Calculate validity
        valid_from = datetime.utcnow()
        valid_until = None
        if valid_days:
            valid_until = valid_from + timedelta(days=valid_days)
        
        # Create access key
        access_key = AccessKey(
            key=key,
            name=name,
            business_type=business_type,
            max_businesses=max_businesses,
            used_count=0,
            is_active=True,
            valid_from=valid_from,
            valid_until=valid_until,
            created_by=admin_id
        )
        
        db.add(access_key)
        await db.commit()
        await db.refresh(access_key)
        
        logger.info(f"Generated access key: {key} for {business_type}")
        
        return {
            "id": str(access_key.id),
            "key": key,
            "name": name,
            "business_type": business_type,
            "max_businesses": max_businesses,
            "valid_from": valid_from.isoformat(),
            "valid_until": valid_until.isoformat() if valid_until else None,
            "is_active": True,
            "created_at": access_key.created_at.isoformat()
        }
    
    @staticmethod
    async def validate_access_key(
        db: AsyncSession,
        key: str,
        business_type: Optional[str] = None
    ) -> Optional[AccessKey]:
        """Validate access key"""
        query = select(AccessKey).where(
            and_(
                AccessKey.key == key,
                AccessKey.is_active == True
            )
        )
        
        if business_type:
            query = query.where(AccessKey.business_type == business_type)
        
        result = await db.execute(query)
        access_key = result.scalar_one_or_none()
        
        if not access_key:
            return None
        
        # Check validity period
        now = datetime.utcnow()
        if access_key.valid_until and access_key.valid_until < now:
            logger.warning(f"Access key {key} has expired")
            return None
        
        # Check usage limit
        if access_key.used_count >= access_key.max_businesses:
            logger.warning(f"Access key {key} usage limit reached")
            return None
        
        return access_key
    
    @staticmethod
    async def use_access_key(
        db: AsyncSession,
        key_id: str
    ) -> bool:
        """Increment access key usage count"""
        result = await db.execute(
            select(AccessKey).where(AccessKey.id == key_id)
        )
        access_key = result.scalar_one_or_none()
        
        if not access_key:
            return False
        
        # Check if can be used
        if access_key.used_count >= access_key.max_businesses:
            return False
        
        # Increment usage count
        access_key.used_count += 1
        
        # Deactivate if reached limit
        if access_key.used_count >= access_key.max_businesses:
            access_key.is_active = False
        
        await db.commit()
        
        logger.info(f"Access key {access_key.key} used. Count: {access_key.used_count}/{access_key.max_businesses}")
        return True
    
    @staticmethod
    async def get_access_key_stats(
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get access key statistics"""
        # Total access keys
        result = await db.execute(select(func.count(AccessKey.id)))
        total_keys = result.scalar()
        
        # Active keys
        result = await db.execute(
            select(func.count(AccessKey.id)).where(AccessKey.is_active == True)
        )
        active_keys = result.scalar()
        
        # Used keys
        result = await db.execute(
            select(func.count(AccessKey.id)).where(AccessKey.used_count > 0)
        )
        used_keys = result.scalar()
        
        # Expired keys
        result = await db.execute(
            select(func.count(AccessKey.id)).where(
                and_(
                    AccessKey.valid_until.isnot(None),
                    AccessKey.valid_until < datetime.utcnow()
                )
            )
        )
        expired_keys = result.scalar()
        
        # Usage by business type
        result = await db.execute(
            select(
                AccessKey.business_type,
                func.count(AccessKey.id).label('count'),
                func.sum(AccessKey.used_count).label('total_used')
            )
            .group_by(AccessKey.business_type)
        )
        usage_by_type = result.fetchall()
        
        return {
            "total_keys": total_keys,
            "active_keys": active_keys,
            "used_keys": used_keys,
            "expired_keys": expired_keys,
            "usage_by_type": [
                {
                    "business_type": row[0],
                    "total_keys": row[1],
                    "total_used": row[2],
                    "usage_rate": round((row[2] / (row[1] * 10)) * 100, 2) if row[1] > 0 else 0  # Assuming max_businesses=10 average
                }
                for row in usage_by_type
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def get_access_key_details(
        db: AsyncSession,
        key_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get access key details with usage information"""
        result = await db.execute(
            select(AccessKey, User)
            .join(User, AccessKey.created_by == User.id)
            .where(AccessKey.id == key_id)
        )
        
        row = result.first()
        if not row:
            return None
        
        access_key, creator = row
        
        # Get businesses using this key
        from app.models.global.business_model import Business
        result = await db.execute(
            select(Business)
            .where(Business.access_key_id == key_id)
        )
        businesses = result.scalars().all()
        
        return {
            "id": str(access_key.id),
            "key": access_key.key,
            "name": access_key.name,
            "description": access_key.description,
            "business_type": access_key.business_type,
            "max_businesses": access_key.max_businesses,
            "used_count": access_key.used_count,
            "is_active": access_key.is_active,
            "valid_from": access_key.valid_from.isoformat(),
            "valid_until": access_key.valid_until.isoformat() if access_key.valid_until else None,
            "created_by": {
                "id": str(creator.id),
                "name": creator.full_name,
                "email": creator.email
            },
            "created_at": access_key.created_at.isoformat(),
            "updated_at": access_key.updated_at.isoformat() if access_key.updated_at else None,
            "businesses": [
                {
                    "id": str(business.id),
                    "name": business.name,
                    "business_type": business.business_type,
                    "owner_id": str(business.owner_id),
                    "created_at": business.created_at.isoformat()
                }
                for business in businesses
            ],
            "usage_percentage": round((access_key.used_count / access_key.max_businesses) * 100, 2) if access_key.max_businesses > 0 else 0,
            "is_expired": access_key.valid_until and access_key.valid_until < datetime.utcnow()
        }
    
    @staticmethod
    async def update_access_key(
        db: AsyncSession,
        key_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        max_businesses: Optional[int] = None,
        valid_until: Optional[datetime] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """Update access key"""
        result = await db.execute(
            select(AccessKey).where(AccessKey.id == key_id)
        )
        access_key = result.scalar_one_or_none()
        
        if not access_key:
            return None
        
        # Update fields
        if name is not None:
            access_key.name = name
        
        if description is not None:
            access_key.description = description
        
        if max_businesses is not None:
            if max_businesses < access_key.used_count:
                raise Exception("Cannot set max_businesses less than current usage")
            access_key.max_businesses = max_businesses
        
        if valid_until is not None:
            access_key.valid_until = valid_until
        
        if is_active is not None:
            access_key.is_active = is_active
        
        await db.commit()
        await db.refresh(access_key)
        
        return {
            "id": str(access_key.id),
            "key": access_key.key,
            "name": access_key.name,
            "is_active": access_key.is_active,
            "updated_at": access_key.updated_at.isoformat() if access_key.updated_at else None
        }
    
    @staticmethod
    async def revoke_access_key(
        db: AsyncSession,
        key_id: str
    ) -> bool:
        """Revoke (deactivate) access key"""
        result = await db.execute(
            select(AccessKey).where(AccessKey.id == key_id)
        )
        access_key = result.scalar_one_or_none()
        
        if not access_key:
            return False
        
        access_key.is_active = False
        await db.commit()
        
        logger.info(f"Access key {access_key.key} revoked")
        return True
    
    @staticmethod
    async def search_access_keys(
        db: AsyncSession,
        search: Optional[str] = None,
        business_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """Search access keys"""
        query = select(AccessKey)
        
        if search:
            query = query.where(
                or_(
                    AccessKey.key.ilike(f"%{search}%"),
                    AccessKey.name.ilike(f"%{search}%"),
                    AccessKey.description.ilike(f"%{search}%")
                )
            )
        
        if business_type:
            query = query.where(AccessKey.business_type == business_type)
        
        if is_active is not None:
            query = query.where(AccessKey.is_active == is_active)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.order_by(AccessKey.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await db.execute(query)
        access_keys = result.scalars().all()
        
        keys_list = []
        for key in access_keys:
            keys_list.append({
                "id": str(key.id),
                "key": key.key,
                "name": key.name,
                "business_type": key.business_type,
                "max_businesses": key.max_businesses,
                "used_count": key.used_count,
                "is_active": key.is_active,
                "valid_from": key.valid_from.isoformat(),
                "valid_until": key.valid_until.isoformat() if key.valid_until else None,
                "created_at": key.created_at.isoformat()
            })
        
        return keys_list, total