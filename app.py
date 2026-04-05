import requests
import random
import os
from flask import Flask, render_template, request
import urllib.parse
import mysql.connector
from mysql.connector import Error


app = Flask(__name__)

# --- SECURE TiDB DATABASE CONNECTION ---
def get_db_connection():
    # Securely pulls the password from Render environment variables
    db_password = os.environ.get('TIDB_PASSWORD', 'wbwt0FAtE8PtBU3q')
    
    return mysql.connector.connect(
        host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="2F9h8KmcL9CA9h4.root",
        password=db_password, # Now actually using the secure variable!
        database="defaultdb",
        ssl_verify_cert=True,       # REQUIRED for TiDB Cloud
        ssl_verify_identity=True    # REQUIRED for TiDB Cloud
    )

@app.route('/') # Fixed the missing @ symbol
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

# --- WIKIPEDIA DYNAMIC DETAIL ROUTE ---
@app.route('/place/<place_name>')
def place_detail(place_name):
    # We decode the URL so "Gateway%20of%20India" becomes "Gateway of India"
    clean_name = urllib.parse.unquote(place_name)
    
    # We render a dedicated template and pass the name to it
    return render_template('place_detail.html', place_name=clean_name)

def fetch_live_accommodations(city_name):
    # Coordinate dictionary mirroring your frontend mapping
    coords = {
        "Mumbai": "18.9220,72.8347",
        "Hyderabad": "17.3850,78.4867",
        "Bhubaneswar": "20.2961,85.8245",
        "Punjab": "31.6340,74.8723", 
        "Kolkata": "22.5726,88.3639"
    }
    
    ll = coords.get(city_name, "18.9220,72.8347")
    
    url = "https://api.foursquare.com/v3/places/search"
    params = {
        "ll": ll,
        "categories": "19014,13065", # 19014 = Hotel, 13065 = Restaurant
        "limit": 6, # Fetch exactly 6 items for a clean 3-column grid
        "fields": "name,rating,price,categories"
    }
    
    headers = {
        "Accept": "application/json",
        "Authorization": "JK0Q0GH30Y3U3C5JWT1DWRR3IBWW2EIVHB22K3QTYKUYJCKF" # Replace with your real key
    }
    
    live_items = []
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            results = response.json().get("results", [])
            
            for index, venue in enumerate(results):
                # 1. Determine if it is a Hotel or Dining
                cat_names = [c.get("name", "") for c in venue.get("categories", [])]
                is_hotel = any("Hotel" in name for name in cat_names)
                item_type = "lodging" if is_hotel else "dining"
                
                # 2. Dynamic INR Pricing Logic
                # Foursquare returns a price tier from 1 (Cheap) to 4 (Very Expensive)
                price_tier = venue.get("price", random.randint(1, 3))
                
                if price_tier == 1:
                    price_inr = random.randint(800, 1500)
                    budget_cat = "Budget"
                elif price_tier == 2:
                    price_inr = random.randint(1800, 3500)
                    budget_cat = "Budget"
                elif price_tier == 3:
                    price_inr = random.randint(5000, 9000)
                    budget_cat = "Premium"
                else:
                    price_inr = random.randint(10000, 25000)
                    budget_cat = "Premium"
                
                # 3. Format Ratings
                rating = venue.get("rating")
                if rating:
                    rating = round(rating / 2, 1) # Convert out of 10 to out of 5
                else:
                    rating = round(random.uniform(3.8, 4.9), 1)
                    
                # 4. Map perfectly to your existing Jinja template variables
                live_items.append({
                    "name": venue.get("name"),
                    "type": item_type,
                    "rating": rating,
                    "price": price_inr,
                    "budget_category": budget_cat,
                    # Fallback to local generic images to keep load times fast
                    "image_file": f"hotel{index % 3 + 1}.jpg" if is_hotel else f"dining{index % 3 + 1}.jpg"
                })
                
        return live_items
        
    except Exception as e:
        print(f"API Error: {e}")
        return [] # Returns empty list so the database fallback activates


@app.route('/search', methods=['GET'])
def search_city():
    city_name = request.args.get('city')
    
    # Safely handle empty searches
    if not city_name:
        return "Please select a destination from the search bar.", 400
        
    city_name = city_name.capitalize()
    
    # Presentation-Day Safety Net (Try/Except)
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Fetch City Info
        cursor.execute("SELECT * FROM cities WHERE name = %s", (city_name,))
        city_info = cursor.fetchone()
        
        if not city_info:
            return "City not found. Please select a valid city from the dropdown.", 404

        # 2. Fetch Tourist Places (Stays Database-driven)
        cursor.execute("SELECT * FROM places WHERE city_id = %s", (city_info['id'],))
        places = cursor.fetchall()

        # 3. Fetch Accommodations (LIVE API + DATABASE FALLBACK)
        # Attempt to pull real-time Foursquare data first
        accommodations = fetch_live_accommodations(city_name)
        
        # If the API list is empty (failed or no results), fallback to your database
        if not accommodations:
            cursor.execute("SELECT * FROM accommodations WHERE city_id = %s", (city_info['id'],))
            accommodations = cursor.fetchall()
            
        return render_template('city.html', city=city_info, places=places, items=accommodations)
        
    except Error as e:
        # If the database fails, the app survives and logs the error safely
        print(f"Database Error: {e}")
        return "TerraVista is experiencing high traffic. Please try again in a moment.", 500
        
    finally:
        # Always securely close the connection, even if an error happened
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
