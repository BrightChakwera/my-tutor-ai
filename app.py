import streamlit as st
import google.generativeai as genai
import json
import pdfplumber
import io

# 1. SETUP: API & System Prompt
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- PDF EXTRACTION HELPER ---
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

# 2. SIDEBAR: The Tiered Menu
st.sidebar.title("🛰️ Radar Grad-Tutors")

# TIER SELECTOR
access_mode = st.sidebar.radio("Account Tier:", ["Basic (Pre-built)", "Premium (Custom Radar)"])

selected_course = None
active_unit_context = ""
selected_module = "General Module" # Placeholder for logic consistency

if access_mode == "Basic (Pre-built)":
    course_list = ["Elementary Calculus", "Elementary Microeconomics", "Elementary Macroeconomics"]
    selected_course = st.sidebar.selectbox("Choose Course:", course_list)
    # Note: Insert your previous unit selection logic for basic courses here

else:
    st.sidebar.subheader("💎 Premium: Syllabus Sync")
    syllabus_file = st.sidebar.file_uploader("1. Upload Syllabus (The Map)", type=["pdf"])
    
    if syllabus_file:
        if "custom_units" not in st.session_state:
            with st.spinner("Mapping Curriculum..."):
                raw_syllabus = extract_text_from_pdf(syllabus_file)
                prompt = f"Extract a numbered list of Units/Topics from this syllabus: {raw_syllabus[:3000]}"
                st.session_state.custom_units = model.generate_content(prompt).text
        
        st.sidebar.info("Course Map Detected")
        st.sidebar.caption(st.session_state.custom_units)
        
        unit_notes = st.sidebar.file_uploader("2. Upload Unit Notes (The Content)", type=["pdf"])
        if unit_notes:
            active_unit_context = extract_text_from_pdf(unit_notes)
            st.sidebar.success("Unit Content Loaded!")

# 3. MAIN INTERFACE
st.title("Radar Learning Platform")

# Logic to handle if a course is active
active_courses = ["Elementary Calculus", "Elementary Microeconomics", "Elementary Macroeconomics"]

if access_mode == "Premium (Custom Radar)" or (selected_course in active_courses):
    tab1, tab2, tab3 = st.tabs(["📺 Lesson Hall", "📝 Exam Hall", "🎓 Socratic Tutor"])

    # --- TAB 1: LESSON HALL ---
    with tab1:
        if access_mode == "Premium (Custom Radar)" and active_unit_context:
            st.subheader("📚 Your Personalized Radar Digest")
            if st.button("Generate Unit Digest"):
                with st.spinner("Designing Visual Notes..."):
                    digest_prompt = (
                        f"Using these notes: {active_unit_context[:5000]}, create a study guide. "
                        "Use H1 for titles, H3 for sub-topics, bold for terms, and > for definitions. "
                        "Format as a 'Mastery Document' with high visual hierarchy."
                    )
                    response = model.generate_content(digest_prompt)
                    st.markdown(response.text)
        else:
            st.info("Please upload unit notes in Premium mode or select a Basic course to see content.")

    # --- TAB 2: EXAM HALL ---
    with tab2:
        st.subheader("📝 Adaptive Exam Hall")
        if st.button("🚀 Generate 7-Question Assessment"):
            with st.spinner("Analyzing context..."):
                source = active_unit_context if active_unit_context else "General knowledge of " + str(selected_course)
                
                prompt = (
                    f"Based on: {source[:4000]}, generate 7 MCQs. "
                    "Ensure the 'answer' matches an option exactly. Output ONLY JSON."
                )
                response = model.generate_content(prompt)
                st.write("Questions generated! (Insert quiz logic here)")

    # --- TAB 3: SOCRATIC TUTOR ---
    with tab3:
        st.subheader("🎓 Socratic Mentor")
        
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "failed_concept" in st.session_state:
            st.warning("⚠️ Logic Gap Detected")
            st.write(f"I see you struggled with: *{st.session_state['failed_concept']['question']}*")
            if st.button("Coach me on this"):
                context_prompt = (
                    f"The student just missed a quiz question. They thought the answer was "
                    f"'{st.session_state.failed_concept['wrong_ans']}' but it was actually "
                    f"'{st.session_state.failed_concept['right_ans']}'. Don't give the answer, "
                    "ask a guiding question to help them realize why the correct answer makes sense."
                )
                st.session_state.messages.append({"role": "user", "content": context_prompt})
                del st.session_state.failed_concept
                st.rerun()

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Ask your tutor a question..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            full_prompt = (
                f"System: You are a Socratic University Tutor. "
                "Never give answers immediately. Always ask a helpful guiding question first."
                f"\nStudent: {prompt}"
            )
            
            response = model.generate_content(full_prompt)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.chat_message("assistant").write(response.text)

else:
    st.subheader(selected_course)
    st.warning("🚀 This course is launching soon!")
    st.write("Check back next week!")

# --- FOOTER ---
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
