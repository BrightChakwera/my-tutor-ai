import streamlit as st
import google.generativeai as genai
import json
import pdfplumber
import io
from fpdf import FPDF 

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

def create_pdf_report(course, score, difficulty, percent):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Radar Grad-Tutors: Performance Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Course: {course}", ln=True)
    pdf.cell(200, 10, f"Difficulty Level: {difficulty}", ln=True)
    pdf.cell(200, 10, f"Score: {score} out of 7", ln=True)
    pdf.cell(200, 10, f"Accuracy: {percent}%", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, "Detecting Gaps, Delivering Grades.", ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1')

# 2. SIDEBAR
st.sidebar.title("🛰️ Radar Grad-Tutors")
access_mode = st.sidebar.radio("Account Tier:", ["Basic (Pre-built)", "Premium (Custom Radar)"])

course_list = [
    "College Algebra", "Elementary Calculus", "Elementary Microeconomics", 
    "Elementary Macroeconomics", "Mathematics for Economists",
    "Statistics for Social Scientist", "Intermediate Microeconomics", 
    "Intermediate Macroeconomics", "Econometrics 1", "Econometrics 2"
]
selected_course = st.sidebar.selectbox("Choose a Course:", course_list)

# --- SESSION STATE ---
if "quiz_set" not in st.session_state: st.session_state.quiz_set = []
if "current_idx" not in st.session_state: st.session_state.current_idx = 0
if "score" not in st.session_state: st.session_state.score = 0
if "quiz_complete" not in st.session_state: st.session_state.quiz_complete = False
if "answered" not in st.session_state: st.session_state.answered = False
if "snow_triggered" not in st.session_state: st.session_state.snow_triggered = False
if "last_selected_course" not in st.session_state: st.session_state.last_selected_course = selected_course

if st.session_state.last_selected_course != selected_course:
    st.session_state.quiz_set = []
    st.session_state.quiz_complete = False
    st.session_state.current_idx = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.snow_triggered = False
    st.session_state.last_selected_course = selected_course

selected_module = "General Module"
active_unit_context = "" 

if access_mode == "Basic (Pre-built)":
    if selected_course == "Elementary Calculus":
        modules = ["Unit 1: Limits & Continuity", "Unit 2: Derivatives", "Unit 3: Integration"]
        selected_module = st.sidebar.radio("Course Curriculum:", modules)
    elif selected_course == "Elementary Macroeconomics":
        modules = ["Unit 1: GDP & Growth", "Unit 2: Inflation", "Unit 3: Fiscal Policy"]
        selected_module = st.sidebar.radio("Course Curriculum:", modules)
    elif selected_course == "Intermediate Macroeconomics":
        modules = ["Unit 1: IS-LM Models", "Unit 2: Aggregate Supply", "Unit 3: Open Economy Macro"]
        selected_module = st.sidebar.radio("Course Curriculum:", modules)
    elif selected_course == "Statistics for Social Scientist":
        modules = ["Unit 1: Probability", "Unit 2: Distributions", "Unit 3: Hypothesis Testing"]
        selected_module = st.sidebar.radio("Course Curriculum:", modules)
    elif selected_course == "Econometrics 2":
        modules = ["Unit 1: Time Series", "Unit 2: Panel Data", "Unit 3: Limited Dependent Variables"]
        selected_module = st.sidebar.radio("Course Curriculum:", modules)
else:
    st.sidebar.subheader("💎 Premium Package")
    syllabus_file = st.sidebar.file_uploader("📂 Course Outline", type=["pdf"], key="syllabus_up")
    if syllabus_file:
        if "custom_units" not in st.session_state:
            with st.spinner("Mapping..."):
                raw_syllabus = extract_text_from_pdf(syllabus_file)
                prompt = f"Identify main units from: {raw_syllabus[:3000]}. Return ONLY a list."
                st.session_state.custom_units = model.generate_content(prompt).text
        st.sidebar.caption(st.session_state.custom_units)
        unit_notes = st.sidebar.file_uploader("📄 Unit Notes", type=["pdf"], key="notes_up")
        if unit_notes: active_unit_context = extract_text_from_pdf(unit_notes)

# 3. MAIN ROUTING
active_courses = ["Elementary Calculus", "Elementary Macroeconomics", "Intermediate Macroeconomics", "Statistics for Social Scientist", "Econometrics 2"]

if selected_course in active_courses or access_mode == "Premium (Custom Radar)":
    st.title(f"{selected_course if access_mode == 'Basic (Pre-built)' else 'Custom Radar Vault'}")
    tab1, tab2, tab3 = st.tabs(["📺 Lesson Hall", "📝 Exam Hall", "🎓 Socratic Tutor"])

    with tab1:
        if access_mode == "Basic (Pre-built)":
            st.video("https://youtu.be/REEAJ_T8v7U" if "Calculus" in selected_course else "https://youtu.be/i_bn4E9EK_Q")
        elif active_unit_context and st.button("✨ Generate Unit Digest"):
            st.markdown(model.generate_content(f"Create a study guide for: {active_unit_context[:5000]}").text)

    with tab2:
        st.subheader("📝 Adaptive Exam Hall")
        difficulty = st.select_slider("Difficulty:", options=["Foundational", "Intermediate", "Advanced"])

        if st.button("🚀 Generate New 7-Question Set"):
            with st.spinner("Drafting...will be ready in seconds!"):
                # IMPROVED PROMPT: Strict instruction on 'answer' format
                json_prompt = f"""Generate 7 MCQs for {selected_course} on {selected_module} at {difficulty} level. 
                Return ONLY a JSON list of objects with keys: "question", "options" (list of strings), "answer" (the exact string from options), and "explanation". 
                IMPORTANT: The 'answer' field MUST match one of the strings in the 'options' list exactly."""
                
                response = model.generate_content(json_prompt)
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                st.session_state.quiz_set = json.loads(clean_json)
                st.session_state.current_idx, st.session_state.score = 0, 0
                st.session_state.quiz_complete, st.session_state.answered, st.session_state.snow_triggered = False, False, False
                st.rerun()

        if st.session_state.quiz_set and not st.session_state.quiz_complete:
            idx = st.session_state.current_idx
            q_data = st.session_state.quiz_set[idx]
            st.markdown(f"### Question {idx + 1} of 7")
            st.info(q_data["question"])
            
            user_choice = st.radio("Select answer:", q_data["options"], key=f"q_{idx}", disabled=st.session_state.answered)

            if not st.session_state.answered and st.button("Check Answer"):
                st.session_state.answered = True
                st.rerun()
            
            if st.session_state.answered:
                # IMPROVED COMPARISON: Stripping and Lowering to avoid mismatch
                is_correct = str(user_choice).strip().lower() == str(q_data["answer"]).strip().lower()
                
                if is_correct:
                    st.success(f"✅ Correct! {q_data.get('explanation', '')}")
                    if f"scored_{idx}" not in st.session_state:
                        st.session_state.score += 1
                        st.session_state[f"scored_{idx}"] = True
                else:
                    st.error(f"❌ Incorrect.")
                    st.success(f"💡 Right answer: {q_data['answer']}")
                    st.session_state.failed_concept = {"course": selected_course, "question": q_data["question"]}

                if st.button("Next Question ➡️"):
                    if st.session_state.current_idx < (len(st.session_state.quiz_set) - 1):
                        st.session_state.current_idx += 1
                        st.session_state.answered = False
                    else: st.session_state.quiz_complete = True
                    st.rerun()

        elif st.session_state.quiz_complete:
            percent = int((st.session_state.score / 7) * 100)
            st.metric("Final Accuracy", f"{percent}%")
            if percent >= 70: st.snow()
            
            pdf_data = create_pdf_report(selected_course, st.session_state.score, difficulty, percent)
            st.download_button("📥 Download PDF Scorecard", data=pdf_data, file_name=f"Radar_Report.pdf", mime="application/pdf")
            
            if st.button("🔄 Restart"):
                st.session_state.quiz_set = []
                st.session_state.quiz_complete = False
                st.rerun()

    with tab3:
        st.subheader("🎓 Socratic Tutor")
        chat_key = f"messages_{selected_course}"
        if chat_key not in st.session_state: st.session_state[chat_key] = []
        
        if "failed_concept" in st.session_state:
            if st.button("Coach me on the missed question"):
                gap_prompt = f"Lead me to the answer for: {st.session_state.failed_concept['question']}"
                st.session_state[chat_key].append({"role": "assistant", "content": model.generate_content(gap_prompt).text})
                del st.session_state.failed_concept
                st.rerun()

        for msg in st.session_state[chat_key]: st.chat_message(msg["role"]).write(msg["content"])
        if prompt := st.chat_input("Ask Radar..."):
            st.session_state[chat_key].append({"role": "user", "content": prompt})
            st.session_state[chat_key].append({"role": "assistant", "content": model.generate_content(prompt).text})
            st.rerun()
else:
    st.title(selected_course)
    st.warning("🚀 This course is launching soon!")

# --- FOOTER ---
st.markdown("---") 
st.markdown("<div style='text-align: center;'><p>© 2026 Radar Grad-Tutors | \"Detecting Gaps, Delivering Grades\"</p></div>", unsafe_allow_html=True)
