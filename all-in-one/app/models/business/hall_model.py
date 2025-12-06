from sqlalchemy import Column, String, DateTime, Boolean, Float, JSON, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.models.business import Base

class Hall(Base):
    __tablename__ = "halls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Hall Info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    capacity = Column(Integer, nullable=False)  # Number of people
    area_sqft = Column(Float, nullable=True)
    
    # Amenities
    amenities = Column(JSON, default=list)  # ["AC", "Sound System", "Projector", etc.]
    
    # Pricing
    price_per_hour = Column(Float, nullable=False)
    price_per_day = Column(Float, nullable=True)
    min_booking_hours = Column(Integer, default=2)
    max_booking_hours = Column(Integer, default=12)
    
    # Images
    main_image = Column(String(500), nullable=True)
    gallery_images = Column(JSON, default=list)
    
    # Availability
    is_available = Column(Boolean, default=True)
    booking_slots = Column(JSON, default=dict)  # {"2024-01-01": ["09:00-12:00", "14:00-17:00"]}
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Hall {self.name} (Capacity: {self.capacity})>"

class HallBooking(Base):
    __tablename__ = "hall_bookings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hall_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Booking Details
    booking_date = Column(DateTime, nullable=False)
    start_time = Column(String(10), nullable=False)  # "09:00"
    end_time = Column(String(10), nullable=False)    # "12:00"
    total_hours = Column(Integer, nullable=False)
    
    # Event Info
    event_type = Column(String(100), nullable=True)  # "Wedding", "Conference", etc.
    attendees_count = Column(Integer, nullable=True)
    special_requirements = Column(Text, nullable=True)
    
    # Pricing
    base_price = Column(Float, nullable=False)
    additional_charges = Column(JSON, default=list)
    discount_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    
    # Payment
    payment_method = Column(String(50), nullable=False)
    payment_status = Column(String(50), default="pending")
    
    # Status
    status = Column(String(50), default="pending")  # pending, confirmed, cancelled, completed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<HallBooking {self.booking_date} {self.start_time}-{self.end_time}>"