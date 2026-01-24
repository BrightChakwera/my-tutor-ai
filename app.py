import streamlit as st
import google.generativeai as genai

# 1. SETUP: API Configuration
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

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

# --- NEW: MODULE SELECTOR LOGIC ---
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
# ----------------------------------

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
            st.video("https://youtu.be/REEAJ_T8v7U") # Example Limits Video
            st.write("Welcome to Limits. We are exploring how functions behave as they approach a specific point.")
        
        elif selected_module == "Unit 2: Derivatives":
            st.video("https://youtu.be/ANyVpMS3HL4") # Example Derivatives Video
            st.write("In this unit, we master the Power Rule and the concept of instantaneous rate of change.")

        elif selected_module == "Unit 1: GDP & Growth":
            st.video("https://youtu.be/yUiU_xrpP-c") # Example GDP Video
            st.write("Learn how nations measure wealth and the difference between Real and Nominal GDP.")

        elif selected_module == "Unit 2: Elasticity":
            st.video("https://youtu.be/HHcblIxiAAk") # Example Elasticity Video
            st.write("We are analyzing how sensitive consumers are to price changes.")

        else:
            # Default video if module isn't specifically mapped yet
            st.video("https://youtu.be/i_bn4E9EK_Q?si=576fE6mF7isaCkQT")
            st.write(f"Welcome to the module: {selected_module}. Please follow the lecture video above.")

    with tab2:
        # --- 1. LOCAL SIDEBAR ELEMENTS ---
        # This slider only appears when the user has clicked on the Exam Hall tab
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 Exam Settings")
        difficulty = st.sidebar.select_slider(
            "Set Challenge Level:",
            options=["Foundational", "Intermediate", "Advanced"],
            help="Foundational = Concepts | Intermediate = Application | Advanced = Complex Analysis"
        )

        st.subheader("📝 Adaptive Exam Hall")
        st.write(f"Current Level: **{difficulty}**")

        # --- 2. INITIALIZE QUIZ STATE ---
        if "quiz_questions" not in st.session_state:
            st.session_state.quiz_questions = []
            st.session_state.current_idx = 0
            st.session_state.score = 0
            st.session_state.quiz_complete = False

        # --- 3. GENERATION LOGIC ---
        if st.button("🚀 Generate New 7-Question Set"):
            with st.spinner(f"Radar is scanning {selected_module} to craft {difficulty} questions..."):
                # The Prompt now includes the difficulty from the slider
                quiz_prompt = (
                    f"Generate a set of 7 unique Multiple Choice Questions for {selected_course}: {selected_module}. "
                    f"Difficulty Level: {difficulty}. "
                    "Return ONLY the questions and options. "
                    "Format: Question | A) .. | B) .. | C) .. | D) .. | Correct: [Letter]"
                )
                
                # Call Gemini
                response = model.generate_content(quiz_prompt)
                
                # Split the AI response into a list of 7 items
                # We assume the AI separates questions with double newlines
                raw_questions = response.text.strip().split("\n\n")
                
                # Store in session state
                st.session_state.quiz_questions = raw_questions[:7] # Ensure exactly 7
                st.session_state.current_idx = 0
                st.session_state.score = 0
                st.session_state.quiz_complete = False
                st.rerun()

        # --- 4. DISPLAY & NAVIGATION ---
        if st.session_state.quiz_questions and not st.session_state.quiz_complete:
            idx = st.session_state.current_idx
            st.markdown(f"### Question {idx + 1} of 7")
            
            # Show the current question
            st.info(st.session_state.quiz_questions[idx])
            
            # Answer Input
            user_ans = st.text_input("Enter A, B, C, or D:", key=f"input_{idx}").upper()

            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Submit Answer"):
                    # For now, we move forward. 
                    # Tomorrow we add the logic to 'parse' the AI's correct answer and score it.
                    if st.session_state.current_idx < 6:
                        st.session_state.current_idx += 1
                        st.rerun()
                    else:
                        st.session_state.quiz_complete = True
                        st.rerun()
            with col2:
                st.caption("Submit to proceed to the next question.")

        # --- 5. FINAL RESULTS ---
        elif st.session_state.quiz_complete:
            st.success("🏁 Exam Completed!")
            st.metric("Total Score", f"{st.session_state.score}/7")
            if st.button("Clear Results & Restart"):
                del st.session_state.quiz_questions
                st.session_state.quiz_complete = False
                st.rerun()
    with tab3:
        # 2. Page UI
        st.header("Socratic Assistant")
        st.caption(f"I am your {selected_course} expert. I’ll guide you with questions to help you master {selected_module or 'the material'}.")

        # 3. Chat Logic
        model = genai.GenerativeModel('gemini-1.5-flash') # Updated to a stable model version

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input():
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            # Socratic Prompting with Course Context
            full_prompt = (
                f"System: You are a Socratic University Tutor for the course {selected_course}, specifically teaching {selected_module}. "
                "Never give answers immediately. Always ask a helpful guiding question first. \n"
                f"Student: {prompt}"
            )
            
            response = model.generate_content(full_prompt)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.chat_message("assistant").write(response.text)

else:
    # Landing page for courses not yet built
    st.title(selected_course)
    st.warning("🚀 This course is launching soon!")
    st.write("We are currently organizing the curriculum for this subject. Check back next week!")

# --- FOOTER SECTION ---
st.markdown("---") 
st.markdown(
    """
    <div style="text-align: center;">
        <p style="color: gray;">© 2026 Radar Grad-Tutors | Precision Learning for University Students</p>
        <p> <i>"Detecting Gaps, Delivering Grades"</i></p>
    </div>
    """, 
    unsafe_allow_html=True

)
