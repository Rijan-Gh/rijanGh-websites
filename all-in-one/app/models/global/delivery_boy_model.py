from sqlalchemy import Column, String, DateTime, Boolean, Float, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

class DeliveryBoy(Base):
    __tablename__ = "delivery_boys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Personal Info
    vehicle_type = Column(String(50), nullable=False)  # bike, car, scooter, walk
    vehicle_number = Column(String(50), nullable=True)
    license_number = Column(String(100), nullable=True)
    
    # Documents
    license_image = Column(String(500), nullable=True)
    rc_image = Column(String(500), nullable=True)
    insurance_image = Column(String(500), nullable=True)
    
    # Current Status
    current_status = Column(String(50), default="offline")  # offline, available, busy
    current_location_lat = Column(Float, nullable=True)
    current_location_lng = Column(Float, nullable=True)
    
    # Availability
    is_available = Column(Boolean, default=False)
    working_hours = Column(JSON, default={
        "start": "09:00",
        "end": "21:00"
    })
    
    # Stats
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    cancelled_deliveries = Column(Integer, default=0)
    total_earnings = Column(Float, default=0.0)
    avg_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # Payment
    wallet_balance = Column(Float, default=0.0)
    pending_balance = Column(Float, default=0.0)
    
    # Settings
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="delivery_profile")
    deliveries = relationship("DeliveryAssignment", back_populates="delivery_boy")
    
    def __repr__(self):
        return f"<DeliveryBoy {self.user_id}>"