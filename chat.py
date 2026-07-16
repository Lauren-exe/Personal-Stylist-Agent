import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from weather import get_weather, get_coordinates, get_coordinates_with_fallback, normalize_location_input
from wardrobe import (
    get_wardrobe_context,
    get_available_styles_by_season,
    get_available_items_by_type,
    recommend_outfit,
    format_outfit,
)


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


def resolve_location(initial_location, client):
    """Resolve a user-provided location and confirm it before using it."""
    if not initial_location:
        return 37.8715, -122.2730, "Berkeley, California"

    normalized = normalize_location_input(initial_location)
    if normalized is None:
        print("I couldn't understand that location. Please enter a city or place name again.")
        alternate = input("Enter a different city or place: ").strip()
        if not alternate:
            return 37.8715, -122.2730, "Berkeley, California"
        return resolve_location(alternate, client)

    if normalized.lower() != initial_location.strip().lower():
        print(f"Did you mean: {normalized}?")

    latitude, longitude, location_name = get_coordinates_with_fallback(normalized, client)
    if latitude is None:
        print(f"I couldn't find location '{normalized}'. Please enter a city or place name again.")
        alternate = input("Enter a different city or place: ").strip()
        if not alternate:
            return 37.8715, -122.2730, "Berkeley, California"
        return resolve_location(alternate, client)

    if client is None:
        confirmation = input(f"I found '{location_name}'. Is that the right place? [Y/n]: ").strip().lower()
        while confirmation not in {"", "y", "yes", "n", "no"}:
            confirmation = input("Please answer yes or no: ").strip().lower()

        if confirmation in {"", "y", "yes"}:
            return latitude, longitude, location_name

        alternate = input("Enter a different city or place: ").strip()
        if not alternate:
            return 37.8715, -122.2730, "Berkeley, California"
        return resolve_location(alternate, client)

    try:
        prompt = (
            f"The user typed '{initial_location}'. Reply with one short sentence naming the most likely place "
            f"and asking for confirmation."
        )
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        ai_reply = response.choices[0].message.content.strip()
        print(f"AI location check: {ai_reply}")
    except Exception as e:
        print(f"AI location check unavailable ({e}). Using the geocoded result.")
        ai_reply = f"I found {location_name}."

    confirmation = input("Is that the right place? [Y/n]: ").strip().lower()
    while confirmation not in {"", "y", "yes", "n", "no"}:
        confirmation = input("Please answer yes or no: ").strip().lower()

    if confirmation in {"", "y", "yes"}:
        return latitude, longitude, location_name

    alternate = input("Enter a different city or place: ").strip()
    if not alternate:
        return 37.8715, -122.2730, "Berkeley, California"
    return resolve_location(alternate, client)


def should_use_local_recommender(user_input):
    keywords = ["outfit", "what to wear", "wear", "style", "recommend", "suggest", "clothing", "wardrobe"]
    text = user_input.lower()
    return any(keyword in text for keyword in keywords)


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

    if should_use_local_recommender(user_input):
        outfit = recommend_outfit(weather_info=weather_info, occasion=user_input)
        if outfit:
            print("AI: Here are actual catalog items from your wardrobe:")
            print(format_outfit(outfit))
        else:
            print("AI: I couldn't find matching items in the catalog.")
        continue

    if client is None:
        if "help" in user_input.lower():
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

