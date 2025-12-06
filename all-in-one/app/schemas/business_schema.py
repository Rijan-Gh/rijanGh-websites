from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import time
from enum import Enum

class BusinessType(str, Enum):
    RESTAURANT = "restaurant"
    GROCERY = "grocery"
    PHARMACY = "pharmacy"
    CLOUD_KITCHEN = "cloud_kitchen"
    HOTEL = "hotel"
    HALL = "hall"
    SHOP = "shop"
    CAFE = "cafe"
    BAKERY = "bakery"
    OTHER = "other"

class BusinessCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    contact_phone: str = Field(..., min_length=10, max_length=15)
    contact_email: Optional[str] = None
    
    # Address
    address: str
    city: str
    state: str
    country: str = "India"
    pincode: str
    latitude: float
    longitude: float
    
    # Business Info
    business_type: BusinessType
    category: str
    subcategories: List[str] = []
    
    # Timing
    opening_time: str = Field(..., regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    closing_time: str = Field(..., regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    working_days: List[int] = Field(default=[0,1,2,3,4,5,6])
    
    # Images
    logo_url: Optional[str] = None
    cover_url: Optional[str] = None
    
    class Config:
        json_encoders = {
            time: lambda v: v.strftime("%H:%M")
        }

class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    working_days: Optional[List[int]] = None
    is_active: Optional[bool] = None

class BusinessResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    contact_phone: str
    contact_email: Optional[str]
    address: str
    city: str
    state: str
    country: str
    pincode: str
    latitude: float
    longitude: float
    business_type: str
    category: str
    subcategories: List[str]
    opening_time: str
    closing_time: str
    working_days: List[int]
    logo_url: Optional[str]
    cover_url: Optional[str]
    is_active: bool
    is_verified: bool
    avg_rating: float
    rating_count: int
    total_orders: int
    created_at: datetime