from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    PICKED_UP = "picked_up"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    COD = "cod"
    CARD = "card"
    WALLET = "wallet"
    UPI = "upi"
    NETBANKING = "netbanking"

class OrderItem(BaseModel):
    item_id: str
    name: str
    quantity: int = Field(..., gt=0)
    price: float
    variants: Optional[Dict[str, Any]] = None
    special_instructions: Optional[str] = None

class Address(BaseModel):
    street: str
    city: str
    state: str
    country: str = "India"
    pincode: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    landmark: Optional[str] = None
    contact_person: str
    contact_phone: str

class OrderCreate(BaseModel):
    items: List[OrderItem] = Field(..., min_items=1)
    delivery_address: Address
    delivery_instructions: Optional[str] = None
    payment_method: PaymentMethod
    use_wallet: bool = Field(default=False)
    coupon_code: Optional[str] = None
    
    @validator('items')
    def validate_items(cls, v):
        for item in v:
            if item.quantity <= 0:
                raise ValueError("Item quantity must be positive")
        return v

class OrderResponse(BaseModel):
    id: str
    order_number: str
    customer_id: str
    customer_name: str
    customer_phone: str
    status: OrderStatus
    items: List[Dict[str, Any]]
    subtotal: float
    tax_amount: float
    delivery_fee: float
    discount_amount: float
    total_amount: float
    payment_method: PaymentMethod
    payment_status: str
    transaction_id: Optional[str]
    delivery_address: Dict[str, Any]
    delivery_instructions: Optional[str]
    delivery_latitude: Optional[float]
    delivery_longitude: Optional[float]
    delivery_distance_km: float
    order_time: datetime
    confirmed_time: Optional[datetime]
    prepared_time: Optional[datetime]
    picked_up_time: Optional[datetime]
    delivered_time: Optional[datetime]
    estimated_delivery_time: Optional[datetime]
    special_instructions: Optional[str]
    delivery_boy_id: Optional[str]
    delivery_boy_name: Optional[str]
    delivery_boy_phone: Optional[str]
    tracking_url: Optional[str]
    current_location: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    delivery_boy_id: Optional[str] = None
    current_location: Optional[Dict[str, Any]] = None
    special_instructions: Optional[str] = None

class CartItem(BaseModel):
    item_id: str
    quantity: int = Field(..., gt=0)
    variants: Optional[Dict[str, Any]] = None

class CartUpdate(BaseModel):
    items: List[CartItem]