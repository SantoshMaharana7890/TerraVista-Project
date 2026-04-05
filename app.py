import os
import requests
import random
from flask import Flask, render_template, request
import urllib.parse
import mysql.connector
from mysql.connector import Error

# --- YOUR FOURSQUARE API KEY ---
FOURSQUARE_API_KEY = "fsq3HaOuSdgI03eyLi9dBNuFpZud/h1w2dDBseeV8jAeeak="

app = Flask(__name__)

# --- SECURE TiDB DATABASE CONNECTION ---
def get_db_connection():
    db_password = os.environ.get('TIDB_PASSWORD', 'wbwt0FAtE8PtBU3q')
    return mysql.connector.connect(
        host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="2F9h8KmcL9CA9h4.root",
        password=db_password,
        database="defaultdb",
        ssl_verify_cert=True,
        ssl_verify_identity=True
    )

# --- THE LIVE FOURSQUARE ENGINE ---
def fetch_live_accommodations(city_name):
    """Fetches live data and formats it to perfectly match the TiDB database structure."""
    
    # 1. Map your presentation cities to their map coordinates
    coords = {
        "Mumbai": "18.9220,72.8347",
        "Hyderabad": "17.3850,78.4867",
        "Bhubaneswar": "20.2961,85.8245",
        "Punjab": "31.6340,74.8723", 
        "Kolkata": "22.5726,88.3639"
    }
    ll = coords.get(city_name, "18.9220,72.8347")
    
    url = "https://places-api.foursquare.com/places/search"
    params = {
        "ll": ll,
        "categories": "19014,13065", # 19014 = Hotel, 13065 = Restaurant
        "limit": 6, # Fetch 6 items for a perfect 3-column UI grid
        "fields": "name,rating,price,categories"
    }
    
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY,
        "X-Places-Api-Version": "2025-02-05" 
    }
    
    live_items = []
    
    try:
        # 5-second timeout. If it takes longer, we abort and use the database.
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            results = response.json().get("results", [])
            
            for index, venue in enumerate(results):
                # Classify as Lodging or Dining
                cat_names = [c.get("name", "") for c in venue.get("categories", [])]
                is_hotel = any("Hotel" in name for name in cat_names)
                item_type = "lodging" if is_hotel else "dining"
                
                # Dynamic INR Pricing & Budget Categories based on Foursquare Price Tiers (1-4)
                price_tier = venue.get("price", random.randint(1, 3))
                if is_hotel:
                    price_inr = random.randint(1500, 3500) if price_tier <= 2 else random.randint(5000, 12000)
                else:
                    price_inr = random.randint(300, 800) if price_tier <= 2 else random.randint(1200, 3000)
                    
                budget_cat = "Premium" if price_tier >= 3 else "Budget"
                
                # Format Ratings (Foursquare uses a 10-point scale; we use 5)
                rating = venue.get("rating")
                rating = round(rating / 2, 1) if rating else round(random.uniform(3.8, 4.9), 1)
                    
                # Create a dictionary that mimics a database row exactly
                live_items.append({
                    "name": venue.get("name"),
                    "type": item_type,
                    "rating": rating,
                    "price": price_inr,
                    "budget_category": budget_cat,
                    # Fallback to local generic images
                    "image_file": f"hotel{index % 3 + 1}.jpg" if is_hotel else f"dining{index % 3 + 1}.jpg"
                })
                
        return live_items
        
    except Exception as e:
        print(f"Foursquare API Error (Falling back to Database): {e}")
        return [] 


# --- ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/place/<place_name>')
def place_detail(place_name):
    clean_name = urllib.parse.unquote(place_name)
    return render_template('place_detail.html', place_name=clean_name)

@app.route('/search', methods=['GET'])
def search_city():
    city_name = request.args.get('city')
    
    if not city_name:
        return "Please select a destination from the search bar.", 400
        
    city_name = city_name.capitalize()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Fetch City Info
        cursor.execute("SELECT * FROM cities WHERE name = %s", (city_name,))
        city_info = cursor.fetchone()
        
        if not city_info:
            return "City not found. Please select a valid city from the dropdown.", 404

        # 2. Fetch Tourist Places (Static Database)
        cursor.execute("SELECT * FROM places WHERE city_id = %s", (city_info['id'],))
        places = cursor.fetchall()

        # 3. Fetch Accommodations (Dynamic API First, Database Second)
        accommodations = fetch_live_accommodations(city_name)
        
        # The Graceful Fallback
        if not accommodations:
            cursor.execute("SELECT * FROM accommodations WHERE city_id = %s", (city_info['id'],))
            accommodations = cursor.fetchall()
        
        return render_template('city.html', city=city_info, places=places, items=accommodations)
        
    except Error as e:
        print(f"Database Error: {e}")
        return "TerraVista is experiencing high traffic. Please try again in a moment.", 500
        
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
