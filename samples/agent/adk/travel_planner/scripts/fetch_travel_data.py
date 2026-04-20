import os
import json
import urllib.request
import urllib.parse
import ssl
from pathlib import Path

# Manual ENV loading since we can't use python-dotenv
def load_env_manual():
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value

load_env_manual()
API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

if not API_KEY:
    print("Error: GOOGLE_MAPS_API_KEY not found.")
    exit(1)

CITIES = ["Tokyo", "Paris", "New York", "London", "Shanghai"]
DATA_DIR = Path("samples/agent/adk/travel_planner/data")
IMAGE_DIR = DATA_DIR / "images"
OUTPUT_FILE = DATA_DIR / "travel_data.json"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)

def http_get(url):
    # Bypass SSL cert issues in some environments
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    with urllib.request.urlopen(url, context=ctx) as response:
        return response.read()

def download_photo(photo_reference, filename):
    try:
        url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_reference}&key={API_KEY}"
        data = http_get(url)
        filepath = IMAGE_DIR / filename
        with open(filepath, 'wb') as f:
            f.write(data)
        return f"static/{filename}"
    except Exception as e:
        print(f"Failed to download photo {filename}: {e}")
        return None

def fetch_city_data(city_name):
    print(f"Fetching data for {city_name}...")
    
    # 1. Search for places
    query = urllib.parse.quote(f"top attractions in {city_name}")
    search_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={API_KEY}"
    
    search_data = json.loads(http_get(search_url).decode('utf-8'))
    
    landmarks = []
    for i, place in enumerate(search_data.get('results', [])[:5]):
        place_id = place['place_id']
        
        # 2. Get Place Details
        details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_address,rating,editorial_summary,photos&key={API_KEY}"
        details_resp = json.loads(http_get(details_url).decode('utf-8'))
        result = details_resp.get('result', {})
        
        photo_path = None
        if 'photos' in result:
            photo_ref = result['photos'][0]['photo_reference']
            filename = f"{city_name.lower().replace(' ', '_')}_{i}.jpg"
            photo_path = download_photo(photo_ref, filename)

        landmarks.append({
            "id": place_id,
            "name": result.get('name'),
            "address": result.get('formatted_address'),
            "rating": result.get('rating'),
            "description": result.get('editorial_summary', {}).get('overview', 'No description available.'),
            "image_url": photo_path
        })
    
    return {
        "city": city_name,
        "landmarks": landmarks
    }

def main():
    all_data = []
    for city in CITIES:
        try:
            city_data = fetch_city_data(city)
            all_data.append(city_data)
        except Exception as e:
            print(f"Failed to fetch data for {city}: {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nSuccess! Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
