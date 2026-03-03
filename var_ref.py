import streamlit as st
import boto3
import uuid

# --- UPDATED VAR CONFIGURATION FOR STOCKHOLM ---
AGENT_ID = "THLFCHYCH4"
AGENT_ALIAS_ID = "PEEURIASNU"
REGION = "eu-north-1"  # Updated to Stockholm

# Page Styling
st.set_page_config(page_title="VAR Oracle V2", page_icon="⚖️")
st.title("⚖️ VAR-Oracle-V2")
st.subheader("Official Laws of the Game Assistant (Stockholm Node)")

# Initialize Session
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Describe the incident (e.g., handball, offside)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Calling Bedrock in Stockholm Region
    client = boto3.client("bedrock-agent-runtime", region_name=REGION)
    
    with st.spinner("Consulting Rulebook..."):
        try:
            response = client.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                sessionId=st.session_state.session_id,
                inputText=prompt
            )
            
            full_response = ""
            for event in response.get("completion"):
                chunk = event.get("chunk")
                if chunk:
                    full_response += chunk.get("bytes").decode()

            if not full_response:
                full_response = "The Oracle is analyzing the play. Please provide more detail."

            with st.chat_message("assistant"):
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"VAR System Error: {str(e)}")
            st.info("Tip: Ensure your Agent is 'Prepared' in the Stockholm (eu-north-1) AWS Console.")