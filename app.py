import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import date, datetime

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
.big-title { font-size: 42px; font-weight: bold; color: #FFD700; }
.water { font-size: 40px; }
.section { margin-top: 30px; }
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
if "water_count" not in st.session_state:
    st.session_state.water_count = 0

# ---------------- LOGIN ----------------
if st.session_state.user is None:

    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

if st.button("Enter"):
    users = users_sheet.get_all_records()

    for user in users:
        sheet_username = str(user.get("username", "")).strip()
        sheet_password = str(user.get("password", "")).strip()

        if sheet_username == username.strip() and sheet_password == password.strip():
            st.session_state.user = sheet_username
            st.session_state.xp = int(user.get("xp", 0))
            st.success("Login successful!")
            st.rerun()

    st.error("Wrong credentials")

# ---------------- MAIN APP ----------------
else:

    # -------- DATE PREVIEW --------
    st.sidebar.header("Date Preview")
    preview_date = st.sidebar.date_input("Select Date", value=date.today())
    today_str = str(preview_date)

    page = st.sidebar.radio("Navigate", ["Dashboard","Missions","Stats"])

    timetable = timetable_sheet.get_all_records()
    today_tasks = [t for t in timetable if t["date"] == today_str]

    # ================= DASHBOARD =================
    if page == "Dashboard":

        st.header(f"Plan for {preview_date.strftime('%A, %d %B %Y')}")

        for task in today_tasks:
            if task["category"] == "TED" and task["link"]:
                st.markdown(f"• [{task['title']}]({task['link']})")
            else:
                st.write("• " + task["title"])

        # Reading questions
        reading_tasks = [t for t in today_tasks if t["category"] == "Reading"]
        if reading_tasks:
            st.subheader("📘 Reading Questions")
            reading_data = reading_sheet.get_all_records()
            for r_task in reading_tasks:
                for row in reading_data:
                    if row["book"] in r_task["title"]:
                        st.write("• " + row["question"])

        # Presentation prompts
        presentation_data = presentation_sheet.get_all_records()
        todays_prompts = [p for p in presentation_data if p["date"] == today_str]
        if todays_prompts:
            st.subheader("🎤 Presentation Prompts")
            for p in todays_prompts:
                st.write("• " + p["prompt"])

        st.divider()
        st.write(f"Current XP: {st.session_state.xp}")
        st.write(f"Difficulty: {st.session_state.difficulty_multiplier:.2f}")

    # ================= MISSIONS =================
    if page == "Missions":

        st.header("Daily Health Tracker")

        xp_today = 0

        # -------- WATER VISUAL FILL --------
        st.subheader("💧 Water Intake")

        cols = st.columns(8)
        for i in range(8):
            if i < st.session_state.water_count:
                glass = "🟦"  # filled
            else:
                glass = "⬜"  # empty

            if cols[i].button(glass, key=f"water_{i}"):
                st.session_state.water_count = i + 1

        st.write(f"{st.session_state.water_count}/8 glasses")

        if st.session_state.water_count >= 8:
            xp_today += int(10 * st.session_state.difficulty_multiplier)

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

        for icon, key in veg_colors.items():
            count = st.number_input(icon, 0, 5, key=f"veg_{key}")
            if count > 0:
                veg_total_colors += 1

        if veg_total_colors >= 3:
            xp_today += int(10 * st.session_state.difficulty_multiplier)

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

        for icon, key in food_groups.items():
            portions = st.number_input(icon, 0, 6, key=f"food_{key}")
            if portions > 0:
                food_total_groups += 1

        if food_total_groups >= 4:
            xp_today += int(10 * st.session_state.difficulty_multiplier)

        st.divider()

        # -------- TASKS --------
        st.header("Today's Missions")

        for task in today_tasks:
            key = f"{today_str}_{task['title']}"
            done = st.checkbox(task["title"], key=key)
            if done:
                xp_today += int(int(task["xp"]) * st.session_state.difficulty_multiplier)

        st.write(f"XP Earned Today: {xp_today}")

        if st.button("Submit Day"):
            target = sum(int(t["xp"]) for t in today_tasks)

            if xp_today < target:
                st.session_state.difficulty_multiplier += 0.1
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
