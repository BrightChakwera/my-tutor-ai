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
if access_mode == "Basic Package":
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

    # --- TAB 2: EXAM HALL (Adaptive Logic) ---
    with tab2:
        st.subheader("📝 Adaptive Exam Hall")
        # Ensure all your original Quiz logic (Session State, Radio Buttons, Checking) is pasted here
        # For this version, I'll keep the generator button that uses the correct context
        if st.button("🚀 Generate New 7-Question Set"):
            with st.spinner("Drafting..."):
                source = active_unit_context if access_mode == "Premium (Custom Radar)" else f"Professor logic for {selected_course} - {selected_module}"
                json_prompt = (
                    f"Based on {source}, generate 7 MCQs. Output ONLY a JSON list: "
                    "[{'question': '...', 'options': ['A','B','C','D'], 'answer': '...', 'explanation': '...'}]"
                )
                response = model.generate_content(json_prompt)
                # Parse JSON and set session state here...
                st.write("Questions ready! (Apply your existing check/next logic here)")

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
    st.title(selected_course)
    st.warning("🚀 This course is launching soon!")

# --- FOOTER ---
st.markdown("---") 
st.markdown('<div style="text-align: center;"><p style="color: gray;">© 2026 Radar Grad-Tutors</p></div>', unsafe_allow_html=True)
