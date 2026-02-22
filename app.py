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
.rank { font-size: 28px; color: #FF4B4B; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">🏴‍☠️ Luffy\'s Grand Line Tracker</div>', unsafe_allow_html=True)

# ---- SESSION INIT ----
if "user" not in st.session_state:
    st.session_state.user = None

if "just_leveled_up" not in st.session_state:
    st.session_state.just_leveled_up = False

# ---- LOGIN SYSTEM ----
if st.session_state.user is None:

    st.header("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Enter the Grand Line"):
        users = users_sheet.get_all_records()

        for user in users:
            if str(user.get("username")).strip() == username.strip() and \
               str(user.get("password")).strip() == password.strip():

                st.session_state.user = username
                st.session_state.xp = int(user.get("xp", 0))
                st.session_state.water_streak = int(user.get("water_streak", 0))
                st.success("Welcome aboard!")
                st.rerun()

        st.error("Wrong credentials.")

# ---- MAIN APP ----
else:

    st.header("⚓ Daily Missions")

    # ---- MISSIONS ----
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

    today_str = str(date.today())

    # ---- SUBMIT BUTTON ----
    if st.button("🏆 Submit Day"):

        users = users_sheet.get_all_records()
        current_user = next((u for u in users if u["username"] == st.session_state.user), None)

        if current_user and str(current_user.get("last_login")) == today_str:
            st.warning("You already completed today’s missions.")
        else:
            old_level = st.session_state.xp // 500

            st.session_state.xp += total_today

            new_level = st.session_state.xp // 500
            if new_level > old_level:
                st.session_state.just_leveled_up = True

            log_sheet.append_row([
                st.session_state.user,
                today_str,
                water, veg, food, exercise, yoga, reading,
                writing, drums, piano, ted, skill,
                outdoor, chores, cooking,
                total_today
            ])

            for idx, u in enumerate(users):
                if u["username"] == st.session_state.user:
                    users_sheet.update(f"C{idx+2}", st.session_state.xp)
                    users_sheet.update(f"D{idx+2}", st.session_state.water_streak)
                    users_sheet.update(f"E{idx+2}", today_str)

            st.success(f"+{total_today} XP earned!")

    # ---- LEVEL SYSTEM ----
    level = st.session_state.xp // 500 + 1
    xp_progress = st.session_state.xp % 500
    progress_ratio = xp_progress / 500

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

    st.markdown(f"<div class='rank'>🏴‍☠️ Rank: {rank}</div>", unsafe_allow_html=True)
    st.write(f"⭐ Total XP: {st.session_state.xp}")
    st.write(f"🏅 Level: {level}")

    # ---- GOLD PROGRESS BAR ----
    if progress_ratio >= 0.8:
        st.markdown(
            f"""
            <div style="background-color:#333;border-radius:10px;padding:3px;">
                <div style="
                    width:{progress_ratio*100}%;
                    background:linear-gradient(90deg,gold,orange);
                    height:20px;
                    border-radius:8px;
                    transition: width 0.5s;">
                </div>
            </div>
            <p style='color:gold;font-weight:bold;'>🔥 Almost Level Up!</p>
            """,
            unsafe_allow_html=True
        )
    else:
        st.progress(progress_ratio)

    # ---- LEVEL UP CELEBRATION ----
    if st.session_state.just_leveled_up:
        st.balloons()
        st.image("https://media.giphy.com/media/12jcwKEZNh4GSQ/giphy.gif")
        st.success("LEVEL UP! Luffy just powered up!")
        st.session_state.just_leveled_up = False

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
