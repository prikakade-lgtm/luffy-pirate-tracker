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
    
    if not force_refresh and st.session_state.cache_timetable is not None:
        if current_time - cache_time < 300:
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
        if current

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
    
    .crew-badge {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 2px solid #FFD700;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        text-align: center;
    }
    
    .island-card {
        background: linear-gradient(to right, #1e3c72, #2a5298);
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        text-align: center;
    }
    
    .achievement-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #4a4a6a;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin: 5px;
    }
    
    .xp-bar-container {
        background: #333;
        border-radius: 10px;
        height: 25px;
        overflow: hidden;
        margin: 10px 0;
    }
    
    .xp-fill {
        background: linear-gradient(90deg, #FFD700 0%, #FFA500 100%);
        height: 100%;
        transition: width 0.5s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #000;
        font-weight: bold;
        font-size: 12px;
    }
    
    .water-glass {
        font-size: 32px;
        cursor: pointer;
        transition: transform 0.2s;
    }
    
    .water-glass:hover {
        transform: scale(1.2);
    }
    
    .stMetric {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #4a4a6a;
        border-radius: 10px;
        padding: 15px;
    }
    
    .stMetric > div {
        color: #ffffff !important;
    }
    
    .stMetric label {
        color: #FFD700 !important;
    }
    
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #0a0a1a 100%);
    }
    
    .sidebar-title {
        color: #FFD700;
        font-size: 20px;
        font-weight: bold;
    }
    
    .task-complete {
        text-decoration: line-through;
        color: #888;
    }
    
    .task-pending {
        color: #ffffff;
    }
    
    .highlight-xp {
        color: #FFD700;
        font-weight: bold;
        font-size: 18px;
    }
    
    .streak-fire {
        font-size: 24px;
    }
    </style>
    """, unsafe_allow_html=True)

def display_header():
    """Display the main header"""
    st.markdown('<div class="big-title">🏴‍☠️ Luffy\'s Grand Line RPG</div>', unsafe_allow_html=True)

def get_welcome_message():
    """Get a personalized welcome message"""
    message = random.choice(WELCOME_MESSAGES)
    return message.format(user=st.session_state.user)

def display_crew_badge():
    """Display user's current crew role with styling"""
    role, icon, description = get_crew_role(st.session_state.xp)
    
    st.markdown(f"""
    <div class="crew-badge">
        <h2 style="color: #FFD700; margin: 0;">⚔️ {icon} {role} ⚔️</h2>
        <p style="color: #ffffff; margin: 10px 0 0 0;">{description}</p>
        <p style="color: #aaaaaa; font-size: 12px; margin: 5px 0 0 0;">Total XP: {st.session_state.xp:,}</p>
    </div>
    """, unsafe_allow_html=True)

