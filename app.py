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
        difficulty = st.select_slider("Challenge Level:", options=["Foundational", "Intermediate", "Advanced"], key="exam
