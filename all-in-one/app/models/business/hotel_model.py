from sqlalchemy import Column, String, DateTime, Boolean, Float, JSON, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.models.business import Base

class HotelRoom(Base):
    __tablename__ = "hotel_rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Room Info
    room_number = Column(String(50), nullable=False)
    room_type = Column(String(100), nullable=False)  # "Deluxe", "Suite", etc.
    description = Column(Text, nullable=True)
    max_occupancy = Column(Integer, nullable=False)
    
    # Amenities
    amenities = Column(JSON, default=list)  # ["AC", "TV", "WiFi", "Mini Bar", etc.]
    bed_type = Column(String(100), nullable=True)  # "King", "Queen", "Twin"
    bed_count = Column(Integer, default=1)
    
    # Pricing
    base_price_per_night = Column(Float, nullable=False)
    weekend_price_per_night = Column(Float, nullable=True)
    seasonal_prices = Column(JSON, default=dict)
    
    # Images
    main_image = Column(String(500), nullable=True)
    gallery_images = Column(JSON, default=list)
    
    # Availability
    is_available = Column(Boolean, default=True)
    availability_calendar = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<HotelRoom {self.room_number} ({self.room_type})>"

class HotelBooking(Base):
    __tablename__ = "hotel_bookings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Booking Dates
    check_in_date = Column(DateTime, nullable=False)
    check_out_date = Column(DateTime, nullable=False)
    total_nights = Column(Integer, nullable=False)
    
    # Guest Info
    guest_name = Column(String(255), nullable=False)
    guest_phone = Column(String(20), nullable=False)
    guest_email = Column(String(255), nullable=True)
    guest_count = Column(Integer, default=1)
    
    # Special Requests
    special_requests = Column(Text, nullable=True)
    
    # Pricing
    base_price = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    additional_charges = Column(JSON, default=list)
    discount_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    
    # Payment
    payment_method = Column(String(50), nullable=False)
    payment_status = Column(String(50), default="pending")
    
    # Status
    status = Column(String(50), default="pending")  # pending, confirmed, checked_in, checked_out, cancelled
    
    # Check-in/out times
    actual_check_in = Column(DateTime, nullable=True)
    actual_check_out = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<HotelBooking {self.check_in_date} to {self.check_out_date}>"