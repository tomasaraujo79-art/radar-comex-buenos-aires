from __future__ import annotations

import math
from dataclasses import dataclass

from src.classifiers.rules import normalize
from src.models import JobPosting


@dataclass
class RouteEstimate:
    location: str
    latitude: float | None
    longitude: float | None
    distance_km: float | None
    travel_minutes: float | None
    is_estimated: bool = True


KNOWN_POINTS = {
    "belgrano": (-34.5627, -58.4583),
    "nunez": (-34.5482, -58.4633),
    "nuñez": (-34.5482, -58.4633),
    "palermo": (-34.5781, -58.4265),
    "saavedra": (-34.5542, -58.4866),
    "colegiales": (-34.5749, -58.4482),
    "retiro": (-34.5920, -58.3749),
    "microcentro": (-34.6037, -58.3816),
    "monserrat": (-34.6107, -58.3816),
    "barracas": (-34.6420, -58.3776),
    "villa crespo": (-34.5987, -58.4411),
    "caba": (-34.6037, -58.3816),
    "buenos aires": (-34.6037, -58.3816),
    "vicente lopez": (-34.5290, -58.4730),
    "vicente lópez": (-34.5290, -58.4730),
    "martinez": (-34.4870, -58.4986),
    "martínez": (-34.4870, -58.4986),
    "san isidro": (-34.4721, -58.5275),
    "munro": (-34.5295, -58.5229),
    "florida": (-34.5322, -58.4901),
    "olivos": (-34.5086, -58.4870),
    "san martin": (-34.5753, -58.5373),
    "general san martin": (-34.5753, -58.5373),
    "ezeiza": (-34.8537, -58.5229),
    "ciudad evita": (-34.7244, -58.5351),
    "avellaneda": (-34.6627, -58.3647),
    "llavallol": (-34.7961, -58.4276),
    "general pacheco": (-34.4524, -58.6346),
    "tigre": (-34.4260, -58.5796),
    "pilar": (-34.4587, -58.9142),
    "campana": (-34.1633, -58.9592),
}


def estimate_route_for_job(job: JobPosting, reference_location: str) -> RouteEstimate:
    ref = _coords_for(reference_location) or KNOWN_POINTS["belgrano"]
    coords = _coords_for(job.location)
    if coords is None:
        return RouteEstimate(job.location, None, None, None, None, True)

    straight = _haversine_km(ref[0], ref[1], coords[0], coords[1])
    road_km = straight * 1.35
    speed = 32 if _is_caba(job.location) else 42
    minutes = max(8, (road_km / speed) * 60)
    return RouteEstimate(job.location, coords[0], coords[1], round(road_km, 1), round(minutes, 0), True)


def _coords_for(location: str) -> tuple[float, float] | None:
    clean = normalize(location)
    if "buenos aires y alrededores" in clean:
        return KNOWN_POINTS["caba"]
    generic = {"buenos aires", "caba"}
    specific_items = sorted(
        ((key, coords) for key, coords in KNOWN_POINTS.items() if key not in generic),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    for key, coords in specific_items + [(key, KNOWN_POINTS[key]) for key in generic]:
        if key in clean:
            return coords
    return None


def _is_caba(location: str) -> bool:
    clean = normalize(location)
    return any(key in clean for key in ["caba", "ciudad autonoma", "retiro", "palermo", "belgrano", "nunez", "nuñez"])


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
