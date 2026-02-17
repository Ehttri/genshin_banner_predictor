import streamlit as st
import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'genshin_tracker.db')

st.set_page_config(page_title="Genshin Tracker", layout="wide")
st.title("🌟 Genshin Impact Character Tracker")

@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

conn = get_connection()

# Fetch the data using the JOIN query
query = """
    SELECT 
        c.CharacterID,
        c.Name, 
        c.Element, 
        COUNT(b.BannerID) as TotalBanners,
        GROUP_CONCAT(b.StartDate, ' || ') as RerunDates
    FROM Characters c
    LEFT JOIN BannerHistory b ON c.CharacterID = b.CharacterID
    GROUP BY c.CharacterID
"""
df = pd.read_sql_query(query, conn)

st.subheader("Current Roster & Banner History")

# Display the merged data
st.dataframe(
    df, 
    use_container_width=False, 
    hide_index=True,
    column_config={
        "CharacterID": st.column_config.NumberColumn("ID", format="%d"),
        "Name": "Character Name",
        "Element": "Vision",
        "TotalBanners": st.column_config.NumberColumn("Total Appearances"),
        "RerunDates": "Dates Available (YYYY-MM-DD)"
    }
)