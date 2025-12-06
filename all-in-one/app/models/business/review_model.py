from sqlalchemy import Column, String, DateTime, Boolean, Float, JSON, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.models.business import Base

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Rating
    rating = Column(Integer, nullable=False)  # 1-5
    taste_rating = Column(Integer, nullable=True)
    packaging_rating = Column(Integer, nullable=True)
    delivery_rating = Column(Integer, nullable=True)
    
    # Review content
    title = Column(String(200), nullable=True)
    comment = Column(Text, nullable=True)
    
    # Images
    images = Column(JSON, default=list)
    
    # Helpfulness
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    
    # Status
    is_approved = Column(Boolean, default=False)
    is_edited = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="reviews")
    item = relationship("Item", back_populates="reviews")
    
    def __repr__(self):
        return f"<Review {self.rating}/5 by {self.customer_id}>"