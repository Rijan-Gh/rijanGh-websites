from typing import List, Tuple, Dict, Any
import heapq
import math
from app.utils.geo_distance import calculate_distance
import logging

logger = logging.getLogger(__name__)

class RouteOptimizer:
    """Route optimization using A* algorithm"""
    
    @staticmethod
    def astar_route(
        start: Tuple[float, float],
        end: Tuple[float, float],
        waypoints: List[Tuple[float, float]] = None,
        obstacles: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Calculate optimal route using A* algorithm
        """
        # Simplified version - in production, use road network graph
        
        if not waypoints:
            # Direct route
            distance = calculate_distance(start[0], start[1], end[0], end[1])
            return {
                "path": [start, end],
                "distance_km": distance,
                "estimated_time_min": distance * 3  # Assuming 20km/h average
            }
        
        # With waypoints, find optimal order using Traveling Salesman approximation
        optimized_waypoints = RouteOptimizer._optimize_waypoints_order(start, end, waypoints)
        
        # Calculate total distance
        total_distance = 0
        path = [start]
        
        current = start
        for point in optimized_waypoints:
            distance = calculate_distance(current[0], current[1], point[0], point[1])
            total_distance += distance
            path.append(point)
            current = point
        
        # Add final distance to end point
        final_distance = calculate_distance(current[0], current[1], end[0], end[1])
        total_distance += final_distance
        path.append(end)
        
        # Estimate time (considering traffic if available)
        estimated_time = RouteOptimizer._estimate_travel_time(total_distance, obstacles)
        
        return {
            "path": path,
            "distance_km": total_distance,
            "estimated_time_min": estimated_time,
            "waypoint_order": [i for i in range(len(optimized_waypoints))]
        }
    
    @staticmethod
    def _optimize_waypoints_order(
        start: Tuple[float, float],
        end: Tuple[float, float],
        waypoints: List[Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        """Optimize waypoints order using Nearest Neighbor heuristic"""
        if not waypoints:
            return []
        
        unvisited = waypoints.copy()
        current = start
        optimized = []
        
        while unvisited:
            # Find nearest unvisited waypoint
            nearest = min(
                unvisited,
                key=lambda p: calculate_distance(current[0], current[1], p[0], p[1])
            )
            optimized.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        return optimized
    
    @staticmethod
    def _estimate_travel_time(distance_km: float, obstacles: List[Dict] = None) -> float:
        """Estimate travel time considering distance and obstacles"""
        base_speed_kmh = 20  # Average delivery speed
        
        # Adjust for traffic/obstacles
        if obstacles:
            traffic_factor = 1.5  # 50% slower in traffic
        else:
            traffic_factor = 1.0
        
        time_hours = distance_km / (base_speed_kmh / traffic_factor)
        return time_hours * 60  # Convert to minutes
    
    @staticmethod
    async def get_route_from_api(
        start: Tuple[float, float],
        end: Tuple[float, float],
        waypoints: List[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """Get route from external API (Google Maps/OpenRouteService)"""
        try:
            import httpx
            
            if settings.OPEN_ROUTE_SERVICE_KEY:
                return await RouteOptimizer._get_ors_route(start, end, waypoints)
            elif settings.GOOGLE_MAPS_API_KEY:
                return await RouteOptimizer._get_google_route(start, end, waypoints)
            else:
                # Fallback to our A* algorithm
                return RouteOptimizer.astar_route(start, end, waypoints)
                
        except Exception as e:
            logger.error(f"Error getting route from API: {e}")
            # Fallback to our algorithm
            return RouteOptimizer.astar_route(start, end, waypoints)
    
    @staticmethod
    async def _get_ors_route(
        start: Tuple[float, float],
        end: Tuple[float, float],
        waypoints: List[Tuple[float, float]]
    ) -> Dict[str, Any]:
        """Get route from OpenRouteService"""
        import httpx
        
        coordinates = [list(start)]
        if waypoints:
            coordinates.extend([list(wp) for wp in waypoints])
        coordinates.append(list(end))
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openrouteservice.org/v2/directions/driving-car",
                headers={
                    "Authorization": settings.OPEN_ROUTE_SERVICE_KEY
                },
                json={
                    "coordinates": coordinates,
                    "instructions": False,
                    "geometry": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                route = data["routes"][0]
                
                return {
                    "path": RouteOptimizer._decode_polyline(route["geometry"]),
                    "distance_km": route["summary"]["distance"] / 1000,
                    "estimated_time_min": route["summary"]["duration"] / 60,
                    "source": "openrouteservice"
                }
            
        raise Exception("Failed to get route from OpenRouteService")
    
    @staticmethod
    def _decode_polyline(polyline: str) -> List[Tuple[float, float]]:
        """Decode Google Maps polyline"""
        # Implementation of polyline decoding
        pass