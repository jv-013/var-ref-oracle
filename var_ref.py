import streamlit as st
import boto3
import uuid
import speech_recognition as sr
from pydub import AudioSegment
import io

# --- SYSTEM CONFIGURATION ---
AGENT_ID = "THLFCHYCH4"
AGENT_ALIAS_ID = "PEEURIASNU"
REGION = "eu-north-1" 

st.set_page_config(page_title="VARmageddon AI", page_icon="⚽", layout="wide")

# Professional Branding
st.title("⚽ VARmageddon AI")
st.markdown("### *Official Technical Support & Regulatory Analysis*")

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
    st.caption("Record disciplinary actions for contextual accuracy.")
    event_input = st.text_input("Enter Match Event:", placeholder="e.g. Red #10 Yellow Card - Unsporting Behavior")
    
    if st.button("Commit Event", use_container_width=True) and event_input:
        st.session_state.ledger.append(event_input)
        st.toast(f"Event Logged: {event_input}")

    if st.session_state.ledger:
        st.write("**Active Context Ledger:**")
        for i, item in enumerate(st.session_state.ledger, 1):
            st.info(f"{i}. {item}")
        if st.button("Reset Session Ledger", use_container_width=True):
            st.session_state.ledger = []
            st.rerun()

    st.divider()
    
    st.header("🎙️ Voice Entry")
    st.caption("Record incident details for automated transcription.")
    # Unique key helps reset the widget state after use
    audio_value = st.audio_input("Record Audio", key="match_audio_recorder")
    
    if audio_value:
        try:
            # Process audio only if voice_text is currently empty to prevent loops
            if not st.session_state.voice_text:
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_value.read()))
                wav_io = io.BytesIO()
                audio_segment.export(wav_io, format="wav")
                wav_io.seek(0)

                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_io) as source:
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data)
                    st.session_state.voice_text = text
                    st.rerun()
        except Exception:
            # Silently handle the widget's internal timeout; the logic already has the data
            pass

# --- MAIN COMMUNICATION INTERFACE ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Primary input field
prompt = st.chat_input("Enter incident details for regulatory review...")

# Voice Input Confirmation Logic
if st.session_state.voice_text:
    st.warning(f"**Transcription Detected:** {st.session_state.voice_text}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm Voice Entry", use_container_width=True):
            prompt = st.session_state.voice_text
            st.session_state.voice_text = "" 
    with col2:
        if st.button("❌ Discard", use_container_width=True):
            st.session_state.voice_text = ""
            st.rerun()

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # SECURE CONNECTION TO REGULATORY DATABASE
    client = boto3.client(
        "bedrock-agent-runtime",
        region_name=REGION,
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
    )
    
    ledger_str = ", ".join(st.session_state.ledger) if st.session_state.ledger else "No previous disciplinary records."
    full_prompt = f"Match Ledger: {ledger_str}\nCurrent Incident: {prompt}\nTarget Output Language: {language}"

    with st.status("Analyzing official regulations...", expanded=False) as status:
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

            status.update(label="Analysis Complete", state="complete")
            with st.chat_message("assistant"):
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error("System Error: Regulatory database connection timeout.")
