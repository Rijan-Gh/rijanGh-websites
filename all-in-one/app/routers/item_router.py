from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

from app.dependencies import get_business_db, get_current_business, get_current_vendor
from app.schemas.item_schema import (
    ItemCreate, ItemUpdate, ItemResponse,
    CategoryCreate, VariantCreate
)
from app.models.business.item_model import Item, Category
from app.services.item_service import ItemService
from app.utils.pagination import PaginationParams, paginate
import logging

router = APIRouter(prefix="/business/{business_id}/items", tags=["Items"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=ItemResponse)
async def create_item(
    business_id: str,
    item_data: ItemCreate,
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_business_db),
    vendor = Depends(get_current_vendor)
):
    """Create new item for business"""
    try:
        item = await ItemService.create_item(db, business_id, item_data, str(vendor.id))
        return item
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create item"
        )

@router.get("/", response_model=List[ItemResponse])
async def get_items(
    business_id: str,
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_business_db),
    category_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    is_vegetarian: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(True),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get items with filters"""
    try:
        items, total = await ItemService.get_items(
            db=db,
            business_id=business_id,
            category_id=category_id,
            search=search,
            min_price=min_price,
            max_price=max_price,
            is_vegetarian=is_vegetarian,
            is_active=is_active,
            page=page,
            limit=limit
        )
        
        return paginate(items, total, page, limit)
        
    except Exception as e:
        logger.error(f"Error getting items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get items"
        )

@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    business_id: str,
    item_id: str,
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_business_db)
):
    """Get item by ID"""
    try:
        item = await ItemService.get_item(db, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get item"
        )

@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    business_id: str,
    item_id: str,
    item_data: ItemUpdate,
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_business_db),
    vendor = Depends(get_current_vendor)
):
    """Update item"""
    try:
        item = await ItemService.update_item(db, item_id, item_data)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update item"
        )

@router.delete("/{item_id}")
async def delete_item(
    business_id: str,
    item_id: str,
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_business_db),
    vendor = Depends(get_current_vendor)
):
    """Delete item (soft delete)"""
    try:
        success = await ItemService.delete_item(db, item_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        return {"message": "Item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete item"
        )

@router.post("/{item_id}/image")
async def upload_item_image(
    business_id: str,
    item_id: str,
    file: UploadFile = File(...),
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_business_db),
    vendor = Depends(get_current_vendor)
):
    """Upload item image"""
    try:
        from app.utils.file_upload import upload_file, validate_image
        
        await validate_image(file)
        
        file_url = await upload_file(
            file,
            folder=f"business/{business_id}/items/{item_id}"
        )
        
        # Update item with image
        await ItemService.update_item_image(db, item_id, file_url)
        
        return {"image_url": file_url}
        
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        )

@router.post("/categories", response_model=dict)
async def create_category(
    business_id: str,
    category_data: CategoryCreate,
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_business_db),
    vendor = Depends(get_current_vendor)
):
    """Create category for business"""
    try:
        category = await ItemService.create_category(db, category_data)
        return category
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category"
        )

@router.get("/categories", response_model=List[dict])
async def get_categories(
    business_id: str,
    business = Depends(get_current_business),
    db: AsyncSession = Depends(get_business_db),
    is_active: Optional[bool] = Query(True)
):
    """Get categories for business"""
    try:
        categories = await ItemService.get_categories(db, is_active)
        return categories
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get categories"
        )