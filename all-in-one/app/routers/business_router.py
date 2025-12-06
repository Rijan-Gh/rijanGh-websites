from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json

from app.dependencies import (
    get_global_db, 
    get_current_vendor, 
    get_current_business,
    get_business_db
)
from app.schemas.business_schema import (
    BusinessCreate, 
    BusinessUpdate, 
    BusinessResponse
)
from app.models.global.business_model import Business
from app.models.global.user_model import User
from app.services.business_db_service import BusinessDBService
from app.utils.file_upload import upload_file, validate_image
import logging

router = APIRouter(prefix="/business", tags=["Business Management"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=BusinessResponse)
async def create_business(
    data: BusinessCreate,
    vendor: User = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_global_db)
):
    """Create a new business"""
    from sqlalchemy import select
    
    # Check if vendor already has a business
    result = await db.execute(
        select(Business).where(Business.owner_id == vendor.id)
    )
    existing_business = result.scalar_one_or_none()
    
    if existing_business:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a business"
        )
    
    # Generate slug
    import re
    slug = data.name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = re.sub(r'^-+|-+$', '', slug)
    
    # Check slug uniqueness
    result = await db.execute(
        select(Business).where(Business.slug == slug)
    )
    if result.scalar_one_or_none():
        # Add random string to make unique
        import secrets
        slug = f"{slug}-{secrets.token_hex(4)}"
    
    # Create business
    business = Business(
        **data.dict(),
        slug=slug,
        owner_id=vendor.id,
        contact_phone=vendor.phone,
        contact_email=vendor.email
    )
    
    db.add(business)
    await db.commit()
    await db.refresh(business)
    
    # Create business database
    await db_manager.create_business_database(str(business.id))
    
    # Initialize business database
    await BusinessDBService.initialize_business_database(str(business.id), db)
    
    return business

@router.put("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: str,
    data: BusinessUpdate,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_global_db)
):
    """Update business information"""
    update_data = data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(business, field, value)
    
    await db.commit()
    await db.refresh(business)
    
    return business

@router.post("/{business_id}/logo")
async def upload_logo(
    business_id: str,
    file: UploadFile = File(...),
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_global_db)
):
    """Upload business logo"""
    # Validate image
    await validate_image(file)
    
    # Upload file
    file_url = await upload_file(
        file,
        folder=f"business/{business_id}/logo"
    )
    
    # Update business record
    business.logo_url = file_url
    await db.commit()
    
    return {"logo_url": file_url}

@router.post("/{business_id}/cover")
async def upload_cover(
    business_id: str,
    file: UploadFile = File(...),
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_global_db)
):
    """Upload business cover image"""
    await validate_image(file)
    
    file_url = await upload_file(
        file,
        folder=f"business/{business_id}/cover"
    )
    
    business.cover_url = file_url
    await db.commit()
    
    return {"cover_url": file_url}

@router.get("/{business_id}/stats")
async def get_business_stats(
    business_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_global_db)
):
    """Get business statistics"""
    stats = await BusinessDBService.get_business_stats(business_id)
    return stats

@router.post("/{business_id}/backup")
async def backup_business_data(
    business_id: str,
    business: Business = Depends(get_current_business)
):
    """Create backup of business database"""
    success = await BusinessDBService.backup_business_database(business_id)
    
    if success:
        return {"message": "Backup created successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create backup"
        )

@router.get("/search")
async def search_businesses(
    q: Optional[str] = None,
    city: Optional[str] = None,
    business_type: Optional[str] = None,
    category: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: float = 5.0,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_global_db)
):
    """Search businesses with filters"""
    from sqlalchemy import select, or_, and_
    from app.utils.geo_distance import calculate_distance
    import math
    
    query = select(Business).where(Business.is_active == True)
    
    # Text search
    if q:
        query = query.where(
            or_(
                Business.name.ilike(f"%{q}%"),
                Business.description.ilike(f"%{q}%"),
                Business.category.ilike(f"%{q}%")
            )
        )
    
    # Location filter
    if lat and lng:
        # This is a simplified version - in production, use PostGIS
        businesses = []
        result = await db.execute(query)
        all_businesses = result.scalars().all()
        
        for business in all_businesses:
            distance = calculate_distance(
                lat, lng,
                business.latitude, business.longitude
            )
            if distance <= radius_km:
                businesses.append({
                    **business.__dict__,
                    "distance_km": distance
                })
        
        # Sort by distance
        businesses.sort(key=lambda x: x["distance_km"])
        
        # Paginate
        start = (page - 1) * limit
        end = start + limit
        paginated = businesses[start:end]
        
        return {
            "businesses": paginated,
            "total": len(businesses),
            "page": page,
            "limit": limit,
            "has_more": end < len(businesses)
        }
    
    # Regular pagination
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    businesses = result.scalars().all()
    
    # Get total count
    count_query = select(sqlalchemy.func.count(Business.id)).where(Business.is_active == True)
    if q:
        count_query = count_query.where(
            or_(
                Business.name.ilike(f"%{q}%"),
                Business.description.ilike(f"%{q}%")
            )
        )
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    return {
        "businesses": businesses,
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": (page * limit) < total
    }