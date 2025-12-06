from math import radians, sin, cos, sqrt, atan2
from typing import Tuple

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees) using Haversine formula
    
    Returns distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    r = 6371  # Radius of earth in kilometers
    
    return round(c * r, 2)

def calculate_bounding_box(lat: float, lng: float, radius_km: float) -> Tuple[float, float, float, float]:
    """
    Calculate bounding box coordinates for a given point and radius
    
    Returns: (min_lat, max_lat, min_lng, max_lng)
    """
    # Earth radius in kilometers
    R = 6371
    
    # Convert radius to radians
    radius_rad = radius_km / R
    
    # Convert latitude and longitude to radians
    lat_rad = radians(lat)
    lng_rad = radians(lng)
    
    # Calculate min and max latitude
    min_lat = lat_rad - radius_rad
    max_lat = lat_rad + radius_rad
    
    # Calculate min and max longitude
    delta_lng = asin(sin(radius_rad) / cos(lat_rad))
    min_lng = lng_rad - delta_lng
    max_lng = lng_rad + delta_lng
    
    # Convert back to degrees
    min_lat = degrees(min_lat)
    max_lat = degrees(max_lat)
    min_lng = degrees(min_lng)
    max_lng = degrees(max_lng)
    
    return min_lat, max_lat, min_lng, max_lng

def is_within_radius(lat1: float, lon1: float, lat2: float, lon2: float, radius_km: float) -> bool:
    """Check if point is within given radius of another point"""
    distance = calculate_distance(lat1, lon1, lat2, lon2)
    return distance <= radius_km

def calculate_eta(distance_km: float, speed_kmh: float = 20, traffic_factor: float = 1.0) -> float:
    """
    Calculate estimated time of arrival in minutes
    
    Args:
        distance_km: Distance in kilometers
        speed_kmh: Average speed in km/h
        traffic_factor: Traffic multiplier (1.0 = normal, >1.0 = slower)
    
    Returns: ETA in minutes
    """
    if distance_km <= 0:
        return 0
    
    time_hours = distance_km / (speed_kmh / traffic_factor)
    return round(time_hours * 60, 1)  # Convert to minutes