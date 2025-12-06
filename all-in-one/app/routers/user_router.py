from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.dependencies import get_global_db, get_current_customer, get_current_user
from app.models.global.user_model import User
from app.services.user_service import UserService
import logging

router = APIRouter(prefix="/user", tags=["User"])
logger = logging.getLogger(__name__)

@router.get("/profile")
async def get_user_profile(
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db)
):
    """Get user profile"""
    try:
        profile = await UserService.get_user_profile(db, str(user.id))
        return profile
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )

@router.put("/profile")
async def update_user_profile(
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    date_of_birth: Optional[datetime] = None,
    gender: Optional[str] = None,
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db)
):
    """Update user profile"""
    try:
        updated_user = await UserService.update_user_profile(
            db=db,
            user_id=str(user.id),
            full_name=full_name,
            email=email,
            date_of_birth=date_of_birth,
            gender=gender
        )
        return updated_user
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

@router.post("/profile/picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db)
):
    """Upload profile picture"""
    try:
        from app.utils.file_upload import upload_file, validate_image
        
        await validate_image(file)
        
        file_url = await upload_file(
            file,
            folder=f"users/{user.id}/profile"
        )
        
        # Update user profile
        user.profile_picture = file_url
        await db.commit()
        
        return {"profile_picture_url": file_url}
        
    except Exception as e:
        logger.error(f"Error uploading profile picture: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile picture"
        )

@router.get("/addresses")
async def get_user_addresses(
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db)
):
    """Get user addresses"""
    try:
        addresses = await UserService.get_user_addresses(db, str(user.id))
        return addresses
    except Exception as e:
        logger.error(f"Error getting user addresses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get addresses"
        )

@router.post("/addresses")
async def add_user_address(
    address: dict,
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db)
):
    """Add new address"""
    try:
        new_address = await UserService.add_user_address(
            db=db,
            user_id=str(user.id),
            address=address
        )
        return new_address
    except Exception as e:
        logger.error(f"Error adding address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add address"
        )

@router.put("/addresses/{address_id}")
async def update_user_address(
    address_id: str,
    address: dict,
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db)
):
    """Update address"""
    try:
        updated_address = await UserService.update_user_address(
            db=db,
            user_id=str(user.id),
            address_id=address_id,
            address=address
        )
        
        if not updated_address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        
        return updated_address
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update address"
        )

@router.delete("/addresses/{address_id}")
async def delete_user_address(
    address_id: str,
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db)
):
    """Delete address"""
    try:
        success = await UserService.delete_user_address(
            db=db,
            user_id=str(user.id),
            address_id=address_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        
        return {"message": "Address deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete address"
        )

@router.get("/wallet")
async def get_wallet_info(
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db)
):
    """Get wallet information"""
    try:
        wallet_info = await UserService.get_wallet_info(db, str(user.id))
        return wallet_info
    except Exception as e:
        logger.error(f"Error getting wallet info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get wallet info"
        )

@router.get("/transactions")
async def get_transactions(
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db),
    transaction_type: Optional[str] = Query(None, regex="^(all|credit|debit)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get wallet transactions"""
    try:
        transactions, total = await UserService.get_transactions(
            db=db,
            user_id=str(user.id),
            transaction_type=transaction_type,
            page=page,
            limit=limit
        )
        
        from app.utils.pagination import paginate
        return paginate(transactions, total, page, limit)
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transactions"
        )

@router.get("/rewards")
async def get_reward_points(
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db)
):
    """Get reward points information"""
    try:
        rewards = await UserService.get_reward_points(db, str(user.id))
        return rewards
    except Exception as e:
        logger.error(f"Error getting reward points: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get reward points"
        )

@router.get("/notifications")
async def get_user_notifications(
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db),
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get user notifications"""
    try:
        notifications, total = await UserService.get_notifications(
            db=db,
            user_id=str(user.id),
            unread_only=unread_only,
            page=page,
            limit=limit
        )
        
        from app.utils.pagination import paginate
        return paginate(notifications, total, page, limit)
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications"
        )

@router.post("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db)
):
    """Mark notification as read"""
    try:
        success = await UserService.mark_notification_read(
            db=db,
            user_id=str(user.id),
            notification_id=notification_id
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

@router.get("/favorites")
async def get_favorites(
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get user's favorite items"""
    try:
        favorites, total = await UserService.get_favorites(
            db=db,
            user_id=str(user.id),
            page=page,
            limit=limit
        )
        
        from app.utils.pagination import paginate
        return paginate(favorites, total, page, limit)
    except Exception as e:
        logger.error(f"Error getting favorites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get favorites"
        )

@router.post("/favorites/{item_id}")
async def add_to_favorites(
    item_id: str,
    business_id: str,
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db)
):
    """Add item to favorites"""
    try:
        success = await UserService.add_to_favorites(
            db=db,
            user_id=str(user.id),
            item_id=item_id,
            business_id=business_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add to favorites"
            )
        
        return {"message": "Added to favorites"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to favorites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add to favorites"
        )

@router.delete("/favorites/{item_id}")
async def remove_from_favorites(
    item_id: str,
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db)
):
    """Remove item from favorites"""
    try:
        success = await UserService.remove_from_favorites(
            db=db,
            user_id=str(user.id),
            item_id=item_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found in favorites"
            )
        
        return {"message": "Removed from favorites"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from favorites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove from favorites"
        )

@router.get("/reviews")
async def get_user_reviews(
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get user's reviews"""
    try:
        reviews, total = await UserService.get_user_reviews(
            db=db,
            user_id=str(user.id),
            page=page,
            limit=limit
        )
        
        from app.utils.pagination import paginate
        return paginate(reviews, total, page, limit)
    except Exception as e:
        logger.error(f"Error getting user reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get reviews"
        )

@router.get("/order-history")
async def get_order_history(
    user: User = Depends(get_current_customer),
    db: AsyncSession = Depends(get_global_db),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get user's order history"""
    try:
        orders, total = await UserService.get_order_history(
            db=db,
            user_id=str(user.id),
            status=status,
            page=page,
            limit=limit
        )
        
        from app.utils.pagination import paginate
        return paginate(orders, total, page, limit)
    except Exception as e:
        logger.error(f"Error getting order history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order history"
        )