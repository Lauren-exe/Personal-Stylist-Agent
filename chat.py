import json
import os
import sys
import http.server
import socketserver

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from weather import get_weather, get_coordinates, get_coordinates_with_fallback, normalize_location_input
from wardrobe import (
    get_wardrobe_context,
    recommend_outfit,
    recommend_category_item,
    format_outfit,
    load_styles_catalog,
)

# Read API key and optional base URL from environment
api_key = os.getenv('OPENAI_API_KEY') or os.getenv('GROK_API_KEY')
base_url = os.getenv('OPENAI_BASE_URL') or os.getenv('GROK_BASE_URL', 'https://api.groq.com/openai/v1')

if api_key and OpenAI is not None:
    client = OpenAI(api_key=api_key, base_url=base_url)
else:
    client = None
    if OpenAI is None:
        print('Warning: openai package not installed; running in offline mock mode.')
    else:
        print('Warning: OPENAI_API_KEY or GROK_API_KEY not set — running in offline mock mode.')

session_state = {
    'last_occasion': None,
    'last_outfit': None,
}


def target_outfit_component(message):
    if not message:
        return None
    text = message.lower()
    accessory_keywords = ['accessory', 'belt', 'bag', 'watch', 'jewellery', 'jewelry', 'scarf', 'sunglasses', 'bracelet', 'pendant', 'wallet']
    top_keywords = ['top', 'shirt', 't-shirt', 'tshirt', 'blouse', 'jacket', 'coat', 'blazer', 'sweatshirt', 'hoodie', 'kurta', 'dress', 'dresses']
    bottom_keywords = ['bottom', 'pants', 'trouser', 'trousers', 'jeans', 'skirt', 'short', 'shorts', 'saree']
    footwear_keywords = ['shoe', 'shoes', 'sandal', 'sandals', 'heel', 'heels', 'sneaker', 'sneakers', 'boot', 'boots', 'footwear']

    if any(word in text for word in accessory_keywords):
        return 'Accessory'
    if any(word in text for word in top_keywords):
        return 'Top'
    if any(word in text for word in bottom_keywords):
        return 'Bottom'
    if any(word in text for word in footwear_keywords):
        return 'Footwear'
    return None


def resolve_location_api(initial_location):
    """Resolve a location for API use without interactive prompts."""
    if not initial_location:
        return 37.8715, -122.2730, 'Berkeley, California'

    normalized = normalize_location_input(initial_location)
    if normalized is None:
        return 37.8715, -122.2730, 'Berkeley, California'

    latitude, longitude, location_name = get_coordinates(normalized)
    if latitude is None or longitude is None:
        latitude, longitude, location_name = get_coordinates_with_fallback(normalized, client=client)

    if latitude is None or longitude is None:
        return 37.8715, -122.2730, 'Berkeley, California'

    return latitude, longitude, location_name


def should_use_local_recommender(user_input):
    keywords = [
        'outfit', 'what to wear', 'wear', 'style', 'recommend', 'suggest',
        'clothing', 'wardrobe', 'meeting', 'work', 'professional', 'formal',
        'different', 'another', 'new look', 'accessory', 'top', 'bottom',
        'shoes', 'shoe', 'jacket', 'coat', 'dress', 'skirt', 'pants', 'trousers',
        'blazer', 'bag', 'belt', 'jeans', 'shirt', 'sweater', 'suit', 'casual',
        'business casual', 'business-casual', 'sports', 'gym'
    ]
    text = user_input.lower()
    return any(keyword in text for keyword in keywords)


def is_variation_request(message):
    if not message:
        return False
    text = message.lower().strip()
    variation_keywords = [
        'different outfit', 'another outfit', 'new outfit', 'other outfit',
        'change outfit', 'new look', 'different look', 'another look',
    ]
    return any(keyword in text for keyword in variation_keywords)


def create_system_prompt(location_name, weather_info, preferred_gender, wardrobe_context):
    return f'''You are a helpful personal stylist AI assistant.
You help users with clothing and fashion advice.

Current weather in {location_name}: {weather_info}
Preferred clothing profile: {preferred_gender}

{wardrobe_context}

When giving outfit recommendations:
1. Consider the current weather and suggest appropriate items
2. Reference specific article types, colors, and styles from the available catalog
3. Consider season, warmth, and formality level for the occasion
4. Give specific recommendations (e.g., "A Navy Blue casual shirt with blue jeans")
5. Explain why recommendations work for the weather and occasion'''


