from sqlalchemy import Column, String, DateTime, Boolean, Float, JSON, Enum, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database_manager import db_manager

class Business(Base):
    __tablename__ = "businesses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Contact
    contact_phone = Column(String(20), nullable=False)
    contact_email = Column(String(255), nullable=True)
    
    # Location
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False, default="India")
    pincode = Column(String(20), nullable=False)
    
    # Coordinates
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Business Info
    business_type = Column(String(50), nullable=False)  # restaurant, grocery, pharmacy, etc.
    category = Column(String(100), nullable=False)      # main category
    subcategories = Column(JSON, default=list)          # list of subcategories
    
    # Images
    logo_url = Column(String(500), nullable=True)
    cover_url = Column(String(500), nullable=True)
    gallery = Column(JSON, default=list)                # list of image URLs
    
    # Timing
    opening_time = Column(String(10), nullable=False)   # "09:00"
    closing_time = Column(String(10), nullable=False)   # "22:00"
    working_days = Column(JSON, default=[0,1,2,3,4,5,6])  # 0=Sunday, 6=Saturday
    
    # Settings
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    commission_rate = Column(Float, default=10.0)  # Platform commission percentage
    
    # Stats
    total_orders = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    avg_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # Owner
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="business")
    
    # Staff (many-to-many through separate table)
    staff_members = relationship("BusinessStaff", back_populates="business")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Business {self.name} ({self.business_type})>"

class BusinessStaff(Base):
    __tablename__ = "business_staff"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Staff role: manager, staff, chef, etc.
    role = Column(String(50), nullable=False, default="staff")
    permissions = Column(JSON, default=list)  # ["order.view", "order.edit", etc.]
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    business = relationship("Business", back_populates="staff_members")
    user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint('business_id', 'user_id', name='unique_staff_member'),
    )