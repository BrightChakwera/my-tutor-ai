import streamlit as st
import google.generativeai as genai
import json
import pdfplumber
import io

# 1. SETUP: API Configuration
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- HELPERS ---
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

# 2. SIDEBAR: The Tiered Menu
st.sidebar.title("🛰️ Radar Grad-Tutors")

access_mode = st.sidebar.radio("Account Tier:", ["Basic (Pre-built)", "Premium (Custom Radar)"])

# Initial List of Pre-built Courses
course_list = [
    "College Algebra", "Elementary Calculus", "Elementary Microeconomics", 
    "Elementary Macroeconomics", "Mathematics for Economists",
    "Statistics for Social Scientist", "Intermediate Microeconomics", 
    "Intermediate Macroeconomics", "Econometrics 1", "Econometrics 2"
]

selected_course = st.sidebar.selectbox("Choose a Course:", course_list)
selected_module = None
active_unit_context = "" # Context for AI

# --- LOGIC FOR BASIC TIER (PRE-BUILT) ---
# Fixed: Matches the radio button label exactly
if access_mode == "Basic (Pre-built)":
    if selected_course == "Elementary Calculus":
        modules = ["Unit 1: Limits & Continuity", "Unit 2: Derivatives", "Unit 3: Integration"]
        selected_module = st.sidebar.radio("Course Curriculum:", modules)
    elif selected_course == "Elementary Macroeconomics":
        modules = ["Unit 1: GDP & Growth", "Unit 2: Inflation", "Unit 3: Fiscal Policy"]
        selected_module = st.sidebar.radio("Course Curriculum:", modules)
    elif selected_course == "Elementary Microeconomics":
        modules = ["Unit 1: Supply & Demand", "Unit 2: Elasticity", "Unit 3: Market Structures"]
        selected_module = st.sidebar.radio("Course Curriculum:", modules)

# --- LOGIC FOR PREMIUM TIER (CUSTOM) ---
else:
    st.sidebar.subheader("💎 Premium Package")
    syllabus_file = st.sidebar.file_uploader("1. Upload Syllabus (The Map)", type=["pdf"])
    
    if syllabus_file:
        if "custom_units" not in st.session_state:
            with st.spinner("Mapping Curriculum..."):
                raw_syllabus = extract_text_from_pdf(syllabus_file)
                prompt = f"Identify the main units from this syllabus: {raw_syllabus[:3000]}. Return ONLY a numbered list."
                st.session_state.custom_units = model.generate_content(prompt).text
        
        st.sidebar.info("Course Map Detected")
        st.sidebar.caption(st.session_state.custom_units)
        
        unit_notes = st.sidebar.file_uploader("2. Upload Unit Notes (The Content)", type=["pdf"])
        if unit_notes:
            active_unit_context = extract_text_from_pdf(unit_notes)
            st.sidebar.success("Unit Content Loaded!")

# 3. MAIN ROUTING
active_courses = ["Elementary Calculus", "Elementary Macroeconomics", "Intermediate Macroeconomics", "Statistics for Social Scientist", "Econometrics 2", "Elementary Microeconomics"]

