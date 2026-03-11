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

# Professional Branding
st.title("⚽ VARmageddon AI")
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
    
    # AUTOMATED LEDGER UI (No more manual input!)
    st.header("📒 Match Ledger")
    st.caption("Disciplinary actions are now tracked automatically by the AI.")
    
    if st.session_state.ledger:
        st.write("**Active Context Ledger:**")
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
                    text = recognizer.recognize_google(audio_data)
                    st.session_state.voice_text = text
                    st.rerun()
        except Exception:
            pass

# --- MAIN COMMUNICATION INTERFACE ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Enter incident details for regulatory review...")

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

    client = boto3.client(
        "bedrock-agent-runtime",
        region_name=REGION,
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
    )
    
    # THE MAGIC INSTRUCTION
   full_prompt = f"""
    Match Ledger: {ledger_str}
    Current Incident: {prompt}
    Target Output Language: {language}
    
    CRITICAL INSTRUCTIONS:
    1. Answer the query directly using ONLY the provided Knowledge Base documents.
    2. DO NOT use XML tags, HTML tags, or internal system formatting (like <user__askuser>). Speak in plain, conversational {language}. If you need clarification, ask in plain text.
    3. If your ruling results in a Yellow Card or Red Card for a specific player, you MUST append a tracking tag at the very bottom of your response in this exact format:
    [LOG: Team/Player - Card Type]
    Example: [LOG: Blue #10 - Yellow Card]
    If no card is given, do not output the log tag.
    """

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
            
            # --- THE AUTO-EXTRACTOR ---
            # Search the AI's answer for our secret [LOG: ...] tag
            match = re.search(r'\[LOG:\s*(.*?)\]', answer)
            if match:
                new_event = match.group(1)
                st.session_state.ledger.append(new_event) # Save it to the sidebar automatically
                st.toast(f"VAR Auto-Logged: {new_event}") # Pop up a nice notification
                # Erase the tag from the text so the user doesn't see the robot language
                answer = re.sub(r'\[LOG:\s*(.*?)\]', '', answer).strip()

            with st.chat_message("assistant"):
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            # If we found a tag, rerun to instantly update the sidebar visuals
            if match:
                st.rerun()

        except Exception as e:
            st.error("System Error: Regulatory database connection timeout.")
