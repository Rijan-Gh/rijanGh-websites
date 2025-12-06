from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime
import logging

from app.recommender.hybrid_recommender import HybridRecommender
from app.recommender.collaborative_filtering import CollaborativeFiltering
from app.recommender.content_based import ContentBasedRecommender

logger = logging.getLogger(__name__)

class RecommendationService:
    
    _recommender = None
    
    @classmethod
    def get_recommender(cls):
        """Get or create recommender instance"""
        if cls._recommender is None:
            cls._recommender = HybridRecommender()
        return cls._recommender
    
    @staticmethod
    async def get_personalized_recommendations(
        db: AsyncSession,
        user_id: str,
        limit: int = 10,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get personalized recommendations for user"""
        try:
            # Get recommender instance
            recommender = RecommendationService.get_recommender()
            
            # In production, fetch user history and items from database
            # For now, return mock recommendations
            
            mock_recommendations = []
            
            for i in range(limit):
                score = 0.9 - (i * 0.05)
                recommendation_types = ["collaborative", "content_based", "popular", "context"]
                rec_type = recommendation_types[i % len(recommendation_types)]
                
                mock_recommendations.append({
                    "item_id": f"recommended_item_{i}",
                    "item_name": f"Recommended Item {i}",
                    "business_name": f"Business {i % 5}",
                    "business_type": ["restaurant", "grocery", "pharmacy"][i % 3],
                    "price": 100 + (i * 50),
                    "image_url": f"https://example.com/image_{i}.jpg",
                    "score": score,
                    "type": rec_type,
                    "reason": f"Recommended because you liked similar items" if i % 2 == 0 else f"Trending in your area",
                    "distance_km": round(0.5 + (i * 0.2), 1),
                    "rating": round(4.0 + (i * 0.1), 1),
                    "rating_count": 50 + (i * 10)
                })
            
            # Apply context if provided
            if context:
                mock_recommendations = RecommendationService._apply_context_filter(
                    mock_recommendations, context
                )
            
            return mock_recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {e}")
            return []
    
    @staticmethod
    def _apply_context_filter(
        recommendations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply context filters to recommendations"""
        filtered = recommendations.copy()
        
        # Filter by time of day
        if 'time_of_day' in context:
            time_of_day = context['time_of_day']
            if time_of_day == 'morning':
                filtered = [r for r in filtered if r['business_type'] in ['restaurant', 'cafe']]
            elif time_of_day == 'afternoon':
                filtered = [r for r in filtered if r['business_type'] in ['restaurant', 'cloud_kitchen']]
            elif time_of_day == 'evening':
                filtered = [r for r in filtered if r['business_type'] in ['restaurant', 'bakery']]
        
        # Filter by weather
        if 'weather' in context:
            weather = context['weather']
            if weather == 'rainy':
                # Recommend items suitable for rainy weather
                filtered = [r for r in filtered if r['business_type'] in ['restaurant', 'cloud_kitchen']]
            elif weather == 'hot':
                # Recommend cold items
                filtered = [r for r in filtered if 'cold' in r.get('item_name', '').lower() or 
                          r['business_type'] in ['restaurant', 'cafe']]
        
        # Filter by location
        if 'max_distance_km' in context:
            max_distance = context['max_distance_km']
            filtered = [r for r in filtered if r.get('distance_km', 0) <= max_distance]
        
        return filtered
    
    @staticmethod
    async def get_business_recommendations(
        db: AsyncSession,
        business_id: str,
        user_id: str,
        limit: int = 10,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recommendations for specific business"""
        # Mock implementation
        mock_recommendations = []
        
        for i in range(limit):
            mock_recommendations.append({
                "item_id": f"business_item_{i}",
                "item_name": f"Special Item {i}",
                "description": f"This is a recommended item from business {business_id}",
                "price": 150 + (i * 75),
                "image_url": f"https://example.com/business_{business_id}_item_{i}.jpg",
                "category": category or f"Category {i % 3}",
                "is_vegetarian": i % 2 == 0,
                "rating": round(4.2 + (i * 0.05), 1),
                "rating_count": 30 + (i * 5),
                "preparation_time": 15 + (i * 5),
                "score": 0.85 - (i * 0.03)
            })
        
        return mock_recommendations[:limit]
    
    @staticmethod
    async def get_trending_items(
        db: AsyncSession,
        city: Optional[str],
        business_type: Optional[str],
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get trending items"""
        # Mock implementation
        trending_items = []
        
        for i in range(limit):
            trending_items.append({
                "item_id": f"trending_{i}",
                "item_name": f"Trending Item {i}",
                "business_name": f"Popular Business {i % 5}",
                "business_type": business_type or ["restaurant", "grocery", "pharmacy"][i % 3],
                "city": city or "Delhi",
                "price": 200 + (i * 60),
                "image_url": f"https://example.com/trending_{i}.jpg",
                "orders_today": 50 + (i * 10),
                "total_orders": 500 + (i * 100),
                "trend_score": 0.9 - (i * 0.02),
                "rating": round(4.5 - (i * 0.02), 1),
                "is_new": i < 3
            })
        
        return trending_items[:limit]
    
    @staticmethod
    async def get_similar_items(
        db: AsyncSession,
        item_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get items similar to given item"""
        # Mock implementation
        similar_items = []
        
        for i in range(limit):
            similarity = 0.8 - (i * 0.05)
            similar_items.append({
                "item_id": f"similar_{i}",
                "item_name": f"Similar Item {i}",
                "business_name": f"Business {i % 4}",
                "price": 180 + (i * 40),
                "image_url": f"https://example.com/similar_{i}.jpg",
                "similarity_score": similarity,
                "matching_features": ["vegetarian", "spicy", "quick_prep"][:i % 3 + 1],
                "rating": round(4.3 - (i * 0.03), 1),
                "distance_km": round(1.5 + (i * 0.3), 1)
            })
        
        return similar_items[:limit]
    
    @staticmethod
    async def get_recommended_businesses(
        db: AsyncSession,
        user_id: str,
        lat: Optional[float],
        lng: Optional[float],
        radius_km: float,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recommended businesses for user"""
        # Mock implementation
        recommended_businesses = []
        
        for i in range(limit):
            distance = 0.5 + (i * 0.3) if lat and lng else None
            
            recommended_businesses.append({
                "business_id": f"recommended_biz_{i}",
                "business_name": f"Recommended Business {i}",
                "business_type": ["restaurant", "grocery", "pharmacy", "cafe"][i % 4],
                "description": f"A highly recommended business based on your preferences",
                "logo_url": f"https://example.com/business_{i}_logo.jpg",
                "cover_url": f"https://example.com/business_{i}_cover.jpg",
                "avg_rating": round(4.2 - (i * 0.02), 1),
                "rating_count": 100 + (i * 20),
                "total_orders": 1000 + (i * 200),
                "is_open": i % 5 != 0,  # 1 in 5 is closed
                "delivery_time": f"{20 + (i * 5)}-{30 + (i * 5)} mins",
                "distance_km": round(distance, 1) if distance else None,
                "recommendation_score": 0.75 - (i * 0.02),
                "recommendation_reason": ["Based on your orders", "Popular in your area", "High ratings"][i % 3]
            })
        
        # Sort by distance if location provided
        if lat and lng:
            recommended_businesses.sort(key=lambda x: x.get('distance_km', float('inf')))
        
        return recommended_businesses[:limit]
    
    @staticmethod
    async def record_feedback(
        db: AsyncSession,
        user_id: str,
        item_id: str,
        feedback_type: str
    ) -> bool:
        """Record user feedback on recommendations"""
        # In production, store feedback in database
        logger.info(f"User {user_id} gave {feedback_type} feedback for item {item_id}")
        return True
    
    @staticmethod
    async def get_seasonal_recommendations(
        db: AsyncSession,
        user_id: str,
        hour: int,
        month: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get seasonal/time-based recommendations"""
        seasonal_items = []
        
        # Time-based recommendations
        if 6 <= hour < 11:  # Morning
            time_category = "breakfast"
            items = ["Idli", "Dosa", "Poha", "Upma", "Sandwich"]
        elif 11 <= hour < 16:  # Afternoon
            time_category = "lunch"
            items = ["Thali", "Biryani", "Curry", "Rice Bowl", "Wrap"]
        elif 16 <= hour < 22:  # Evening
            time_category = "dinner"
            items = ["Pizza", "Burger", "Pasta", "Noodles", "Soup"]
        else:  # Late night
            time_category = "late_night"
            items = ["Snacks", "Coffee", "Tea", "Dessert", "Juice"]
        
        # Season-based recommendations
        season = RecommendationService._get_season(month)
        if season == "winter":
            seasonal_addition = ["Soup", "Hot Chocolate", "Stew"]
        elif season == "summer":
            seasonal_addition = ["Cold Drinks", "Ice Cream", "Salads"]
        elif season == "monsoon":
            seasonal_addition = ["Pakoras", "Tea", "Snacks"]
        else:  # spring/autumn
            seasonal_addition = ["Seasonal Specials", "Fresh Items"]
        
        # Combine time and seasonal items
        all_items = items + seasonal_addition
        
        for i, item_name in enumerate(all_items[:limit]):
            seasonal_items.append({
                "item_id": f"seasonal_{i}",
                "item_name": item_name,
                "business_name": f"Seasonal Special {i % 3}",
                "business_type": "restaurant",
                "price": 100 + (i * 40),
                "image_url": f"https://example.com/seasonal_{i}.jpg",
                "time_category": time_category,
                "season": season,
                "reason": f"Perfect for {time_category} in {season}",
                "rating": round(4.3 + (i * 0.02), 1),
                "distance_km": round(1.0 + (i * 0.2), 1)
            })
        
        return seasonal_items[:limit]
    
    @staticmethod
    def _get_season(month: int) -> str:
        """Get season from month"""
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8, 9]:
            return "monsoon"
        else:  # 10, 11
            return "autumn"