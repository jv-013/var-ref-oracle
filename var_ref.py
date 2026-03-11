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

# Main Header
st.title("⚽ VARmageddon AI")
st.subheader("The Ultimate Multi-League Authority. Making football arguments scalable.")

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "ledger" not in st.session_state:
    st.session_state.ledger = []
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

# --- SIDEBAR: PRO TOOLS ---
with st.sidebar:
    st.header("🌍 Global Argument Settler")
    language = st.selectbox(
        "AI Output Language:",
        ["English", "Spanish", "French", "German", "Arabic", "Italian", "Portuguese"]
    )
    
    st.divider()
    
    st.header("📒 Match Ledger")
    st.info("Log incidents here so the AI remembers the game context.")
    event_input = st.text_input("New Event (e.g. 'Red #10 Yellow Card'):")
    if st.button("Log Event") and event_input:
        st.session_state.ledger.append(event_input)
        st.success(f"Added: {event_input}")

    if st.session_state.ledger:
        st.write("**Current Ledger:**")
        for i, item in enumerate(st.session_state.ledger, 1):
            st.write(f"{i}. {item}")
        if st.button("Clear Ledger"):
            st.session_state.ledger = []
            st.rerun()

    st.divider()
    st.header("🎙️ Voice Command")
    audio_value = st.audio_input("Speak Incident")
    
    if audio_value:
        try:
            # Convert the audio stream to WAV so the 'Ear' can read it
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_value.read()))
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)

            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_io) as source:
                audio_data = recognizer.record(source)
                # Use Google's Speech API (Free)
                text = recognizer.recognize_google(audio_data)
                st.session_state.voice_text = text
                st.success(f"Heard: '{text}'")
        except Exception as e:
            st.error("Audio error: Please ensure you are not using the Instagram browser.")

# --- CHAT INTERFACE ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Logic to catch input from either the keyboard or the voice success button
prompt = st.chat_input("Ask about a UCL, PL, or IFAB incident...")

if st.session_state.voice_text:
    if st.button(f"Submit Voice Command: '{st.session_state.voice_text}'"):
        prompt = st.session_state.voice_text
        st.session_state.voice_text = "" # Clear it for the next one

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
    
    # Bundle everything for the AI
    ledger_str = ", ".join(st.session_state.ledger) if st.session_state.ledger else "None"
    full_prompt = f"""
    MATCH CONTEXT (Previous events): {ledger_str}
    NEW QUERY: {prompt}
    INSTRUCTION: Answer using the Knowledge Base (IFAB, UCL, PL, etc). 
    LANGUAGE: Provide the final ruling strictly in {language}.
    """

    with st.spinner(f"VAR is checking the booth in {language}..."):
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
            st.error(f"VAR System Error: {str(e)}")
