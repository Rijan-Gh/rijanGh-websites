from sqlalchemy import Column, String, DateTime, Boolean, Float, JSON, ForeignKey, Integer, Numeric, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from enum import Enum as PyEnum

class OrderStatus(PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    PICKED_UP = "picked_up"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Customer Info (from global DB)
    customer_id = Column(UUID(as_uuid=True), nullable=False)
    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(20), nullable=False)
    
    # Order Details
    status = Column(String(50), default=OrderStatus.PENDING.value)
    items = Column(JSON, nullable=False)  # List of ordered items
    
    # Pricing
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0.0)
    delivery_fee = Column(Numeric(10, 2), default=0.0)
    discount_amount = Column(Numeric(10, 2), default=0.0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    
    # Payment
    payment_method = Column(String(50), nullable=False)  # cod, card, wallet, upi
    payment_status = Column(String(50), default="pending")  # pending, paid, failed, refunded
    transaction_id = Column(String(255), nullable=True)
    
    # Delivery
    delivery_address = Column(JSON, nullable=False)
    delivery_instructions = Column(Text, nullable=True)
    delivery_latitude = Column(Float, nullable=True)
    delivery_longitude = Column(Float, nullable=True)
    delivery_distance_km = Column(Float, default=0.0)
    
    # Timing
    order_time = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_time = Column(DateTime(timezone=True), nullable=True)
    prepared_time = Column(DateTime(timezone=True), nullable=True)
    picked_up_time = Column(DateTime(timezone=True), nullable=True)
    delivered_time = Column(DateTime(timezone=True), nullable=True)
    estimated_delivery_time = Column(DateTime(timezone=True), nullable=True)
    
    # Special Instructions
    special_instructions = Column(Text, nullable=True)
    
    # Delivery Boy Info
    delivery_boy_id = Column(UUID(as_uuid=True), nullable=True)
    delivery_boy_name = Column(String(255), nullable=True)
    delivery_boy_phone = Column(String(20), nullable=True)
    
    # Tracking
    tracking_url = Column(String(500), nullable=True)
    current_location = Column(JSON, nullable=True)  # {lat: x, lng: y}
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    reviews = relationship("Review", back_populates="order")
    
    def generate_order_number(self):
        """Generate unique order number"""
        import random
        import string
        prefix = "ORD"
        date_part = datetime.utcnow().strftime("%Y%m%d")
        random_part = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}{date_part}{random_part}"

class Cart(Base):
    __tablename__ = "carts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    items = Column(JSON, default=list)
    total_amount = Column(Numeric(10, 2), default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('customer_id', name='unique_customer_cart'),
    )