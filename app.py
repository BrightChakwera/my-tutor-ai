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

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    # Enrollments table: Links users to courses
    c.execute('''CREATE TABLE IF NOT EXISTS enrollments 
                 (username TEXT, course_name TEXT, 
                  PRIMARY KEY (username, course_name))''')
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def add_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password) VALUES (?,?)', (username, make_hashes(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError: return False
    finally: conn.close()

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username =?', (username,))
    data = c.fetchone()
    conn.close()
    if data and data[0] == make_hashes(password): return True
    return False

# --- ENROLLMENT LOGIC ---
def enroll_user_in_course(username, course_name):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO enrollments(username, course_name) VALUES (?,?)', (username, course_name))
        conn.commit()
        return True
    except sqlite3.IntegrityError: return False
    finally: conn.close()

def get_user_courses(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT course_name FROM enrollments WHERE username = ?', (username,))
    data = c.fetchall()
    conn.close()
    return [item[0] for item in data]

init_db()

# --- AUTHENTICATION SYSTEM ---
def auth_page():
    st.title("🔐 Radar Grad-Tutors")
    auth_mode = st.tabs(["Login", "Register"])
    
    with auth_mode[0]:
        st.subheader("Welcome Back")
        user = st.text_input("Username", key="login_user")
        pw = st.text_input("Password", type="password", key="login_pw")
        if st.button("Login"):
            if login_user(user, pw):
                st.session_state.logged_in = True
                st.session_state.user_name = user
                st.rerun()
            else: st.error("Invalid Username or Password")

    with auth_mode[1]:
        st.subheader("Create New Account")
        new_user = st.text_input("Choose Username")
        new_pw = st.text_input("Choose Password", type="password")
        if st.button("Register"):
            if add_user(new_user, new_pw):
                st.success("Account created! Please log in.")
            else: st.error("Username already exists")

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    auth_page()
    st.stop()

# --- APP MASTER DATA ---
all_available_courses = [
    "College Algebra", "Elementary Calculus", "Elementary Microeconomics", 
    "Elementary Macroeconomics", "Mathematics for Economists",
    "Statistics for Social Scientist", "Intermediate Microeconomics", 
    "Intermediate Macroeconomics", "Econometrics 1", "Econometrics 2"
]

# --- SIDEBAR & COURSE FILTERING ---
st.sidebar.title("Radar Grad-Tutors")
st.sidebar.write(f"User: **{st.session_state.user_name}**")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# Get only courses this specific user has enrolled in
user_enrolled_courses = get_user_courses(st.session_state.user_name)

if not user_enrolled_courses:
    st.warning("You are not enrolled in any courses yet. Go to the 'Enrollment' tab to add one.")
    selected_course = None
else:
    selected_course = st.sidebar.selectbox("Your Active Courses:", user_enrolled_courses)

access_mode = st.sidebar.radio("Account Tier:", ["Basic (Pre-built)", "Premium (Custom Radar)"])

# --- SESSION STATE MANAGEMENT ---
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

# --- MAIN INTERFACE ---
tab_lesson, tab_exam, tab_socratic, tab_enroll = st.tabs(["📺 Lesson Hall", "📝 Exam Hall", "🎓 Socratic Tutor", "💳 Enrollment"])

with tab_enroll:
    st.subheader("Manage Your Subscriptions")
    st.info("Select a course to add to your personal learning hall.")
    course_to_add = st.selectbox("Select Course to Enroll:", [c for c in all_available_courses if c not in user_enrolled_courses])
    if st.button("✅ Confirm Enrollment"):
        if enroll_user_in_course(st.session_state.user_name, course_to_add):
            st.success(f"Successfully enrolled in {course_to_add}!")
            st.rerun()
        else:
            st.error("Enrollment failed.")

# --- COURSE CONTENT LOGIC (Only runs if a course is selected) ---
if selected_course:
    # Logic for Units
    selected_module = "General Module"
    if access_mode == "Basic (Pre-built)":
        if selected_course == "Elementary Calculus":
            modules = ["Unit 1: Limits & Continuity", "Unit 2: Derivatives", "Unit 3: Integration"]
            selected_module = st.sidebar.radio("Course Curriculum:", modules)
        # ... (Additional module logic for other courses can go here)

    with tab_lesson:
        st.title(f"Lesson: {selected_course}")
        st.video("https://youtu.be/REEAJ_T8v7U" if "Calculus" in selected_course else "https://youtu.be/i_bn4E9EK_Q")

    with tab_exam:
        st.subheader(f"Exam Hall: {selected_course}")
        difficulty = st.select_slider("Difficulty:", options=["Foundational", "Intermediate", "Advanced"])
        if st.button("🚀 Generate New 7-Question Set"):
            with st.spinner("Drafting..."):
                json_prompt = f"Generate 7 MCQs for {selected_course} on {selected_module} at {difficulty} level. Return ONLY raw JSON list. Keys: 'question', 'options', 'answer', 'explanation'."
                response = model.generate_content(json_prompt)
                raw_text = response.text.replace("```json", "").replace("```", "").strip()
                try:
                    st.session_state.quiz_set = json.loads(raw_text)
                    st.session_state.current_idx, st.session_state.score = 0, 0
                    st.session_state.quiz_complete, st.session_state.answered, st.session_state.snow_triggered = False, False, False
                    st.rerun()
                except: st.error("AI Formatting error. Try again.")

        if st.session_state.quiz_set and not st.session_state.quiz_complete:
            idx = st.session_state.current_idx
            q_data = st.session_state.quiz_set[idx]
            st.info(f"**Q{idx+1}: {q_data.get('question', '')}**")
            user_choice = st.radio("Answer:", q_data["options"], key=f"q_{idx}")
            if not st.session_state.answered and st.button("Check Answer"):
                st.session_state.answered = True
                st.rerun()
            if st.session_state.answered:
                if str(user_choice).lower() == str(q_data["answer"]).lower():
                    st.success("Correct!")
                    if f"sc_{idx}" not in st.session_state:
                        st.session_state.score += 1
                        st.session_state[f"sc_{idx}"] = True
                else:
                    st.error(f"Incorrect. Answer: {q_data['answer']}")
                    st.session_state.missed_questions_queue.append({"question": q_data["question"]})
                if st.button("Next ➡️"):
                    if st.session_state.current_idx < 6: st.session_state.current_idx += 1
                    else: st.session_state.quiz_complete = True
                    st.session_state.answered = False
                    st.rerun()

    with tab_socratic:
        st.subheader("Socratic Mentor")
        chat_key = f"msgs_{selected_course}"
        if chat_key not in st.session_state: st.session_state[chat_key] = []
        for msg in st.session_state[chat_key]: st.chat_message(msg["role"]).write(msg["content"])
        if prompt := st.chat_input("Ask about your course..."):
            st.session_state[chat_key].append({"role": "user", "content": prompt})
            resp = model.generate_content(prompt).text
            st.session_state[chat_key].append({"role": "assistant", "content": resp})
            st.rerun()

st.markdown("---") 
st.markdown("<div style='text-align: center;'><p style='color: #666; font-size: 0.85em;'>© 2026 Radar Grad-Tutors</p></div>", unsafe_allow_html=True)
