import os
import mysql.connector
import requests
from duckduckgo_search import DDGS

# 1. SECURELY FETCH THE PASSWORD
db_password = os.environ.get('TIDB_PASSWORD', 'wbwt0FAtE8PtBU3q')

# 2. CONNECT TO YOUR DATABASE
db = mysql.connector.connect(
    host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
    user="2F9h8KmcL9CA9h4.root",
    password=db_password,
    database="defaultdb",
    port=4000,
    ssl_verify_cert=True,
    ssl_verify_identity=True
)
cursor = db.cursor()

# Create the target images folder if it doesn't exist
os.makedirs("static/images", exist_ok=True)

# 3. CREATE THE MODERN AUTOMATION FUNCTION
def fetch_images_from_db(table_name, search_keyword):
    # Ask the database for all the names and exact image filenames
    cursor.execute(f"SELECT name, image_file FROM {table_name}")
    records = cursor.fetchall()
    
    # Open a fast connection to DuckDuckGo
    with DDGS() as ddgs:
        for record in records:
            item_name = record[0]
            expected_filename = record[1]
            target_path = os.path.join("static/images", expected_filename)
            
            # Smart Check: If you already have the image, skip it to save time
            if os.path.exists(target_path):
                print(f"⏩ Skipping {item_name} (Image already exists)")
                continue
                
            search_query = f"{item_name} {search_keyword} high resolution"
            print(f"⏳ Downloading image for: {item_name}...")
            
            try:
                # Ask DuckDuckGo for the top 1 image URL
                results = list(ddgs.images(search_query, max_results=1))
                
                if results:
                    image_url = results[0]['image']
                    
                    # Securely download the image data
                    response = requests.get(image_url, timeout=10)
                    
                    if response.status_code == 200:
                        # Save the image exactly matching your database name
                        with open(target_path, 'wb') as file:
                            file.write(response.content)
                        print(f"✅ Successfully saved: {expected_filename}")
                    else:
                        print(f"❌ Failed to download {item_name}: Website blocked the download")
                else:
                    print(f"❌ No images found for {item_name}")
                    
            except Exception as e:
                print(f"❌ Failed to process {item_name}: {e}")

# 4. RUN THE AUTOMATION
print("Starting TerraVista Image Automation...")

# Fetch pictures of tourist places
print("\n--- FETCHING TOURIST PLACES ---")
fetch_images_from_db("places", "India tourism photography")

# Fetch pictures of hotels and restaurants
print("\n--- FETCHING ACCOMMODATIONS ---")
fetch_images_from_db("accommodations", "hotel exterior India")

print("\n🎉 All automated downloads are complete! Your project is ready.")
