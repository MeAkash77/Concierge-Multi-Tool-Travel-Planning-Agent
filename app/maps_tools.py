import json
import os
import urllib.parse
import urllib.request


def geocode_address(address: str) -> str:
    """Uses Google Geocoding API to convert an address or place name into geographic coordinates.

    Args:
        address: The address or place name to geocode (e.g. 'Tokyo Tower', 'Eiffel Tower, Paris').

    Returns:
        JSON string with key fields (formatted_address, location: {latitude, longitude}).
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not configured."

    encoded_address = urllib.parse.quote_plus(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data.get("status") == "OK" and data.get("results"):
                top_result = data["results"][0]
                formatted = top_result.get("formatted_address")
                location = top_result.get("geometry", {}).get("location", {})
                return json.dumps(
                    {
                        "status": "success",
                        "input_address": address,
                        "formatted_address": formatted,
                        "location": {
                            "latitude": location.get("lat"),
                            "longitude": location.get("lng"),
                        },
                    },
                    indent=2,
                )
            return f"Geocoding failed for '{address}': {data.get('status', 'ZERO_RESULTS')}"
    except Exception as e:
        return f"Error executing Geocoding request: {str(e)}"


def search_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "restaurant",
    radius_meters: float = 1000.0,
) -> str:
    """Uses Google Places API (New) searchNearby endpoint to find places of a given type around coordinates.

    Args:
        latitude: Latitude coordinate of the search center.
        longitude: Longitude coordinate of the search center.
        place_type: Type of place to search for (e.g. 'restaurant', 'cafe', 'tourist_attraction', 'museum', 'lodging').
        radius_meters: Search radius in meters (default 1000.0).

    Returns:
        JSON string containing matching places with key fields (name, address, location).
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not configured."

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }

    body = {
        "includedTypes": [place_type.lower().strip()],
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": radius_meters,
            }
        },
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            places_raw = data.get("places", [])
            results = []
            for p in places_raw[:10]:  # Return top 10 places
                display_name = p.get("displayName", {}).get("text")
                address = p.get("formattedAddress")
                loc = p.get("location", {})
                results.append(
                    {
                        "name": display_name,
                        "address": address,
                        "location": {
                            "latitude": loc.get("latitude"),
                            "longitude": loc.get("longitude"),
                        },
                    }
                )
            return json.dumps(
                {
                    "status": "success",
                    "search_type": place_type,
                    "count": len(results),
                    "places": results,
                },
                indent=2,
            )
    except Exception as e:
        return f"Error executing Places (New) nearby search: {str(e)}"
