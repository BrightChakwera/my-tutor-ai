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

access_mode = st.sidebar.radio("Select Your Experience:", ["Basic (Pre-built)", "Premium (Private Vault)"])

# Initial List of Pre-built Courses
course_list = [
    "College Algebra", "Elementary Calculus", "Elementary Microeconomics", 
    "Elementary Macroeconomics", "Mathematics for Economists",
    "Statistics for Social Scientist", "Intermediate Microeconomics", 
    "Intermediate Macroeconomics", "Econometrics 1", "Econometrics 2"
]

selected_course = st.sidebar.selectbox("Choose a Course:", course_list)
selected_module = None
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

# --- PREMIUM TIER LOGIC (Syllabus + Notes) ---
else:
    st.sidebar.markdown("---")
    st.sidebar.subheader("💎 Premium: Syllabus Sync")
    st.sidebar.info("Step 1: Upload your Syllabus to create your course map.")
    syllabus_file = st.sidebar.file_uploader("📂 Upload Course Syllabus", type=["pdf"])
    
    if syllabus_file:
        if "custom_units" not in st.session_state:
            with st.spinner("Scanning Syllabus..."):
                raw_syllabus = extract_text_from_pdf(syllabus_file)
                prompt = f"Identify the main units from this syllabus: {raw_syllabus[:3000]}. Return ONLY a numbered list."
                st.session_state.custom_units = model.generate_content(prompt).text
        
        st.sidebar.success("✅ Syllabus Mapped")
        st.sidebar.caption(st.session_state.custom_units)
        
        st.sidebar.markdown("---")
        st.sidebar.info("Step 2: Upload lecture notes for the unit you are studying.")
        unit_notes = st.sidebar.file_uploader("📄 Upload Unit Materials", type=["pdf"])
        if unit_notes:
            active_unit_context = extract_text_from_pdf(unit_notes)
            st.sidebar.success("✅ Unit Content Ingested")

# 3. MAIN ROUTING
active_courses = ["Elementary Calculus", "Elementary Macroeconomics", "Intermediate Macroeconomics", "Statistics for Social Scientist", "Econometrics 2", "Elementary Microeconomics"]

if selected_course in active_courses or access_mode == "Premium (Private Vault)":
    st.title(f"{selected_course if access_mode == 'Basic (Pre-built)' else 'Custom Radar Vault'}")
    
    tab1, tab2, tab3 = st.tabs(["📺 Lesson Hall", "📝 Exam Hall", "🎓 Socratic Tutor"])

    # --- TAB 1: LESSON HALL ---
    with tab1:
        if access_mode == "Basic (Pre-built)":
            st.subheader("Today's Learning Material")
            # (Insert your original video switching logic here as used before)
            st.write(f"Follow the curriculum for {selected_module} below.")
            st.video("https://youtu.be/i_bn4E9EK_Q")
        
        elif access_mode == "Premium (Private Vault)" and active_unit_context:
            st.subheader("📚 Your Personalized Radar Digest")
            if st.button("Generate Unit Digest"):
                with st.spinner("Formatting Visual Notes..."):
                    digest_prompt = f"Using these notes: {active_unit_context[:5000]}, create a structured study guide with high visual hierarchy, bold terms, and clear sections."
                    response = model.generate_content(digest_prompt)
                    st.markdown(response.text)
        else:
            st.warning("Please upload materials in the sidebar to view your Lesson Digest.")

    # --- TAB 2: EXAM HALL (The Connection Hub) ---
    with tab2:
        st.subheader("📝 Adaptive Exam Hall")
        # (Insert your initialization and MCQ logic here)
        if st.button("🚀 Generate New 7-Question Set"):
            with st.spinner("Drafting..."):
                source = active_unit_context if access_mode == "Premium (Private Vault)" else f"{selected_course} {selected_module}"
                json_prompt = f"Based on {source}, generate 7 MCQs. Output ONLY a JSON list: [{{'question': '...', 'options': ['...', '...'], 'answer': '...', 'explanation': '...'}}]"
                response = model.generate_content(json_prompt)
                st.session_state.quiz_set = json.loads(response.text.replace("```json", "").replace("```", "").strip())
                st.session_state.current_idx = 0
                st.session_state.quiz_complete = False
                st.session_state.answered = False
                st.rerun()

        # Logic for displaying questions and setting 'failed_concept' for Tab 3...
        if "quiz_set" in st.session_state and not st.session_state.quiz_complete:
            # (Standard MCQ display logic goes here)
            # IMPORTANT: When user gets it wrong:
            # st.session_state.failed_concept = {"question": q, "wrong_ans": w, "right_ans": r}
            st.write("Current Quiz Active...")

    # --- TAB 3: SOCRATIC TUTOR (Re-Connected) ---
    with tab3:
        st.subheader("🎓 Socratic Mentor")
        
        # This is the connection you noticed was missing!
        if "failed_concept" in st.session_state:
            st.warning("⚠️ Logic Gap Detected")
            st.write(f"I see you struggled with: *{st.session_state['failed_concept']['question']}*")
            if st.button("Coach me on this"):
                gap_prompt = f"The student missed this question: {st.session_state.failed_concept['question']}. They chose {st.session_state.failed_concept['wrong_ans']}. Help them find the logic for {st.session_state.failed_concept['right_ans']} without giving it away."
                st.session_state.messages = [{"role": "user", "content": gap_prompt}]
                del st.session_state.failed_concept
                st.rerun()

        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if user_query := st.chat_input():
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)
            context = active_unit_context if access_mode == "Premium (Private Vault)" else selected_course
            full_prompt = f"System: Socratic Tutor for {context}. \nStudent: {user_query}"
            response = model.generate_content(full_prompt)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.chat_message("assistant").write(response.text)

else:
    st.title(selected_course)
    st.warning("🚀 This course is launching soon!")

# --- FOOTER (Restored Branding) ---
st.markdown("---") 
st.markdown(
    """
    <div style="text-align: center;">
        <p style="color: gray;">© 2026 Radar Grad-Tutors | Precision Learning for University Students</p>
        <p style="font-weight: bold; color: #1E90FF;">"Detecting Gaps, Delivering Grades"</p>
    </div>
    """, 
    unsafe_allow_html=True
)
