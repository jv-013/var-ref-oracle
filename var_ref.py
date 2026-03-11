import streamlit as st
import boto3
import uuid
import speech_recognition as sr
from pydub import AudioSegment
import io
import re

# --- SYSTEM CONFIGURATION ---
AGENT_ID = "THLFCHYCH4"
AGENT_ALIAS_ID = "PEEURIASNU"
REGION = "eu-north-1" 

st.set_page_config(page_title="VARmageddon AI", page_icon="⚽", layout="wide")

st.title("⚽ VARmageddon AI ⚖️")
st.markdown("### *Making Football Arguments Scalable*")

# --- DATA PERSISTENCE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "ledger" not in st.session_state:
    st.session_state.ledger = []
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

# --- SIDEBAR: MATCH OFFICIAL TOOLKIT ---
with st.sidebar:
    st.header("🌍 System Language")
    language = st.selectbox(
        "Select Regulatory Language:",
        ["English", "Spanish", "French", "German", "Arabic", "Italian", "Portuguese"]
    )
    
    st.divider()
    st.header("📒 Match Ledger")
    if st.session_state.ledger:
        for i, item in enumerate(st.session_state.ledger, 1):
            st.warning(f"{i}. {item}")
        if st.button("Reset Session Ledger", use_container_width=True):
            st.session_state.ledger = []
            st.rerun()
    else:
        st.info("No disciplinary events logged yet.")

    st.divider()
    st.header("🎙️ Voice Entry")
    audio_value = st.audio_input("Record Audio", key="match_audio_recorder")
    
    if audio_value:
        try:
            if not st.session_state.voice_text:
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_value.read()))
                wav_io = io.BytesIO()
                audio_segment.export(wav_io, format="wav")
                wav_io.seek(0)
                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_io) as source:
                    audio_data = recognizer.record(source)
                    st.session_state.voice_text = recognizer.recognize_google(audio_data)
                    st.rerun()
        except Exception:
            pass

# --- MAIN INTERFACE ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Enter incident details...")

# FIXED: Voice Entry cleanup so it doesn't get "stuck"
if st.session_state.voice_text:
    st.warning(f"**Transcription Detected:** {st.session_state.voice_text}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm Voice Entry", use_container_width=True):
            prompt = st.session_state.voice_text
            st.session_state.voice_text = "" # Clear the state
            # Logic will continue to the 'if prompt' block below
    with col2:
        if st.button("❌ Discard", use_container_width=True):
            st.session_state.voice_text = ""
            st.rerun()

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = boto3.client(
        "bedrock-agent-runtime",
        region_name=REGION,
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
    )
    
    ledger_str = ", ".join(st.session_state.ledger) if st.session_state.ledger else "None."
    
    # SIMPLIFIED PROMPT: No more league-specific overrides
    full_prompt = f"""
    Current Language: {language}
    Match Ledger: {ledger_str}
    User Query: {prompt}
    
    INSTRUCTIONS:
    1. Answer using the provided Knowledge Base documents. 
    2. DO NOT use XML/system tags like <user__askuser>.
    3. AUTO-LEDGER: If a Yellow or Red card is issued, add [LOG: Team/Player - Card Type] to the end.
    """

    with st.status("Analyzing...", expanded=False) as status:
        try:
            response = client.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                sessionId=st.session_state.session_id,
                inputText=full_prompt
            )
            
            answer = ""
            for event in response.get("completion"):
                chunk = event.get("chunk")
                if chunk:
                    answer += chunk.get("bytes").decode()

            # Smart extraction to avoid the duplicate ledger entries you saw earlier
            match = re.search(r'\[LOG:\s*(.*?)\]', answer)
            if match:
                new_event = match.group(1)
                if new_event not in st.session_state.ledger:
                    st.session_state.ledger.append(new_event)
                answer = re.sub(r'\[LOG:\s*(.*?)\]', '', answer).strip()

            with st.chat_message("assistant"):
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            
            st.rerun() # Refresh to clear any remaining voice UI elements

        except Exception as e:
            st.error("Connection error.")
