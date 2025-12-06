from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database_manager import db_manager
from app.models.global.business_model import Business
from app.models.business.item_model import Item, Category
from app.models.business.order_model import Order, Cart
import logging

logger = logging.getLogger(__name__)

class BusinessDBService:
    """Service for managing business-specific database operations"""
    
    @staticmethod
    async def initialize_business_database(business_id: str, session: AsyncSession) -> bool:
        """Initialize tables in new business database"""
        try:
            # Get business database session
            business_session = await db_manager.get_business_session(business_id)
            
            # Create all tables
            from app.models.business import Base as BusinessBase
            from sqlalchemy.schema import CreateTable
            
            # Create tables
            async with business_session.bind.begin() as conn:
                await conn.run_sync(BusinessBase.metadata.create_all)
            
            # Create default categories
            default_categories = [
                {"name": "Popular", "display_order": 1},
                {"name": "Recommended", "display_order": 2},
                {"name": "Special Offers", "display_order": 3},
            ]
            
            for cat_data in default_categories:
                category = Category(**cat_data)
                business_session.add(category)
            
            await business_session.commit()
            await business_session.close()
            
            logger.info(f"Initialized database for business: {business_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing business database: {e}")
            return False
    
    @staticmethod
    async def get_business_stats(business_id: str) -> Dict[str, Any]:
        """Get business statistics from its database"""
        try:
            session = await db_manager.get_business_session(business_id)
            
            # Get total items
            from sqlalchemy import func, select
            result = await session.execute(select(func.count(Item.id)))
            total_items = result.scalar()
            
            # Get total orders
            result = await session.execute(select(func.count(Order.id)))
            total_orders = result.scalar()
            
            # Get today's orders
            from datetime import datetime, timedelta
            today = datetime.utcnow().date()
            result = await session.execute(
                select(func.count(Order.id)).where(
                    func.date(Order.created_at) == today
                )
            )
            today_orders = result.scalar()
            
            # Get revenue
            result = await session.execute(select(func.sum(Order.total_amount)))
            total_revenue = result.scalar() or 0
            
            await session.close()
            
            return {
                "total_items": total_items,
                "total_orders": total_orders,
                "today_orders": today_orders,
                "total_revenue": float(total_revenue),
            }
            
        except Exception as e:
            logger.error(f"Error getting business stats: {e}")
            return {}
    
    @staticmethod
    async def backup_business_database(business_id: str) -> bool:
        """Create backup of business database"""
        try:
            import subprocess
            import os
            from datetime import datetime
            
            # Create backup directory
            backup_dir = "backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            db_name = f"{settings.BUSINESS_DB_PREFIX}{business_id}"
            backup_file = f"{backup_dir}/{db_name}_{timestamp}.sql"
            
            # Create backup using pg_dump
            cmd = [
                "pg_dump",
                f"--dbname=postgresql://{settings.BUSINESS_DB_USER}:{settings.BUSINESS_DB_PASSWORD}@{settings.BUSINESS_DB_HOST}:{settings.BUSINESS_DB_PORT}/{db_name}",
                "-F", "c",  # Custom format
                "-f", backup_file
            ]
            
            subprocess.run(cmd, check=True)
            
            logger.info(f"Created backup for business {business_id}: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False