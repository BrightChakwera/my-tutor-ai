import streamlit as st
import google.generativeai as genai
import json
import pdfplumber
import io

# 1. SETUP: API Configuration
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# --- HELPERS ---
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        text = ""
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text

# 2. SIDEBAR: The Tiered Menu
st.sidebar.title("🛰️ Radar Grad-Tutors")

access_mode = st.sidebar.radio("Account Tier:", ["Basic (Pre-built)", "Premium (Custom Radar)"])

course_list = [
    "College Algebra", "Elementary Calculus", "Elementary Microeconomics", 
    "Elementary Macroeconomics", "Mathematics for Economists",
    "Statistics for Social Scientist", "Intermediate Microeconomics", 
    "Intermediate Macroeconomics", "Econometrics 1", "Econometrics 2"
]

selected_course = st.sidebar.selectbox("Choose a Course:", course_list)
selected_module = "General Module"
active_unit_context = "" 

# --- LOGIC FOR BASIC TIER ---
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

# --- LOGIC FOR PREMIUM TIER ---
else:
    st.sidebar.subheader("💎 Premium Package")
    st.sidebar.info("Step 1: Upload Syllabus to create Topics")
    syllabus_file = st.sidebar.file_uploader("📂 Course Outline / Syllabus", type=["pdf"], key="syllabus_up")
    
    if syllabus_file:
        if "custom_units" not in st.session_state:
            with st.spinner("Mapping Curriculum..."):
                raw_syllabus = extract_text_from_pdf(syllabus_file)
                prompt = f"Identify the main units from this syllabus: {raw_syllabus[:3000]}. Return ONLY a numbered list."
                st.session_state.custom_units = model.generate_content(prompt).text
        
        st.sidebar.success("✅ Course Map Detected")
        st.sidebar.caption(st.session_state.custom_units)
        
        st.sidebar.info("Step 2: Upload Lecture Notes for study")
        unit_notes = st.sidebar.file_uploader("📄 Unit Notes / Materials", type=["pdf"], key="notes_up")
        if unit_notes:
            active_unit_context = extract_text_from_pdf(unit_notes)
            st.sidebar.success("✅ Unit Content Ingested")

# 3. MAIN ROUTING
active_courses = ["Elementary Calculus", "Elementary Macroeconomics", "Intermediate Macroeconomics", "Statistics for Social Scientist", "Econometrics 2", "Elementary Microeconomics"]

