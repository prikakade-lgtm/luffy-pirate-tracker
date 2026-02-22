import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import date, datetime
import hashlib
import csv
import io
import random

# ================= CONFIGURATION =================

# Google Sheets Configuration
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Crew Roles Configuration
CREW_ROLES = [
    ("Passenger", 0, "🚢", "Just starting your journey!"),
    ("Deck Hand", 100, "⚓", "Learning the ropes of productivity"),
    ("Navigator", 500, "🗺️", "Charting your course through tasks"),
    ("Cook", 1500, "🍳", "Preparing success one meal at a time"),
    ("Sniper", 3000, "🎯", "Hitting your targets with precision"),
    ("Doctor", 5000, "💊", "Keeping your productivity healthy"),
    ("Archaeologist", 8000, "📜", "Uncovering ancient productivity wisdom"),
    ("Shipwright", 12000, "🔧", "Building your success ship"),
    ("Musician", 18000, "🎵", "Setting the rhythm of achievement"),
    ("Captain", 25000, "🏴‍☠️", "Leading your crew to glory"),
    ("Pirate King", 50000, "👑", "The ultimate productivity legend!")
]

# Island Progression Configuration
ISLANDS = [
    ("Foosha Village", 0, "🌸", "Where it all began. Your journey starts here!"),
    ("Windmill Village", 500, "🌬️", "First steps away from home."),
    ("Shells Town", 1500, "🏘️", "Meeting your first challenges."),
    ("Orange Town", 3000, "🍊", "Building momentum."),
    ("Syrup Village", 5000, "🏝️", "Finding your crew."),
    ("Baratie", 8000, "🍽️", "Refueling for the journey ahead."),
    ("Gecko Islands", 12000, "🦎", "Exploring new territories."),
    ("Dressrosa", 18000, "🌹", "Major battles ahead."),
    ("Wano Country", 25000, "🎎", "The final stretch!"),
    ("Laugh Tale", 50000, "💰", "You've found the One Piece!")
]

# Achievements Configuration
ACHIEVEMENTS = {
    "first_login": {"name": "Setting Sail", "icon": "⛵", "condition": lambda: True},
    "water_warrior": {"name": "Water Warrior", "icon": "💧", "condition": lambda: st.session_state.get("water_streak", 0) >= 7},
    "perfect_day": {"name": "Perfect Day", "icon": "⭐", "condition": lambda: st.session_state.get("perfect_days", 0) >= 1},
    "task_master": {"name": "Task Master", "icon": "📋", "condition": lambda: st.session_state.get("tasks_completed", 0) >= 100},
    "healthy_eater": {"name": "Healthy Eater", "icon": "🥗", "condition": lambda: st.session_state.get("healthy_days", 0) >= 30},
    "week_warrior": {"name": "Week Warrior", "icon": "🔥", "condition": lambda: st.session_state.get("streak", 0) >= 7},
    "month_master": {"name": "Month Master", "icon": "🌙", "condition": lambda: st.session_state.get("streak", 0) >= 30},
    "early_bird": {"name": "Early Bird", "icon": "🐦", "condition": lambda: st.session_state.get("early_submissions", 0) >= 10},
    "night_owl": {"name": "Night Owl", "icon": "🦉", "condition": lambda: st.session_state.get("late_submissions", 0) >= 10},
    "balanced_diet": {"name": "Balanced Diet", "icon": "⚖️", "condition": lambda: st.session_state.get("balanced_days", 0) >= 50}
}

# Welcome Messages
WELCOME_MESSAGES = [
    "🏴‍☠️ Ready to claim the treasure, {user}?",
    "⚓ The winds are favorable, {user}!",
    "🗺️ Your crew awaits your command, Captain {user}!",
    "🌊 The Grand Line calls, {user}!",
    "🍖 Time to feast before our next adventure, {user}!",
    "🎯 Target locked, {user}! Let's make this day count!",
    "💧 Hydration check! Ready to set sail, {user}?",
    "📜 The ancient texts speak of {user}'s legendary productivity!",
    "🦜 Polly says: '{user} is going to have an amazing day!'",
    "🌟 The stars align for {user} today!"
]

# ================= SESSION STATE MANAGEMENT =================

