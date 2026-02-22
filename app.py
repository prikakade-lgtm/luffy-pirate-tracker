import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import random

# ================= CONFIGURATION =================

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

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Luffy Grand Line RPG", layout="wide")

# ================= CSS =================
st.markdown("""
<style>
.big-title { 
    font-size: 42px; 
    font-weight: bold; 
    color: #FFD700; 
    text-align: center;
    text-shadow: 3px 3px 0px #8B0000;
    margin-bottom: 30px;
}
.stHeader { color: #FFD700 !important; }
.stSubheader { color: #FF6347 !important; }
.stButton>button {
    background: linear-gradient(135deg, #8B0000 0%, #FF0000 100%);
    color: white;
    border: 2px solid #FFD700;
    border-radius: 10px;
}
.stNumberInput>div>div>input {
    background: #1a1a2e;
    color: #ffffff;
    border: 1px solid #FFD700;
}
.crew-badge {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 2px solid #FFD700;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    margin: 10px 0;
}
.island-card {
    background: linear-gradient(to right, #1e3c72, #2a5298);
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    margin: 10px 0;
}
.achievement-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #4a4a6a;
    border-radius: 10px;
    padding: 15px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">🏴‍☠️ Luffy\'s Grand Line RPG</div>', unsafe_allow_html=True)

# ================= SESSION STATE =================
defaults = {
    "user": None, "xp": 0, "difficulty_multiplier": 1.0,
    "water_count": 0, "streak": 0,
    "water_streak": 0, "perfect_days": 0, "tasks_completed": 0,
    "healthy_days": 0, "early_submissions": 0, "late_submissions": 0,
    "balanced_days": 0, "achievements": []
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ================= HELPER FUNCTIONS =================

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

def get_welcome_message():
    """Get a personalized welcome message"""
    message = random.choice(WELCOME_MESSAGES)
    return message.format(user=st.session_state.user)

def check_achievements():
    """Check and award new achievements"""
    new_achievements = []
    for achievement_id, achievement_data in ACHIEVEMENTS.items():
        if achievement_id not in st.session_state.achievements:
            if achievement_data["condition"]():
                st.session_state.achievements.append(achievement_id)
                new_achievements.append(achievement_data)
    return new_achievements

# ================= GOOGLE SHEETS =================
def get_sheet():
    """Initialize Google Sheets connection"""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open("Pirate_Tracker_DB")
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

# ================= LOGIN =================
def login_page(sheet):
    st.header("🛡️ Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("⚓ Set Sail"):
        if not username or not password:
            st.warning("Please enter both username and password")
            return
        
        try:
            users_sheet = sheet.worksheet("USERS")
            users = users_sheet.get_all_records()
            
            for user in users:
                if str(user.get("username", "")).strip() == username.strip():
                    if str(user.get("password", "")).strip() == password.strip():
                        st.session_state.user = username
                        st.session_state.xp = int(user.get("xp", 0))
                        st.session_state.difficulty_multiplier = float(user.get("difficulty_multiplier", 1.0))
                        st.session_state.streak = int(user.get("streak", 0))
                        
                        # Load achievements
                        achievements_str = user.get("achievements", "")
                        st.session_state.achievements = achievements_str.split(",") if achievements_str else []
                        
                        # Check for first login achievement
                        new_achievements = check_achievements()
                        for achievement in new_achievements:
                            st.balloons()
                            st.success(f"🏆 Achievement Unlocked: {achievement['icon']} {achievement['name']}!")
                        
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Wrong password!")
                        return
            
            st.error("User not found!")
        except Exception as e:
            st.error(f"Error: {e}")

# ================= DASHBOARD =================
def dashboard_page(sheet, preview_date):
    st.info(get_welcome_message())
    
    # Crew role badge
    role, icon, description = get_crew_role(st.session_state.xp)
    st.markdown(f"""
    <div class="crew-badge">
        <h2 style="color: #FFD700; margin: 0;">⚔️ {icon} {role} ⚔️</h2>
        <p style="color: #ffffff; margin: 10px 0 0 0;">{description}</p>
        <p style="color: #aaaaaa; font-size: 12px;">Total XP: {st.session_state.xp:,}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Island progress
    current_island, next_island = get_current_island(st.session_state.xp)
    st.markdown(f"""
    <div class="island-card">
        <h3 style="color: #FFD700; margin: 0;">🗺️ Current Location: {current_island[2]} {current_island[0]}</h3>
        <p style="color: #ffffff; margin: 10px 0 0 0;">{current_island[3]}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if next_island:
        progress = min(100, (st.session_state.xp - current_island[1]) / (next_island[1] - current_island[1]) * 100)
        st.write(f"📍 Progress to {next_island[2]} {next_island[0]}: {progress:.1f}%")
        st.progress(progress / 100)
    
    # Streak
    if st.session_state.streak > 0:
        fire_count = min(10, st.session_state.streak)
        st.markdown(f"<span style='font-size: 24px;'>{'🔥' * fire_count}</span> "
                   f"<span style='color: #FFD700; font-size: 18px;'>{st.session_state.streak} Day Streak!</span>", 
                   unsafe_allow_html=True)
    
    st.divider()
    
    # Date header
    st.header(f"📅 {preview_date.strftime('%A, %d %B %Y')}")
    
    today_str = str(preview_date)
    
    # Get timetable
    try:
        timetable_sheet = sheet.worksheet("TIMETABLE")
        timetable = timetable_sheet.get_all_records()
        today_tasks = [t for t in timetable if t.get("date") == today_str]
    except:
        today_tasks = []
    
    # Display tasks
    if today_tasks:
        st.subheader("📜 Today's Tasks")
        for task in today_tasks:
            if task.get("category") == "TED" and task.get("link"):
                st.markdown(f"• 🎬 [{task.get('title', 'Task')}]({task.get('link')})")
            else:
                st.write("• " + task.get("title", "Task"))
    
    # Reading questions
    try:
        reading_sheet = sheet.worksheet("READING_REFLECTIONS")
        reading_data = reading_sheet.get_all_records()
        reading_tasks = [t for t in today_tasks if t.get("category") == "Reading"]
        
        if reading_tasks:
            st.subheader("📘 Reading Questions")
            for r_task in reading_tasks:
                for row in reading_data:
                    if row.get("book", "").lower() in r_task.get("title", "").lower():
                        st.write("• " + row.get("question", ""))
    except:
        pass
    
    # Presentation prompts
    try:
        presentation_sheet = sheet.worksheet("PRESENTATIONS")
        presentation_data = presentation_sheet.get_all_records()
        todays_prompts = [p for p in presentation_data if p.get("date") == today_str]
        
        if todays_prompts:
            st.subheader("🎤 Presentation Prompts")
            for p in todays_prompts:
                st.write("• " + p.get("prompt", ""))
    except:
        pass
    
    st.divider()
    st.write(f"**Difficulty:** {st.session_state.difficulty_multiplier:.2f}x")

# ================= MISSIONS =================
def missions_page(sheet, preview_date):
    st.header("⚔️ Daily Health Tracker")
    
    today_str = str(preview_date)
    xp_today = 0
    
    # Water
    st.subheader("💧 Water Intake")
    water_cols = st.columns(8)
    for i in range(8):
        if i < st.session_state.water_count:
            glass = "🟦"
        else:
            glass = "⬜"
        if water_cols[i].button(glass, key=f"water_{i}"):
            st.session_state.water_count = i + 1
    st.write(f"{st.session_state.water_count}/8 glasses")
    
    if st.session_state.water_count >= 8:
        xp_today += int(10 * st.session_state.difficulty_multiplier)
        st.success("💧 Water goal achieved! +10 XP")
    
    st.divider()
    
    # Vegetables
    st.subheader("🥕 Vegetable Colors")
    veg_colors = {"🔴 Red": "red", "🟡 Yellow": "yellow", "🟢 Green": "green", 
                  "⚪ White": "white", "🌸 Pink": "pink"}
    veg_total = 0
    veg_cols = st.columns(5)
    for idx, (icon, key) in enumerate(veg_colors.items()):
        with veg_cols[idx]:
            count = st.number_input(icon, 0, 5, key=f"veg_{key}")
            if count > 0:
                veg_total += 1
    
    if veg_total >= 3:
        xp_today += int(10 * st.session_state.difficulty_multiplier)
        st.success("🥕 Vegetable goal achieved! +10 XP")
    
    st.divider()
    
    # Food Groups
    st.subheader("🍽️ Food Groups")
    food_groups = {"🍗 Protein": "protein", "🍎 Fruits": "fruits", "🥦 Vegetables": "vegetables",
                   "🥑 Fats": "fats", "🍞 Carbs": "carbs"}
    food_total = 0
    food_cols = st.columns(5)
    for idx, (icon, key) in enumerate(food_groups.items()):
        with food_cols[idx]:
            portions = st.number_input(icon, 0, 6, key=f"food_{key}")
            if portions > 0:
                food_total += 1
    
    if food_total >= 4:
        xp_today += int(10 * st.session_state.difficulty_multiplier)
        st.success("🍽️ Food groups goal achieved! +10 XP")
    
    st.divider()
    
    # Tasks
    st.header("📋 Today's Missions")
    
    try:
        timetable_sheet = sheet.worksheet("TIMETABLE")
        timetable = timetable_sheet.get_all_records()
        today_tasks = [t for t in timetable if t.get("date") == today_str]
    except:
        today_tasks = []
    
    task_xp_total = 0
    tasks_done = 0
    
    for task in today_tasks:
        task_title = task.get("title", "Task")
        task_xp = int(task.get("xp", 0))
        task_xp_total += task_xp
        
        col1, col2 = st.columns([4, 1])
        with col1:
            done = st.checkbox(task_title, key=f"{today_str}_{task_title}")
        with col2:
            st.write(f"{task_xp} XP")
        
        if done:
            xp_today += int(task_xp * st.session_state.difficulty_multiplier)
            tasks_done += 1
            st.session_state.tasks_completed += 1
    
    st.divider()
    
    # Summary
    st.header("📊 Summary")
    st.write(f"**XP Earned Today:** {xp_today}")
    st.write(f"**Tasks Completed:** {tasks_done}/{len(today_tasks)}")
    
    if st.button("🚀 Submit Day"):
        # Update difficulty
        if xp_today < task_xp_total:
            st.session_state.difficulty_multiplier = min(2.0, st.session_state.difficulty_multiplier + 0.1)
        else:
            st.session_state.difficulty_multiplier = max(1.0, st.session_state.difficulty_multiplier - 0.05)
        
        # Update XP and streak
        st.session_state.xp += xp_today
        if xp_today >= task_xp_total:
            st.session_state.streak += 1
            st.session_state.perfect_days += 1
        else:
            st.session_state.streak = 0
        
        # Update special counters
        if st.session_state.water_count >= 8:
            st.session_state.water_streak += 1
        else:
            st.session_state.water_streak = 0
        
        if food_total >= 4 and veg_total >= 3:
            st.session_state.balanced_days += 1
        
        # Check achievements
        new_achievements = check_achievements()
        for achievement in new_achievements:
            st.balloons()
            st.success(f"🏆 Achievement Unlocked: {achievement['icon']} {achievement['name']}!")
        
        # Save to Google Sheets
        try:
            log_sheet = sheet.worksheet("DAILY_LOG")
            log_sheet.append_row([
                st.session_state.user,
                today_str,
                xp_today,
                st.session_state.difficulty_multiplier,
                st.session_state.streak
            ])
            
            # Update user XP
            users_sheet = sheet.worksheet("USERS")
            users = users_sheet.get_all_records()
            for idx, user in enumerate(users, start=2):
                if str(user.get("username", "")).strip() == st.session_state.user:
                    users_sheet.update_cell(idx, 4, st.session_state.xp)
                    users_sheet.update_cell(idx, 5, st.session_state.difficulty_multiplier)
                    users_sheet.update_cell(idx, 6, st.session_state.streak)
                    users_sheet.update_cell(idx, 7, ",".join(st.session_state.achievements))
                    break
            
            st.success("Day submitted!")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"Error saving: {e}")

# ================= STATS =================
def stats_page(sheet):
    st.header("📊 Statistics")
    
    # Overview
    st.subheader("📈 Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total XP", st.session_state.xp)
    col2.metric("🔥 Streak", f"{st.session_state.streak} days")
    col3.metric("💧 Water Streak", f"{st.session_state.water_streak} days")
    col4.metric("📋 Tasks Done", st.session_state.tasks_completed)
    
    # Crew role
    role, icon, description = get_crew_role(st.session_state.xp)
    st.markdown(f"""
    <div class="crew-badge">
        <h3 style="color: #FFD700; margin: 0;">⚔️ {icon} {role} ⚔️</h3>
        <p style="color: #ffffff; margin: 10px 0 0 0;">{description}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Island progress
    current_island, next_island = get_current_island(st.session_state.xp)
    st.markdown(f"""
    <div class="island-card">
        <h3 style="color: #FFD700; margin: 0;">🗺️ {current_island[2]} {current_island[0]}</h3>
        <p style="color: #ffffff; margin: 10px 0 0 0;">{current_island[3]}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Achievements
    st.subheader("🏆 Achievements")
    earned = set(st.session_state.achievements)
    ach_cols = st.columns(5)
    for idx, (achievement_id, achievement_data) in enumerate(ACHIEVEMENTS.items()):
        with ach_cols[idx % 5]:
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
    
    # Historical stats
    try:
        log_sheet = sheet.worksheet("DAILY_LOG")
        records = log_sheet.get_all_records()
        user_records = [r for r in records if r.get("username") == st.session_state.user]
        
        if user_records:
            st.divider()
            st.subheader("📜 Pirate Log History")
            xp_values = [int(r.get("xp_today", 0)) for r in user_records]
            st.write(f"**Days Logged:** {len(user_records)}")
            st.write(f"**Total XP Earned:** {sum(xp_values)}")
            st.write(f"**Average XP:** {sum(xp_values)/len(xp_values):.1f}")
            st.write(f"**Best Day:** {max(xp_values)}")
            
            st.line_chart(xp_values)
    except:
        pass

# ================= MAIN =================
def main():
    sheet = get_sheet()
    if sheet is None:
        return
    
    if not st.session_state.user:
        login_page(sheet)
    else:
        # Sidebar
        st.sidebar.title("🏴‍☠️ Navigation")
        preview_date = st.sidebar.date_input("Date", value=date.today())
        page = st.sidebar.radio("Go to", ["Dashboard", "Missions", "Stats"])
        
        st.sidebar.divider()
        if st.sidebar.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                if key not in ["_is_running", "_is_local"]:
                    del st.session_state[key]
            st.rerun()
        
        # Main content
        if page == "Dashboard":
            dashboard_page(sheet, preview_date)
        elif page == "Missions":
            missions_page(sheet, preview_date)
        elif page == "Stats":
            stats_page(sheet)

if __name__ == "__main__":
    main()
