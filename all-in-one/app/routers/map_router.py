from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Tuple
import json

from app.utils.route_optimizer import RouteOptimizer
from app.utils.geo_distance import calculate_distance
from app.dependencies import get_current_user
import logging

router = APIRouter(prefix="/maps", tags=["Maps & Routing"])
logger = logging.getLogger(__name__)

@router.get("/distance")
async def calculate_distance_between_points(
    lat1: float = Query(..., ge=-90, le=90),
    lng1: float = Query(..., ge=-180, le=180),
    lat2: float = Query(..., ge=-90, le=90),
    lng2: float = Query(..., ge=-180, le=180)
):
    """Calculate distance between two coordinates"""
    try:
        distance = calculate_distance(lat1, lng1, lat2, lng2)
        return {
            "distance_km": distance,
            "distance_m": distance * 1000,
            "point1": {"lat": lat1, "lng": lng1},
            "point2": {"lat": lat2, "lng": lng2}
        }
    except Exception as e:
        logger.error(f"Error calculating distance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate distance"
        )

@router.get("/route")
async def get_route(
    start_lat: float = Query(..., ge=-90, le=90),
    start_lng: float = Query(..., ge=-180, le=180),
    end_lat: float = Query(..., ge=-90, le=90),
    end_lng: float = Query(..., ge=-180, le=180),
    waypoints: Optional[str] = Query(None),
    optimize: bool = Query(True)
):
    """Get optimized route between points"""
    try:
        start = (start_lat, start_lng)
        end = (end_lat, end_lng)
        
        waypoints_list = []
        if waypoints:
            try:
                waypoints_data = json.loads(waypoints)
                if isinstance(waypoints_data, list):
                    waypoints_list = [(wp["lat"], wp["lng"]) for wp in waypoints_data]
            except:
                pass
        
        if optimize and waypoints_list:
            # Use A* algorithm for optimization
            route = RouteOptimizer.astar_route(start, end, waypoints_list)
        else:
            # Get route from external API
            route = await RouteOptimizer.get_route_from_api(start, end, waypoints_list)
        
        return route
        
    except Exception as e:
        logger.error(f"Error getting route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get route"
        )

@router.get("/delivery-route")
async def get_delivery_route(
    business_lat: float = Query(..., ge=-90, le=90),
    business_lng: float = Query(..., ge=-180, le=180),
    delivery_points: str = Query(...),
    user = Depends(get_current_user)
):
    """Get optimized delivery route with multiple stops"""
    try:
        delivery_data = json.loads(delivery_points)
        if not isinstance(delivery_data, list) or len(delivery_data) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid delivery points format"
            )
        
        # Convert to list of tuples
        points = [(dp["lat"], dp["lng"]) for dp in delivery_data]
        
        # Start from business location
        start = (business_lat, business_lng)
        
        # Optimize route
        optimized_route = []
        total_distance = 0
        
        current = start
        remaining = points.copy()
        
        while remaining:
            # Find nearest point
            nearest = min(
                remaining,
                key=lambda p: calculate_distance(current[0], current[1], p[0], p[1])
            )
            
            distance = calculate_distance(current[0], current[1], nearest[0], nearest[1])
            total_distance += distance
            
            optimized_route.append({
                "point": nearest,
                "distance_from_previous_km": distance
            })
            
            current = nearest
            remaining.remove(nearest)
        
        # Return to business (optional)
        return_distance = calculate_distance(current[0], current[1], start[0], start[1])
        total_distance += return_distance
        
        return {
            "optimized_route": optimized_route,
            "total_distance_km": round(total_distance, 2),
            "estimated_time_min": round(total_distance * 3, 1),  # 20km/h average
            "stops_count": len(points)
        }
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format for delivery_points"
        )
    except Exception as e:
        logger.error(f"Error getting delivery route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get delivery route"
        )

@router.get("/nearby")
async def find_nearby(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(5.0, ge=0.1, le=50),
    type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """Find nearby points of interest"""
    try:
        # In production, this would query a spatial database
        # For now, return mock data
        
        mock_results = [
            {
                "id": f"poi_{i}",
                "name": f"Point of Interest {i}",
                "type": type or "generic",
                "lat": lat + (i * 0.01),
                "lng": lng + (i * 0.01),
                "distance_km": calculate_distance(lat, lng, lat + (i * 0.01), lng + (i * 0.01)),
                "address": f"Address {i}",
                "phone": f"+123456789{i}"
            }
            for i in range(min(limit, 10))
        ]
        
        # Filter by radius
        results = [r for r in mock_results if r["distance_km"] <= radius_km]
        
        return {
            "center": {"lat": lat, "lng": lng},
            "radius_km": radius_km,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error finding nearby points: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find nearby points"
        )

@router.get("/geocode")
async def geocode_address(
    address: str,
    user = Depends(get_current_user)
):
    """Convert address to coordinates"""
    try:
        # In production, use Google Maps Geocoding API or similar
        # For now, return mock coordinates
        
        # Mock geocoding
        mock_coordinates = {
            "delhi": (28.6139, 77.2090),
            "mumbai": (19.0760, 72.8777),
            "bangalore": (12.9716, 77.5946),
            "chennai": (13.0827, 80.2707),
            "kolkata": (22.5726, 88.3639),
        }
        
        address_lower = address.lower()
        for city, coords in mock_coordinates.items():
            if city in address_lower:
                return {
                    "address": address,
                    "latitude": coords[0],
                    "longitude": coords[1],
                    "formatted_address": f"{city.capitalize()}, India"
                }
        
        # Default to Delhi if no match
        return {
            "address": address,
            "latitude": 28.6139,
            "longitude": 77.2090,
            "formatted_address": "Delhi, India"
        }
        
    except Exception as e:
        logger.error(f"Error geocoding address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to geocode address"
        )

@router.get("/reverse-geocode")
async def reverse_geocode(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    user = Depends(get_current_user)
):
    """Convert coordinates to address"""
    try:
        # Mock reverse geocoding
        # In production, use Google Maps Reverse Geocoding API
        
        return {
            "coordinates": {"lat": lat, "lng": lng},
            "address": f"Sample Address near ({lat}, {lng})",
            "city": "Sample City",
            "state": "Sample State",
            "country": "India",
            "pincode": "110001"
        }
        
    except Exception as e:
        logger.error(f"Error reverse geocoding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reverse geocode"
        )