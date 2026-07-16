import os
from openai import OpenAI
from weather import get_weather, get_coordinates
from wardrobe import get_wardrobe_context, get_available_styles_by_season, get_available_items_by_type


# Read API key and optional base URL from environment
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")

if api_key:
    client = OpenAI(api_key=api_key, base_url=base_url)
else:
    client = None
    print("Warning: OPENAI_API_KEY not set — running in offline mock mode.")

# Ask user for location
print("Where are you located? (Default: Berkeley, California)")
user_location = input("Enter your location (or press Enter for Berkeley): ").strip()

if not user_location:
    user_location = "Berkeley, California"
    latitude, longitude, location_name = 37.8715, -122.2730, "Berkeley, California"
else:
    latitude, longitude, location_name = get_coordinates(user_location)
    if latitude is None:
        print(f"Could not find location '{user_location}'. Using Berkeley as default.")
        latitude, longitude, location_name = 37.8715, -122.2730, "Berkeley, California"

# Get weather for the user's location
print(f"\nFetching weather for {location_name}...")
weather_info = get_weather(latitude, longitude)
if not weather_info:
    weather_info = "Weather data unavailable"


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

