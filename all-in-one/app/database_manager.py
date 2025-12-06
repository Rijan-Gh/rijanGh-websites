from typing import Dict, Any, Optional
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import asyncpg
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages multiple business databases"""
    
    def __init__(self):
        self._global_engine = create_async_engine(
            settings.GLOBAL_DB_URL,
            echo=False,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True
        )
        self._global_session_factory = async_sessionmaker(
            self._global_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self._business_engines: Dict[str, Any] = {}
        self._business_session_factories: Dict[str, Any] = {}
    
    def get_business_db_url(self, business_id: str) -> str:
        """Generate business database URL"""
        return f"postgresql://{settings.BUSINESS_DB_USER}:{settings.BUSINESS_DB_PASSWORD}@{settings.BUSINESS_DB_HOST}:{settings.BUSINESS_DB_PORT}/{settings.BUSINESS_DB_PREFIX}{business_id}"
    
    async def get_business_session(self, business_id: str) -> AsyncSession:
        """Get session for specific business database"""
        if business_id not in self._business_session_factories:
            # Create new engine for this business
            db_url = self.get_business_db_url(business_id)
            engine = create_async_engine(
                db_url,
                echo=False,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )
            session_factory = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            self._business_session_factories[business_id] = session_factory
            self._business_engines[business_id] = engine
        
        return self._business_session_factories[business_id]()
    
    async def create_business_database(self, business_id: str) -> bool:
        """Create a new database for a business"""
        try:
            # Connect to default postgres database
            conn = await asyncpg.connect(
                user=settings.BUSINESS_DB_USER,
                password=settings.BUSINESS_DB_PASSWORD,
                host=settings.BUSINESS_DB_HOST,
                port=settings.BUSINESS_DB_PORT,
                database='postgres'
            )
            
            # Create database
            db_name = f"{settings.BUSINESS_DB_PREFIX}{business_id}"
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            await conn.close()
            
            logger.info(f"Created database for business: {business_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating business database: {e}")
            return False
    
    async def get_global_session(self) -> AsyncSession:
        """Get session for global database"""
        return self._global_session_factory()
    
    async def close(self):
        """Close all database connections"""
        for engine in self._business_engines.values():
            await engine.dispose()
        await self._global_engine.dispose()

# Global instance
db_manager = DatabaseManager()