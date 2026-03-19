from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

# Database connection setup - Remember to paste your TiDB credentials here!
def get_db_connection():
    return mysql.connector.connect(
        host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="2F9h8KmcL9CA9h4.root",
        password="wbwt0FAtE8PtBU3q",
        database="defaultdb"
    )

@app.route('/')
def home():
    # Renders the main frontpage
    return render_template('index.html')

@app.route('/about')
def about():
    # Renders the About Us page
    return render_template('about.html')

@app.route('/search', methods=['GET'])
def search_city():
    city_name = request.args.get('city')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch City Info
    cursor.execute("SELECT * FROM cities WHERE name = %s", (city_name,))
    city_info = cursor.fetchone()
    
    if not city_info:
        return "City not found. Please try Mumbai, Hyderabad, Bhubaneswar, Punjab, or Kolkata.", 404

    # Fetch Tourist Places
    cursor.execute("SELECT * FROM places WHERE city_id = %s", (city_info['id'],))
    places = cursor.fetchall()

    # Fetch Accommodations (Hotels, Lodges, Restaurants, Cafes)
    cursor.execute("SELECT * FROM accommodations WHERE city_id = %s", (city_info['id'],))
    accommodations = cursor.fetchall()
    
    conn.close()
    
    return render_template('city.html', city=city_info, places=places, items=accommodations)

if __name__ == '__main__':
    app.run(debug=True)
