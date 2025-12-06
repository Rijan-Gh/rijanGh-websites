from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ItemStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = None
    
    category_id: Optional[str] = None
    
    # Pricing
    price: float = Field(..., gt=0)
    compare_at_price: Optional[float] = None
    cost_price: Optional[float] = None
    
    # Inventory
    stock_quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)
    is_track_inventory: bool = Field(default=True)
    
    # Variants
    has_variants: bool = Field(default=False)
    variants: List[Dict[str, Any]] = Field(default=list)
    
    # Attributes
    attributes: Dict[str, Any] = Field(default=dict)
    
    # Dietary Info
    is_vegetarian: bool = Field(default=True)
    is_vegan: bool = Field(default=False)
    contains_allergens: bool = Field(default=False)
    allergens: List[str] = Field(default=list)
    
    # Preparation
    preparation_time: int = Field(default=15, ge=0)  # minutes
    
    class Config:
        from_attributes = True

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    category_id: Optional[str] = None
    price: Optional[float] = None
    compare_at_price: Optional[float] = None
    cost_price: Optional[float] = None
    stock_quantity: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    is_track_inventory: Optional[bool] = None
    is_vegetarian: Optional[bool] = None
    is_vegan: Optional[bool] = None
    contains_allergens: Optional[bool] = None
    allergens: Optional[List[str]] = None
    preparation_time: Optional[int] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None

class ItemResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    sku: Optional[str]
    category_id: Optional[str]
    price: float
    compare_at_price: Optional[float]
    cost_price: Optional[float]
    stock_quantity: int
    low_stock_threshold: int
    is_track_inventory: bool
    has_variants: bool
    variants: List[Dict[str, Any]]
    attributes: Dict[str, Any]
    main_image: Optional[str]
    gallery_images: List[str]
    is_vegetarian: bool
    is_vegan: bool
    contains_allergens: bool
    allergens: List[str]
    preparation_time: int
    is_active: bool
    is_featured: bool
    total_orders: int
    total_revenue: float
    avg_rating: float
    rating_count: int
    created_at: datetime
    updated_at: Optional[datetime]

class VariantCreate(BaseModel):
    name: str
    options: List[Dict[str, Any]] = Field(..., min_items=1)
    price_adjustment: Optional[float] = 0

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)