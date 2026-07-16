import requests

def get_weather():
    url = "https://api.open-meteo.com/v1/forecast"  # ← Fix: Add the full endpoint path
    
    query_parameters = {
        "latitude": 37.8715,
        "longitude": -122.2730,
        "current": "temperature_2m,wind_speed_10m",
        "temperature_unit": "fahrenheit"
    }
    
    try:
        response = requests.get(url, params=query_parameters)
        
        # Check if the server sent an error code
        if response.status_code != 200:
            print(f"Server returned Error Status Code: {response.status_code}")
            print(f"Server Raw Message: {response.text}")
            return
            
        # Try parsing JSON safely
        data = response.json()
        current = data["current"]
        temp = current["temperature_2m"]
        wind = current["wind_speed_10m"]
        units = data["current_units"]
        
        print("\n--- Current Weather (Berkeley, CA) ---")
        print(f"Temperature: {temp}{units['temperature_2m']}")
        print(f"Wind Speed:  {wind}{units['wind_speed_10m']}")
        print("--------------------------------------\n")
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
    except ValueError as e:
        print(f"JSON Parsing Error: {e}")
        print(f"The web response was not valid JSON. Response content: {response.text}")

if __name__ == "__main__":
    get_weather()
    