def display_island_progress():
    """Display island progression with visual map"""
    current_island, next_island = get_current_island(st.session_state.xp)
    
    st.markdown(f"""
    <div class="island-card">
        <h2 style="color: #FFD700; margin: 0;">🗺️ Current Location: {current_island[2]} {current_island[0]}</h2>
        <p style="color: #ffffff; font-size: 16px; margin: 10px 0;">{current_island[3]}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if next_island:
        progress = min(100, (st.session_state.xp - current_island[1]) / (next_island[1] - current_island[1]) * 100)
        st.write(f"📍 Progress to {next_island[2]} {next_island[0]}: {progress:.1f}%")
        st.progress(progress / 100)

def display_xp_progress():
    """Display XP progress bar to next rank"""
    current_role, _, _ = get_crew_role(st.session_state.xp)
    next_role_xp = 0
    current_role_xp = 0
    
    for role_data in CREW_ROLES:
        if role_data[0] == current_role:
            idx = CREW_ROLES.index(role_data)
            current_role_xp = role_data[1]
            if idx < len(CREW_ROLES) - 1:
                next_role_xp = CREW_ROLES[idx + 1][1]
            break
    
    if next_role_xp > 0:
        xp_in_current_level = st.session_state.xp - current_role_xp
        xp_needed = next_role_xp - current_role_xp
        progress = (xp_in_current_level / xp_needed) * 100
        
        st.markdown(f"""
        <div class="xp-bar-container">
            <div class="xp-fill" style="width: {min(100, progress)}%;">
                {progress:.1f}% to {CREW_ROLES[CREW_ROLES.index([r for r in CREW_ROLES if r[0] == current_role][0]) + 1][0]}
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_achievements():
    """Display all earned and available achievements"""
    st.subheader("🏆 Achievement Gallery")
    
    earned = set(st.session_state.achievements)
    all_achievements = list(Achievements.keys())
    
    cols = st.columns(5)
    for idx, (achievement_id, achievement_data) in enumerate(Achievements.items()):
        with cols[idx % 5]:
            if achievement_id in earned:
                st.markdown(f"""
                <div class="achievement-card">
                    <div style="font-size: 24px;">{achievement_data['icon']}</div>
                    <div style="color: #FFD700; font-weight: bold;">{achievement_data['name']}</div>
                    <div style="color: #00FF00; font-size: 12px;">✅ Unlocked</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="achievement-card">
                    <div style="font-size: 24px; opacity: 0.5;">❓</div>
                    <div style="color: #888; font-weight: bold;">{achievement_data['name']}</div>
                    <div style="color: #ff6b6b; font-size: 12px;">🔒 Locked</div>
                </div>
                """, unsafe_allow_html=True)

def display_streak():
    """Display current streak with fire emoji"""
    if st.session_state.streak > 0:
        fire_count = min(10, st.session_state.streak)
        fire_emoji = "🔥" * fire_count
        st.markdown(f"""
        <div style="text-align: center; margin: 10px 0;">
            <span style="font-size: 24px;">{fire_emoji}</span>
            <span style="color: #FFD700; font-size: 18px; margin-left: 10px;">
                {st.session_state.streak} Day Streak!
            </span>
        </div>
        """, unsafe_allow_html=True)

# ================= CALCULATION FUNCTIONS =================

def calculate_user_stats(records, username):
    """Calculate comprehensive user statistics"""
    user_records = [r for r in records if r.get("username") == username]
    
    if not user_records:
        return None
    
    stats = {
        "total_days": len(user_records),
        "total_xp": sum(int(r.get("xp_today", 0)) for r in user_records),
        "average_xp": 0,
        "best_day": 0,
        "current_streak": 0,
        "longest_streak": 0,
        "water_days": 0,
        "perfect_days": 0,
        "difficulty_history": [],
        "xp_history": []
    }
    
    if user_records:
        xp_values = [int(r.get("xp_today", 0)) for r in user_records]
        stats["average_xp"] = sum(xp_values) / len(xp_values)
        stats["best_day"] = max(xp_values)
        stats["difficulty_history"] = [float(r.get("difficulty_multiplier", 1.0)) for r in user_records]
        stats["xp_history"] = xp_values
        
        # Calculate streaks
        dates = sorted(set(r.get("date") for r in user_records))
        current_streak = 0
        longest_streak = 0
        
        for i, d in enumerate(dates):
            day_record = next((r for r in user_records if r.get("date") == d), None)
            if day_record and int(day_record.get("xp_today", 0)) > 0:
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
            else:
                current_streak = 0
        
        stats["current_streak"] = current_streak
        stats["longest_streak"] = longest_streak
    
    return stats

# ================= EXPORT FUNCTIONS =================

def export_user_data(user_records):
    """Export user data as CSV"""
    if not user_records:
        st.warning("No data to export")
        return
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=user_records[0].keys())
    writer.writeheader()
    writer.writerows(user_records)
    
    st.download_button(
        label="📥 Download Pirate Log (CSV)",
        data=output.getvalue(),
        file_name=f"pirate_log_{st.session_state.user}_{date.today()}.csv",
        mime="text/csv"
    )

# ================= PAGE FUNCTIONS =================

