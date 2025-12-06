from sqlalchemy import Column, String, DateTime, Boolean, Float, JSON, ForeignKey, Integer, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    items = relationship("Item", back_populates="category")

class Item(Base):
    __tablename__ = "items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sku = Column(String(100), unique=True, nullable=True)
    
    # Category
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    
    # Pricing
    price = Column(Numeric(10, 2), nullable=False)
    compare_at_price = Column(Numeric(10, 2), nullable=True)  # Original price
    cost_price = Column(Numeric(10, 2), nullable=True)  # Cost to business
    
    # Inventory
    stock_quantity = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=5)
    is_track_inventory = Column(Boolean, default=True)
    
    # Variants
    has_variants = Column(Boolean, default=False)
    variants = Column(JSON, default=list)  # List of variant options
    
    # Attributes
    attributes = Column(JSON, default=dict)  # { "size": ["S", "M", "L"], "color": ["Red", "Blue"] }
    
    # Images
    main_image = Column(String(500), nullable=True)
    gallery_images = Column(JSON, default=list)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Dietary Info (for food businesses)
    is_vegetarian = Column(Boolean, default=True)
    is_vegan = Column(Boolean, default=False)
    contains_allergens = Column(Boolean, default=False)
    allergens = Column(JSON, default=list)
    
    # Preparation time (in minutes)
    preparation_time = Column(Integer, default=15)
    
    # Stats
    total_orders = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    avg_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="items")
    reviews = relationship("Review", back_populates="item")
    
    def __repr__(self):
        return f"<Item {self.name} (${self.price})>"