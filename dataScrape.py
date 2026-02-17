import sqlite3
import requests
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'genshin_tracker.db')

def update_character_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS BannerHistory')
    cursor.execute('DROP TABLE IF EXISTS Characters')

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
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return

    api_data.sort(key=lambda x: x.get('version', '9.9'))

    for char in api_data:
        name = char.get('name')
        element = char.get('element')
        version = char.get('version')
        
        # 1. NEW: Extract the rarity and convert it to a string for safety
        rarity = str(char.get('rarity'))
        
        # 2. NEW: Skip if the character is not a 5-star
        if rarity != "5":
            continue
            
        if "Traveler" in name or name == "Aloy" or name == "Aether" or name == "Lumine":
            continue

        cursor.execute('''
            INSERT INTO Characters (Name, Element, ReleaseVersion) 
            VALUES (?, ?, ?)
        ''', (name, element, version))

    banner_url = "https://raw.githubusercontent.com/Ehttri/genshin_banner_api/refs/heads/main/banners.json"