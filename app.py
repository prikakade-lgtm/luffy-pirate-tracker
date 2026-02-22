import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import random

# ---- GOOGLE SHEETS CONNECTION ----
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

# ---- PAGE CONFIG ----
st.set_page_config(page_title="Luffy Pirate Tracker", layout="wide")

# ---- LUFFY THEME ----
st.markdown("""
<style>
body { background-color: #111827; color: white; }
.big-title { font-size: 48px; font-weight: bold; color: #FFD700; }
.rank { font-size: 28px; color: #FF0000; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">🏴‍☠️ Luffy\'s Grand Line Tracker</div>', unsafe_allow_html=True)

# ---- LOGIN SYSTEM ----
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.header("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Enter the Grand Line"):
        users = users_sheet.get_all_records()
        for user in users:
            if user["username"] == username and user["password"] == password:
                st.session_state.user = username
                st.session_state.xp = user["xp"]
                st.session_state.water_streak = user["water_streak"]
                st.success("Welcome aboard!")
                st.rerun()

        st.error("Wrong credentials.")

else:
    st.header("⚓ Daily Missions")

    water = st.checkbox("💧 6-8 Glasses Water")
    veg = st.checkbox("🥦 3 Veg Colors")
    food = st.checkbox("🍗 4 Food Groups")
    exercise = st.checkbox("💪 Training Arc")
    yoga = st.checkbox("🧘 Recovery")
    reading = st.checkbox("📚 Reading")
    writing = st.checkbox("✍️ Story Mode")
    drums = st.checkbox("🥁 Drum Power")
    piano = st.checkbox("🎹 Piano Skill")
    ted = st.checkbox("🎥 Knowledge Boost")
    skill = st.checkbox("🧠 Skill Upgrade")
    outdoor = st.checkbox("🌊 Adventure Time")
    chores = st.checkbox("🧹 Ship Duties")
    cooking = st.checkbox("🍳 Chef Training")

    missions = [water, veg, food, exercise, yoga, reading,
                writing, drums, piano, ted, skill,
                outdoor, chores, cooking]

    completed = sum(missions)
    base_xp = completed * 10
    perfect_bonus = 40 if completed >= 12 else 0

    if water:
        st.session_state.water_streak += 1
    else:
        st.session_state.water_streak = 0

    streak_bonus = st.session_state.water_streak * 2
    total_today = base_xp + perfect_bonus + streak_bonus

    if st.button("🏆 Submit Day"):
        st.session_state.xp += total_today

        log_sheet.append_row([
            st.session_state.user,
            str(date.today()),
            water, veg, food, exercise, yoga, reading,
            writing, drums, piano, ted, skill,
            outdoor, chores, cooking,
            total_today
        ])

        users = users_sheet.get_all_records()
        for idx, user in enumerate(users):
            if user["username"] == st.session_state.user:
                users_sheet.update(f"C{idx+2}", st.session_state.xp)
                users_sheet.update(f"D{idx+2}", st.session_state.water_streak)

        st.balloons()
        st.success(f"+{total_today} XP earned!")

    # ---- LEVEL SYSTEM ----
    level = st.session_state.xp // 500 + 1
    xp_progress = st.session_state.xp % 500

    if level < 3:
        rank = "Straw Hat Rookie"
    elif level < 5:
        rank = "East Blue Fighter"
    elif level < 8:
        rank = "Grand Line Warrior"
    elif level < 12:
        rank = "Warlord Tier"
    else:
        rank = "Future Pirate King 👑"

    st.markdown(f"<div class='rank'>Rank: {rank}</div>", unsafe_allow_html=True)
    st.write(f"Total XP: {st.session_state.xp}")
    st.progress(xp_progress / 500)

    # ---- QUEST ----
    quests = [
        "Write a Luffy-style battle speech",
        "Create your own Devil Fruit power",
        "Cook a pirate feast",
        "Train like Luffy (extra 20 pushups)",
        "Design your pirate flag",
        "Build a mini science experiment"
    ]

    st.header("🎯 Daily Pirate Quest")
    st.info(random.choice(quests))