def init_session_state():
    """Initialize all session state variables with defaults"""
    defaults = {
        "user": None,
        "xp": 0,
        "difficulty_multiplier": 1.0,
        "water_count": 0,
        "streak": 0,
        "last_login_date": None,
        "achievements": [],
        "current_crew_role": "Passenger",
        "water_streak": 0,
        "perfect_days": 0,
        "tasks_completed": 0,
        "healthy_days": 0,
        "early_submissions": 0,
        "late_submissions": 0,
        "balanced_days": 0,
        "logged_in_today": False,
        # Cache storage
        "cache_timetable": None,
        "cache_timetable_time": 0,
        "cache_reading": None,
        "cache_reading_time": 0,
        "cache_presentation": None,
        "cache_presentation_time": 0,
        "cache_log": None,
        "cache_log_time": 0,
        "cache_users": None,
        "cache_users_time": 0
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ================= GOOGLE SHEETS FUNCTIONS =================

def init_google_sheets():
    """Initialize Google Sheets connection"""
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPE
        )
        client = gspread.authorize(creds)
        sheet = client.open("Pirate_Tracker_DB")
        return sheet
    except Exception as e:
        st.error(f"⚓ Failed to connect to Google Sheets: {e}")
        return None

def get_timetable_data(sheet, force_refresh=False):
    """Get timetable data with session-based caching"""
    current_time = datetime.now().timestamp()
    cache_time = st.session_state.get("cache_timetable_time", 0)
    
    # Refresh if forced or cache is older than 5 minutes
    if not force_refresh and st.session_state.cache_timetable is not None:
        if current_time - cache_time < 300:  # 5 minutes
            return st.session_state.cache_timetable
    
    try:
        timetable_sheet = sheet.worksheet("TIMETABLE")
        records = timetable_sheet.get_all_records()
        st.session_state.cache_timetable = records
        st.session_state.cache_timetable_time = current_time
        return records
    except Exception as e:
        st.error(f"📜 Failed to load timetable: {e}")
        return st.session_state.cache_timetable if st.session_state.cache_timetable else []

def get_reading_data(sheet, force_refresh=False):
    """Get reading reflections data with session-based caching"""
    current_time = datetime.now().timestamp()
    cache_time = st.session_state.get("cache_reading_time", 0)
    
    if not force_refresh and st.session_state.cache_reading is not None:
        if current_time - cache_time < 300:
            return st.session_state.cache_reading
    
    try:
        reading_sheet = sheet.worksheet("READING_REFLECTIONS")
        records = reading_sheet.get_all_records()
        st.session_state.cache_reading = records
        st.session_state.cache_reading_time = current_time
        return records
    except Exception as e:
        st.error(f"📜 Failed to load reading reflections: {e}")
        return st.session_state.cache_reading if st.session_state.cache_reading else []

def get_presentation_data(sheet, force_refresh=False):
    """Get presentation prompts data with session-based caching"""
    current_time = datetime.now().timestamp()
    cache_time = st.session_state.get("cache_presentation_time", 0)
    
    if not force_refresh and st.session_state.cache_presentation is not None:
        if current_time - cache_time < 300:
            return st.session_state.cache_presentation
    
    try:
        presentation_sheet = sheet.worksheet("PRESENTATIONS")
        records = presentation_sheet.get_all_records()
        st.session_state.cache_presentation = records
        st.session_state.cache_presentation_time = current_time
        return records
    except Exception as e:
        st.error(f"📜 Failed to load presentation prompts: {e}")
        return st.session_state.cache_presentation if st.session_state.cache_presentation else []

def get_log_data(sheet, force_refresh=False):
    """Get daily log data with session-based caching"""
    current_time = datetime.now().timestamp()
    cache_time = st.session_state.get("cache_log_time", 0)
    
    if not force_refresh and st.session_state.cache_log is not None:
        if current_time - cache_time < 300:
            return st.session_state.cache_log
    
    try:
        log_sheet = sheet.worksheet("DAILY_LOG")
        records = log_sheet.get_all_records()
        st.session_state.cache_log = records
        st.session_state.cache_log_time = current_time
        return records
    except Exception as e:
        st.error(f"📜 Failed to load daily log: {e}")
        return st.session_state.cache_log if st.session_state.cache_log else []

def get_users_data(sheet, force_refresh=False):
    """Get users data with session-based caching (shorter cache for login)"""
    current_time = datetime.now().timestamp()
    cache_time = st.session_state.get("cache_users_time", 0)
    
    # Shorter cache for users (30 seconds) since login needs fresh data
    if not force_refresh and st.session_state.cache_users is not None:
        if current_time - cache_time < 30:
            return st.session_state.cache_users
    
    try:
        users_sheet = sheet.worksheet("USERS")
        records = users_sheet.get_all_records()
        st.session_state.cache_users = records
        st.session_state.cache_users_time = current_time
        return records
    except Exception as e:
        st.error(f"📜 Failed to load users: {e}")
        return st.session_state.cache_users if st.session_state.cache_users else []

