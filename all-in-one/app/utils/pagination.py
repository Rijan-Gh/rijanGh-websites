from typing import List, TypeVar, Generic, Optional
from pydantic.generics import GenericModel
from pydantic import BaseModel
from math import ceil

T = TypeVar('T')

class PaginatedResponse(GenericModel, Generic[T]):
    """Generic paginated response model"""
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_prev: bool

class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = 1
    limit: int = 20
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit
    
    def validate(self):
        """Validate pagination parameters"""
        if self.page < 1:
            raise ValueError("Page must be >= 1")
        if self.limit < 1 or self.limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        return self

def paginate(items: List[T], total: int, page: int, limit: int) -> PaginatedResponse[T]:
    """Create paginated response"""
    pages = ceil(total / limit) if limit > 0 else 0
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )

async def paginate_query(query, count_query, session, page: int = 1, limit: int = 20):
    """Paginate SQLAlchemy query"""
    from sqlalchemy import func
    
    # Get total count
    total_result = await session.execute(
        select(func.count()).select_from(count_query)
    )
    total = total_result.scalar()
    
    # Apply pagination
    items_result = await session.execute(
        query.offset((page - 1) * limit).limit(limit)
    )
    items = items_result.scalars().all()
    
    return paginate(items, total, page, limit)