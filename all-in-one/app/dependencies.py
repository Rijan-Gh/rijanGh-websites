from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.database_manager import db_manager
from app.core.auth import verify_token, get_current_user
from app.models.global.user_model import User
from app.models.global.business_model import Business
from app.models.global.access_key_model import AccessKey
import redis.asyncio as redis
from app.config import settings

# Redis connection
async def get_redis() -> redis.Redis:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield redis_client
    finally:
        await redis_client.close()

# Database dependencies
async def get_global_db() -> AsyncSession:
    """Dependency for global database session"""
    async with db_manager.get_global_session() as session:
        yield session

async def get_business_db(business_id: str) -> AsyncSession:
    """Dependency for business-specific database session"""
    async with db_manager.get_business_session(business_id) as session:
        yield session

# Auth dependencies with role checking
async def get_current_customer(
    token: str = Depends(verify_token),
    db: AsyncSession = Depends(get_global_db)
) -> User:
    """Get current customer user"""
    user = await get_current_user(token, db)
    if user.role != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized as customer"
        )
    return user

async def get_current_vendor(
    token: str = Depends(verify_token),
    db: AsyncSession = Depends(get_global_db)
) -> User:
    """Get current vendor user"""
    user = await get_current_user(token, db)
    if user.role != "vendor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized as vendor"
        )
    return user

async def get_current_delivery_boy(
    token: str = Depends(verify_token),
    db: AsyncSession = Depends(get_global_db)
) -> User:
    """Get current delivery boy"""
    user = await get_current_user(token, db)
    if user.role != "delivery":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized as delivery boy"
        )
    return user

async def get_current_admin(
    token: str = Depends(verify_token),
    db: AsyncSession = Depends(get_global_db)
) -> User:
    """Get current admin user"""
    user = await get_current_user(token, db)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized as admin"
        )
    return user

# Business context dependency
async def get_current_business(
    business_id: str,
    vendor: User = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_global_db)
) -> Business:
    """Verify vendor owns this business"""
    from sqlalchemy import select
    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.owner_id == vendor.id
        )
    )
    business = result.scalar_one_or_none()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found or access denied"
        )
    
    return business