import re
from itertools import product
import requests


def _expand_abbreviations(text):
    """Expand common abbreviations for states and countries."""
    replacements = {
        "al": "alabama",
        "az": "arizona",
        "ar": "arkansas",
        "ca": "california",
        "calif": "california",
        "california": "california",
        "co": "colorado",
        "ct": "connecticut",
        "de": "delaware",
        "fl": "florida",
        "ga": "georgia",
        "hi": "hawaii",
        "id": "idaho",
        "il": "illinois",
        "in": "indiana",
        "ia": "iowa",
        "ks": "kansas",
        "ky": "kentucky",
        "la": "louisiana",
        "me": "maine",
        "md": "maryland",
        "ma": "massachusetts",
        "mi": "michigan",
        "mn": "minnesota",
        "ms": "mississippi",
        "mo": "missouri",
        "mt": "montana",
        "ne": "nebraska",
        "nv": "nevada",
        "nh": "new hampshire",
        "nj": "new jersey",
        "nm": "new mexico",
        "ny": "new york",
        "nc": "north carolina",
        "nd": "north dakota",
        "oh": "ohio",
        "ok": "oklahoma",
        "or": "oregon",
        "ore": "oregon",
        "oregon": "oregon",
        "pa": "pennsylvania",
        "ri": "rhode island",
        "sc": "south carolina",
        "sd": "south dakota",
        "tn": "tennessee",
        "tx": "texas",
        "tex": "texas",
        "texas": "texas",
        "ut": "utah",
        "vt": "vermont",
        "va": "virginia",
        "wa": "washington",
        "wash": "washington",
        "washington": "washington",
        "wv": "west virginia",
        "wi": "wisconsin",
        "wy": "wyoming",
        "uk": "united kingdom",
        "u.k.": "united kingdom",
        "usa": "united states",
        "us": "united states",
        "unitedstates": "united states"
    }

    words = []
    for word in text.split():
        words.append(replacements.get(word.lower().strip(".,;:-"), word))
    return " ".join(words)


def _format_location_label(result):
    """Build a readable label using city, region, and country in that order."""
    parts = []

    city = (result.get("name") or "").strip()
    if city:
        parts.append(city)

    admin1 = (result.get("admin1") or "").strip()
    if admin1 and admin1.lower() != city.lower():
        parts.append(admin1)

    country = (result.get("country") or "").strip()
    if country:
        parts.append(country)

    return ", ".join(parts)


def _apply_simple_location_corrections(text):
    """Apply a small set of common typo fixes for place names."""
    if not text:
        return text

    corrections = {
        "berkely": "berkeley",
        "berkley": "berkeley",
        "seatlle": "seattle",
        "sealtte": "seattle",
        "seattl": "seattle",
        "snafransico": "san francisco",
        "sanfransisco": "san francisco",
        "sanfransico": "san francisco",
        "potland": "portland",
        "orgon": "oregon",
        "londn": "london",
        "parsi": "paris",
        "frnace": "france",
        "frncae": "france",
    }

    cleaned = text.strip()
    for typo, fixed in corrections.items():
        cleaned = re.sub(rf"\b{re.escape(typo)}\b", fixed, cleaned, flags=re.IGNORECASE)

    cleaned = cleaned.replace(",", ", ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def normalize_location_input(location_name):
    """Apply a simple, conservative normalization for city/state input."""
    if not location_name:
        return None

    cleaned = location_name.strip()
    if not cleaned:
        return None

    cleaned = _apply_simple_location_corrections(cleaned)
    if re.fullmatch(r"[\W_]+", cleaned):
        return None

    if "," in cleaned:
        parts = [part.strip() for part in cleaned.split(",") if part.strip()]
        if len(parts) == 2:
            city, state = parts
            expanded_state = _expand_abbreviations(state).strip()
            expanded_state_title = expanded_state.title()
            return f"{city.title()}, {expanded_state_title}"

    if " " in cleaned:
        words = [word for word in cleaned.split() if word]
        if len(words) >= 2:
            last_word = words[-1]
            expanded_last = _expand_abbreviations(last_word).strip()
            if expanded_last.lower() != last_word.lower():
                return f"{' '.join(words[:-1]).title()} {expanded_last.title()}"

    return cleaned.title()


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
    normalized = normalize_location_input(location_name)
    if normalized is None:
        return None, None, None

    candidates = [normalized]
    if "," in normalized:
        parts = [part.strip() for part in normalized.split(",") if part.strip()]
        if len(parts) == 2:
            city, state = parts
            state_key = state.lower().strip(".,;:-")
            expanded_state = _expand_abbreviations(state).strip()
            expanded_state_title = expanded_state.title()
            candidates.extend([
                city,
                f"{city}, {state}",
                f"{city}, {expanded_state_title}",
                f"{city}, {state.title()}",
                f"{city}, {state.upper()}",
                f"{city} {state}",
                f"{city} {expanded_state_title}",
            ])

            if state_key != expanded_state:
                candidates.append(f"{city}, {expanded_state}")
                candidates.append(f"{city} {expanded_state}")

    for candidate in candidates:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": candidate,
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
                place = _format_location_label(result)
                return lat, lon, place
        except Exception as e:
            print(f"Geocoding error for '{candidate}': {e}")

    print(f"Location '{normalized}' not found.")
    return None, None, None


def get_coordinates_with_fallback(location_name, client=None):
    """Try a simple normalized geocode first, then optionally ask the model for help."""
    normalized = normalize_location_input(location_name)
    if normalized is None:
        return None, None, None

    lat, lon, place = get_coordinates(normalized)
    if lat is not None:
        return lat, lon, place

    if client is None:
        return None, None, None

    try:
        prompt = (
            f"The user typed '{location_name}'. Return only one short location name that is likely the intended place."
        )
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        refined = response.choices[0].message.content.strip()
        if refined:
            return get_coordinates(refined)
    except Exception:
        pass

    return None, None, None

