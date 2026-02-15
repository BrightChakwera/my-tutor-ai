import streamlit as st
import google.generativeai as genai
import json
import pdfplumber
import io
import sqlite3
import hashlib
from fpdf import FPDF 

# 1. SETUP: API Configuration
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# --- DATABASE SETUP & AUTO-REPAIR ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # 1. Create Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    
    # 2. Create Enrollments Table
    c.execute('''CREATE TABLE IF NOT EXISTS enrollments 
                 (username TEXT, course TEXT, PRIMARY KEY (username, course))''')
    
    # 3. SCHEMA MIGRATION: Check if 'enrollments' exists in an old DB
    c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='enrollments'")
    if c.fetchone()[0] == 0:
        c.execute('''CREATE TABLE enrollments 
                     (username TEXT, course TEXT, PRIMARY KEY (username, course))''')
    
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def add_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password) VALUES (?,?)', (username, make_hashes(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username =?', (username,))
    data = c.fetchone()
    conn.close()
    if data:
        return check_hashes(password, data[0])
    return False

def enroll_course(username, course):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO enrollments(username, course) VALUES (?,?)', (username, course))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def get_user_courses(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('SELECT course FROM enrollments WHERE username = ?', (username,))
        courses = [row[0] for row in c.fetchall()]
    except sqlite3.OperationalError:
        courses = [] # Fallback if table still hasn't initialized
    conn.close()
    return courses

# Initialize the database on startup
init_db()

# --- AUTHENTICATION SYSTEM ---
def auth_page():
    st.title("🔐 Radar Grad-Tutors")
    auth_mode = st.tabs(["Login", "Register"])
    
    with auth_mode[0]:
        st.subheader("Welcome Back")
        col1, col2 = st.columns(2)
        with col1:
            user = st.text_input("Username", key="login_user")
            pw = st.text_input("Password", type="password", key="login_pw")
            if st.button("Login"):
                if login_user(user, pw):
                    st.session_state.logged_in = True
                    st.session_state.user_name = user
                    st.success(f"Logged in as {user}")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
        
        with col2:
            st.write("--- or ---")
            if st.button("🔴 Continue with Google"):
                st.session_state.logged_in = True
                st.session_state.user_name = "Google_User"
                st.rerun()
            if st.button("🔵 Continue with LinkedIn"):
                st.session_state.logged_in = True
                st.session_state.user_name = "LinkedIn_User"
                st.rerun()

    with auth_mode[1]:
        st.subheader("Create New Account")
        new_user = st.text_input("Choose Username")
        new_pw = st.text_input("Choose Password", type="password")
        confirm_pw = st.text_input("Confirm Password", type="password")
        
        if st.button("Register"):
            if new_pw != confirm_pw:
                st.error("Passwords do not match")
            elif len(new_pw) < 4:
                st.error("Password too short")
            else:
                if add_user(new_user, new_pw):
                    st.success("Account created successfully! Please go to the Login tab.")
                else:
                    st.error("Username already exists")

# --- AUTH INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    auth_page()
    st.stop()

