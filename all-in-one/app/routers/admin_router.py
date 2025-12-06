from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from app.dependencies import get_global_db, get_current_admin
from app.models.global.user_model import User
from app.models.global.business_model import Business
from app.models.global.access_key_model import AccessKey
from app.models.global.delivery_boy_model import DeliveryBoy
from app.services.admin_service import AdminService
from app.utils.pagination import paginate
import logging

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)

@router.get("/dashboard")
async def get_admin_dashboard(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_global_db)
):
    """Get admin dashboard statistics"""
    try:
        stats = await AdminService.get_dashboard_stats(db)
        return stats
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard stats"
        )

@router.get("/businesses")
async def get_all_businesses(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_global_db),
    status: Optional[str] = Query(None),
    business_type: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get all businesses"""
    try:
        businesses, total = await AdminService.get_businesses(
            db=db,
            status=status,
            business_type=business_type,
            city=city,
            page=page,
            limit=limit
        )
        
        return paginate(businesses, total, page, limit)
        
    except Exception as e:
        logger.error(f"Error getting businesses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get businesses"
        )

@router.post("/business/{business_id}/verify")
async def verify_business(
    business_id: str,
    verify: bool,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_global_db)
):
    """Verify or unverify business"""
    try:
        success = await AdminService.verify_business(
            db=db,
            business_id=business_id,
            verify=verify
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )
        
        action = "verified" if verify else "unverified"
        return {"message": f"Business {action} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying business: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify business"
        )

@router.post("/business/{business_id}/block")
async def block_business(
    business_id: str,
    block: bool,
    reason: Optional[str] = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_global_db)
):
    """Block or unblock business"""
    try:
        success = await AdminService.block_business(
            db=db,
            business_id=business_id,
            block=block,
            reason=reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )
        
        action = "blocked" if block else "unblocked"
        return {"message": f"Business {action} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error blocking business: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to block business"
        )

@router.get("/access-keys")
async def get_access_keys(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_global_db),
    is_active: Optional[bool] = Query(None),
    business_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get all access keys"""
    try:
        keys, total = await AdminService.get_access_keys(
            db=db,
            is_active=is_active,
            business_type=business_type,
            page=page,
            limit=limit
        )
        
        return paginate(keys, total, page, limit)
        
    except Exception as e:
        logger.error(f"Error getting access keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get access keys"
        )

@router.post("/access-keys")
async def create_access_key(
    name: str,
    business_type: str,
    max_businesses: int = 1,
    valid_until: Optional[datetime] = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_global_db)
):
    """Create new access key"""
    try:
        access_key = await AdminService.create_access_key(
            db=db,
            name=name,
            business_type=business_type,
            max_businesses=max_businesses,
            valid_until=valid_until,
            created_by=str(admin.id)
        )
        
        return {
            "message": "Access key created",
            "access_key": access_key.key,
            "details": access_key
        }
        
    except Exception as e:
        logger.error(f"Error creating access key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create access key"
        )

@router.post("/access-keys/{key_id}/deactivate")
async def deactivate_access_key(
    key_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_global_db)
):
    """Deactivate access key"""
    try:
        success = await AdminService.deactivate_access_key(db, key_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Access key not found"
            )
        
        return {"message": "Access key deactivated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating access key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate access key"
        )

@router.get("/users")
async def get_all_users(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_global_db),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    city: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get all users"""
    try:
        users, total = await AdminService.get_users(
            db=db,
            role=role,
            is_active=is_active,
            city=city,
            page=page,
            limit=limit
        )
        
        return paginate(users, total, page, limit)
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users"
        )

@router.post("/users/{user_id}/block")
async def block_user(
    user_id: str,
    block: bool,
    reason: Optional[str] = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_global_db)
):
    """Block or unblock user"""
    try:
        success = await AdminService.block_user(
            db=db,
            user_id=user_id,
            block=block,
            reason=reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        action = "blocked" if block else "unblocked"
        return {"message": f"User {action} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error blocking user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to block user"
        )

@router.get("/delivery-boys")
async def get_delivery_boys(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_global_db),
    is_verified: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(None),
    city: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get all delivery boys"""
    try:
        delivery_boys, total = await AdminService.get_delivery_boys(
            db=db,
            is_verified=is_verified,
            is_active=is_active,
            city=city,
            page=page,
            limit=limit
        )
        
        return paginate(delivery_boys, total, page, limit)
        
    except Exception as e:
        logger.error(f"Error getting delivery boys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get delivery boys"
        )

@router.post("/delivery-boys/{delivery_boy_id}/verify")
async def verify_delivery_boy(
    delivery_boy_id: str,
    verify: bool,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_global_db)
):
    """Verify delivery boy"""
    try:
        success = await AdminService.verify_delivery_boy(
            db=db,
            delivery_boy_id=delivery_boy_id,
            verify=verify
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Delivery boy not found"
            )
        
        action = "verified" if verify else "unverified"
        return {"message": f"Delivery boy {action} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying delivery boy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify delivery boy"
        )

@router.get("/analytics/revenue")
async def get_revenue_analytics(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_global_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    period: str = Query("daily", regex="^(daily|weekly|monthly|yearly)$")
):
    """Get revenue analytics"""
    try:
        analytics = await AdminService.get_revenue_analytics(
            db=db,
            start_date=start_date,
            end_date=end_date,
            period=period
        )
        return analytics
    except Exception as e:
        logger.error(f"Error getting revenue analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get revenue analytics"
        )

@router.get("/analytics/orders")
async def get_order_analytics(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_global_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    business_type: Optional[str] = Query(None)
):
    """Get order analytics"""
    try:
        analytics = await AdminService.get_order_analytics(
            db=db,
            start_date=start_date,
            end_date=end_date,
            business_type=business_type
        )
        return analytics
    except Exception as e:
        logger.error(f"Error getting order analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order analytics"
        )

@router.get("/analytics/users")
async def get_user_analytics(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_global_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get user growth analytics"""
    try:
        analytics = await AdminService.get_user_analytics(
            db=db,
            start_date=start_date,
            end_date=end_date
        )
        return analytics
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user analytics"
        )