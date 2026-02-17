import sqlite3
import requests
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'genshin_tracker.db')

def update_character_database():
    # 1. THE NUCLEAR OPTION: Physically delete the locked file
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("Successfully deleted the old, cached database file.")
        except PermissionError:
            print("CRITICAL ERROR: Windows blocked the deletion! You must stop Streamlit first (Ctrl+C).")
            return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE Characters (
        CharacterID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT UNIQUE,
        Element TEXT,
        ReleaseVersion TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE BannerHistory (
        BannerID INTEGER PRIMARY KEY AUTOINCREMENT,
        CharacterID INTEGER,
        StartDate TEXT,
        EndDate TEXT,
        FOREIGN KEY(CharacterID) REFERENCES Characters(CharacterID)
    )
    ''')

    print("Fetching latest character data...")
    url = "https://genshin-db-api.vercel.app/api/v5/characters?query=names&matchCategories=true&verboseCategories=true"
    
    try:
        response = requests.get(url)
        response.raise_for_status() 
        api_data = response.json()
    except Exception as e:
        print(f"Failed to fetch Genshin data: {e}")
        return

    api_data.sort(key=lambda x: x.get('version', '9.9'))

    # 2. THE CLEANER EXCLUSION LIST
    standard_characters = [
        "Aloy", "Aether", "Lumine", "Diluc", "Jean", 
        "Qiqi", "Keqing", "Mona", "Tighnari", "Dehya"
    ]

    for char in api_data:
        name = char.get('name')
        element = char.get('element')
        version = char.get('version')
        rarity = str(char.get('rarity'))
        
        if rarity != "5":
            continue
            
        # If the name is Traveler, or in our standard banner list, skip them!
        if "Traveler" in name or name in standard_characters:
            continue

        cursor.execute('''
            INSERT INTO Characters (Name, Element, ReleaseVersion) 
            VALUES (?, ?, ?)
        ''', (name, element, version))

    # 3. FETCHING FROM YOUR GITHUB
    banner_url = "https://raw.githubusercontent.com/Ehttri/genshin_banner_api/refs/heads/main/banners.json"
    
    try:
        print("Fetching historical banner dates from GitHub...")
        banner_response = requests.get(banner_url)
        banner_response.raise_for_status()
        external_banner_dates = banner_response.json()
    except Exception as e:
        print(f"Failed to fetch custom banner API: {e}")
        return

    for char_name, dates in external_banner_dates.items():
        cursor.execute('SELECT CharacterID FROM Characters WHERE Name = ?', (char_name,))
        result = cursor.fetchone()
        
        if result:
            char_id = result[0]
            for start, end in dates:
                cursor.execute('''
                    INSERT INTO BannerHistory (CharacterID, StartDate, EndDate)
                    VALUES (?, ?, ?)
                ''', (char_id, start, end))

    conn.commit()
    conn.close()
    print("Database built! Only Limited 5-star characters and their banners were added.")

# THIS IS THE EXECUTION BLOCK THAT WAS MISSING
if __name__ == "__main__":
    update_character_database()