def display_login(users_sheet):
    """Display login form"""
    st.header("🛡️ Ship Access")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        username_input = st.text_input("Username", placeholder="Enter your pirate name")
        password_input = st.text_input("Password", type="password", placeholder="Enter your secret code")
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    border: 2px solid #4a4a6a; border-radius: 15px; padding: 20px; height: 150px;">
            <h4 style="color: #FFD700; margin-top: 0;">🏴‍☠️ Welcome, Pirate!</h4>
            <p style="color: #ffffff; font-size: 14px;">
                Enter your credentials to access the Grand Line RPG tracker. 
                Complete daily missions, track your health habits, and level up your crew role!
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("⚓ Set Sail (Login)", use_container_width=True):
        if not username_input or not password_input:
            st.warning("⚠️ Please enter both username and password to board the ship!")
        else:
            users = safe_get_records(users_sheet)
            login_successful = False
            
            for user in users:
                sheet_username = str(user.get("username", "")).strip()
                stored_password_hash = str(user.get("password_hash", "")).strip()
                
                # Support both old plaintext passwords and new hashed passwords
                old_password = str(user.get("password", "")).strip()
                
                if sheet_username == username_input.strip():
                    # Check hashed password first
                    if stored_password_hash and verify_password(password_input, stored_password_hash):
                        login_successful = True
                    # Fallback to old plaintext check (for migration)
                    elif old_password == password_input:
                        login_successful = True
                        # Update to hashed password
                        try:
                            users_sheet.update_cell(user.get("row", 2), 3, hash_password(password_input))
                        except:
                            pass
                
                if login_successful:
                    st.session_state.user = sheet_username
                    st.session_state.xp = int(user.get("xp", 0))
                    st.session_state.difficulty_multiplier = float(user.get("difficulty_multiplier", 1.0))
                    st.session_state.streak = int(user.get("streak", 0))
                    st.session_state.achievements = user.get("achievements", "").split(",") if user.get("achievements") else []
                    st.session_state.logged_in_today = True
                    
                    # Check for new achievements
                    new_achievements = check_achievements()
                    if new_achievements:
                        for achievement in new_achievements:
                            st.balloons()
                            st.success(f"🏆 Achievement Unlocked: {achievement['icon']} {achievement['name']}!")
                    
                    st.success("🎉 Login successful! The Grand Line awaits!")
                    st.rerun()
                    break
            
            if not login_successful:
                st.error("❌ Wrong credentials! Are you an imposter?")

