import streamlit as st
from st_keyup import st_keyup 
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

# --- NEW: Added c.IconURL right before c.Name so it shows up next to it ---
query = """
    SELECT 
        c.CharacterID,
        c.IconURL,
        c.Name, 
        c.Element, 
        COUNT(b.BannerID) as TotalBanners,
        GROUP_CONCAT(b.StartDate, ' || ') as RerunDates,
        MAX(b.EndDate) as LastBannerEnd,
        CAST(julianday('now') - julianday(MAX(b.EndDate)) AS INTEGER) as DaysSinceLastBanner
    FROM Characters c
    LEFT JOIN BannerHistory b ON c.CharacterID = b.CharacterID
    GROUP BY c.CharacterID
"""
df = pd.read_sql_query(query, conn)

st.sidebar.header("Filter Options")

def clear_filter():
    st.session_state.element_filter = []
    st.session_state.name_search = ""

with st.sidebar:
    search_query = st_keyup(
        "Search Character",
        key="name_search",
        placeholder="e.g. Zhongli..."
    )

available_elements = df['Element'].unique().tolist()

selected_elements = st.sidebar.multiselect(
    "Filter by Element", 
    options=available_elements, 
    default=[],
    key="element_filter"
)

st.sidebar.button("Clear All", on_click=clear_filter)

filtered_df = df

if search_query:
    filtered_df = filtered_df[filtered_df['Name'].str.contains(search_query, case=False, na=False)]

if selected_elements:
    filtered_df = filtered_df[filtered_df['Element'].isin(selected_elements)]

st.subheader("Limited 5-Star Roster & Banner History")

st.dataframe(
    filtered_df, 
    use_container_width=False, 
    hide_index=True,
    column_config={
        "CharacterID": st.column_config.NumberColumn("ID", format="%d"),
        "IconURL": st.column_config.ImageColumn("Avatar"),  # <-- NEW: Renders the URL as an image
        "Name": "Character Name",
        "Element": "Element",
        "TotalBanners": st.column_config.NumberColumn("Total Appearances"),
        "RerunDates": "Dates Available",
        "LastBannerEnd": "Last Banner Ended",
        "DaysSinceLastBanner": st.column_config.NumberColumn("Days Since Last Banner")
    }
)