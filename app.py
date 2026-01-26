import streamlit as st
import google.generativeai as genai
import json
import pdfplumber
import io

# 1. SETUP: API & UI Configuration
st.set_page_config(page_title="Radar Grad-Tutors", page_icon="🛰️", layout="wide")
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# --- HELPERS ---
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        text = ""
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text

# 2. SIDEBAR: Branding & Vault Controls
st.sidebar.title("🛰️ Radar Grad-Tutors")
access_mode = st.sidebar.radio(
    "Select Your Experience:", 
    ["Basic (Pre-built)", "Premium (Private Vault)"],
    help="Premium allows you to upload your own syllabus and lecture notes."
)

course_list = [
    "College Algebra", "Elementary Calculus", "Elementary Microeconomics", 
    "Elementary Macroeconomics", "Mathematics for Economists",
    "Statistics for Social Scientist", "Intermediate Microeconomics", 
    "Intermediate Macroeconomics", "Econometrics 1", "Econometrics 2"
]

selected_course = st.sidebar.selectbox("Choose a Course:", course_list)
selected_module = "General Module"
active_unit_context = "" 

# --- BASIC TIER LOGIC ---
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

# --- PREMIUM TIER LOGIC (Syllabus Sync) ---
else:
    st.sidebar.markdown("---")
    st.sidebar.subheader("💎 Premium: Syllabus Sync")
    
    with st.sidebar.expander("ℹ️ How to set up your Vault", expanded=True):
        st.write("1. Upload **Syllabus** to map the course.")
        st.write("2. Upload **Unit Notes** to start learning.")

    syllabus_file = st.sidebar.file_uploader("📂 Step 1: Upload Syllabus (The Map)", type=["pdf"])
    
    if syllabus_file:
        if "custom_units" not in st.session_state:
            with st.spinner("Mapping Curriculum..."):
                raw_syllabus = extract_text_from_pdf(syllabus_file)
                prompt = f"Identify the main units/chapters from this syllabus: {raw_syllabus[:3000]}. Return ONLY a numbered list."
                st.session_state.custom_units = model.generate_content(prompt).text
        
        st.sidebar.success("✅ Syllabus Mapped")
        st.sidebar.caption(st.session_state.custom_units)
        
        st.sidebar.markdown("---")
        unit_notes = st.sidebar.file_uploader("📄 Step 2: Upload Unit Materials", type=["pdf"])
        if unit_notes:
            active_unit_context = extract_text_from_pdf(unit_notes)
            st.sidebar.success("✅ Content Ingested")

# 3. MAIN INTERFACE
active_courses = ["Elementary Calculus", "Elementary Macroeconomics", "Intermediate Macroeconomics", "Statistics for Social Scientist", "Econometrics 2", "Elementary Microeconomics"]

if selected_course in active_courses or access_mode == "Premium (Private Vault)":
    st.title(f"{selected_course if access_mode == 'Basic (Pre-built)' else 'Custom Radar Vault'}")
    
    tab1, tab2, tab3 = st.tabs(["📺 Lesson Hall", "📝 Exam Hall", "🎓 Socratic Tutor"])

    # --- TAB 1: LESSON HALL ---
    with tab1:
        if access_mode == "Premium (Private Vault)" and active_unit_context:
            st.subheader("📚 Your Personalized Radar Digest")
            if st.button("✨ Generate Unit Digest"):
                with st.spinner("Designing your visual study guide..."):
                    digest_prompt = (
                        f"Using these notes: {active_unit_context[:5000]}, create a structured study guide. "
                        "Rules: Use H1 for main topic, H3 for sub-points. Use bold for key terms. "
                        "Add a 'Real World Application' section for this unit."
                    )
                    response = model.generate_content(digest_prompt)
                    st.markdown(response.text)
        elif access_mode == "Basic (Pre-built)":
            st.subheader(f"Lesson: {selected_module}")
            st.video("https://youtu.be/i_bn4E9EK_Q")
            st.write("Review the concepts above before heading to the Exam Hall.")
        else:
            st.info("Please upload unit notes in the sidebar to generate your visual digest.")

    # --- TAB 2: EXAM HALL ---
    with tab2:
        st.subheader("📝 Adaptive Exam Hall")
        difficulty = st.select_slider("Challenge Level:", options=["Foundational", "Intermediate", "Advanced"])

        if "quiz_set" not in st.session_state:
            st.session_state.quiz_set = []
            st.session_state.current_idx = 0
            st.session_state.score = 0
            st.session_state.quiz_complete = False
            st.session_state.answered = False 

        if st.button("🚀 Generate 7-Question Assessment"):
            with st.spinner("Drafting..."):
                source = active_unit_context if access_mode == "Premium (Private Vault)" else f"{selected_course} {selected_module}"
                json_prompt = (
                    f"Generate 7 MCQs for {selected_course} on {source} at {difficulty} level. "
                    "Output ONLY a JSON list: [{'question': '...', 'options': ['A','B','C','D'], 'answer': 'exact string', 'explanation': '...'}]"
                )
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
            
            user_choice = st.radio("Select Answer:", q_data["options"], key=f"q_{st.session_state.current_idx}", disabled=st.session_state.answered)

            if not st.session_state.answered:
                if st.button("Check Answer"):
                    st.session_state.answered = True
                    st.rerun()
            
            if st.session_state.answered:
                if str(user_choice).strip() == str(q_data["answer"]).strip():
                    st.success(f"✅ Correct! {q_data['explanation']}")
                    if f"scored_{st.session_state.current_idx}" not in st.session_state:
                        st.session_state.score += 1
                        st.session_state[f"scored_{st.session_state.current_idx}"] = True
                else:
                    st.error(f"❌ Incorrect. Correct answer: {q_data['answer']}")
                    st.session_state.failed_concept = {"question": q_data["question"], "wrong_ans": user_choice, "right_ans": q_data["answer"]}

                if st.button("Next Question ➡️"):
                    if st.session_state.current_idx < 6:
                        st.session_state.current_idx += 1
                        st.session_state.answered = False
                        st.rerun()
                    else:
                        st.session_state.quiz_complete = True
                        st.rerun()

        elif st.session_state.quiz_complete:
            st.metric("Final Score", f"{st.session_state.score}/7")
            if st.button("🔄 Restart"):
                st.session_state.quiz_set = []
                st.rerun()

    # --- TAB 3: SOCRATIC TUTOR (The Connected Mentor) ---
    with tab3:
        st.subheader("🎓 Socratic Mentor")
        
        if "failed_concept" in st.session_state:
            st.warning("⚠️ Logic Gap Detected")
            st.write(f"I see you struggled with: *{st.session_state['failed_concept']['question']}*")
            if st.button("Coach me on this"):
                gap_prompt = (
                    f"The student missed: {st.session_state.failed_concept['question']}. "
                    f"They chose {st.session_state.failed_concept['wrong_ans']}. "
                    f"Help them understand why {st.session_state.failed_concept['right_ans']} is correct by asking a guiding question."
                )
                st.session_state.messages = [{"role": "user", "content": gap_prompt}]
                del st.session_state.failed_concept
                st.rerun()

        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if user_query := st.chat_input("Ask a question about your notes..."):
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)
            context = active_unit_context if access_mode == "Premium (Private Vault)" else selected_course
            full_prompt = f"System: Socratic Tutor for {context}. Lead the student to the answer. \nStudent: {user_query}"
            response = model.generate_content(full_prompt)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.chat_message("assistant").write(response.text)

else:
    st.title(selected_course)
    st.warning("🚀 This course is launching soon!")

# --- FOOTER (The Signature) ---
st.markdown("---") 
st.markdown(
    """
    <div style="text-align: center;">
        <p style="color: #666666; font-size: 0.85em;">© 2026 Radar Grad-Tutors | Precision Learning for University Students</p>
        <p style="color: #444444; font-style: italic; font-weight: 500; font-size: 1.1em;">"Detecting Gaps, Delivering Grades"</p>
    </div>
    """, 
    unsafe_allow_html=True
    )
