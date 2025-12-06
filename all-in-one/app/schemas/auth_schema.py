from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    CUSTOMER = "customer"
    VENDOR = "vendor"
    DELIVERY = "delivery"
    ADMIN = "admin"

class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=6)
    device_token: Optional[str] = None
    platform: Optional[str] = None

class RegisterRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=6)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER
    device_token: Optional[str] = None
    
    @validator('role')
    def validate_role(cls, v):
        if v == UserRole.VENDOR:
            raise ValueError("Vendor registration requires access key")
        if v == UserRole.ADMIN:
            raise ValueError("Admin registration not allowed")
        return v

class VendorRegisterRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=6)
    email: Optional[EmailStr] = None
    full_name: str
    business_name: str
    access_key: str = Field(..., min_length=32, max_length=64)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: datetime
    iat: datetime
    type: str
    role: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    phone: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str