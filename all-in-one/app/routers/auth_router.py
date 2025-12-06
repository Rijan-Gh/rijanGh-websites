from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_global_db
from app.schemas.auth_schema import (
    LoginRequest, 
    RegisterRequest, 
    VendorRegisterRequest,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from app.services.auth_service import AuthService
from app.utils.exceptions import AuthenticationError
import logging

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_global_db)
):
    """User login"""
    try:
        user = await AuthService.authenticate_user(data.phone, data.password, db)
        
        # Update device token if provided
        if data.device_token:
            user.device_token = data.device_token
            user.platform = data.platform
            await db.commit()
        
        tokens = await AuthService.create_tokens(user)
        return tokens
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/register", response_model=TokenResponse)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_global_db)
):
    """Register new customer"""
    try:
        user = await AuthService.register_user(data, db)
        tokens = await AuthService.create_tokens(user)
        return tokens
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/register/vendor", response_model=TokenResponse)
async def register_vendor(
    data: VendorRegisterRequest,
    db: AsyncSession = Depends(get_global_db)
):
    """Register new vendor with access key"""
    try:
        result = await AuthService.register_vendor(data, db)
        tokens = await AuthService.create_tokens(result["user"])
        return tokens
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    try:
        new_token = jwt_handler.refresh_access_token(refresh_token)
        return {"access_token": new_token, "token_type": "bearer"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_global_db)
):
    """Send OTP for password reset"""
    from sqlalchemy import select
    from app.core.security import generate_otp
    
    result = await db.execute(
        select(User).where(User.phone == data.phone)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Generate OTP
    otp = generate_otp()
    
    # Store OTP in Redis (expires in 10 minutes)
    from app.dependencies import get_redis
    redis_client = await get_redis().__anext__()
    await redis_client.setex(
        f"reset_otp:{data.phone}",
        600,  # 10 minutes
        otp
    )
    
    # Send OTP via SMS (mock)
    logger.info(f"OTP for {data.phone}: {otp}")
    
    return {"message": "OTP sent to your phone"}

@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_global_db)
):
    """Reset password using OTP"""
    from sqlalchemy import select
    from app.core.security import verify_password
    from jose import jwt
    
    try:
        # Verify token
        payload = jwt.decode(
            data.token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        phone = payload.get("sub")
        
        if not phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
        
        # Get user
        result = await db.execute(
            select(User).where(User.phone == phone)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update password
        user.password_hash = get_password_hash(data.new_password)
        await db.commit()
        
        return {"message": "Password reset successful"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )