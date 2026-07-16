from openai import OpenAI
from weather import get_weather

client = OpenAI(
    api_key="apikey",
    base_url="https://api.groq.com/openai/v1"
)

# Get weather
weather_info = get_weather()
if not weather_info:
    weather_info = "Weather data unavailable"a

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

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )

    print("AI:", response.choices[0].message.content)
