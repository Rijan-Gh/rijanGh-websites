from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DeliveryStatus(str, Enum):
    OFFLINE = "offline"
    AVAILABLE = "available"
    BUSY = "busy"
    ON_BREAK = "on_break"

class VehicleType(str, Enum):
    BIKE = "bike"
    SCOOTER = "scooter"
    CAR = "car"
    CYCLE = "cycle"
    WALK = "walk"

class DeliveryBoyRegister(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=6)
    full_name: str
    email: Optional[str] = None
    vehicle_type: VehicleType
    vehicle_number: Optional[str] = None
    license_number: str
    
    @validator('vehicle_number')
    def validate_vehicle_number(cls, v, values):
        vehicle_type = values.get('vehicle_type')
        if vehicle_type in [VehicleType.BIKE, VehicleType.SCOOTER, VehicleType.CAR] and not v:
            raise ValueError(f"Vehicle number is required for {vehicle_type}")
        return v

class DeliveryBoyProfile(BaseModel):
    id: str
    user_id: str
    phone: str
    full_name: str
    email: Optional[str]
    vehicle_type: str
    vehicle_number: Optional[str]
    license_number: str
    current_status: str
    is_available: bool
    is_verified: bool
    total_deliveries: int
    successful_deliveries: int
    cancelled_deliveries: int
    total_earnings: float
    wallet_balance: float
    avg_rating: float
    rating_count: int
    current_location: Optional[Dict[str, float]]
    created_at: datetime

class AvailableOrder(BaseModel):
    order_id: str
    order_number: str
    business_name: str
    business_address: str
    customer_name: str
    customer_address: str
    total_amount: float
    delivery_fee: float
    distance_km: float
    pickup_location: Dict[str, float]
    delivery_location: Dict[str, float]
    estimated_pickup_time: datetime
    estimated_delivery_time: datetime
    items_count: int
    priority: str

class DeliveryAssignment(BaseModel):
    order_id: str
    delivery_boy_id: str
    assigned_time: datetime
    status: str
    pickup_location: Dict[str, float]
    delivery_location: Dict[str, float]
    customer_phone: str
    customer_name: str
    business_phone: str

class DeliveryUpdate(BaseModel):
    status: Optional[str] = None
    current_location: Optional[Dict[str, float]] = None
    notes: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["accepted", "picked_up", "on_the_way", "arrived", "delivered", "cancelled"]
        if v and v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v

class DeliveryEarnings(BaseModel):
    period: str
    total_earnings: float
    wallet_balance: float
    pending_balance: float
    completed_deliveries: int
    cancelled_deliveries: int
    earnings_breakdown: List[Dict[str, Any]]
    top_earning_days: List[Dict[str, Any]]

class DeliveryStats(BaseModel):
    today: Dict[str, Any]
    this_week: Dict[str, Any]
    this_month: Dict[str, Any]
    all_time: Dict[str, Any]
    performance_metrics: Dict[str, float]
    ratings_summary: Dict[str, Any]

class LocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = Field(None, ge=0)
    speed: Optional[float] = Field(None, ge=0)
    bearing: Optional[float] = Field(None, ge=0, le=360)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DeliveryProof(BaseModel):
    order_id: str
    proof_type: str = Field(..., regex="^(photo|signature|otp)$")
    proof_data: str  # Base64 encoded image or OTP code
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RouteOptimizationRequest(BaseModel):
    pickup_location: Dict[str, float]
    delivery_locations: List[Dict[str, float]]
    constraints: Optional[Dict[str, Any]] = None
    
    @validator('delivery_locations')
    def validate_delivery_locations(cls, v):
        if len(v) < 1:
            raise ValueError("At least one delivery location is required")
        if len(v) > 10:
            raise ValueError("Maximum 10 delivery locations allowed")
        return v

class RouteOptimizationResponse(BaseModel):
    optimized_route: List[Dict[str, Any]]
    total_distance_km: float
    estimated_time_minutes: float
    fuel_estimate: Optional[float] = None
    traffic_conditions: Optional[Dict[str, Any]] = None