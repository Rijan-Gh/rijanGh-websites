from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.global.user_model import User
from app.core.security import verify_password, get_password_hash
from app.core.jwt_handler import jwt_handler
from app.schemas.auth_schema import RegisterRequest, VendorRegisterRequest
from app.utils.exceptions import AuthenticationError, BusinessError
import logging

logger = logging.getLogger(__name__)

class AuthService:
    
    @staticmethod
    async def authenticate_user(
        phone: str, 
        password: str, 
        db: AsyncSession
    ) -> User:
        """Authenticate user with phone and password"""
        result = await db.execute(
            select(User).where(User.phone == phone)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationError("Invalid phone or password")
        
        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid phone or password")
        
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")
        
        if user.is_blocked:
            raise AuthenticationError("Account is blocked")
        
        return user
    
    @staticmethod
    async def register_user(
        data: RegisterRequest,
        db: AsyncSession
    ) -> User:
        """Register new user"""
        # Check if phone already exists
        result = await db.execute(
            select(User).where(User.phone == data.phone)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise AuthenticationError("Phone number already registered")
        
        # Check email if provided
        if data.email:
            result = await db.execute(
                select(User).where(User.email == data.email)
            )
            if result.scalar_one_or_none():
                raise AuthenticationError("Email already registered")
        
        # Create user
        user = User(
            phone=data.phone,
            email=data.email,
            password_hash=get_password_hash(data.password),
            full_name=data.full_name,
            role=data.role.value,
            device_token=data.device_token
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"New user registered: {user.phone} ({user.role})")
        return user
    
    @staticmethod
    async def register_vendor(
        data: VendorRegisterRequest,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Register new vendor with access key validation"""
        from app.models.global.access_key_model import AccessKey
        from app.services.business_db_service import BusinessDBService
        
        # Validate access key
        result = await db.execute(
            select(AccessKey).where(
                AccessKey.key == data.access_key,
                AccessKey.is_active == True
            )
        )
        access_key = result.scalar_one_or_none()
        
        if not access_key:
            raise AuthenticationError("Invalid or expired access key")
        
        if access_key.used_count >= access_key.max_businesses:
            raise AuthenticationError("Access key usage limit reached")
        
        # Register user
        user = await AuthService.register_user(
            RegisterRequest(
                phone=data.phone,
                password=data.password,
                email=data.email,
                full_name=data.full_name,
                role="vendor"
            ),
            db
        )
        
        # Create business
        from app.models.global.business_model import Business
        import uuid
        
        business = Business(
            name=data.business_name,
            slug=AuthService._generate_slug(data.business_name),
            owner_id=user.id,
            contact_phone=data.phone,
            contact_email=data.email,
            business_type=access_key.business_type
        )
        
        db.add(business)
        
        # Update access key usage
        access_key.used_count += 1
        await db.commit()
        await db.refresh(business)
        
        # Create business database
        await db_manager.create_business_database(str(business.id))
        
        # Initialize business database
        await BusinessDBService.initialize_business_database(str(business.id), db)
        
        return {
            "user": user,
            "business": business,
            "access_key": access_key
        }
    
    @staticmethod
    def _generate_slug(name: str) -> str:
        """Generate URL slug from business name"""
        import re
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = re.sub(r'^-+|-+$', '', slug)
        return slug
    
    @staticmethod
    async def create_tokens(user: User) -> Dict[str, Any]:
        """Create access and refresh tokens"""
        access_token = jwt_handler.create_access_token({
            "sub": str(user.id),
            "role": user.role
        })
        
        refresh_token = jwt_handler.create_refresh_token(str(user.id))
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": str(user.id),
                "phone": user.phone,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "wallet_balance": user.wallet_balance
            }
        }