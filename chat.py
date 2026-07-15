
from openai import OpenAI

client = OpenAI(
    api_key="putapikeyhere",
    base_url="https://api.groq.com/openai/v1"
)

print("Talk to the AI (type 'quit' to stop)")

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": user_input}]
    )

    print("AI:", response.choices[0].message.content)