def process_user_message(message, location, gender):
    latitude, longitude, location_name = resolve_location_api(location)
    weather_info = get_weather(latitude, longitude)
    if not weather_info:
        weather_info = 'Weather data unavailable'

    result = {
        'location_name': location_name,
        'weather_info': weather_info,
        'preferred_gender': gender,
    }

    use_local = should_use_local_recommender(message) or (is_variation_request(message) and session_state.get('last_occasion'))
    if use_local:
        category = target_outfit_component(message)
        if category and session_state.get('last_outfit'):
            occasion = session_state.get('last_occasion') or message
            exclude_ids = [item['id'] for item in session_state['last_outfit'] if item.get('component') == category]
            replacement = recommend_category_item(
                category,
                weather_info=weather_info,
                occasion=occasion,
                gender=gender,
                variation=True,
                exclude_ids=exclude_ids,
            )
            if replacement:
                outfit = []
                for item in session_state['last_outfit']:
                    if item.get('component') == category:
                        new_item = dict(replacement)
                        new_item['component'] = category
                        outfit.append(new_item)
                    else:
                        outfit.append(item)
                session_state['last_outfit'] = outfit
                result.update({
                    'type': 'outfit',
                    'outfit': outfit,
                })
                return result

        if is_variation_request(message) and session_state.get('last_occasion'):
            occasion = session_state['last_occasion']
            variation = True
        elif session_state.get('last_occasion') and any(keyword in message.lower() for keyword in ['different', 'another', 'change', 'accessory', 'top', 'bottom', 'shoe', 'shoes', 'jacket', 'coat', 'dress', 'skirt', 'pants', 'trousers', 'blazer', 'bag', 'belt']):
            occasion = session_state['last_occasion']
            variation = True
        else:
            occasion = message
            variation = False
            session_state['last_occasion'] = message

        outfit = recommend_outfit(weather_info=weather_info, occasion=occasion, gender=gender, variation=variation)
        session_state['last_outfit'] = outfit
        result.update({
            'type': 'outfit',
            'outfit': outfit,
        })
        return result

    if client is None:
        result.update({
            'type': 'text',
            'content': f'(mock) Based on the weather ({weather_info}) and your wardrobe, I would suggest pieces that fit the occasion.',
        })
        return result

    try:
        wardrobe_context = get_wardrobe_context()
        system_prompt = create_system_prompt(location_name, weather_info, gender, wardrobe_context)
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': message},
            ],
        )
        text = response.choices[0].message.content
        result.update({
            'type': 'text',
            'content': text,
        })
    except Exception as exc:
        if should_use_local_recommender(message) or is_variation_request(message):
            occasion = session_state.get('last_occasion') or message
            outfit = recommend_outfit(weather_info=weather_info, occasion=occasion, gender=gender, variation=is_variation_request(message))
            result.update({
                'type': 'outfit',
                'outfit': outfit,
            })
        else:
            result.update({
                'type': 'error',
                'content': f'AI: (error calling API) {exc}',
            })
    return result


class AgentHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.path = '/personal-stylist-ui.html'
        return super().do_GET()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        if self.path == '/api/setup':
            location = data.get('location', '')
            gender = data.get('gender', 'Unisex')
            latitude, longitude, location_name = resolve_location_api(location)
            weather_info = get_weather(latitude, longitude)
            if not weather_info:
                weather_info = 'Weather data unavailable'
            wardrobe_context = get_wardrobe_context()
            payload = {
                'location_name': location_name,
                'weather_info': weather_info,
                'preferred_gender': gender,
                'catalog_count': len(load_styles_catalog()),
                'wardrobe_context': wardrobe_context,
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode('utf-8'))
            return

        if self.path == '/api/message':
            message = data.get('message', '')
            location = data.get('location', '')
            gender = data.get('gender', 'Unisex')
            payload = process_user_message(message, location, gender)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()


def run_server(port=8000):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with socketserver.TCPServer(('0.0.0.0', port), AgentHTTPRequestHandler) as httpd:
        print(f'Serving UI and agent at http://localhost:{port}')
        httpd.serve_forever()


def run_cli():
    print('This application now prefers the web UI.')
    print('Run: python3 chat.py')


if __name__ == '__main__':
    if '--cli' in sys.argv:
        run_cli()
    else:
        run_server()
