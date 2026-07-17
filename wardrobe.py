import csv
import os
import random

def load_styles_catalog(filepath="styles.csv"):
    """Load the full styles catalog with all clothing metadata."""
    styles = {}
    try:
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                styles[row['id']] = row
    except FileNotFoundError:
        print(f"Styles catalog not found: {filepath}")
    return styles

def load_clothes_links(filepath="clothes.csv"):
    """Load the clothes-to-image mapping."""
    links = {}
    try:
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Extract ID from filename (e.g., "15970.jpg" -> "15970")
                filename = row['filename']
                item_id = filename.replace('.jpg', '')
                links[item_id] = row['link']
    except FileNotFoundError:
        print(f"Clothes links file not found: {filepath}")
    return links

def get_wardrobe_context():
    """Generate context about available clothing catalog for the AI."""
    styles = load_styles_catalog()
    
    # Get some stats about what's available
    categories = set()
    types = set()
    colors = set()
    seasons = set()
    genders = set()
    
    for item in styles.values():
        if item.get('masterCategory'):
            categories.add(item.get('masterCategory'))
        if item.get('articleType'):
            types.add(item.get('articleType'))
        if item.get('baseColour'):
            colors.add(item.get('baseColour'))
        if item.get('season'):
            seasons.add(item.get('season'))
        if item.get('gender'):
            genders.add(item.get('gender'))
    
    context = f"""Available Clothing Catalog:
Total items: {len(styles)}
Categories: {', '.join(sorted(categories))}
Article Types: {', '.join(sorted(types)[:10])}... and more
Colors: {', '.join(sorted(colors)[:10])}... and more
Seasons: {', '.join(sorted(seasons))}
Demographics: {', '.join(sorted(genders))}

You can recommend items based on their attributes like:
- Article type (Shirts, Jeans, Tshirts, Dresses, Shoes, etc.)
- Season (Spring, Summer, Fall, Winter)
- Color and formality (Casual, Formal, Ethnic)
- Gender category (Men, Women, Boys, Girls, Unisex)
- Usage type (Casual, Formal, Sports, Ethnic)"""
    
    return context

def get_available_styles_by_season(season, limit=10):
    """Get available clothing styles for a specific season."""
    styles = load_styles_catalog()
    season_items = [
        item for item in styles.values() 
        if item.get('season', '').lower() == season.lower()
    ]
    return season_items[:limit]

def get_available_items_by_type(article_type, limit=10):
    """Get available items by article type (e.g., 'Shirts', 'Jeans')."""
    styles = load_styles_catalog()
    type_items = [
        item for item in styles.values() 
        if item.get('articleType', '').lower() == article_type.lower()
    ]
    return type_items[:limit]


def _parse_temperature(weather_info):
    if not weather_info:
        return None
    import re
    # Match temperature patterns like: 72°F, -96°F, 72.5°C, etc.
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*°[FC]", weather_info)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    # Fallback: try matching without degree symbol
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*[FC]", weather_info)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def _infer_season(weather_info):
    temp = _parse_temperature(weather_info)
    if temp is None:
        # If we can't parse temperature, default to Spring (moderate season)
        return "Spring"
    if temp <= 50:
        return "Winter"
    if temp <= 65:
        return "Fall"
    if temp <= 75:
        return "Spring"
    return "Summer"


def _is_variation_request(occasion):
    if not occasion:
        return False
    text = occasion.lower()
    variation_keywords = [
        'different outfit', 'another outfit', 'new outfit', 'other outfit',
        'change outfit', 'new look', 'different look', 'another look',
    ]
    return any(keyword in text for keyword in variation_keywords)


def _match_items(styles, season=None, usage=None, gender=None, article_types=None, max_items=10):
    candidates = []
    for item in styles.values():
        if season and item.get('season', '').lower() != season.lower():
            continue
        if usage and usage.lower() not in item.get('usage', '').lower():
            continue
        if gender and gender.lower() != "unisex" and item.get('gender', '').lower() not in [gender.lower(), "unisex"]:
            continue
        if article_types and item.get('articleType', '').lower() not in [a.lower() for a in article_types]:
            continue
        candidates.append(item)
    return candidates[:max_items]