# --- HELPERS ---
def create_pdf_report(course, score, difficulty, percent):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Radar Grad-Tutors Performance", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Course: {course}", ln=True)
    pdf.cell(200, 10, f"Score: {score}/7 ({percent}%)", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# 2. SIDEBAR
st.sidebar.title("Radar Grad-Tutors")
st.sidebar.write(f"Logged in: **{st.session_state.user_name}**")
if st.sidebar.button("Logout"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

access_mode = st.sidebar.radio("Account Tier:", ["Basic (Pre-built)", "Premium (Custom Radar)"])

course_list = [
    "College Algebra", "Elementary Calculus", "Elementary Microeconomics", 
    "Elementary Macroeconomics", "Mathematics for Economists",
    "Statistics for Social Scientist", "Intermediate Microeconomics", 
    "Intermediate Macroeconomics", "Econometrics 1", "Econometrics 2"
]

user_enrolled_courses = get_user_courses(st.session_state.user_name)
selected_course = None

if user_enrolled_courses:
    selected_course = st.sidebar.selectbox("Choose a Course:", user_enrolled_courses)

# --- SESSION STATE ---
if "quiz_set" not in st.session_state: st.session_state.quiz_set = []
if "current_idx" not in st.session_state: st.session_state.current_idx = 0
if "score" not in st.session_state: st.session_state.score = 0
if "quiz_complete" not in st.session_state: st.session_state.quiz_complete = False
if "answered" not in st.session_state: st.session_state.answered = False
if "snow_triggered" not in st.session_state: st.session_state.snow_triggered = False
if "last_selected_course" not in st.session_state: st.session_state.last_selected_course = selected_course
if "missed_questions_queue" not in st.session_state: st.session_state.missed_questions_queue = []

if st.session_state.last_selected_course != selected_course:
    st.session_state.quiz_set = []
    st.session_state.quiz_complete = False
    st.session_state.current_idx = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.snow_triggered = False
    st.session_state.last_selected_course = selected_course
    st.session_state.missed_questions_queue = []

# --- MAIN INTERFACE TABS ---
main_tabs = st.tabs(["📚 My Courses", "🛒 Course Manager"])

with main_tabs[1]:
    st.subheader("Enroll in New Courses")
    to_enroll = st.multiselect("Available Courses:", [c for c in course_list if c not in user_enrolled_courses])
    if st.button("Confirm Enrollment"):
        for c in to_enroll:
            enroll_course(st.session_state.user_name, c)
        st.success("Courses added! Refreshing...")
        st.rerun()

with main_tabs[0]:
    if selected_course:
        selected_module = "General Module"
        if access_mode == "Basic (Pre-built)":
            if selected_course == "Elementary Calculus":
                modules = ["Unit 1: Limits & Continuity", "Unit 2: Derivatives", "Unit 3: Integration"]
                selected_module = st.sidebar.radio("Course Curriculum:", modules)
            # (Add other course module logic here as per previous versions)

        st.title(f"Vault: {selected_course}")
        tab1, tab2, tab3 = st.tabs(["📺 Lesson Hall", "📝 Exam Hall", "🎓 Socratic Tutor"])

        with tab1:
            st.info(f"Welcome to the {selected_course} Learning Hall.")
            if "Calculus" in selected_course:
                st.video("https://youtu.be/REEAJ_T8v7U")

        with tab2:
            st.subheader("📝 Adaptive Exam Hall")
            difficulty = st.select_slider("Difficulty:", options=["Foundational", "Intermediate", "Advanced"])
            if st.button("🚀 Generate New 7-Question Set"):
                with st.spinner("Drafting..."):
                    json_prompt = f"Generate 7 MCQs for {selected_course} on {selected_module} at {difficulty} level. Return ONLY raw JSON list."
                    response = model.generate_content(json_prompt)
                    raw_text = response.text.replace("```json", "").replace("```", "").strip()
                    try:
                        st.session_state.quiz_set = json.loads(raw_text)
                        st.session_state.current_idx, st.session_state.score = 0, 0
                        st.session_state.quiz_complete, st.session_state.answered = False, False
                        st.rerun()
                    except:
                        st.error("Error generating quiz.")

            if st.session_state.quiz_set and not st.session_state.quiz_complete:
                idx = st.session_state.current_idx
                q_data = st.session_state.quiz_set[idx]
                st.markdown(f"### Question {idx + 1} of 7")
                st.info(f"**{q_data.get('question', '')}**")
                user_choice = st.radio("Select your answer:", q_data["options"], key=f"q_{idx}")
                if not st.session_state.answered and st.button("Check Answer"):
                    st.session_state.answered = True
                    st.rerun()
                if st.session_state.answered:
                    if str(user_choice).strip().lower() == str(q_data["answer"]).strip().lower():
                        st.success("✅ Correct!")
                        if f"scored_{idx}" not in st.session_state:
                            st.session_state.score += 1
                            st.session_state[f"scored_{idx}"] = True
                    else:
                        st.error(f"❌ Incorrect. Correct answer: {q_data['answer']}")
                    if st.button("Next Question ➡️"):
                        if st.session_state.current_idx < 6:
                            st.session_state.current_idx += 1
                            st.session_state.answered = False
                        else:
                            st.session_state.quiz_complete = True
                        st.rerun()

        with tab3:
            st.subheader("🎓 Socratic Tutor")
            chat_key = f"messages_{selected_course}"
            if chat_key not in st.session_state: st.session_state[chat_key] = []
            for msg in st.session_state[chat_key]:
                st.chat_message(msg["role"]).write(msg["content"])
            if prompt := st.chat_input("Ask about your course..."):
                st.session_state[chat_key].append({"role": "user", "content": prompt})
                response = model.generate_content(prompt)
                st.session_state[chat_key].append({"role": "assistant", "content": response.text})
                st.rerun()
    else:
        st.info("No courses enrolled yet. Go to 'Course Manager' to add courses.")

st.markdown("---")
st.markdown("<div style='text-align: center;'><p style='color: #666; font-size: 0.85em;'>© 2026 Radar Grad-Tutors</p></div>", unsafe_allow_html=True)
