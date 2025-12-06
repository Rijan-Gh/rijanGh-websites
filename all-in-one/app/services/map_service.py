from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import json
import logging

from app.config import settings
from app.utils.geo_distance import calculate_distance
from app.utils.route_optimizer import RouteOptimizer

logger = logging.getLogger(__name__)

class MapService:
    
    @staticmethod
    async def get_directions(
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        waypoints: Optional[List[Tuple[float, float]]] = None,
        mode: str = "driving",
        alternatives: bool = False
    ) -> Dict[str, Any]:
        """Get directions between points"""
        try:
            if settings.GOOGLE_MAPS_API_KEY:
                return await MapService._get_google_directions(
                    origin, destination, waypoints, mode, alternatives
                )
            elif settings.OPEN_ROUTE_SERVICE_KEY:
                return await MapService._get_ors_directions(
                    origin, destination, waypoints, mode, alternatives
                )
            else:
                # Use local route optimization
                return await MapService._get_local_directions(
                    origin, destination, waypoints, mode
                )
                
        except Exception as e:
            logger.error(f"Error getting directions: {e}")
            raise Exception(f"Failed to get directions: {str(e)}")
    
    @staticmethod
    async def _get_google_directions(
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        waypoints: Optional[List[Tuple[float, float]]],
        mode: str,
        alternatives: bool
    ) -> Dict[str, Any]:
        """Get directions from Google Maps API"""
        async with httpx.AsyncClient() as client:
            params = {
                "origin": f"{origin[0]},{origin[1]}",
                "destination": f"{destination[0]},{destination[1]}",
                "key": settings.GOOGLE_MAPS_API_KEY,
                "mode": mode,
                "alternatives": "true" if alternatives else "false"
            }
            
            if waypoints:
                waypoints_str = "|".join([f"{wp[0]},{wp[1]}" for wp in waypoints])
                params["waypoints"] = waypoints_str
            
            response = await client.get(
                "https://maps.googleapis.com/maps/api/directions/json",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data["status"] == "OK":
                    routes = data["routes"]
                    primary_route = routes[0]
                    
                    # Parse route information
                    legs = []
                    total_distance = 0
                    total_duration = 0
                    
                    for leg in primary_route["legs"]:
                        legs.append({
                            "distance": leg["distance"]["value"],  # meters
                            "duration": leg["duration"]["value"],  # seconds
                            "start_address": leg["start_address"],
                            "end_address": leg["end_address"],
                            "start_location": {
                                "lat": leg["start_location"]["lat"],
                                "lng": leg["start_location"]["lng"]
                            },
                            "end_location": {
                                "lat": leg["end_location"]["lat"],
                                "lng": leg["end_location"]["lng"]
                            }
                        })
                        
                        total_distance += leg["distance"]["value"]
                        total_duration += leg["duration"]["value"]
                    
                    return {
                        "success": True,
                        "source": "google_maps",
                        "routes": routes if alternatives else [primary_route],
                        "summary": {
                            "total_distance_meters": total_distance,
                            "total_duration_seconds": total_duration,
                            "total_distance_km": round(total_distance / 1000, 2),
                            "total_duration_minutes": round(total_duration / 60, 1)
                        },
                        "legs": legs,
                        "polyline": primary_route.get("overview_polyline", {}).get("points", ""),
                        "bounds": primary_route.get("bounds"),
                        "copyrights": primary_route.get("copyrights", "")
                    }
                else:
                    raise Exception(f"Google Maps API error: {data['status']}")
            else:
                raise Exception(f"HTTP error: {response.status_code}")
    
    @staticmethod
    async def _get_ors_directions(
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        waypoints: Optional[List[Tuple[float, float]]],
        mode: str,
        alternatives: bool
    ) -> Dict[str, Any]:
        """Get directions from OpenRouteService"""
        async with httpx.AsyncClient() as client:
            coordinates = [list(origin)]
            if waypoints:
                coordinates.extend([list(wp) for wp in waypoints])
            coordinates.append(list(destination))
            
            # Map mode to ORS profile
            profile_map = {
                "driving": "driving-car",
                "walking": "foot-walking",
                "bicycling": "cycling-regular",
                "transit": "driving-car"  # ORS doesn't have transit
            }
            
            profile = profile_map.get(mode, "driving-car")
            
            headers = {
                "Authorization": settings.OPEN_ROUTE_SERVICE_KEY
            }
            
            body = {
                "coordinates": coordinates,
                "instructions": False,
                "geometry": True,
                "format": "geojson"
            }
            
            response = await client.post(
                f"https://api.openrouteservice.org/v2/directions/{profile}",
                headers=headers,
                json=body
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("features"):
                    route = data["features"][0]
                    properties = route["properties"]
                    geometry = route["geometry"]
                    
                    summary = properties.get("summary", {})
                    
                    return {
                        "success": True,
                        "source": "openrouteservice",
                        "routes": [route],
                        "summary": {
                            "total_distance_meters": summary.get("distance", 0),
                            "total_duration_seconds": summary.get("duration", 0),
                            "total_distance_km": round(summary.get("distance", 0) / 1000, 2),
                            "total_duration_minutes": round(summary.get("duration", 0) / 60, 1)
                        },
                        "geometry": geometry,
                        "segments": properties.get("segments", []),
                        "way_points": properties.get("way_points", [])
                    }
                else:
                    raise Exception("No route found in ORS response")
            else:
                raise Exception(f"OpenRouteService error: {response.status_code}")
    
    @staticmethod
    async def _get_local_directions(
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        waypoints: Optional[List[Tuple[float, float]]],
        mode: str
    ) -> Dict[str, Any]:
        """Get directions using local route optimization"""
        # Use local route optimizer
        route = RouteOptimizer.astar_route(origin, destination, waypoints)
        
        # Calculate speed based on mode
        speed_kmh = {
            "driving": 40,
            "walking": 5,
            "bicycling": 15,
            "transit": 25
        }.get(mode, 20)
        
        # Calculate duration
        duration_minutes = route["estimated_time_min"]
        if mode != "driving":
            # Adjust for slower modes
            speed_factor = 40 / speed_kmh  # Compared to driving
            duration_minutes *= speed_factor
        
        return {
            "success": True,
            "source": "local",
            "route": route,
            "summary": {
                "total_distance_km": route["distance_km"],
                "total_duration_minutes": duration_minutes,
                "total_distance_meters": route["distance_km"] * 1000,
                "total_duration_seconds": duration_minutes * 60
            },
            "path": route["path"],
            "waypoint_order": route.get("waypoint_order", []),
            "mode": mode,
            "speed_kmh": speed_kmh
        }
    
    @staticmethod
    async def get_distance_matrix(
        origins: List[Tuple[float, float]],
        destinations: List[Tuple[float, float]],
        mode: str = "driving"
    ) -> Dict[str, Any]:
        """Get distance matrix between multiple points"""
        try:
            if settings.GOOGLE_MAPS_API_KEY:
                return await MapService._get_google_distance_matrix(origins, destinations, mode)
            else:
                return await MapService._get_local_distance_matrix(origins, destinations, mode)
                
        except Exception as e:
            logger.error(f"Error getting distance matrix: {e}")
            raise Exception(f"Failed to get distance matrix: {str(e)}")
    
    @staticmethod
    async def _get_google_distance_matrix(
        origins: List[Tuple[float, float]],
        destinations: List[Tuple[float, float]],
        mode: str
    ) -> Dict[str, Any]:
        """Get distance matrix from Google Maps"""
        async with httpx.AsyncClient() as client:
            origins_str = "|".join([f"{lat},{lng}" for lat, lng in origins])
            destinations_str = "|".join([f"{lat},{lng}" for lat, lng in destinations])
            
            params = {
                "origins": origins_str,
                "destinations": destinations_str,
                "key": settings.GOOGLE_MAPS_API_KEY,
                "mode": mode
            }
            
            response = await client.get(
                "https://maps.googleapis.com/maps/api/distancematrix/json",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data["status"] == "OK":
                    matrix = []
                    
                    for i, row in enumerate(data["rows"]):
                        row_data = []
                        for j, element in enumerate(row["elements"]):
                            if element["status"] == "OK":
                                row_data.append({
                                    "origin_index": i,
                                    "destination_index": j,
                                    "distance_meters": element["distance"]["value"],
                                    "duration_seconds": element["duration"]["value"],
                                    "status": "OK"
                                })
                            else:
                                row_data.append({
                                    "origin_index": i,
                                    "destination_index": j,
                                    "status": element["status"]
                                })
                        matrix.append(row_data)
                    
                    return {
                        "success": True,
                        "source": "google_maps",
                        "origin_addresses": data["origin_addresses"],
                        "destination_addresses": data["destination_addresses"],
                        "matrix": matrix
                    }
                else:
                    raise Exception(f"Google Maps API error: {data['status']}")
            else:
                raise Exception(f"HTTP error: {response.status_code}")
    
    @staticmethod
    async def _get_local_distance_matrix(
        origins: List[Tuple[float, float]],
        destinations: List[Tuple[float, float]],
        mode: str
    ) -> Dict[str, Any]:
        """Calculate distance matrix locally"""
        matrix = []
        
        # Calculate speed based on mode
        speed_kmh = {
            "driving": 40,
            "walking": 5,
            "bicycling": 15,
            "transit": 25
        }.get(mode, 20)
        
        for i, origin in enumerate(origins):
            row = []
            for j, destination in enumerate(destinations):
                # Calculate distance
                distance_km = calculate_distance(origin[0], origin[1], destination[0], destination[1])
                
                # Calculate duration based on speed
                duration_hours = distance_km / speed_kmh if speed_kmh > 0 else 0
                duration_seconds = duration_hours * 3600
                
                row.append({
                    "origin_index": i,
                    "destination_index": j,
                    "distance_meters": distance_km * 1000,
                    "duration_seconds": duration_seconds,
                    "distance_km": distance_km,
                    "duration_minutes": duration_seconds / 60,
                    "status": "OK"
                })
            
            matrix.append(row)
        
        return {
            "success": True,
            "source": "local",
            "origin_addresses": [f"Origin {i+1}" for i in range(len(origins))],
            "destination_addresses": [f"Destination {j+1}" for j in range(len(destinations))],
            "matrix": matrix,
            "mode": mode,
            "speed_kmh": speed_kmh
        }
    
    @staticmethod
    async def geocode_address(
        address: str,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """Geocode address to coordinates"""
        try:
            if settings.GOOGLE_MAPS_API_KEY:
                return await MapService._google_geocode(address, region)
            else:
                return await MapService._local_geocode(address)
                
        except Exception as e:
            logger.error(f"Error geocoding address: {e}")
            raise Exception(f"Failed to geocode address: {str(e)}")
    
    @staticmethod
    async def _google_geocode(
        address: str,
        region: Optional[str]
    ) -> Dict[str, Any]:
        """Geocode using Google Maps"""
        async with httpx.AsyncClient() as client:
            params = {
                "address": address,
                "key": settings.GOOGLE_MAPS_API_KEY
            }
            
            if region:
                params["region"] = region
            
            response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data["status"] == "OK":
                    result = data["results"][0]
                    
                    return {
                        "success": True,
                        "source": "google_maps",
                        "formatted_address": result["formatted_address"],
                        "location": result["geometry"]["location"],
                        "place_id": result["place_id"],
                        "types": result["types"],
                        "address_components": result["address_components"],
                        "bounds": result["geometry"].get("bounds"),
                        "viewport": result["geometry"].get("viewport")
                    }
                else:
                    raise Exception(f"Google Geocoding API error: {data['status']}")
            else:
                raise Exception(f"HTTP error: {response.status_code}")
    
    @staticmethod
    async def _local_geocode(address: str) -> Dict[str, Any]:
        """Local geocoding (mock)"""
        # Mock geocoding based on common city names
        city_coordinates = {
            "delhi": (28.6139, 77.2090),
            "mumbai": (19.0760, 72.8777),
            "bangalore": (12.9716, 77.5946),
            "chennai": (13.0827, 80.2707),
            "kolkata": (22.5726, 88.3639),
            "hyderabad": (17.3850, 78.4867),
            "pune": (18.5204, 73.8567),
            "ahmedabad": (23.0225, 72.5714),
            "jaipur": (26.9124, 75.7873),
            "lucknow": (26.8467, 80.9462)
        }
        
        address_lower = address.lower()
        
        for city, coords in city_coordinates.items():
            if city in address_lower:
                return {
                    "success": True,
                    "source": "local",
                    "formatted_address": f"{city.capitalize()}, India",
                    "location": {"lat": coords[0], "lng": coords[1]},
                    "place_id": f"local_{city}",
                    "types": ["locality", "political"],
                    "address_components": [
                        {"long_name": city.capitalize(), "short_name": city.upper(), "types": ["locality", "political"]},
                        {"long_name": "India", "short_name": "IN", "types": ["country", "political"]}
                    ]
                }
        
        # Default to Delhi
        return {
            "success": True,
            "source": "local",
            "formatted_address": "Delhi, India",
            "location": {"lat": 28.6139, "lng": 77.2090},
            "place_id": "local_delhi",
            "types": ["locality", "political"],
            "address_components": [
                {"long_name": "Delhi", "short_name": "DL", "types": ["locality", "political"]},
                {"long_name": "India", "short_name": "IN", "types": ["country", "political"]}
            ]
        }
    
    @staticmethod
    async def reverse_geocode(
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """Reverse geocode coordinates to address"""
        try:
            if settings.GOOGLE_MAPS_API_KEY:
                return await MapService._google_reverse_geocode(latitude, longitude)
            else:
                return await MapService._local_reverse_geocode(latitude, longitude)
                
        except Exception as e:
            logger.error(f"Error reverse geocoding: {e}")
            raise Exception(f"Failed to reverse geocode: {str(e)}")
    
    @staticmethod
    async def _google_reverse_geocode(
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """Reverse geocode using Google Maps"""
        async with httpx.AsyncClient() as client:
            params = {
                "latlng": f"{latitude},{longitude}",
                "key": settings.GOOGLE_MAPS_API_KEY
            }
            
            response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data["status"] == "OK":
                    result = data["results"][0]
                    
                    return {
                        "success": True,
                        "source": "google_maps",
                        "formatted_address": result["formatted_address"],
                        "location": {"lat": latitude, "lng": longitude},
                        "place_id": result["place_id"],
                        "types": result["types"],
                        "address_components": result["address_components"]
                    }
                else:
                    raise Exception(f"Google Reverse Geocoding API error: {data['status']}")
            else:
                raise Exception(f"HTTP error: {response.status_code}")
    
    @staticmethod
    async def _local_reverse_geocode(
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """Local reverse geocoding (mock)"""
        # Simple mock implementation
        return {
            "success": True,
            "source": "local",
            "formatted_address": f"Location near ({latitude:.4f}, {longitude:.4f})",
            "location": {"lat": latitude, "lng": longitude},
            "place_id": f"local_{latitude:.4f}_{longitude:.4f}",
            "types": ["street_address"],
            "address_components": [
                {"long_name": "Sample Street", "short_name": "St", "types": ["route"]},
                {"long_name": "Sample City", "short_name": "SC", "types": ["locality", "political"]},
                {"long_name": "Sample State", "short_name": "SS", "types": ["administrative_area_level_1", "political"]},
                {"long_name": "India", "short_name": "IN", "types": ["country", "political"]}
            ]
        }
    
    @staticmethod
    async def optimize_delivery_route(
        depot: Tuple[float, float],
        deliveries: List[Tuple[float, float]],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Optimize delivery route for multiple stops"""
        try:
            # Use local route optimizer
            optimized_route = RouteOptimizer.astar_route(depot, depot, deliveries)
            
            # Calculate additional metrics
            total_distance = optimized_route["distance_km"]
            
            # Estimate time based on average speed
            avg_speed_kmh = 20  # Average delivery speed
            total_time_minutes = (total_distance / avg_speed_kmh) * 60
            
            # Add traffic factor if available
            traffic_factor = constraints.get("traffic_factor", 1.0) if constraints else 1.0
            total_time_minutes *= traffic_factor
            
            # Calculate fuel estimate (if applicable)
            fuel_consumption_l_per_km = 0.1  # Example: 10L per 100km
            fuel_estimate = total_distance * fuel_consumption_l_per_km
            
            return {
                "success": True,
                "optimized_route": optimized_route["path"],
                "waypoint_order": optimized_route.get("waypoint_order", []),
                "total_distance_km": total_distance,
                "estimated_time_minutes": round(total_time_minutes, 1),
                "fuel_estimate_liters": round(fuel_estimate, 2),
                "depot": depot,
                "delivery_count": len(deliveries),
                "efficiency_improvement": 0.15  # Mock 15% improvement over naive route
            }
            
        except Exception as e:
            logger.error(f"Error optimizing delivery route: {e}")
            raise Exception(f"Failed to optimize route: {str(e)}")