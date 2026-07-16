import os
from openai import OpenAI
from weather import get_weather

# Read API key and optional base URL from environment
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")

if api_key:
    client = OpenAI(api_key=api_key, base_url=base_url)
else:
    client = None
    print("Warning: OPENAI_API_KEY not set — running in offline mock mode.")

# Get weather
weather_info = get_weather()
if not weather_info:
    weather_info = "Weather data unavailable"

# System prompt with weather
system_prompt = f"""You are a helpful personal stylist AI assistant. 
You help users with clothing and fashion advice.

Current weather in Berkeley, CA: {weather_info}

When giving outfit recommendations, take the current weather into account."""

print("Talk to the AI (type 'quit' to stop)")

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    if client is None:
        # Simple offline fallback so the script remains usable without an API key
        if "outfit" in user_input.lower() or "help" in user_input.lower():
            mock = f"(mock) Based on the weather ({weather_info}), I'd suggest wearing something appropriate for the conditions."
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
