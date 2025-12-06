from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import json

from app.dependencies import get_current_user, get_global_db
from app.recommender.hybrid_recommender import HybridRecommender
from app.services.recommendation_service import RecommendationService
import logging

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])
logger = logging.getLogger(__name__)

@router.get("/for-you")
async def get_personalized_recommendations(
    user = Depends(get_current_user),
    db = Depends(get_global_db),
    limit: int = Query(10, ge=1, le=50),
    context: Optional[str] = Query(None)
):
    """Get personalized recommendations for user"""
    try:
        context_data = None
        if context:
            try:
                context_data = json.loads(context)
            except:
                pass
        
        recommendations = await RecommendationService.get_personalized_recommendations(
            db=db,
            user_id=str(user.id),
            limit=limit,
            context=context_data
        )
        
        return {
            "user_id": str(user.id),
            "recommendations": recommendations,
            "count": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error getting personalized recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommendations"
        )

@router.get("/business/{business_id}")
async def get_business_recommendations(
    business_id: str,
    user = Depends(get_current_user),
    db = Depends(get_global_db),
    limit: int = Query(10, ge=1, le=50),
    category: Optional[str] = Query(None)
):
    """Get recommendations for specific business"""
    try:
        recommendations = await RecommendationService.get_business_recommendations(
            db=db,
            business_id=business_id,
            user_id=str(user.id),
            limit=limit,
            category=category
        )
        
        return {
            "business_id": business_id,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error getting business recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommendations"
        )

@router.get("/trending")
async def get_trending_items(
    user = Depends(get_current_user),
    db = Depends(get_global_db),
    city: Optional[str] = Query(None),
    business_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50)
):
    """Get trending items"""
    try:
        trending = await RecommendationService.get_trending_items(
            db=db,
            city=city,
            business_type=business_type,
            limit=limit
        )
        
        return {
            "trending": trending,
            "count": len(trending),
            "city": city,
            "business_type": business_type
        }
        
    except Exception as e:
        logger.error(f"Error getting trending items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get trending items"
        )

@router.get("/similar-items/{item_id}")
async def get_similar_items(
    item_id: str,
    user = Depends(get_current_user),
    db = Depends(get_global_db),
    limit: int = Query(10, ge=1, le=50)
):
    """Get items similar to given item"""
    try:
        similar_items = await RecommendationService.get_similar_items(
            db=db,
            item_id=item_id,
            limit=limit
        )
        
        return {
            "item_id": item_id,
            "similar_items": similar_items,
            "count": len(similar_items)
        }
        
    except Exception as e:
        logger.error(f"Error getting similar items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get similar items"
        )

@router.get("/for-you/businesses")
async def get_recommended_businesses(
    user = Depends(get_current_user),
    db = Depends(get_global_db),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    radius_km: float = Query(5.0, ge=0.1, le=50),
    limit: int = Query(20, ge=1, le=50)
):
    """Get recommended businesses for user"""
    try:
        recommendations = await RecommendationService.get_recommended_businesses(
            db=db,
            user_id=str(user.id),
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            limit=limit
        )
        
        return {
            "user_id": str(user.id),
            "recommended_businesses": recommendations,
            "count": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error getting recommended businesses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommended businesses"
        )

@router.post("/feedback")
async def provide_recommendation_feedback(
    item_id: str,
    feedback_type: str,  # like, dislike, click, purchase
    user = Depends(get_current_user),
    db = Depends(get_global_db)
):
    """Provide feedback on recommendations"""
    try:
        success = await RecommendationService.record_feedback(
            db=db,
            user_id=str(user.id),
            item_id=item_id,
            feedback_type=feedback_type
        )
        
        return {
            "message": "Feedback recorded",
            "item_id": item_id,
            "feedback_type": feedback_type
        }
        
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record feedback"
        )

@router.get("/seasonal")
async def get_seasonal_recommendations(
    user = Depends(get_current_user),
    db = Depends(get_global_db),
    limit: int = Query(10, ge=1, le=50)
):
    """Get seasonal/time-based recommendations"""
    try:
        from datetime import datetime
        
        current_hour = datetime.now().hour
        current_month = datetime.now().month
        
        recommendations = await RecommendationService.get_seasonal_recommendations(
            db=db,
            user_id=str(user.id),
            hour=current_hour,
            month=current_month,
            limit=limit
        )
        
        return {
            "seasonal_recommendations": recommendations,
            "time_context": {
                "hour": current_hour,
                "month": current_month,
                "season": RecommendationService._get_season(current_month)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting seasonal recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get seasonal recommendations"
        )