def append_log_entry(sheet, row_data):
    """Append entry to daily log and update cache"""
    try:
        log_sheet = sheet.worksheet("DAILY_LOG")
        log_sheet.append_row(row_data)
        # Invalidate cache
        st.session_state.cache_log = None
        return True
    except Exception as e:
        st.error(f"📜 Failed to append log entry: {e}")
        return False

def update_user_data(sheet, username, new_xp):
    """Update user's XP in the database"""
    try:
        users_sheet = sheet.worksheet("USERS")
        records = users_sheet.get_all_records()
        
        for idx, user in enumerate(records, start=2):  # Start at 2 because row 1 is header
            if str(user.get("username", "")).strip() == username:
                # Update XP
                users_sheet.update_cell(idx, 4, new_xp)
                # Update difficulty multiplier
                users_sheet.update_cell(idx, 5, st.session_state.difficulty_multiplier)
                # Update streak
                users_sheet.update_cell(idx, 6, st.session_state.streak)
                # Update achievements
                achievements_str = ",".join(st.session_state.achievements)
                users_sheet.update_cell(idx, 7, achievements_str)
                return True
        
        return False
    except Exception as e:
        st.error(f"📜 Failed to update user data: {e}")
        return False

# ================= SECURITY FUNCTIONS =================

def hash_password(password):
    """Hash password using SHA-256 with salt"""
    salt = "luffys_crew_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(input_password, stored_hash):
    """Verify password against stored hash"""
    return hash_password(input_password) == stored_hash

# ================= GAMIFICATION FUNCTIONS =================

def get_crew_role(xp):
    """Determine crew role based on XP"""
    for role_name, xp_required, icon, description in reversed(CREW_ROLES):
        if xp >= xp_required:
            return role_name, icon, description
    return CREW_ROLES[0][0], CREW_ROLES[0][2], CREW_ROLES[0][3]

def get_current_island(xp):
    """Determine current island based on XP"""
    current_island = ISLANDS[0]
    next_island = ISLANDS[1] if len(ISLANDS) > 1 else None
    
    for island in ISLANDS:
        if xp >= island[1]:
            current_island = island
            if island != ISLANDS[-1]:
                next_island = ISLANDS[ISLANDS.index(island) + 1]
    
    return current_island, next_island

def check_achievements():
    """Check and award new achievements"""
    new_achievements = []
    for achievement_id, achievement_data in ACHIEVEMENTS.items():
        if achievement_id not in st.session_state.achievements:
            if achievement_data["condition"]():
                st.session_state.achievements.append(achievement_id)
                new_achievements.append(achievement_data)
    return new_achievements

def update_difficulty(xp_today, target_xp, current_multiplier):
    """Update difficulty multiplier based on performance"""
    if xp_today < target_xp:
        return min(2.0, current_multiplier + 0.1)
    else:
        return max(1.0, current_multiplier - 0.05)

# ================= UI FUNCTIONS =================

def set_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(page_title="Luffy Grand Line RPG", layout="wide")

def apply_custom_css():
    """Apply custom CSS theming"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=One+Piece&display=swap');
    
    .main {
        background: linear-gradient(180deg, #0a0a1a 0%, #1a1a3a 50%, #0a0a1a 100%);
        min-height: 100vh;
    }
    
    .stApp {
        background: transparent;
    }
    
    .big-title {
        font-family: 'One Piece', cursive;
        font-size: 48px;
        font-weight: bold;
        color: #FFD700;
        text-shadow: 3px 3px 0px #8B0000, 6px 6px 0px #000000;
        text-align: center;
        margin-bottom: 30px;
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    .stHeader {
        color: #FFD700 !important;
        border-bottom: 2px solid #8B0000;
        padding-bottom: 10px;
    }
    
    .stSubheader {
        color: #FF6347 !important;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #8B0000 0%, #FF0000 100%);
        color: white;
        border: 2px solid #FFD700;
        border-radius: 10px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #FF0000 0%, #FFD700 100%);
        transform: scale(1.05);
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
    }
    
    .stCheckbox {
        color: #ffffff;
    }
    
    .stNumberInput>div>div>input {
        background: #1a1a2e;
        color: #ffffff;
        border: 1px solid #FFD700;
    }
    
    .success-message {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 2px solid #00FF00;
        border-radius: 10px;
        padding: 15px;
        color: #00FF00;
    }
    
    .warning-message {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 2px solid #FFD700;
        border-radius: 10px;
        padding: 15px;
        color: #FFD700;
    }
    
    .stats-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 2px solid #4a4a6
