import streamlit as st
import google.generativeai as genai
import json

# 1. SETUP: API Configuration
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# Defining the model
model = genai.GenerativeModel('gemini-2.0-flash-latest')

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

        if "quiz_set" not in st.session_state:
            st.session_state.quiz_set = []
            st.session_state.current_idx = 0
            st.session_state.quiz_complete = False

        if st.button("🚀 Generate 7-Question Set"):
            with st.spinner("Professor AI is drafting your exam..."):
                json_prompt = (
                    f"Act as a university professor for {selected_course}. "
                    f"Generate 7 MCQs on {selected_module} at {difficulty} level. "
                    "Output ONLY a JSON list of objects with these keys: "
                    "'question', 'options' (a list of 4), and 'answer' (the exact string from options)."
                )
                response = model.generate_content(json_prompt)
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                st.session_state.quiz_set = json.loads(clean_json)
                st.session_state.current_idx = 0
                st.session_state.quiz_complete = False
                st.rerun()

        if st.session_state.quiz_set and not st.session_state.quiz_complete:
            q_data = st.session_state.quiz_set[st.session_state.current_idx]
            st.markdown(f"### Question {st.session_state.current_idx + 1} of 7")
            st.info(q_data["question"])
            
            user_choice = st.radio("Choose the best answer:", q_data["options"], key=f"q_{st.session_state.current_idx}")

            if st.button("Submit Answer"):
                if user_choice == q_data["answer"]:
                    st.success("Correct!")
                else:
                    st.error(f"Incorrect. The target was: {q_data['answer']}")
                    st.session_state.failed_concept = {
                        "question": q_data["question"],
                        "wrong_ans": user_choice,
                        "right_ans": q_data["answer"]
                    }
                
                if st.session_state.current_idx < 6:
                    st.session_state.current_idx += 1
                    st.rerun()
                else:
                    st.session_state.quiz_complete = True
                    st.rerun()

        elif st.session_state.quiz_complete:
            st.success("🏁 Exam Complete!")
            if st.button("Restart Quiz"):
                st.session_state.quiz_set = []
                st.session_state.quiz_complete = False
                st.rerun()

    # --- TAB 3: THE SOCRATIC TUTOR ---
    with tab3:
        st.subheader("🎓 Socratic Assistant")
        
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "failed_concept" in st.session_state:
            st.warning("⚠️ Logic Gap Detected")
            st.write(f"I see you struggled with: *{st.session_state['failed_concept']['question']}*")
            if st.button("Coach me on this"):
                context_prompt = f"The student just missed a quiz question. They thought the answer was {st.session_state.failed_concept['wrong_ans']} but it was {st.session_state.failed_concept['right_ans']}. Don't give the answer, ask a guiding question to fix their logic."
                st.session_state.messages.append({"role": "user", "content": context_prompt})
                del st.session_state.failed_concept
                st.rerun()

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input():
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            full_prompt = (
                f"System: You are a Socratic University Tutor for the course {selected_course}, specifically teaching {selected_module}. "
                "Never give answers immediately. Always ask a helpful guiding question first. \n"
                f"Student: {prompt}"
            )
            
            response = model.generate_content(full_prompt)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.chat_message("assistant").write(response.text)

else:
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


