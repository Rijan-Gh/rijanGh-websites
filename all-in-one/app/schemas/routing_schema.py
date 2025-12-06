from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class RouteType(str, Enum):
    FASTEST = "fastest"
    SHORTEST = "shortest"
    ECONOMICAL = "economical"
    SCENIC = "scenic"

class TravelMode(str, Enum):
    DRIVING = "driving"
    WALKING = "walking"
    BICYCLING = "bicycling"
    TRANSIT = "transit"

class Coordinate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    name: Optional[str] = None

class RouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    waypoints: Optional[List[Coordinate]] = None
    route_type: RouteType = RouteType.FASTEST
    travel_mode: TravelMode = TravelMode.DRIVING
    avoid: Optional[List[str]] = Field(default=None)
    departure_time: Optional[str] = None
    traffic_model: Optional[str] = Field(default="best_guess", regex="^(best_guess|pessimistic|optimistic)$")
    
    @validator('waypoints')
    def validate_waypoints(cls, v):
        if v and len(v) > 25:
            raise ValueError("Maximum 25 waypoints allowed")
        return v

class RouteLeg(BaseModel):
    distance_meters: float
    duration_seconds: float
    start_address: str
    end_address: str
    start_location: Coordinate
    end_location: Coordinate
    steps: List[Dict[str, Any]]
    traffic_speed_entry: Optional[List[Dict[str, Any]]] = None
    via_waypoint: Optional[List[Dict[str, Any]]] = None

class RouteResponse(BaseModel):
    route_id: str
    summary: str
    legs: List[RouteLeg]
    total_distance_meters: float
    total_duration_seconds: float
    bounds: Dict[str, Coordinate]
    copyrights: str
    warnings: List[str]
    waypoint_order: Optional[List[int]] = None
    polyline: str
    fare: Optional[Dict[str, Any]] = None
    traffic_info: Optional[Dict[str, Any]] = None

class TrafficInfo(BaseModel):
    traffic_level: str
    congestion_percentage: float
    typical_duration_seconds: float
    current_duration_seconds: float
    delay_seconds: float
    incidents: List[Dict[str, Any]]

class ETARequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    departure_time: Optional[str] = None
    traffic_model: Optional[str] = "best_guess"
    alternatives: bool = False
    
    @validator('departure_time')
    def validate_departure_time(cls, v):
        if v:
            # Validate ISO format datetime
            from datetime import datetime
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError("departure_time must be in ISO 8601 format")
        return v

class ETAResponse(BaseModel):
    origin: Coordinate
    destination: Coordinate
    distance_meters: float
    duration_seconds: float
    duration_in_traffic_seconds: Optional[float] = None
    departure_time: str
    arrival_time: str
    traffic_conditions: Optional[TrafficInfo] = None
    alternative_routes: Optional[List[Dict[str, Any]]] = None

class DistanceMatrixRequest(BaseModel):
    origins: List[Coordinate] = Field(..., min_items=1, max_items=25)
    destinations: List[Coordinate] = Field(..., min_items=1, max_items=25)
    travel_mode: TravelMode = TravelMode.DRIVING
    departure_time: Optional[str] = None
    
    @validator('origins', 'destinations')
    def validate_coordinates_length(cls, v):
        if len(v) > 25:
            raise ValueError("Maximum 25 coordinates allowed")
        return v

class DistanceMatrixElement(BaseModel):
    status: str
    distance_meters: Optional[float] = None
    duration_seconds: Optional[float] = None
    duration_in_traffic_seconds: Optional[float] = None

class DistanceMatrixResponse(BaseModel):
    origin_addresses: List[str]
    destination_addresses: List[str]
    rows: List[List[DistanceMatrixElement]]
    error_messages: Optional[List[str]] = None

class GeocodeRequest(BaseModel):
    address: str
    bounds: Optional[Dict[str, Coordinate]] = None
    components: Optional[Dict[str, str]] = None
    region: Optional[str] = None

class GeocodeResponse(BaseModel):
    formatted_address: str
    location: Coordinate
    place_id: str
    types: List[str]
    address_components: List[Dict[str, Any]]
    plus_code: Optional[Dict[str, str]] = None
    viewport: Dict[str, Coordinate]

class ReverseGeocodeRequest(BaseModel):
    location: Coordinate
    result_type: Optional[List[str]] = None
    location_type: Optional[List[str]] = None

class RouteOptimization(BaseModel):
    deliveries: List[Coordinate]
    depot: Optional[Coordinate] = None
    constraints: Optional[Dict[str, Any]] = None
    objectives: Optional[List[str]] = Field(default=["minimize_distance"])
    
    @validator('deliveries')
    def validate_deliveries(cls, v):
        if len(v) < 2:
            raise ValueError("At least 2 delivery points required")
        if len(v) > 100:
            raise ValueError("Maximum 100 delivery points allowed")
        return v

class OptimizedRoute(BaseModel):
    sequence: List[int]
    route: List[Coordinate]
    total_distance_meters: float
    total_duration_seconds: float
    segments: List[Dict[str, Any]]
    optimization_metrics: Dict[str, float]