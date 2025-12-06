from sqlalchemy import Column, String, DateTime, Boolean, Float, JSON, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database_manager import db_manager
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Roles: customer, vendor, delivery, admin
    role = Column(String(50), nullable=False, default="customer")
    
    # Profile
    profile_picture = Column(String(500), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(20), nullable=True)
    
    # Wallet
    wallet_balance = Column(Float, default=0.0)
    reward_points = Column(Integer, default=0)
    
    # Addresses (stored as JSON)
    addresses = Column(JSON, default=list)
    
    # Settings
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    
    # Device info
    device_token = Column(String(500), nullable=True)
    platform = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    business = relationship("Business", back_populates="owner", uselist=False)
    delivery_profile = relationship("DeliveryBoy", back_populates="user", uselist=False)
    
    def __repr__(self):
        return f"<User {self.phone} ({self.role})>"