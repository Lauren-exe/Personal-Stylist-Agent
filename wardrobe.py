import csv
import os

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

if __name__ == "__main__":
    print(get_wardrobe_context())

