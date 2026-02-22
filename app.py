import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import random

# ---------------- GOOGLE SHEETS ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open("Pirate_Tracker_DB")

users_sheet = sheet.worksheet("USERS")
log_sheet = sheet.worksheet("DAILY_LOG")
timetable_sheet = sheet.worksheet("TIMETABLE")
reading_sheet = sheet.worksheet("READING_REFLECTIONS")
presentation_sheet = sheet.worksheet("PRESENTATIONS")

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Luffy Grand Line RPG", layout="wide")

st.markdown("""
<style>
body { background-color: #111827; color: white; }
.big-title { font-size: 48px; font-weight: bold; color: #FFD700; }
.rank { font-size: 28px; color: #FF4B4B; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">🏴‍☠️ Luffy\'s Grand Line RPG</div>', unsafe_allow_html=True)

# ---------------- SESSION INIT ----------------
if "user" not in st.session_state:
    st.session_state.user = None
if "xp" not in st.session_state:
    st.session_state.xp = 0
if "difficulty_multiplier" not in st.session_state:
    st.session_state.difficulty_multiplier = 1.0
if "task_progress" not in st.session_state:
    st.session_state.task_progress = {}

# ---------------- LOGIN ----------------
if st.session_state.user is None:

    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Enter"):
        users = users_sheet.get_all_records()

        for user in users:
            if user["username"] == username and user["password"] == password:
                st.session_state.user = username
                st.session_state.xp = int(user.get("xp", 0))
                st.rerun()

        st.error("Wrong credentials")

# ---------------- MAIN APP ----------------
else:

    page = st.sidebar.radio("Navigate", ["Dashboard","Missions","Stats"])

    today_str = str(date.today())
    timetable = timetable_sheet.get_all_records()
    today_tasks = [t for t in timetable if t["date"] == today_str]

    # ================= DASHBOARD =================
    if page == "Dashboard":

        st.header("Today’s Plan")

        # Global health targets (always visible)
        st.subheader("Daily Health Targets")
        st.write("• 8 glasses of water")
        st.write("• 3 vegetable colors")
        st.write("• 4–5 food groups")

        st.divider()

        for task in today_tasks:
            title = task["title"]
            category = task["category"]
            link = task.get("link","")

            if category == "TED" and link:
                st.markdown(f"• [{title}]({link})")
            else:
                st.write("• " + title)

        # Show reading questions
        reading_tasks = [t for t in today_tasks if t["category"] == "Reading"]
        if reading_tasks:
            st.divider()
            st.subheader("Reading Reflection Questions")

            reading_data = reading_sheet.get_all_records()

            for r_task in reading_tasks:
                for row in reading_data:
                    if row["book"] in r_task["title"]:
                        st.write("• " + row["question"])

        # Show presentation prompts
        presentation_data = presentation_sheet.get_all_records()
        todays_prompts = [p for p in presentation_data if p["date"] == today_str]

        if todays_prompts:
            st.divider()
            st.subheader("Presentation Prompts")

            for p in todays_prompts:
                st.write(f"• {p['prompt']}")

        st.divider()
        st.write(f"Current XP: {st.session_state.xp}")
        st.write(f"Difficulty Multiplier: {st.session_state.difficulty_multiplier:.2f}")

    # ================= MISSIONS =================
    if page == "Missions":

        st.header("Today's Missions")

        xp_today = 0

        # -------- Global Health Missions --------
        st.subheader("Daily Health")

        water = st.selectbox("Glasses of Water", list(range(0, 9)))
        veg = st.selectbox("Vegetable Colors Eaten", list(range(0, 6)))
        food = st.selectbox("Food Groups Eaten", list(range(0, 7)))

        if water >= 8:
            xp_today += int(10 * st.session_state.difficulty_multiplier)
        if veg >= 3:
            xp_today += int(10 * st.session_state.difficulty_multiplier)
        if food >= 4:
            xp_today += int(10 * st.session_state.difficulty_multiplier)

        st.divider()

        # -------- Timetable Tasks --------
        for task in today_tasks:
            key = f"{today_str}_{task['title']}"
            done = st.checkbox(task["title"], key=key)

            if done:
                base_xp = int(task["xp"])
                xp_today += int(base_xp * st.session_state.difficulty_multiplier)

        st.divider()
        st.write(f"XP Earned Today: {xp_today}")

        if st.button("Submit Day"):

            # Difficulty scaling
            target = sum(int(t["xp"]) for t in today_tasks)

            if xp_today < target:
                st.session_state.difficulty_multiplier += 0.1
                st.warning("Target missed. Difficulty increased.")
            else:
                st.session_state.difficulty_multiplier = max(
                    1.0,
                    st.session_state.difficulty_multiplier - 0.05
                )

            st.session_state.xp += xp_today

            log_sheet.append_row([
                st.session_state.user,
                today_str,
                xp_today,
                st.session_state.difficulty_multiplier
            ])

            st.success("Day submitted!")
            st.rerun()

    # ================= STATS =================
    if page == "Stats":

        records = log_sheet.get_all_records()
        user_logs = [r for r in records if r["username"] == st.session_state.user]

        xp_list = [int(r.get("xp_today", 0)) for r in user_logs]

        if xp_list:
            st.line_chart(xp_list)

        st.write(f"Total XP: {st.session_state.xp}")
        st.write(f"Difficulty Multiplier: {st.session_state.difficulty_multiplier:.2f}")
