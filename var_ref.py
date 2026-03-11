import streamlit as st
import boto3
import uuid
import speech_recognition as sr
from pydub import AudioSegment
import io

# --- CONFIGURATION ---
AGENT_ID = "THLFCHYCH4"
AGENT_ALIAS_ID = "PEEURIASNU"
REGION = "eu-north-1" 

st.set_page_config(page_title="VARmageddon AI", page_icon="⚽", layout="wide")

st.title("⚽ VARmageddon AI")
st.subheader("Automated Match Official Intelligence")

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "ledger" not in st.session_state:
    st.session_state.ledger = []
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

# --- SIDEBAR: MATCH TOOLS ---
with st.sidebar:
    st.header("🌍 Output Language")
    language = st.selectbox(
        "Select Language:",
        ["English", "Spanish", "French", "German", "Arabic", "Italian", "Portuguese"]
    )
    
    st.divider()
    
    st.header("📒 Match Ledger")
    event_input = st.text_input("Log Match Event:", placeholder="e.g. Red #10 Yellow Card")
    if st.button("Commit Event") and event_input:
        st.session_state.ledger.append(event_input)
        st.success(f"Event Logged: {event_input}")

    if st.session_state.ledger:
        st.write("**Active Match Context:**")
        for i, item in enumerate(st.session_state.ledger, 1):
            st.write(f"{i}. {item}")
        if st.button("Reset Ledger"):
            st.session_state.ledger = []
            st.rerun()

    st.divider()
    st.header("🎙️ Voice Input")
    audio_value = st.audio_input("Record Match Incident")
    
    if audio_value:
        with st.status("Transcribing audio...", expanded=False):
            try:
                # Process audio through pydub and speech_recognition
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_value.read()))
                wav_io = io.BytesIO()
                audio_segment.export(wav_io, format="wav")
                wav_io.seek(0)

                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_io) as source:
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data)
                    st.session_state.voice_text = text
                    st.write(f"Transcription: {text}")
            except Exception:
                st.error("Transcription Error: Audio processing failed. Please ensure clear input.")

# --- MAIN INTERFACE ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Enter incident details for review...")

# Voice Command Submission
if st.session_state.voice_text:
    if st.button("Confirm Voice Input"):
        prompt = st.session_state.voice_text
        st.session_state.voice_text = "" 

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AWS CONNECTION
    client = boto3.client(
        "bedrock-agent-runtime",
        region_name=REGION,
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
    )
    
    ledger_str = ", ".join(st.session_state.ledger) if st.session_state.ledger else "No previous events."
    full_prompt = f"Match Context: {ledger_str}\nIncident: {prompt}\nLanguage: {language}"

    with st.spinner("Analyzing regulations..."):
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

            with st.chat_message("assistant"):
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error(f"System Error: Connection to AWS Bedrock failed.")
