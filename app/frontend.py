import streamlit as st
import requests
import re

# Page Config with Logo
st.set_page_config(
    page_title="Write any code",
    page_icon="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/Code.org_logo.svg/1200px-Code.org_logo.svg.png",
    layout="centered",
)

# Custom CSS for Logo & UI
st.markdown("""
    <style>
        /* Full Center Alignment */
        .main-container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 90vh;
        }

        /* Logo Centered */
        .logo {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            margin-bottom: 10px;
        }

        /* Title Centered */
        .title {
            text-align: center;
            font-size: 28px;
            font-weight: bold;
            color: #03dac6;
        }

        /* Chatbox UI */
        .chat-container {
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
            background-color: #262626;
            color: white;
        }

        /* User & AI Message Styling */
        .user-message { border-left: 5px solid #03dac6; padding-left: 10px; }
        .ai-message { border-left: 5px solid #ff9800; padding-left: 10px; }
        pre { white-space: pre-wrap; word-wrap: break-word; }

        /* Search Bar Styling */
        .search-container {
            display: flex;
            align-items: center;
            width: 100%;
            max-width: 600px;
            margin: auto;
        }

        .search-input {
            flex-grow: 1;
            padding: 12px 15px;
            border-radius: 25px;
            border: 2px solid #03dac6;
            background-color: #262626;
            color: white;
            font-size: 16px;
            outline: none;
        }

        /* Search Button */
        .search-button {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: none;
            background-color: #00ffcc;
            color: black;
            font-size: 16px;
            cursor: pointer;
            transition: 0.3s;
            text-align: center;
        }

        .search-button:hover {
            background-color: #02c2ad;
        }
    </style>
""", unsafe_allow_html=True)

# Logo
st.markdown(
    '<div class="logo"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/Code.org_logo.svg/1200px-Code.org_logo.svg.png" width="80"></div>',
    unsafe_allow_html=True
)

# Title
st.markdown('<div class="title">Write any code: Verbose❇️</div>', unsafe_allow_html=True)

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-container user-message"><b>User:</b><br>{msg["content"]}</div>',
                    unsafe_allow_html=True)
    elif msg["role"] == "ai":
        explanation, code = msg["content"]
        st.markdown(f'<div class="chat-container ai-message"><b>AI:</b><br>{explanation}</div>', unsafe_allow_html=True)
        if code:
        #     st.subheader("Generated Code:")
            st.code(code, language="python")

# Input Form
st.markdown('<div class="search-container">', unsafe_allow_html=True)

with st.form(key="input_form"):
    user_input = st.text_input("Your Prompt:", key="user_prompt", placeholder="Enter your prompt...")

    # Single send button
    submit_button = st.form_submit_button("SEND ↗️")

st.markdown("</div>", unsafe_allow_html=True)

# API Call Logic
if submit_button:
    if user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input})
        try:
            response = requests.post("http://127.0.0.1:8000/generate/", json={"prompt": user_input, "response_type": "both"})
            if response.status_code == 200:
                data = response.json()
                raw_text = data.get("response", "").strip()
                if not raw_text or raw_text.lower() == "none":
                    st.warning("⚠️ No valid response generated. Try a different prompt.")
                else:
                    explanation, code = raw_text, None
                    code_match = re.search(r"```(?:python)?\n(.*?)\n```", raw_text, re.DOTALL)
                    if code_match:
                        code = code_match.group(1).strip()
                        explanation = raw_text.replace(code_match.group(0), "").strip()
                    st.session_state.messages.append({"role": "ai", "content": (explanation, code)})
                    st.rerun()
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Cannot connect to backend! Make sure FastAPI is running.")
    else:
        st.warning("Write something in input cell.")
