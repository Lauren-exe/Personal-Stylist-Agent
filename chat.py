import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from weather import get_weather, get_coordinates, get_coordinates_with_fallback, normalize_location_input
from wardrobe import get_wardrobe_context, get_available_styles_by_season, get_available_items_by_type


# Read API key and optional base URL from environment
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")

if api_key and OpenAI is not None:
    client = OpenAI(api_key=api_key, base_url=base_url)
else:
    client = None
    if OpenAI is None:
        print("Warning: openai package not installed; running in offline mock mode.")
    else:
        print("Warning: OPENAI_API_KEY not set — running in offline mock mode.")

from weather import get_weather, get_coordinates, normalize_location_input


def resolve_location(initial_location, client):
    """Resolve a user-provided location and ask again if it is unclear."""
    if not initial_location:
        return 37.8715, -122.2730, "Berkeley, California"

    normalized = normalize_location_input(initial_location)
    if normalized is None:
        print("I couldn't understand that location. Please enter a city or place name again.")
        alternate = input("Enter a different city or place: ").strip()
        if not alternate:
            return 37.8715, -122.2730, "Berkeley, California"
        return resolve_location(alternate, client)

    latitude, longitude, location_name = get_coordinates(normalized)
    if latitude is None:
        print(f"I couldn't confidently place '{initial_location}'. Please enter a city or place name again.")
        alternate = input("Enter a different city or place: ").strip()
        if not alternate:
            return 37.8715, -122.2730, "Berkeley, California"
        return resolve_location(alternate, client)

    confirmation = input(f"I found '{location_name}'. Is that the right place? [Y/n]: ").strip().lower()
    while confirmation not in {"", "y", "yes", "n", "no"}:
        confirmation = input("Please answer yes or no: ").strip().lower()

    if confirmation in {"", "y", "yes"}:
        return latitude, longitude, location_name

    alternate = input("Enter a different city or place: ").strip()
    if not alternate:
        return 37.8715, -122.2730, "Berkeley, California"
    return resolve_location(alternate, client)


# Ask user for location
print("Where are you located? (Default: Berkeley, California)")
user_location = input("Enter your location (or press Enter for Berkeley): ").strip()
latitude, longitude, location_name = resolve_location(user_location, client)

# Get weather for the user's location
print(f"\nFetching weather for {location_name}...")
weather_info = get_weather(latitude, longitude)
if not weather_info:
    weather_info = "Weather data unavailable"
    print("Using a fallback weather message because the live weather service did not respond.")


# Get catalog context
wardrobe_context = get_wardrobe_context()

# System prompt with weather and available catalog
system_prompt = f"""You are a helpful personal stylist AI assistant. 
You help users with clothing and fashion advice.

Current weather in {location_name}: {weather_info}

{wardrobe_context}

When giving outfit recommendations:
1. Consider the current weather and suggest appropriate items
2. Reference specific article types, colors, and styles from the available catalog
3. Consider season, warmth, and formality level for the occasion
4. Give specific recommendations (e.g., "A Navy Blue casual shirt with blue jeans")
5. Explain why recommendations work for the weather and occasion"""

print("Talk to the AI (type 'quit' to stop)")
print("You can ask about outfit recommendations, what to wear, or how to style something!\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    if client is None:
        # Simple offline fallback so the script remains usable without an API key
        if "outfit" in user_input.lower() or "help" in user_input.lower():
            mock = f"(mock) Based on the weather ({weather_info}) and your wardrobe, I'd suggest wearing something appropriate for the conditions."
        else:
            mock = f"(mock) I received: {user_input}"
        print("AI:", mock)
        continue

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )
        print("AI:", response.choices[0].message.content)
    except Exception as e:
        print("AI: (error calling API)", e)