def recommend_category_item(component, weather_info=None, occasion=None, gender="Unisex", variation=False, exclude_ids=None):
    styles = load_styles_catalog()
    links = load_clothes_links()
    season = _infer_season(weather_info)
    variation = variation or _is_variation_request(occasion)

    component_types = {
        'Top': ["Shirts", "Tshirts", "Kurtas", "Tops", "Sweatshirts", "Blazers", "Jackets", "Rain Jacket", "Waistcoat", "Dress", "Dresses"],
        'Bottom': ["Jeans", "Track Pants", "Shorts", "Skirts", "Sarees"],
        'Footwear': ["Shoes", "Formal Shoes", "Casual Shoes", "Sports Shoes", "Sandals", "Flip Flops", "Heels"],
        'Accessory': ["Bags", "Watches", "Belts", "Jewellery", "Sunglasses", "Scarves", "Bracelets", "Pendant", "Wallets"],
    }

    if component not in component_types:
        return None

    article_types = component_types[component]
    usage = None
    if occasion:
        text = occasion.lower()
        if any(k in text for k in ["formal", "professional", "work", "meeting", "business", "interview", "presentation"]):
            if "business casual" in text or "business-casual" in text:
                usage = "Casual"
            else:
                usage = "Formal"
        elif "casual" in text:
            usage = "Casual"
        elif "sports" in text or "sport" in text or "gym" in text:
            usage = "Sports"
        elif "ethnic" in text:
            usage = "Ethnic"

    candidates = _match_items(
        styles,
        season=season,
        usage=usage,
        gender=gender,
        article_types=article_types,
        max_items=50,
    )

    if exclude_ids:
        candidates = [item for item in candidates if item.get('id') not in exclude_ids]

    if not candidates:
        candidates = _match_items(
            styles,
            season=None,
            usage=usage,
            gender=gender,
            article_types=article_types,
            max_items=50,
        )
        if exclude_ids:
            candidates = [item for item in candidates if item.get('id') not in exclude_ids]

    if not candidates:
        return None

    chosen = None
    usage_matches = []
    if usage:
        usage_matches = [c for c in candidates if usage.lower() in c.get('usage', '').lower()]

    if usage and usage_matches:
        chosen = random.choice(usage_matches) if variation else usage_matches[0]
    elif variation and len(candidates) > 0:
        chosen = random.choice(candidates)
    else:
        chosen = sorted(candidates, key=lambda x: (x.get('usage', ''), x.get('articleType', ''), x.get('baseColour', '')))[0]

    item = dict(chosen)
    item['link'] = links.get(item['id'])
    return item


def recommend_outfit(weather_info=None, occasion=None, gender="Unisex", variation=False):
    """Return a set of outfit items from the available catalog."""
    styles = load_styles_catalog()
    links = load_clothes_links()
    season = _infer_season(weather_info)
    variation = variation or _is_variation_request(occasion)

    usage = None
    if occasion:
        text = occasion.lower()
        # Treat work/meeting/professional/business/interview/presentation as formal
        if any(k in text for k in ["formal", "professional", "work", "meeting", "business", "interview", "presentation"]):
            # Allow explicit "business casual" to be treated as casual
            if "business casual" in text or "business-casual" in text:
                usage = "Casual"
            else:
                usage = "Formal"
        elif "casual" in text:
            usage = "Casual"
        elif "sports" in text or "sport" in text or "gym" in text:
            usage = "Sports"
        elif "ethnic" in text:
            usage = "Ethnic"

    outfit_parts = [
        ("Top", ["Shirts", "Tshirts", "Kurtas", "Tops", "Sweatshirts", "Blazers", "Jackets", "Rain Jacket", "Waistcoat", "Dress", "Dresses"]),
        ("Bottom", ["Jeans", "Track Pants", "Shorts", "Skirts", "Sarees"]),
        ("Footwear", ["Shoes", "Formal Shoes", "Casual Shoes", "Sports Shoes", "Sandals", "Flip Flops", "Heels"]),
        ("Accessory", ["Bags", "Watches", "Belts", "Jewellery", "Sunglasses", "Scarves", "Bracelets", "Pendant", "Wallets"]),
    ]

    outfit = []
    for part_name, article_types in outfit_parts:
        candidates = _match_items(
            styles,
            season=season,
            usage=usage,
            gender=gender,
            article_types=article_types,
            max_items=20
        )

        if not candidates:
            candidates = _match_items(
                styles,
                season=None,
                usage=usage,
                gender=gender,
                article_types=article_types,
                max_items=20
            )

        if candidates:
            chosen = None
            usage_matches = []
            if usage:
                usage_matches = [c for c in candidates if usage.lower() in c.get('usage', '').lower()]

            if usage and usage_matches:
                chosen = random.choice(usage_matches) if variation else usage_matches[0]
            elif variation and len(candidates) > 0:
                chosen = random.choice(candidates)
            else:
                chosen = sorted(candidates, key=lambda x: (x.get('usage', ''), x.get('articleType', ''), x.get('baseColour', '')))[0]

            item = dict(chosen)
            item['link'] = links.get(item['id'])
            item['component'] = part_name
            outfit.append(item)

    return outfit


def format_outfit(outfit):
    if not outfit:
        return "No catalog outfit could be found."

    lines = []
    for item in outfit:
        description = f"{item.get('component')}: {item.get('productDisplayName')}"
        details = []
        if item.get('articleType'):
            details.append(item['articleType'])
        if item.get('baseColour'):
            details.append(item['baseColour'])
        if item.get('season'):
            details.append(item['season'])
        if item.get('usage'):
            details.append(item['usage'])
        if details:
            description += f" ({', '.join(details)})"
        if item.get('link'):
            description += f" - {item['link']}"
        lines.append(description)
    return "\n".join(lines)


if __name__ == "__main__":
    print(get_wardrobe_context())