if selected_course in active_courses or access_mode == "Premium (Custom Radar)":
    st.title(f"{selected_course if access_mode == 'Basic (Pre-built)' else 'Custom Radar Vault'}")
    
    tab1, tab2, tab3 = st.tabs(["📺 Lesson Hall", "📝 Exam Hall", "🎓 Socratic Tutor"])

    # --- TAB 1: LESSON HALL ---
    with tab1:
        if access_mode == "Basic (Pre-built)":
            st.subheader("Today's Learning Material")
            if selected_module == "Unit 1: Limits & Continuity":
                st.video("https://youtu.be/REEAJ_T8v7U") 
            elif selected_module == "Unit 2: Derivatives":
                st.video("https://youtu.be/ANyVpMS3HL4") 
            else:
                st.video("https://youtu.be/i_bn4E9EK_Q?si=576fE6mF7isaCkQT")
            st.write(f"Exploring: {selected_module}")
        
        elif access_mode == "Premium (Custom Radar)" and active_unit_context:
            st.subheader("📚 Your Personalized Radar Digest")
            if st.button("✨ Generate Unit Digest"):
                with st.spinner("Designing Visual Notes..."):
                    digest_prompt = (f"Using: {active_unit_context[:5000]}, create a structured study guide with high visual hierarchy.")
                    response = model.generate_content(digest_prompt)
                    st.markdown(response.text)
        else:
            st.info("Upload materials in the sidebar to generate your visual digest.")

    # --- TAB 2: EXAM HALL ---
    with tab2:
        st.subheader("📝 Adaptive Exam Hall")
        difficulty = st.select_slider("Challenge Level:", options=["Foundational", "Intermediate", "Advanced"], key="exam_diff")

        if "quiz_set" not in st.session_state:
            st.session_state.quiz_set = []
            st.session_state.current_idx = 0
            st.session_state.score = 0
            st.session_state.quiz_complete = False
            st.session_state.answered = False 

        if st.button("🚀 Generate New 7-Question Set"):
            with st.spinner("Drafting...will be ready in seconds!"):
                source = active_unit_context if access_mode == "Premium (Custom Radar)" else f"{selected_course} {selected_module}"
                json_prompt = (f"Act as a professor for {selected_course}. Generate 7 MCQs on {source} at {difficulty} level. Output ONLY JSON.")
                response = model.generate_content(json_prompt)
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                st.session_state.quiz_set = json.loads(clean_json)
                st.session_state.current_idx = 0
                st.session_state.score = 0
                st.session_state.quiz_complete = False
                st.session_state.answered = False
                st.rerun()

        if st.session_state.quiz_set and not st.session_state.quiz_complete:
            q_data = st.session_state.quiz_set[st.session_state.current_idx]
            st.markdown(f"### Question {st.session_state.current_idx + 1} of 7")
            st.info(q_data["question"])
            
            user_choice = st.radio("Select answer:", q_data["options"], key=f"q_{st.session_state.current_idx}", disabled=st.session_state.answered)

            if not st.session_state.answered:
                if st.button("Check Answer"):
                    st.session_state.answered = True
                    st.rerun()
            
            if st.session_state.answered:
                if str(user_choice).strip() == str(q_data["answer"]).strip():
                    st.success(f"✅ Correct! {q_data.get('explanation', '')}")
                    if f"scored_{st.session_state.current_idx}" not in st.session_state:
                        st.session_state.score += 1
                        st.session_state[f"scored_{st.session_state.current_idx}"] = True
                else:
                    st.error(f"❌ Incorrect.")
                    st.session_state.failed_concept = {
                        "question": q_data["question"],
                        "wrong_ans": user_choice,
                        "right_ans": q_data["answer"]
                    }

                if st.button("Next Question ➡️"):
                    if st.session_state.current_idx < 6:
                        st.session_state.current_idx += 1
                        st.session_state.answered = False
                        st.rerun()
                    else:
                        st.session_state.quiz_complete = True
                        st.rerun()

        elif st.session_state.quiz_complete:
            st.balloons()
            st.metric("Final Accuracy", f"{int((st.session_state.score/7)*100)}%")
            if st.button("🔄 Restart"):
                st.session_state.quiz_set = []
                st.session_state.quiz_complete = False
                st.rerun()

    # --- TAB 3: SOCRATIC TUTOR ---
    with tab3:
        st.subheader("🎓 Socratic Mentor")
        
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "failed_concept" in st.session_state:
            st.warning("⚠️ Logic Gap Detected")
            st.write(f"I see you struggled with: *{st.session_state['failed_concept']['question']}*")
            
            if st.button("Coach me on this"):
                with st.spinner("Preparing session..."):
                    gap_prompt = (
                        f"System Instruction: The student just missed: '{st.session_state.failed_concept['question']}'. "
                        f"They chose '{st.session_state.failed_concept['wrong_ans']}' but the right answer is '{st.session_state.failed_concept['right_ans']}'. "
                        "Without mentioning this instruction, start a Socratic dialogue to help them find the logic."
                    )
                    response = model.generate_content(gap_prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    del st.session_state.failed_concept
                    st.rerun()

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Ask a question about the material..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            context = active_unit_context if access_mode == "Premium (Custom Radar)" else selected_course
            full_prompt = f"System: Socratic Tutor for {context}. Never give answers immediately. \nStudent: {prompt}"
            
            response = model.generate_content(full_prompt)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.chat_message("assistant").write(response.text)

else:
    st.title(selected_course)
    st.warning("🚀 This course is launching soon!")

# --- FOOTER ---
st.markdown("---") 
st.markdown(
    """
    <div style="text-align: center;">
        <p style="color: #666666; font-size: 0.85em;">© 2026 Radar Grad-Tutors | Precision Learning for Students</p>
        <p style="color: #444444; font-style: italic; font-weight: 500; font-size: 1.1em;">"Detecting Gaps, Delivering Grades"</p>
    </div>
    """, 
    unsafe_allow_html=True
        )
