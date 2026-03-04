import streamlit as st
import boto3
import uuid

# --- CONFIGURATION ---
AGENT_ID = "THLFCHYCH4"
AGENT_ALIAS_ID = "PEEURIASNU"
REGION = "eu-north-1" 

# Page Styling
# Using ⚽ for the browser tab icon
st.set_page_config(page_title="VARmageddon AI", page_icon="⚽")

# Main Header with Football Emoji
st.title("⚽ VARmageddon AI")

# Subheader: Combining your new slogan with the original purpose
st.subheader("The Ultimate Authority on the Laws of the Game. Making football arguments scalable.")

# Initialize Session for Chat
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input Box
if prompt := st.chat_input("Enter the incident for a final ruling..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Secure Connection using Streamlit Secrets
    client = boto3.client(
        "bedrock-agent-runtime",
        region_name=REGION,
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
    )
    
    with st.spinner("Consulting the Laws of the Game..."):
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
                full_response = "The VAR booth is reviewing the footage. Please rephrase your query."

            with st.chat_message("assistant"):
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"VAR System Error: {str(e)}")
            st.info("System Tip: Check your AWS Secrets or ensure the Agent is 'Prepared' in Stockholm.")
