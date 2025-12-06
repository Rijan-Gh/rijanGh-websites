from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from app.dependencies import get_global_db, get_current_vendor, get_current_business
from app.models.global.user_model import User
from app.models.global.business_model import Business
from app.services.vendor_service import VendorService
from app.utils.pagination import paginate
import logging

router = APIRouter(prefix="/vendor", tags=["Vendor"])
logger = logging.getLogger(__name__)

@router.get("/dashboard")
async def vendor_dashboard(
    vendor: User = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_global_db)
):
    """Get vendor dashboard data"""
    try:
        dashboard_data = await VendorService.get_dashboard_data(
            db=db,
            vendor_id=str(vendor.id)
        )
        return dashboard_data
    except Exception as e:
        logger.error(f"Error getting vendor dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard data"
        )

@router.get("/business")
async def get_vendor_business(
    vendor: User = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_global_db)
):
    """Get vendor's business"""
    try:
        business = await VendorService.get_vendor_business(
            db=db,
            vendor_id=str(vendor.id)
        )
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No business found for this vendor"
            )
        return business
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vendor business: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get business"
        )

@router.get("/orders/summary")
async def get_orders_summary(
    business_id: str,
    period: str = Query("today", regex="^(today|week|month|year|custom)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_global_db)
):
    """Get orders summary for vendor"""
    try:
        summary = await VendorService.get_orders_summary(
            db=db,
            business_id=business_id,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        return summary
    except Exception as e:
        logger.error(f"Error getting orders summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get orders summary"
        )

@router.get("/revenue")
async def get_revenue_analytics(
    business_id: str,
    period: str = Query("daily", regex="^(daily|weekly|monthly|yearly)$"),
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_global_db)
):
    """Get revenue analytics for vendor"""
    try:
        analytics = await VendorService.get_revenue_analytics(
            db=db,
            business_id=business_id,
            period=period
        )
        return analytics
    except Exception as e:
        logger.error(f"Error getting revenue analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get revenue analytics"
        )

@router.get("/top-items")
async def get_top_items(
    business_id: str,
    limit: int = Query(10, ge=1, le=50),
    period: str = Query("week", regex="^(day|week|month|year|all)$"),
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_global_db)
):
    """Get top selling items"""
    try:
        top_items = await VendorService.get_top_items(
            db=db,
            business_id=business_id,
            limit=limit,
            period=period
        )
        return top_items
    except Exception as e:
        logger.error(f"Error getting top items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get top items"
        )

@router.get("/customer-insights")
async def get_customer_insights(
    business_id: str,
    limit: int = Query(10, ge=1, le=100),
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_global_db)
):
    """Get customer insights and analytics"""
    try:
        insights = await VendorService.get_customer_insights(
            db=db,
            business_id=business_id,
            limit=limit
        )
        return insights
    except Exception as e:
        logger.error(f"Error getting customer insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get customer insights"
        )

@router.post("/staff")
async def add_staff_member(
    business_id: str,
    phone: str,
    role: str = "staff",
    permissions: Optional[List[str]] = None,
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_global_db),
    vendor: User = Depends(get_current_vendor)
):
    """Add staff member to business"""
    try:
        staff_member = await VendorService.add_staff_member(
            db=db,
            business_id=business_id,
            vendor_id=str(vendor.id),
            phone=phone,
            role=role,
            permissions=permissions or []
        )
        return staff_member
    except Exception as e:
        logger.error(f"Error adding staff member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/staff")
async def get_staff_members(
    business_id: str,
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_global_db)
):
    """Get all staff members"""
    try:
        staff = await VendorService.get_staff_members(
            db=db,
            business_id=business_id
        )
        return staff
    except Exception as e:
        logger.error(f"Error getting staff members: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get staff members"
        )

@router.delete("/staff/{staff_id}")
async def remove_staff_member(
    business_id: str,
    staff_id: str,
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_global_db),
    vendor: User = Depends(get_current_vendor)
):
    """Remove staff member from business"""
    try:
        success = await VendorService.remove_staff_member(
            db=db,
            business_id=business_id,
            staff_id=staff_id,
            vendor_id=str(vendor.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found"
            )
        
        return {"message": "Staff member removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing staff member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove staff member"
        )

@router.post("/update-settings")
async def update_business_settings(
    business_id: str,
    settings: dict,
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_global_db)
):
    """Update business settings"""
    try:
        updated_settings = await VendorService.update_business_settings(
            db=db,
            business_id=business_id,
            settings=settings
        )
        return updated_settings
    except Exception as e:
        logger.error(f"Error updating business settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings"
        )

@router.get("/notifications")
async def get_vendor_notifications(
    vendor: User = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_global_db),
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get vendor notifications"""
    try:
        notifications, total = await VendorService.get_notifications(
            db=db,
            vendor_id=str(vendor.id),
            unread_only=unread_only,
            page=page,
            limit=limit
        )
        
        return paginate(notifications, total, page, limit)
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications"
        )

@router.post("/notifications/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: str,
    vendor: User = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_global_db)
):
    """Mark notification as read"""
    try:
        success = await VendorService.mark_notification_read(
            db=db,
            notification_id=notification_id,
            vendor_id=str(vendor.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )