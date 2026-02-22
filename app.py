import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import date

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
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">🏴‍☠️ Luffy\'s Grand Line RPG</div>', unsafe_allow_html=True)

# ================= SESSION STATE =================
if "user" not in st.session_state:
    st.session_state.user = None
if "xp" not in st.session_state:
    st.session_state.xp = 0
if "difficulty_multiplier" not in st.session_state:
    st.session_state.difficulty_multiplier = 1.0
if "water_count" not in st.session_state:
    st.session_state.water_count = 0
if "streak" not in st.session_state:
    st.session_state.streak = 0

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
    st.write(f"**Current XP:** {st.session_state.xp}")
    st.write(f"**Difficulty:** {st.session_state.difficulty_multiplier:.2f}x")
    st.write(f"**Streak:** {st.session_state.streak} days")

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
        else:
            st.session_state.streak = 0
        
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
                    break
            
            st.success("Day submitted!")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"Error saving: {e}")

# ================= STATS =================
def stats_page(sheet):
    st.header("📊 Statistics")
    
    try:
        log_sheet = sheet.worksheet("DAILY_LOG")
        records = log_sheet.get_all_records()
        user_records = [r for r in records if r.get("username") == st.session_state.user]
        
        if user_records:
            xp_values = [int(r.get("xp_today", 0)) for r in user_records]
            st.write(f"**Total Days:** {len(user_records)}")
            st.write(f"**Total XP:** {sum(xp_values)}")
            st.write(f"**Average XP:** {sum(xp_values)/len(xp_values):.1f}")
            st.write(f"**Best Day:** {max(xp_values)}")
            
            st.subheader("📈 XP Over Time")
            st.line_chart(xp_values)
        else:
            st.info("No data yet. Complete some days to see statistics!")
    except Exception as e:
        st.error(f"Error: {e}")

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