if selected_course in active_courses or access_mode == "Premium (Custom Radar)":
    st.title(f"{selected_course if access_mode == 'Basic (Pre-built)' else 'Custom Radar'}")
    
    tab1, tab2, tab3 = st.tabs(["📺 Lesson Hall", "📝 Exam Hall", "🎓 Socratic Tutor"])

    # --- TAB 1: LESSON HALL ---
    with tab1:
        if access_mode == "Basic (Pre-built)":
            st.subheader("Today's Learning Material")
            if selected_module == "Unit 1: Limits & Continuity":
                st.video("https://youtu.be/REEAJ_T8v7U") 
                st.write("Welcome to Limits. We are exploring how functions behave.")
            elif selected_module == "Unit 2: Derivatives":
                st.video("https://youtu.be/ANyVpMS3HL4") 
                st.write("Mastering the Power Rule.")
            elif selected_module == "Unit 1: GDP & Growth":
                st.video("https://youtu.be/yUiU_xrpP-c") 
            elif selected_module == "Unit 2: Elasticity":
                st.video("https://youtu.be/HHcblIxiAAk")
            else:
                st.video("https://youtu.be/i_bn4E9EK_Q?si=576fE6mF7isaCkQT")
                st.write(f"Welcome to: {selected_module}")
        
        elif access_mode == "Premium (Custom Radar)" and active_unit_context:
            st.subheader("📚 Your Personalized Radar Digest")
            if st.button("Generate Unit Digest"):
                with st.spinner("Designing Visual Notes..."):
                    digest_prompt = f"Using these notes: {active_unit_context[:5000]}, create a structured study guide with high visual hierarchy."
                    response = model.generate_content(digest_prompt)
                    st.markdown(response.text)

    # --- TAB 2: EXAM HALL ---
    with tab2:
        st.subheader("📝 Adaptive Exam Hall")
        difficulty = st.select_slider(
            "Set Your Challenge Level:",
            options=["Foundational", "Intermediate", "Advanced"],
            key="exam_diff"
        )

        # 1. Initialize states
        if "quiz_set" not in st.session_state:
            st.session_state.quiz_set = []
            st.session_state.current_idx = 0
            st.session_state.score = 0
            st.session_state.quiz_complete = False
            st.session_state.answered = False 

        # 2. GENERATE / RESTART LOGIC
        if st.button("🚀 Generate New 7-Question Set"):
            with st.spinner("Drafting...will be ready in seconds"):
                # Use uploaded context if in Premium mode, else use course name
                context_source = active_unit_context if access_mode == "Premium (Custom Radar)" else f"{selected_course} - {selected_module}"
                
                json_prompt = (
                    f"Act as a professor for {selected_course}. Generate 7 MCQs on {context_source} at {difficulty} level. "
                    "The 'answer' key must contain the EXACT string from the 'options' list. Do not add 'A)' or 'B)' to the answer if it is not in the options. "
                    "Include a 'brief_explanation' (max 15 words) for the correct answer. "
                    "Output ONLY a JSON list of 7 objects: [{'question': '...', 'options': ['...', '...', '...', '...'], 'answer': '...', 'explanation': '...'}]"
                )
                response = model.generate_content(json_prompt)
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                
                st.session_state.quiz_set = json.loads(clean_json)
                st.session_state.current_idx = 0
                st.session_state.score = 0
                st.session_state.quiz_complete = False
                st.session_state.answered = False
                st.rerun()

        if not st.session_state.quiz_set and not st.session_state.quiz_complete:
            st.write("---")
            st.info("The Exam Hall is currently quiet. Adjust your difficulty above and tap the button to begin.")

        # 3. QUIZ INTERFACE
        if st.session_state.quiz_set and not st.session_state.quiz_complete:
            q_data = st.session_state.quiz_set[st.session_state.current_idx]
            st.markdown(f"### Question {st.session_state.current_idx + 1} of 7")
            st.info(q_data["question"])
            
            user_choice = st.radio(
                "Select your answer:", 
                q_data["options"], 
                key=f"q_{st.session_state.current_idx}",
                disabled=st.session_state.answered
            )

            if not st.session_state.answered:
                if st.button("Check Answer"):
                    st.session_state.answered = True
                    st.rerun()
            
            # --- COLOR FEEDBACK SECTION & COMPARISON ---
            if st.session_state.answered:
                selected = str(user_choice).strip()
                correct = str(q_data["answer"]).strip()

                if selected == correct:
                    st.success(f"✅ **Correct!** {q_data.get('explanation', '')}")
                    if f"scored_{st.session_state.current_idx}" not in st.session_state:
                        st.session_state.score += 1
                        st.session_state[f"scored_{st.session_state.current_idx}"] = True
                else:
                    st.error(f"❌ **Incorrect.** You chose: {selected}")
                    st.success(f"💡 **The right answer was: {correct}** \n\n {q_data.get('explanation', '')}")
                    
                    st.session_state.failed_concept = {
                        "question": q_data["question"],
                        "wrong_ans": selected,
                        "right_ans": correct
                    }

                # Navigation button
                if st.button("Next Question ➡️"):
                    if st.session_state.current_idx < 6:
                        st.session_state.current_idx += 1
                        st.session_state.answered = False
                        st.rerun()
                    else:
                        st.session_state.quiz_complete = True
                        st.rerun()

        # 4. FINAL RESULTS
        elif st.session_state.quiz_complete:
            percent = (st.session_state.score / 7) * 100
            if percent == 100:
                st.balloons()
                st.success("🏆 **PERFECT SCORE!** You have total mastery of this unit.")
            elif percent >= 70:
                st.snow()
                st.info("📈 **GREAT JOB!** You've passed the Radar assessment.")
            else:
                st.warning("⚠️ **ROOM FOR GROWTH:** Use the Socratic Tutor to bridge your gaps.")

            col1, col2, col3 = st.columns(3)
            col1.metric("Correct", f"{st.session_state.score}")
            col2.metric("Accuracy", f"{int(percent)}%")
            col3.metric("Level", difficulty)

            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔄 Restart with New Questions"):
                    for key in list(st.session_state.keys()):
                        if key.startswith("q_") or key.startswith("scored_"):
                            del st.session_state[key]
                    st.session_state.quiz_set = []
                    st.session_state.quiz_complete = False
                    st.rerun()
            with c2:
                st.write("Need help? Head to the **Socratic Tutor** tab!")

    # --- TAB 3: SOCRATIC TUTOR ---
    with tab3:
        st.subheader("🎓 Socratic Assistant")
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input():
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            # Context-aware system prompt
            context = active_unit_context if access_mode == "Premium (Custom Radar)" else selected_course
            full_prompt = f"System: You are a Socratic Tutor for {context}. Lead the student to the answer. \nStudent: {prompt}"
            
            response = model.generate_content(full_prompt)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.chat_message("assistant").write(response.text)

else:
    # Fixed: Corrected broken st.title syntax
    st.title(selected_course)
    st.warning("🚀 This course is launching soon!")

# --- FOOTER ---
st.markdown("---") 
st.markdown('<div style="text-align: center;"><p style="color: gray;">© 2026 Radar Grad-Tutors</p></div>', unsafe_allow_html=True)
