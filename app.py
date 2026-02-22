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
if "just_leveled_up" not in st.session_state:
    st.session_state.just_leveled_up = False
if "difficulty_multiplier" not in st.session_state:
    st.session_state.difficulty_multiplier = 1.0

# ---------------- TIMETABLE ----------------

TED_LINKS = {
    "Chris Hadfield": "https://www.ted.com/talks/chris_hadfield_what_i_learned_from_going_blind_in_space",
    "Mark Rober": "https://www.ted.com/talks/mark_rober_the_super_mario_effect",
    "Sting": "https://www.ted.com/talks/sting_how_i_started_writing_songs_again",
    "Elon Musk": "https://www.ted.com/talks/elon_musk_the_future_we_re_building",
    "Brian Cox": "https://www.ted.com/talks/brian_cox_why_we_need_the_explorers",
    "Robert Waldinger": "https://www.ted.com/talks/robert_waldinger_what_makes_a_good_life",
    "Cameron Russell": "https://www.ted.com/talks/cameron_russell_looks_aren_t_everything",
    "Kid President": "https://www.ted.com/talks/kid_president_i_think_we_all_need_a_pep_talk",
    "Michio Kaku": "https://www.ted.com/talks/michio_kaku_the_universe_in_a_nutshell",
    "Tom Thum": "https://www.ted.com/talks/tom_thum_the_orchestra_in_my_mouth",
    "Reshma Saujani": "https://www.ted.com/talks/reshma_saujani_teach_girls_bravery_not_perfection"
}

week1 = {
    "Monday": ["Water + Breakfast","Reading","Schoolwork",
               "Exercise","Yoga",
               "TED: Chris Hadfield",
               "Drums","Outdoor","Chores","Dinner","Free"],
    "Tuesday": ["Hydration","Reading","Writing","Piano",
                "Exercise","TED: Mark Rober","Coding",
                "Outdoor","Cook","Family","Journal"],
}

week2_extra = ["Kid President","Michio Kaku","Tom Thum","Reshma Saujani"]

week_number = date.today().isocalendar()[1]
current_week = week1.copy()

if week_number % 2 == 0:
    for day in current_week:
        current_week[day].append("TED: " + random.choice(week2_extra))

XP_TARGETS = {
    "Monday":120,
    "Tuesday":120,
}

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

    page = st.sidebar.radio("Navigate",
                            ["Dashboard","Missions","Stats"])

    today_day = date.today().strftime("%A")
    today_tasks = current_week.get(today_day, [])
    xp_target = XP_TARGETS.get(today_day, 120)

    # ================= DASHBOARD =================
    if page == "Dashboard":

        st.header(f"{today_day} Plan")

        for task in today_tasks:
            if "TED" in task:
                speaker = task.replace("TED: ","")
                url = TED_LINKS.get(speaker,"")
                st.markdown(f"[{task}]({url})")
            else:
                st.write("• " + task)

        st.markdown(f"### 🎯 XP Target: {xp_target}")
        st.write(f"Current XP: {st.session_state.xp}")

    # ================= MISSIONS =================
    if page == "Missions":

        st.header("Today's Missions")

        if "task_progress" not in st.session_state:
            st.session_state.task_progress = {}

        xp_today = 0
        current_hour = datetime.now().hour

        for i, task in enumerate(today_tasks):

            unlock = True

            # sequential unlock
            if i > 0:
                prev_task = today_tasks[i-1]
                if not st.session_state.task_progress.get(prev_task, False):
                    unlock = False

            # time validation (each task ~1 hour block starting 7am)
            task_hour = 7 + i
            if current_hour < task_hour:
                unlock = False

            if unlock:
                done = st.checkbox(task, key=f"task_{i}")
                st.session_state.task_progress[task] = done
                if done:
                    xp_today += int(15 * st.session_state.difficulty_multiplier)
            else:
                st.write(f"🔒 {task}")

        st.markdown(f"XP Earned Today: {xp_today}")

        if st.button("Submit Day"):

            if xp_today < xp_target:
                st.session_state.difficulty_multiplier += 0.1
                st.warning("Target missed. Difficulty increased.")
            else:
                st.session_state.difficulty_multiplier = max(1.0,
                    st.session_state.difficulty_multiplier - 0.05)

            st.session_state.xp += xp_today

            log_sheet.append_row([
                st.session_state.user,
                str(date.today()),
                xp_today
            ])

            st.success("Day submitted!")

    # ================= STATS =================
    if page == "Stats":

        records = log_sheet.get_all_records()
        user_logs = [r for r in records
                     if r["username"] == st.session_state.user]

        xp_list = [int(r.get("xp_today",0))
                   for r in user_logs]

        if xp_list:
            st.line_chart(xp_list)

        st.write(f"Difficulty Multiplier: {st.session_state.difficulty_multiplier:.2f}")
