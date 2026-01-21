import streamlit as st
import google.generativeai as genai

# 1. # Look for the key in the Cloud Secrets instead of local text
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 2. Page UI
st.title("Stature Tutors")
st.caption("I'm your Socratic tutor. I won't give you the answer, but I'll help you find it!")

# 3. Chat Logic
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Socratic Prompting
    full_prompt = f"System: You are a Socratic University Tutor. Never give answers immediately. Always ask a helpful guiding question first. \nStudent: {prompt}"
    
    response = model.generate_content(full_prompt)
    st.session_state.messages.append({"role": "assistant", "content": response.text})
    st.chat_message("assistant").write(response.text)