import requests

def test_osm_api():
    print("🛰️ Pinging OpenStreetMap (Overpass API) for Mumbai...")
    
    # Coordinates for Mumbai (Gateway of India)
    lat, lon = 18.9220, 72.8347
    
    # Query to find real hotels and restaurants within a 2km radius
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["tourism"="hotel"](around:2000,{lat},{lon});
      node["amenity"="restaurant"](around:2000,{lat},{lon});
    );
    out 5;
    """
    
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=10)
        
        if response.status_code == 200:
            print("✅ CONNECTION SUCCESSFUL! No API Key needed.\n")
            data = response.json()
            
            for element in data.get('elements', []):
                tags = element.get('tags', {})
                name = tags.get('name')
                if name:
                    category = "Hotel" if tags.get('tourism') == 'hotel' else "Dining"
                    print(f"📍 Found {category}: {name}")
        else:
            print(f"❌ FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ NETWORK ERROR: {e}")

if __name__ == "__main__":
    test_osm_api()