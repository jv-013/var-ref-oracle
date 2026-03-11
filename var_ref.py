import streamlit as st
import boto3
import uuid

# --- CONFIGURATION ---
AGENT_ID = "THLFCHYCH4"
AGENT_ALIAS_ID = "PEEURIASNU"
REGION = "eu-north-1" 

st.set_page_config(page_title="VARmageddon AI", page_icon="⚽", layout="wide")

st.title("⚽ VARmageddon AI")
st.subheader("The Ultimate Authority on the Laws of the Game. Making football arguments scalable.")

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "ledger" not in st.session_state:
    st.session_state.ledger = []

# --- SIDEBAR: THE PRO TOOLS ---
with st.sidebar:
    st.header("🌍 Global Argument Settler")
    language = st.selectbox(
        "Select AI Output Language:",
        ["English", "Spanish (Español)", "French (Français)", "German (Deutsch)", "Arabic (العربية)", "Italian (Italiano)"]
    )
    
    st.divider()
    
    st.header("📒 Match Ledger")
    st.write("Track incidents so the AI remembers the game context.")
    
    # Input to add events to the ledger
    new_event = st.text_input("Log an event (e.g., 'Blue #7 - Yellow Card'):")
    if st.button("Add to Ledger") and new_event:
        st.session_state.ledger.append(new_event)
        st.success(f"Logged: {new_event}")
        
    # Display the current ledger
    if st.session_state.ledger:
        st.write("**Current Match Events:**")
        for i, event in enumerate(st.session_state.ledger, 1):
            st.write(f"{i}. {event}")
        if st.button("Clear Ledger"):
            st.session_state.ledger = []
            st.rerun()

    st.divider()
    
    st.header("🎙️ Voice Command (Beta)")
    audio_value = st.audio_input("Record incident")
    if audio_value:
        st.info("Audio received! (Note: Backend transcription API required to process voice to text).")

# --- MAIN CHAT INTERFACE ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter the incident for a final ruling..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- THE MAGIC: INJECTING CONTEXT & LANGUAGE ---
    # We silently combine the Ledger, the Language, and the Prompt before sending it to AWS
    ledger_context = "\n".join(st.session_state.ledger) if st.session_state.ledger else "No previous disciplinary events."
    
    enhanced_prompt = f"""
    Current Match Context (Disciplinary Ledger):
    {ledger_context}
    
    Incident to review:
    {prompt}
    
    Please provide your final ruling and explanation strictly in {language}.
    """

    # Connect to AWS
    client = boto3.client(
        "bedrock-agent-runtime",
        region_name=REGION,
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
    )
    
    with st.spinner(f"Consulting the rules and translating to {language}..."):
        try:
            response = client.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                sessionId=st.session_state.session_id,
                inputText=enhanced_prompt
            )
            
            full_response = ""
            for event in response.get("completion"):
                chunk = event.get("chunk")
                if chunk:
                    full_response += chunk.get("bytes").decode()

            if not full_response:
                full_response = "The VAR booth is reviewing the footage. Please rephrase your query."

            with st.chat_message("assistant"):
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"VAR System Error: {str(e)}")
