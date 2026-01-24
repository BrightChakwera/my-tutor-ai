import streamlit as st
import google.generativeai as genai
import json

# 1. SETUP: API Configuration
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# Defining the model
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# 2. SIDEBAR: The Course Menu
st.sidebar.title("Radar Grad-Tutors")
course_list = [
    "College Algebra",
    "Elementary Calculus",
    "Elementary Microeconomics", 
    "Elementary Macroeconomics", 
    "Mathematics for Economists",
    "Statistics for Social Scientist",
    "Intermediate Microeconomics", 
    "Intermediate Macroeconomics", 
    "Econometrics 1", 
    "Econometrics 2"
]
selected_course = st.sidebar.selectbox("Choose a Course:", course_list)

# --- MODULE SELECTOR LOGIC ---
selected_module = None
if selected_course == "Elementary Calculus":
    modules = ["Unit 1: Limits & Continuity", "Unit 2: Derivatives", "Unit 3: Integration"]
    selected_module = st.sidebar.radio("Course Curriculum:", modules)

elif selected_course == "Elementary Macroeconomics":
    modules = ["Unit 1: GDP & Growth", "Unit 2: Inflation", "Unit 3: Fiscal Policy"]
    selected_module = st.sidebar.radio("Course Curriculum:", modules)

elif selected_course == "Elementary Microeconomics":
    modules = ["Unit 1: Supply & Demand", "Unit 2: Elasticity", "Unit 3: Market Structures"]
    selected_module = st.sidebar.radio("Course Curriculum:", modules)

# 3. ROUTING: Active vs. Upcoming Courses
active_courses = ["Elementary Calculus", "Elementary Macroeconomics", "Intermediate Macroeconomics", "Statistics for Social Scientist", "Econometrics 2", "Elementary Microeconomics"]

if selected_course in active_courses:
    st.title(f"{selected_course}")
    if selected_module:
        st.caption(f"Current Module: {selected_module}")
    
    # Create the 3 Tabs
    tab1, tab2, tab3 = st.tabs(["📺 Lesson Hall", "📝 Exam Hall", "🎓 Socratic Tutor"])

    with tab1:
        st.subheader("Today's Learning Material")
        
        # DYNAMIC CONTENT SWITCHER
        if selected_module == "Unit 1: Limits & Continuity":
            st.video("https://youtu.be/REEAJ_T8v7U") 
            st.write("Welcome to Limits. We are exploring how functions behave as they approach a specific point.")
        
        elif selected_module == "Unit 2: Derivatives":
            st.video("https://youtu.be/ANyVpMS3HL4") 
            st.write("In this unit, we master the Power Rule and the concept of instantaneous rate of change.")

        elif selected_module == "Unit 1: GDP & Growth":
            st.video("https://youtu.be/yUiU_xrpP-c") 
            st.write("Learn how nations measure wealth and the difference between Real and Nominal GDP.")

        elif selected_module == "Unit 2: Elasticity":
            st.video("https://youtu.be/HHcblIxiAAk") 
            st.write("We are analyzing how sensitive consumers are to price changes.")

        else:
            st.video("https://youtu.be/i_bn4E9EK_Q?si=576fE6mF7isaCkQT")
            st.write(f"Welcome to the module: {selected_module}. Please follow the lecture video above.")

    # --- TAB 2: THE EXAM HALL ---
    with tab2:
        st.subheader("📝 Adaptive Exam Hall")
        difficulty = st.select_slider(
            "Set Your Challenge Level:",
            options=["Foundational", "Intermediate", "Advanced"],
            key="exam_diff"
        )

        # 1. Initialize states if they don't exist
        if "quiz_set" not in st.session_state:
            st.session_state.quiz_set = []
            st.session_state.current_idx = 0
            st.session_state.score = 0
            st.session_state.quiz_complete = False
            st.session_state.answered = False 

        # 2. GENERATE / RESTART LOGIC
        if st.button("🚀 Generate New 7-Question Set") or (not st.session_state.quiz_set and not st.session_state.quiz_complete):
            with st.spinner("Drafting...will be ready in seconds"):
                json_prompt = (
                    f"Act as a professor for {selected_course}. Generate 7 MCQs on {selected_module} at {difficulty} level. "
                    "Include a 'brief_explanation' (max
