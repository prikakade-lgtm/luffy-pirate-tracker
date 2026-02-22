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
# MISSIONS – VISUAL RPG MODE
# =====================================================
if page == "⚔️ Missions":

    st.header("⚓ Daily Missions")

    # ---------------- WATER SYSTEM ----------------
    st.subheader("💧 Water Intake")

    if "water_count" not in st.session_state:
        st.session_state.water_count = 0

    col1, col2 = st.columns([4,1])

    with col1:
        st.progress(st.session_state.water_count / 8)

    with col2:
        if st.button("Drink 🥛"):
            if st.session_state.water_count < 8:
                st.session_state.water_count += 1

    st.write(f"{st.session_state.water_count}/8 Glasses")

    # ---------------- VEG COLOR SYSTEM ----------------
    st.subheader("🥦 Vegetable Colors")

    veg_colors = {
        "Green": "#22c55e",
        "Red": "#ef4444",
        "Orange": "#f97316"
    }

    if "veg_tracker" not in st.session_state:
        st.session_state.veg_tracker = {c:0 for c in veg_colors}

    for color, hexcode in veg_colors.items():

        col1, col2 = st.columns([4,1])

        with col1:
            filled = st.session_state.veg_tracker[color]
            ratio = min(filled / 3, 1)

            st.markdown(
                f"""
                <div style="background-color:#333;border-radius:20px;">
                    <div style="
                        width:{ratio*100}%;
                        background:{hexcode};
                        height:20px;
                        border-radius:20px;">
                    </div>
                </div>
                <p>{color} Portions: {filled}</p>
                """,
                unsafe_allow_html=True
            )

        with col2:
            if st.button("+", key=f"veg_{color}"):
                st.session_state.veg_tracker[color] += 1

    veg_total = sum(st.session_state.veg_tracker.values())

    # ---------------- FOOD GROUP SYSTEM ----------------
    st.subheader("🍗 Food Groups")

    food_groups = {
        "Protein": "🍗",
        "Carbs": "🍞",
        "Fruits": "🍎",
        "Dairy": "🥛"
    }

    if "food_tracker" not in st.session_state:
        st.session_state.food_tracker = {g:0 for g in food_groups}

    for group, icon in food_groups.items():

        col1, col2 = st.columns([4,1])

        with col1:
            filled = st.session_state.food_tracker[group]
            ratio = min(filled / 3, 1)

            st.progress(ratio)
            st.write(f"{icon} {group}: {filled}")

        with col2:
            if st.button("+", key=f"food_{group}"):
                st.session_state.food_tracker[group] += 1

    food_total = sum(st.session_state.food_tracker.values())

    # ---------------- SKILL LEVEL SYSTEM ----------------
    st.subheader("⚔️ Skills & Training")

    skills = [
        "Exercise",
        "Yoga",
        "Reading",
        "Writing",
        "Drums",
        "Piano",
        "Skill Practice",
        "Outdoor",
        "Chores",
        "Cooking"
    ]

    if "skill_tracker" not in st.session_state:
        st.session_state.skill_tracker = {s:0 for s in skills}

    for skill in skills:

        col1, col2 = st.columns([4,1])

        with col1:
            level = st.session_state.skill_tracker[skill]
            ratio = min(level / 5, 1)

            st.progress(ratio)
            st.write(f"{skill} Level: {level}")

        with col2:
            if st.button("+", key=f"skill_{skill}"):
                st.session_state.skill_tracker[skill] += 1

    skill_total = sum(st.session_state.skill_tracker.values())

    # ---------------- XP CALCULATION ----------------
    water_xp = st.session_state.water_count * 5
    veg_xp = veg_total * 5
    food_xp = food_total * 5
    skill_xp = skill_total * 10

    perfect_bonus = 50 if (
        st.session_state.water_count == 8 and
        veg_total >= 3 and
        food_total >= 4
    ) else 0

    total_today = water_xp + veg_xp + food_xp + skill_xp + perfect_bonus

    st.markdown(f"### ⭐ Potential XP Today: {total_today}")

    # ---------------- SUBMIT ----------------
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
                st.session_state.water_count,
                veg_total,
                food_total,
                skill_total,
                total_today
            ])

            for idx, u in enumerate(users):
                if u["username"] == st.session_state.user:
                    users_sheet.update(f"C{idx+2}", st.session_state.xp)
                    users_sheet.update(f"E{idx+2}", today_str)

            # RESET ALL DAILY DATA
            st.session_state.water_count = 0
            st.session_state.veg_tracker = {c:0 for c in veg_colors}
            st.session_state.food_tracker = {g:0 for g in food_groups}
            st.session_state.skill_tracker = {s:0 for s in skills}

            st.success(f"+{total_today} XP earned!")

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
