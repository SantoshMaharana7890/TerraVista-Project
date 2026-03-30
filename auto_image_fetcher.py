import os
import mysql.connector
from bing_image_downloader import downloader
import shutil

# 1. SECURELY FETCH THE PASSWORD (Just like app.py!)
db_password = os.environ.get('TIDB_PASSWORD', 'wbwt0FAtE8PtBU3q')

# 2. CONNECT TO YOUR DATABASE
db = mysql.connector.connect(
    host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
    user="2F9h8KmcL9CA9h4.root",
    password=db_password,       # The red line is gone, and it is fully secure!
    database="defaultdb",
    port=4000,
    ssl_verify_cert=True,       # Added for TiDB security matching
    ssl_verify_identity=True    # Added for TiDB security matching
)
cursor = db.cursor()

# Create the target images folder if it doesn't exist
os.makedirs("static/images", exist_ok=True)

# 2. CREATE THE AUTOMATION FUNCTION
def fetch_images_from_db(table_name, search_keyword):
    # Ask the database for all the names and exact image filenames
    cursor.execute(f"SELECT name, image_file FROM {table_name}")
    records = cursor.fetchall()
    
    for record in records:
        item_name = record[0]
        expected_filename = record[1]
        target_path = os.path.join("static/images", expected_filename)
        
        # Smart Check: If you already have the image, skip it to save time
        if os.path.exists(target_path):
            print(f"⏩ Skipping {item_name} (Image already exists)")
            continue
            
        # Create a highly specific search query
        search_query = f"{item_name} {search_keyword} high resolution"
        print(f"⏳ Downloading image for: {item_name}...")
        
        try:
            # Download exactly 1 top image from Bing silently
            downloader.download(search_query, limit=1, output_dir='temp_images', adult_filter_off=True, force_replace=True, timeout=10, verbose=False)
            
            # Find the downloaded file
            download_folder = os.path.join('temp_images', search_query)
            downloaded_files = os.listdir(download_folder)
            
            if len(downloaded_files) > 0:
                # Grab the first file downloaded
                downloaded_file_path = os.path.join(download_folder, downloaded_files[0])
                
                # Move it into your static folder and RENAME it to match your database exactly!
                shutil.move(downloaded_file_path, target_path)
                print(f"✅ Successfully saved: {expected_filename}")
        except Exception as e:
            print(f"❌ Failed to download {item_name}: {e}")

# 3. RUN THE AUTOMATION
print("Starting TerraVista Image Automation...")

# Fetch pictures of tourist places
print("\n--- FETCHING TOURIST PLACES ---")
fetch_images_from_db("places", "India tourism photography")

# Fetch pictures of hotels and restaurants
print("\n--- FETCHING ACCOMMODATIONS ---")
fetch_images_from_db("accommodations", "hotel exterior India")

# 4. CLEAN UP
# Deletes the temporary download folder leaving only your clean static/images folder
shutil.rmtree('temp_images', ignore_errors=True)
print("\n🎉 All automated downloads are complete! Your project is ready.")