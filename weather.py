import requests

def get_weather(latitude, longitude):
    """Fetch current weather for given coordinates and return a short string.

    Returns a string like "72°F, wind 5 m/s" or None on failure.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True,
        "temperature_unit": "fahrenheit"
    }

    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current_weather")
        if not current:
            print("Weather API did not return current weather.")
            return None

        temp = current.get("temperature")
        wind = current.get("windspeed")
        temp_unit = "°F" if params["temperature_unit"] == "fahrenheit" else "°C"

        # Build a concise human-readable string
        weather_str = f"{temp}{temp_unit}, wind {wind} m/s"

        print("\n--- Current Weather ---")
        print(f"Temperature: {temp}{temp_unit}")
        print(f"Wind Speed:  {wind} m/s")
        print("--------------------------------------\n")

        return weather_str

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None
    except ValueError as e:
        print(f"JSON Parsing Error: {e}")
        return None


def get_coordinates(location_name):
    """Get latitude/longitude for a location using geocoding."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": location_name,
        "count": 1,
        "language": "en",
        "format": "json"
    }
    
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("results") and len(data["results"]) > 0:
            result = data["results"][0]
            lat = result.get("latitude")
            lon = result.get("longitude")
            city = result.get("name")
            country = result.get("country")
            return lat, lon, f"{city}, {country}"
        else:
            print(f"Location '{location_name}' not found.")
            return None, None, None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None, None, None

