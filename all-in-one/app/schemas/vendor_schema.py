from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class VendorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class VendorBusinessResponse(BaseModel):
    id: str
    name: str
    business_type: str
    is_verified: bool
    is_active: bool
    total_orders: int
    total_revenue: float
    avg_rating: float
    created_at: datetime

class VendorDashboard(BaseModel):
    business: VendorBusinessResponse
    today_stats: Dict[str, Any]
    week_stats: Dict[str, Any]
    month_stats: Dict[str, Any]
    recent_orders: List[Dict[str, Any]]
    top_items: List[Dict[str, Any]]
    low_stock_items: List[Dict[str, Any]]

class OrderSummary(BaseModel):
    total_orders: int
    completed_orders: int
    pending_orders: int
    cancelled_orders: int
    total_revenue: float
    avg_order_value: float
    peak_hours: List[Dict[str, Any]]

class RevenueAnalytics(BaseModel):
    period: str
    data: List[Dict[str, Any]]
    total_revenue: float
    growth_rate: float
    comparison: Dict[str, Any]

class TopItem(BaseModel):
    item_id: str
    name: str
    category: str
    total_quantity: int
    total_revenue: float
    avg_rating: float

class CustomerInsight(BaseModel):
    customer_id: str
    customer_name: str
    total_orders: int
    total_spent: float
    last_order_date: datetime
    avg_order_value: float
    favorite_items: List[str]

class StaffMemberCreate(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)
    role: str = Field(default="staff", regex="^(admin|manager|staff|chef|delivery)$")
    permissions: List[str] = Field(default=["order.view"])

class StaffMemberResponse(BaseModel):
    id: str
    user_id: str
    phone: str
    full_name: Optional[str]
    role: str
    permissions: List[str]
    is_active: bool
    created_at: datetime

class BusinessSettingsUpdate(BaseModel):
    auto_accept_orders: Optional[bool] = None
    preparation_time: Optional[int] = Field(None, ge=5, le=120)
    min_order_amount: Optional[float] = Field(None, ge=0)
    delivery_radius_km: Optional[float] = Field(None, ge=0.1, le=50)
    is_open: Optional[bool] = None
    holiday_mode: Optional[bool] = None
    holiday_message: Optional[str] = None

    @validator('preparation_time')
    def validate_preparation_time(cls, v):
        if v is not None and v < 5:
            raise ValueError("Preparation time must be at least 5 minutes")
        return v

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    type: str
    data: Optional[Dict[str, Any]]
    is_read: bool
    created_at: datetime

class InventoryAlert(BaseModel):
    item_id: str
    item_name: str
    current_stock: int
    threshold: int
    status: str

class VendorAnalyticsRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metrics: List[str] = Field(default=["revenue", "orders", "customers"])
    group_by: str = Field(default="day", regex="^(hour|day|week|month)$")

class VendorAnalyticsResponse(BaseModel):
    period: Dict[str, datetime]
    metrics: Dict[str, Any]
    trends: Dict[str, Any]
    comparisons: Dict[str, Any]
    recommendations: List[str]