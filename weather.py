import re
from itertools import product
import requests


def _distance(a, b):
    """Simple Levenshtein-style distance for tiny typo correction."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def _suggest_word(word, common_words):
    """Return a likely correction for a single word using a small candidate set."""
    if not word:
        return word
    word_lower = word.lower()
    if word_lower in common_words:
        return word_lower

    best_word = word_lower
    best_dist = float("inf")
    for candidate in common_words:
        dist = _distance(word_lower, candidate)
        if dist < best_dist:
            best_dist = dist
            best_word = candidate
    if best_dist <= 2:
        return best_word
    return word_lower


def _word_variants(word):
    """Generate a small set of likely variants for a single word."""
    base = word.lower().strip(".,;:-")
    if not base:
        return [word]

    variants = {base}
    vowels = "aeiou"

    # Transposition of adjacent letters
    for index in range(len(base) - 1):
        swapped = base[:index] + base[index + 1] + base[index] + base[index + 2:]
        variants.add(swapped)

    # Missing-vowel insertions
    for index in range(len(base) + 1):
        for vowel in vowels:
            variants.add(base[:index] + vowel + base[index:])

    # Common one-letter typo patterns
    for index in range(len(base)):
        for vowel in vowels:
            variant = base[:index] + vowel + base[index + 1:]
            variants.add(variant)

    # Drop one letter if the word is longer than 3
    if len(base) > 3:
        for index in range(len(base)):
            variants.add(base[:index] + base[index + 1:])

    return list(variants)[:10]


def _phrase_variants(text):
    """Create a short list of candidate phrases from a user-entered location."""
    cleaned = re.sub(r"\s+", " ", text.strip())
    cleaned = cleaned.replace(",", " , ")
    cleaned = cleaned.strip()

    words = [word.strip(".,;:-") for word in cleaned.split() if word.strip(".,;:-")]
    if not words:
        return []

    variant_lists = [_word_variants(word) for word in words]
    candidates = set()

    for combo in product(*variant_lists):
        phrase = " ".join(combo)
        candidates.add(phrase)
        candidates.add(phrase.replace(" ", ", "))
        candidates.add(phrase.replace(" ", "-"))

    return list(candidates)


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


def normalize_location_input(location_name):
    """Apply simple normalization and typo correction to a city/state input.

    Returns a cleaned string when the input looks understandable, or None when it
    is too ambiguous to use safely.
    """
    if not location_name:
        return None

    cleaned = location_name.strip()
    if not cleaned:
        return None

    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.replace(",", ", ")
    cleaned = cleaned.strip()

    if re.fullmatch(r"[\W_]+", cleaned):
        return None

    # Preserve obvious state abbreviations and common place names.
    candidate_forms = []

    # Keep the original form first.
    candidate_forms.append(cleaned)

    # Add a version with expanded abbreviations, but only when it seems helpful.
    expanded = _expand_abbreviations(cleaned)
    if expanded != cleaned:
        candidate_forms.append(expanded)

    # Add a compact comma-separated version for city,state inputs.
    if "," in cleaned:
        parts = [part.strip() for part in cleaned.split(",") if part.strip()]
        if len(parts) == 2:
            city, state = parts
            compact = f"{city} {state}".strip()
            candidate_forms.append(compact)
            candidate_forms.append(f"{city}, {state}")

    # Avoid over-aggressive variants that can corrupt valid names.
    for variant in _phrase_variants(cleaned):
        normalized_variant = re.sub(r"\s+", " ", variant).strip()
        if normalized_variant and normalized_variant not in candidate_forms:
            candidate_forms.append(normalized_variant)

    seen = []
    for candidate in candidate_forms:
        if not candidate or candidate in seen:
            continue
        seen.append(candidate)

    for candidate in seen:
        if re.fullmatch(r"[\W_]+", candidate):
            continue
        if len(candidate) < 2:
            continue

        parts = [p.strip() for p in candidate.split(",") if p.strip()]
        if len(parts) == 2:
            city = parts[0].strip()
            state = parts[1].strip()
            if state.isupper() and len(state) <= 5:
                return f"{city.title()}, {state.upper()}"
            return f"{city.title()}, {state.title()}"

        if len(parts) == 1:
            return candidate.title()

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
                city = result.get("name")
                country = result.get("country")
                return lat, lon, f"{city}, {country}"
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

