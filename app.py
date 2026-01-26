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

# 2. SIDEBAR: The Tiered Menu & Branding
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
    # ... (Other courses)

# --- PREMIUM TIER LOGIC (The Private Vault) ---
else:
    st.sidebar.markdown("---")
    st.sidebar.subheader("💎 Premium: Syllabus Sync")
    
    with st.sidebar.expander("ℹ️ How to set up your Vault", expanded=True):
        st.write("1. Upload Syllabus to create your units.")
        st.write("2. Select a Unit.")
        st.write("3. Upload notes to start learning.")

    syllabus_file = st.sidebar.file_uploader("📂 Upload Course Syllabus (The Map)", type=["pdf"])
    
    if syllabus_file:
        if "custom_units" not in st.session_state:
            with st.spinner("Analyzing curriculum..."):
                raw_syllabus = extract_text_from_pdf(syllabus_file)
                prompt = f"Extract a numbered list of Units from this syllabus: {raw_syllabus[:3000]}"
                st.session_state.custom_units = model.generate_content(prompt).text
        
        st.sidebar.success("✅ Syllabus Mapped")
        st.sidebar.caption(st.session_state.custom_units)
        
        st.sidebar.markdown("---")
        unit_notes = st.sidebar.file_uploader("📄 Upload Unit Materials (The Content)", type=["pdf"])
        if unit_notes:
            active_unit_context = extract_text_from_pdf(unit_notes)
            st.sidebar.success("✅ Unit Content Ingested")

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
                with st.spinner("Designing your study guide..."):
                    digest_prompt = f"Using: {active_unit_context[:5000]}, create a study guide using H1/H3 headers, bold terms, and bullet points for maximum visual hierarchy."
                    response = model.generate_content(digest_prompt)
                    st.markdown(response.text)
        elif access_mode == "Basic (Pre-built)":
            st.video("https://youtu.be/i_bn4E9EK_Q")
            st.write(f"Focusing on: {selected_module}")
        else:
            st.info("Upload your notes in the sidebar to generate a structured Digest.")

    # --- TAB 2: EXAM HALL ---
    with tab2:
        st.subheader("📝 Adaptive Exam Hall")
        if st.button("🚀 Generate Assessment"):
            with st.spinner("Drafting questions..."):
                source = active_unit_context if access_mode == "Premium (Private Vault)" else f"{selected_course} {selected_module}"
                json_prompt = f"Generate 7 MCQs from: {source}. Return JSON."
                response = model.generate_content(json_prompt)
                st.session_state.quiz_set = json.loads(response.text.replace("```json", "").replace("```", "").strip())
                st.session_state.current_idx = 0
                st.session_state.answered = False
                st.rerun()

        if "quiz_set" in st.session_state:
            # (Insert your Quiz loop logic here, ensuring st.session_state.failed_concept is set on wrong answers)
            st.write("Quiz Logic Active.")

    # --- TAB 3: SOCRATIC TUTOR (The Logic Gap Bridge) ---
    with tab3:
        st.subheader("🎓 Socratic Mentor")
        
        if "failed_concept" in st.session_state:
            st.warning("⚠️ Logic Gap Detected")
            st.write(f"I see you struggled with: *{st.session_state['failed_concept']['question']}*")
            if st.button("Coach me on this"):
                gap_prompt = f"The student missed this question: {st.session_state.failed_concept['question']}. Help them find the logic for {st.session_state.failed_concept['right_ans']} without giving it away."
                st.session_state.messages = [{"role": "user", "content": gap_prompt}]
                del st.session_state.failed_concept
                st.rerun()

        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if user_query := st.chat_input("Ask about a concept..."):
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)
            response = model.generate_content(user_query)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.chat_message("assistant").write(response.text)

else:
    st.title(selected_course)
    st.warning("🚀 This course is launching soon!")

# --- FOOTER (Neutral Branding) ---
st.markdown("---") 
st.markdown(
    """
    <div style="text-align: center;">
        <p style="color: #666666; font-size: 0.8em;">© 2026 Radar Grad-Tutors | Precision Learning for Learners</p>
        <p style="color: #444444; font-style: italic; font-weight: 500;">"Detecting Gaps, Delivering Grades"</p>
    </div>
    """, 
    unsafe_allow_html=True
)
