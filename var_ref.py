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
    
    # IMPROVED LEDGER UI
    st.header("📒 Match Ledger")
    st.caption("Disciplinary actions are tracked automatically by the AI.")
    
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

# CHANGE 1: IMPROVED VOICE ENTRY STATE CLEANUP
if st.session_state.voice_text:
    st.warning(f"**Transcription Detected:** {st.session_state.voice_text}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm Voice Entry", use_container_width=True):
            prompt = st.session_state.voice_text
            st.session_state.voice_text = "" # Immediate clear to remove warning from UI
            # No rerun here; we let the prompt logic below trigger the rerun after AI response
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
    
    ledger_str = ", ".join(st.session_state.ledger) if st.session_state.ledger else "No previous records."
    
    # CHANGE 2: REFINED HIERARCHY PROMPT (Leagues vs UEFA)
    full_prompt = f"""
    MATCH CONTEXT:
    - Target Output Language: {language}
    - Current Incident: {prompt}
    - Match Ledger: {ledger_str}
    
    REGULATORY HIERARCHY (MANDATORY):
    1. PRIMARY: If the query mentions a specific league (e.g., Bundesliga), you MUST prioritize the regulations in that league's specific handbook.
    2. SECONDARY: Use UEFA/IFAB only as a fallback. Bundesliga rules take precedence over UEFA rules if they conflict.
    
    CRITICAL INSTRUCTIONS:
    - Answer using ONLY Knowledge Base documents.
    - NO XML/SYSTEM TAGS. Do not output <user__askuser>. Speak in plain {language}.
    - AUTO-LEDGER: If a card is issued, append this tag at the very bottom: [LOG: Team/Player - Card Type]
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
            
            # --- THE SMART AUTO-EXTRACTOR (Prevents Duplicate Ledger Entries) ---
            match = re.search(r'\[LOG:\s*(.*?)\]', answer)
            if match:
                new_event = match.group(1)
                # Only add to ledger if it's not already there for this specific incident
                if new_event not in st.session_state.ledger:
                    st.session_state.ledger.append(new_event)
                    st.toast(f"VAR Auto-Logged: {new_event}")
                
                # Strip robot tag from visible chat
                answer = re.sub(r'\[LOG:\s*(.*?)\]', '', answer).strip()

            with st.chat_message("assistant"):
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            # Final rerun to update UI and clear confirmed voice alerts
            st.rerun()

        except Exception as e:
            st.error("System Error: Regulatory database connection timeout.")