def display_dashboard(timetable_sheet, reading_sheet, presentation_sheet, preview_date):
    """Display the main dashboard"""
    st.info(get_welcome_message())
    
    # Crew role and island progress
    col1, col2 = st.columns(2)
    with col1:
        display_crew_badge()
    with col2:
        display_island_progress()
    
    # XP Progress
    display_xp_progress()
    
    # Streak display
    display_streak()
    
    st.divider()
    
    # Today's overview
    st.header(f"📅 {preview_date.strftime('%A, %d %B %Y')}")
    
    today_str = str(preview_date)
    timetable = safe_get_records(timetable_sheet)
    today_tasks = [t for t in timetable if t.get("date") == today_str]
    
    # Quick stats
    stats_cols = st.columns(4)
    
    # Calculate today's progress
    water_xp = 10 if st.session_state.water_count >= 8 else 0
    veg_xp = 10 if sum([st.session_state.get(f"veg_{color}", 0) for color in ["red", "yellow", "green", "white", "pink"]]) >= 3 else 0
    food_xp = 10 if sum([st.session_state.get(f"food_{group}", 0) for group in ["protein", "fruits", "vegetables", "fats", "carbs"]]) >= 4 else 0
    
    with stats_cols[0]:
        st.metric("💧 Water", f"{st.session_state.water_count}/8", f"+{water_xp} XP" if water_xp > 0 else None)
    with stats_cols[1]:
        st.metric("🥕 Veg Colors", f"{veg_xp//10}/5", f"+{veg_xp} XP" if veg_xp > 0 else None)
    with stats_cols[2]:
        st.metric("🍽️ Food Groups", f"{food_xp//10}/5", f"+{food_xp} XP" if food_xp > 0 else None)
    with stats_cols[3]:
        task_xp = sum(int(t.get("xp", 0)) for t in today_tasks)
        st.metric("📋 Tasks", f"{len(today_tasks)}", f"{task_xp} XP available")
    
    # Display tasks
    if today_tasks:
        st.subheader("📜 Today's Mission Log")
        
        for idx, task in enumerate(today_tasks):
            task_title = task.get("title", "Unknown Task")
            task_xp = int(task.get("xp", 0))
            task_category = task.get("category", "General")
            task_link = task.get("link", "")
            
            col_task, col_xp = st.columns([4, 1])
            
            with col_task:
                if task_category == "TED" and task_link:
                    st.markdown(f"• 🎬 [{task_title}]({task_link})")
                else:
                    st.markdown(f"• 📌 {task_title}")
            
            with col_xp:
                st.markdown(f"<span class='highlight-xp'>{task_xp} XP</span>", unsafe_allow_html=True)
    
    # Reading questions
    reading_tasks = [t for t in today_tasks if t.get("category") == "Reading"]
    if reading_tasks:
        st.subheader("📘 Reading Questions")
        reading_data = safe_get_records(reading_sheet)
        
        for r_task in reading_tasks:
            for row in reading_data:
                if row.get("book", "").lower() in r_task.get("title", "").lower():
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                                border-left: 4px solid #FFD700; padding: 15px; margin: 10px 0; border-radius: 0 10px 10px 0;">
                        <p style="color: #ffffff; margin: 0;"><strong>📖 {row.get('book', 'Unknown Book')}</strong></p>
                        <p style="color: #aaaaaa; margin: 5px 0 0 0;">{row.get('question', 'No question available')}</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Presentation prompts
    st.subheader("🎤 Presentation Prompts")
    presentation_data = safe_get_records(presentation_sheet)
    todays_prompts = [p for p in presentation_data if p.get("date") == today_str]
    
    if todays_prompts:
        for prompt in todays_prompts:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                        border-left: 4px solid #FF6347; padding: 15px; margin: 10px 0; border-radius: 0 10px 10px 0;">
                <p style="color: #ffffff; margin: 0;">🎤 {prompt.get('prompt', 'No prompt available')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No presentation prompts for today. Enjoy your free day! 🎉")

def display_missions(log_sheet, timetable_sheet, preview_date):
    """Display the missions page"""
    st.header("⚔️ Daily Health Tracker")
    
    today_str = str(preview_date)
    xp_today = 0
    
    # -------- WATER VISUAL FILL --------
    st.subheader("💧 Water Intake")
    
    water_cols = st.columns(8)
    for i in range(8):
        if i < st.session_state.water_count:
            glass = "🟦"
        else:
            glass = "⬜"
        
        if water_cols[i].button(glass, key=f"water_{i}"):
            st.session_state.water_count = i + 1
    
    st.markdown(f"""
    <div style="text-align: center; margin: 10px 0;">
        <span style="font-size: 24px;">{'🟦' * st.session_state.water_count}{'⬜' * (8 - st.session_state.water_count)}</span>
        <span style="color: #FFD700; font-size: 18px; margin-left: 15px;">{st.session_state.water_count}/8 glasses</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.water_count >= 8:
        xp_today += int(10 * st.session_state.difficulty_multiplier)
        st.success("💧 Water goal achieved! +10 XP")
    
    st.divider()
    
    # -------- VEGETABLE COLORS --------
    st.subheader("🥕 Vegetable Colors")
    
    veg_colors = {
        "🔴 Red": "red",
        "🟡 Yellow": "yellow",
        "🟢 Green": "green",
        "⚪ White": "white",
        "🌸 Pink": "pink"
    }
    
    veg_total_colors = 0
    
    veg_cols = st.columns(5)
    for idx, (icon, key) in enumerate(veg_colors.items()):
        with veg_cols[idx]:
            count = st.number_input(icon, 0, 5, key=f"veg_{key}")
            if count > 0:
                veg_total_colors += 1
    
    if veg_total_colors >= 3:
        xp_today += int(10 * st.session_state.difficulty_multiplier)
        st.success("🥕 Vegetable variety goal achieved! +10 XP")
    
    st.divider()
    
    # -------- FOOD GROUPS --------
    st.subheader("🍽️ Food Groups")
    
    food_groups = {
        "🍗 Protein": "protein",
        "🍎 Fruits": "fruits",
        "🥦 Vegetables": "vegetables",
        "🥑 Fats": "fats",
        "🍞 Carbs": "carbs"
    }
    
    food_total_groups = 0
    
    food_cols = st.columns(5)
    for idx, (icon, key) in enumerate(food_groups.items()):
        with food_cols[idx]:
            portions = st.number_input(icon, 0, 6, key=f"food_{key}")
            if portions > 0:
                food_total_groups += 1
    
    if food_total_groups >= 4:
        xp_today += int(10 * st.session_state.difficulty_multiplier)
        st.success("🍽️ Balanced diet goal achieved! +10 XP")
    
    st.divider()
    
    # -------- TASKS --------
    st.header("📋 Today's Missions")
    
    timetable = safe_get_records(timetable_sheet)
    today_tasks = [t for t in timetable if t.get("date") == today_str]
    
    task_xp_total = 0
    tasks_completed = 0
    
    for task in today_tasks:
        task_title = task.get("title", "Unknown Task")
        task_xp = int(task.get("xp", 0))
        key = f"{today_str}_{task_title}"
        
        col_task, col_xp = st.columns([4, 1])
        
        with col_task:
            done = st.checkbox(task_title, key=key)
        
        with col_xp:
            st.markdown(f"<span class='highlight-xp'>{task_xp} XP</span>", unsafe_allow_html=True)
        
        if done:
            xp_today += int(task_xp * st.session_state.difficulty_multiplier)
            tasks_completed += 1
            st.session_state.tasks_completed += 1
    
    task_xp_total = sum(int(t.get("xp", 0)) for t in today_tasks)
    
    st.divider()
    
    # -------- SUMMARY AND SUBMIT --------
    st.header("📊 Day Summary")
    
    summary_cols = st.columns(4)
    with summary_cols[0]:
        st.metric("💧 Water Goal", "✅" if st.session_state.water_count >= 8 else "❌", 
                  f"{st.session_state.water_count}/8")
    with summary_cols[1]:
        st.metric("🥕 Veg Colors", "✅" if veg_total_colors >= 3 else "❌",
                  f"{veg_total_colors}/5")
    with summary_cols[2]:
        st.metric("🍽️ Food Groups", "✅" if food_total_groups >= 4 else "❌",
                  f"{food_total_groups}/5")
    with summary_cols[3]:
        st.metric("📋 Tasks", f"{tasks_completed}/{len(today_tasks)}",
                  f"{task_xp_total} XP available")
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                border: 2px solid #FFD700; border-radius: 15px; padding: 25px; margin: 20px 0; text-align: center;">
        <h2 style="color: #FFD700; margin: 0;">💰 XP Earned Today: {xp_today}</h2>
        <p style="color: #aaaaaa; margin: 10px 0 0 0;">
            Difficulty Multiplier: {st.session_state.difficulty_multiplier:.2f}x
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Submit Day", use_container_width=True):
        target = task_xp_total
        
        # Update difficulty
        new_multiplier = update_difficulty(xp_today, target, st.session_state.difficulty_multiplier)
        st.session_state.difficulty_multiplier = new_multiplier
        
        # Update XP
        st.session_state.xp += xp_today
        
        # Update streak
        if xp_today >= target:
            st.session_state.streak += 1
        else:
            st.session_state.streak = 0
        
        # Update special counters
        if st.session_state.water_count >= 8:
            st.session_state.water_streak += 1
        else:
            st.session_state.water_streak = 0
        
        if xp_today >= target:
            st.session_state.perfect_days += 1
        
        if food_total_groups >= 4 and veg_total_colors >= 3:
            st.session_state.balanced_days += 1
        
        # Log to Google Sheets
        success = safe_append_row(log_sheet, [
            st.session_state.user,
            today_str,
            xp_today,
            new_multiplier,
            st.session_state.streak,
            st.session_state.water_count,
            tasks_completed
        ])
        
        if success:
            # Check for new achievements
            new_achievements = check_achievements()
            if new_achievements:
                for achievement in new_achievements:
                    st.balloons()
                    st.success(f"🏆 Achievement Unlocked: {achievement['icon']} {achievement['name']}!")
            
            st.success("🎉 Day submitted successfully! See you tomorrow, pirate!")
            st.balloons()
            st.rerun()
        else:
            st.error("❌ Failed to save your progress. Please try again.")

def display_stats(log_sheet):
    """Display the statistics page"""
    st.header("📊 Pirate Log Statistics")
    
    records = safe_get_records(log_sheet)
    user_records = [r for r in records if r.get("username") == st.session_state.user]
    stats = calculate_user_stats(user_records, st.session_state.user)
    
    if not stats:
        st.warning("📜 No statistics available yet. Complete some days to see your progress!")
        return
    
    # Overview cards
    stat_cols = st.columns(4)
    with stat_cols[0]:
        st.metric("🏝️ Days Logged", stats["total_days"])
    with stat_cols[1]:
        st.metric("💰 Total XP", f"{stats['total_xp']:,}")
    with stat_cols[2]:
        st.metric("⭐ Average XP", f"{stats['average_xp']:.1f}")
    with stat_cols[3]:
        st.metric("🏆 Best Day", f"{stats['best_day']}")
    
    streak_cols = st.columns(3)
    with streak_cols[0]:
        st.metric("🔥 Current Streak", stats["current_streak"])
    with streak_cols[1]:
        st.metric("📈 Longest Streak", stats["longest_streak"])
    with streak_cols[2]:
        st.metric("💧 Perfect Days", stats.get("perfect_days", 0))
    
    # Charts
    st.subheader("📈 Progress Over Time")
    
    if stats["xp_history"]:
        st.line_chart(stats["xp_history"])
    
    st.subheader("🎯 XP Distribution")
    if stats["xp_history"]:
        st.bar_chart(stats["xp_history"])
    
    st.subheader("⚓ Difficulty Progression")
    if stats["difficulty_history"]:
        st.line_chart(stats["difficulty_history"])
    
    # Export data
    st.divider()
    st.subheader("📥 Export Your Data")
    export_user_data(user_records)
    
    # Achievements
    st.divider()
    display_achievements()

def display_settings():
    """Display settings page"""
    st.header("⚙️ Ship Settings")
    
    st.subheader("👤 Profile")
    st.write(f"**Username:** {st.session_state.user}")
    st.write(f"**Current Role:** {st.session_state.current_crew_role}")
    st.write(f"**Total XP:** {st.session_state.xp:,}")
    
    st.subheader("🎮 Game Stats")
    st.write(f"**Difficulty Multiplier:** {st.session_state.difficulty_multiplier:.2f}")
    st.write(f"**Current Streak:** {st.session_state.streak} days")
    st.write(f"**Tasks Completed:** {st.session_state.tasks_completed}")
    
    st.subheader("🏆 Achievements")
    st.write(f"**Unlocked:** {len(st.session_state.achievements)}/{len(Achievements)}")
    
    if st.button("🚪 Abandon Ship (Logout)"):
        for key in list(st.session_state.keys()):
            if key not in ["_is_running", "_is_local"]:
                del st.session_state[key]
        st.rerun()

# ================= MAIN APPLICATION =================

def main():
    """Main application function"""
    # Initialize
    set_page_config()
    apply_custom_css()
    init_session_state()
    
    # Initialize Google Sheets
    sheet = init_google_sheets()
    if sheet is None:
        st.error("⚓ Failed to connect to the ship logs (Google Sheets). Please check your configuration.")
        return
    
    # Get worksheets
    try:
        users_sheet = sheet.worksheet("USERS")
        log_sheet = sheet.worksheet("DAILY_LOG")
        timetable_sheet = sheet.worksheet("TIMETABLE")
        reading_sheet = sheet.worksheet("READING_REFLECTIONS")
        presentation_sheet = sheet.worksheet("PRESENTATIONS")
    except Exception as e:
        st.error(f"⚓ Failed to access worksheets: {e}")
        return
    
    # Check if user is logged in
    if not st.session_state.user:
        display_login(users_sheet)
    else:
        # Display header
        display_header()
        
        # Sidebar navigation
        st.sidebar.markdown('<div class="sidebar-title">🏴‍☠️ Navigation</div>', unsafe_allow_html=True)
        
        # Date preview
        st.sidebar.subheader("📅 Date Preview")
        preview_date = st.sidebar.date_input("Select Date", value=date.today())
        
        # Navigation
        page = st.sidebar.radio("Go to", ["Dashboard", "Missions", "Stats", "Settings"])
        
        # Logout button
        st.sidebar.divider()
        if st.sidebar.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                if key not in ["_is_running", "_is_local"]:
                    del st.session_state[key]
            st.rerun()
        
        # Display current page
        if page == "Dashboard":
            display_dashboard(timetable_sheet, reading_sheet, presentation_sheet, preview_date)
        elif page == "Missions":
            display_missions(log_sheet, timetable_sheet, preview_date)
        elif page == "Stats":
            display_stats(log_sheet)
        elif page == "Settings":
            display_settings()

if __name__ == "__main__":
    main()
