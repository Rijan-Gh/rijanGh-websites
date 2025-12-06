from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models.business.item_model import Item, Category
from app.schemas.item_schema import ItemCreate, ItemUpdate
import logging

logger = logging.getLogger(__name__)

class ItemService:
    
    @staticmethod
    async def create_item(
        db: AsyncSession,
        business_id: str,
        item_data: ItemCreate,
        created_by: str
    ) -> Item:
        """Create new item"""
        item = Item(
            **item_data.dict(),
            created_by=created_by,
            business_id=business_id
        )
        
        db.add(item)
        await db.commit()
        await db.refresh(item)
        
        logger.info(f"Created item: {item.name} for business {business_id}")
        return item
    
    @staticmethod
    async def get_item(db: AsyncSession, item_id: str) -> Optional[Item]:
        """Get item by ID"""
        result = await db.execute(
            select(Item).where(Item.id == item_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_items(
        db: AsyncSession,
        business_id: str,
        category_id: Optional[str] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        is_vegetarian: Optional[bool] = None,
        is_active: Optional[bool] = True,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Item], int]:
        """Get items with filters and pagination"""
        query = select(Item).where(Item.business_id == business_id)
        
        if category_id:
            query = query.where(Item.category_id == category_id)
        
        if search:
            query = query.where(
                or_(
                    Item.name.ilike(f"%{search}%"),
                    Item.description.ilike(f"%{search}%")
                )
            )
        
        if min_price is not None:
            query = query.where(Item.price >= min_price)
        
        if max_price is not None:
            query = query.where(Item.price <= max_price)
        
        if is_vegetarian is not None:
            query = query.where(Item.is_vegetarian == is_vegetarian)
        
        if is_active is not None:
            query = query.where(Item.is_active == is_active)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.order_by(Item.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        return items, total
    
    @staticmethod
    async def update_item(
        db: AsyncSession,
        item_id: str,
        item_data: ItemUpdate
    ) -> Optional[Item]:
        """Update item"""
        item = await ItemService.get_item(db, item_id)
        if not item:
            return None
        
        update_data = item_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        
        await db.commit()
        await db.refresh(item)
        
        logger.info(f"Updated item: {item_id}")
        return item
    
    @staticmethod
    async def delete_item(db: AsyncSession, item_id: str) -> bool:
        """Soft delete item"""
        item = await ItemService.get_item(db, item_id)
        if not item:
            return False
        
        item.is_active = False
        await db.commit()
        
        logger.info(f"Deleted item: {item_id}")
        return True
    
    @staticmethod
    async def update_item_image(
        db: AsyncSession,
        item_id: str,
        image_url: str
    ) -> bool:
        """Update item image"""
        item = await ItemService.get_item(db, item_id)
        if not item:
            return False
        
        if not item.main_image:
            item.main_image = image_url
        else:
            # Add to gallery
            if not item.gallery_images:
                item.gallery_images = []
            item.gallery_images.append(image_url)
        
        await db.commit()
        return True
    
    @staticmethod
    async def create_category(
        db: AsyncSession,
        category_data: Dict[str, Any]
    ) -> Category:
        """Create category"""
        category = Category(**category_data)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category
    
    @staticmethod
    async def get_categories(
        db: AsyncSession,
        is_active: Optional[bool] = True
    ) -> List[Category]:
        """Get categories"""
        query = select(Category)
        if is_active is not None:
            query = query.where(Category.is_active == is_active)
        
        query = query.order_by(Category.display_order, Category.name)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_stock(
        db: AsyncSession,
        item_id: str,
        quantity_change: int
    ) -> bool:
        """Update item stock quantity"""
        from sqlalchemy import update
        
        await db.execute(
            update(Item)
            .where(Item.id == item_id)
            .values(stock_quantity=Item.stock_quantity + quantity_change)
        )
        await db.commit()
        
        # Check low stock
        item = await ItemService.get_item(db, item_id)
        if item and item.stock_quantity <= item.low_stock_threshold:
            logger.warning(f"Low stock alert for item: {item.name}")
        
        return True