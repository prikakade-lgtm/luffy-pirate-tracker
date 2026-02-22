import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
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
st.set_page_config(page_title="Luffy Pirate RPG", layout="wide")

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
if "just_leveled_up" not in st.session_state:
    st.session_state.just_leveled_up = False
if "water_streak" not in st.session_state:
    st.session_state.water_streak = 0
if "xp" not in st.session_state:
    st.session_state.xp = 0

# ---------------- LOGIN ----------------
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

# ---------------- MAIN APP ----------------
else:

    # -------- NAVIGATION --------
    page = st.sidebar.radio(
        "Navigate the Grand Line",
        ["🏠 Dashboard", "⚔️ Missions", "🐉 Boss Battle", "📊 Stats", "👥 Crew"]
    )

    # =====================================================
    # DASHBOARD
    # =====================================================
    if page == "🏠 Dashboard":

        level = st.session_state.xp // 500 + 1
        xp_progress = st.session_state.xp % 500
        progress_ratio = xp_progress / 500

        if level < 3:
            rank = "Straw Hat Rookie"
            form = "Base Luffy"
        elif level < 5:
            rank = "East Blue Fighter"
            form = "Gear 2"
        elif level < 8:
            rank = "Grand Line Warrior"
            form = "Gear 4"
        elif level < 12:
            rank = "Warlord Tier"
            form = "Snakeman"
        else:
            rank = "Future Pirate King 👑"
            form = "Sun God Mode"

        st.markdown(f"<div class='rank'>🏴‍☠️ Rank: {rank}</div>", unsafe_allow_html=True)
        st.write(f"⭐ Total XP: {st.session_state.xp}")
        st.write(f"🏅 Level: {level}")
        st.write(f"🔥 Current Form: {form}")

        # Gold Progress Bar
        if progress_ratio >= 0.8:
            st.markdown(
                f"""
                <div style="background-color:#333;border-radius:10px;padding:3px;">
                    <div style="
                        width:{progress_ratio*100}%;
                        background:linear-gradient(90deg,gold,orange);
                        height:20px;
                        border-radius:8px;">
                    </div>
                </div>
                <p style='color:gold;font-weight:bold;'>🔥 Almost Level Up!</p>
                """,
                unsafe_allow_html=True
            )
        else:
            st.progress(progress_ratio)

    # =====================================================
    # MISSIONS
    # =====================================================
    if page == "⚔️ Missions":

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

        today_str = str(date.today())

        if st.button("🏆 Submit Day"):

            users = users_sheet.get_all_records()
            current_user = next((u for u in users if u["username"] == st.session_state.user), None)

            if current_user and str(current_user.get("last_login")) == today_str:
                st.warning("Already completed today.")
            else:

                old_level = st.session_state.xp // 500
                st.session_state.xp += total_today
                new_level = st.session_state.xp // 500

                if new_level > old_level:
                    st.session_state.just_leveled_up = True

                log_sheet.append_row([
                    st.session_state.user,
                    today_str,
                    total_today
                ])

                for idx, u in enumerate(users):
                    if u["username"] == st.session_state.user:
                        users_sheet.update(f"C{idx+2}", st.session_state.xp)
                        users_sheet.update(f"D{idx+2}", st.session_state.water_streak)
                        users_sheet.update(f"E{idx+2}", today_str)

                st.success(f"+{total_today} XP earned!")

        if st.session_state.just_leveled_up:
            st.balloons()
            st.image("https://media.giphy.com/media/12jcwKEZNh4GSQ/giphy.gif")
            st.success("LEVEL UP! Luffy powered up!")
            st.session_state.just_leveled_up = False

    # =====================================================
    # BOSS BATTLE
    # =====================================================
    if page == "🐉 Boss Battle":

        today = date.today().strftime("%A")
        boss_hp = 800 if today == "Sunday" else 500

        damage = st.session_state.xp % 100
        remaining = max(0, boss_hp - damage)

        st.subheader("Marine Admiral")
        st.progress(remaining / boss_hp)

        if remaining == 0:
            st.success("🏆 Boss Defeated!")

    # =====================================================
    # STATS
    # =====================================================
    if page == "📊 Stats":

        records = log_sheet.get_all_records()
        user_logs = [r for r in records if r["username"] == st.session_state.user]

        xp_list = []
        for r in user_logs:
            try:
                xp_list.append(int(r["total_today"]))
            except:
                xp_list.append(0)

        if xp_list:
            st.line_chart(xp_list)

        weekly = sum(xp_list[-7:]) if len(xp_list) >= 7 else sum(xp_list)
        st.write(f"🏆 Weekly XP: {weekly}")

    # =====================================================
    # CREW
    # =====================================================
    if page == "👥 Crew":

        xp = st.session_state.xp
        st.header("Straw Hat Crew")

        crew = []

        if xp >= 500: crew.append("Zoro")
        if xp >= 1000: crew.append("Nami")
        if xp >= 2000: crew.append("Sanji")
        if xp >= 3000: crew.append("Robin")
        if xp >= 5000: crew.append("Shanks")

        if crew:
            for member in crew:
                st.success(member)
        else:
            st.info("Train harder to unlock your crew.")
