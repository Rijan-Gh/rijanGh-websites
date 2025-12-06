from app.routers.auth_router import router as auth_router
from app.routers.user_router import router as user_router
from app.routers.vendor_router import router as vendor_router
from app.routers.business_router import router as business_router
from app.routers.item_router import router as item_router
from app.routers.order_router import router as order_router
from app.routers.admin_router import router as admin_router
from app.routers.delivery_router import router as delivery_router
from app.routers.map_router import router as map_router
from app.routers.recommendation_router import router as recommendation_router
from app.routers.websocket_router import router as websocket_router

__all__ = [
    'auth_router',
    'user_router',
    'vendor_router',
    'business_router',
    'item_router',
    'order_router',
    'admin_router',
    'delivery_router',
    'map_router',
    'recommendation_router',
    'websocket_router',
]