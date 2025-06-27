import streamlit as st
from src.app_logic.llm_config import LLMFactory
from src.app_logic.ui_utils import create_sidebar_nav_v2

st.set_page_config(page_title="Azure OpenAI Chat", page_icon="💬")

# Sidebar navigation
create_sidebar_nav_v2("chat")

st.title("💬 Azure OpenAI Chat")

# Check if LLM is configured
agent_system = st.session_state.get("agent_system", None)
llm_config = getattr(agent_system, "config", None)

if not agent_system or not llm_config:
    st.warning("Please configure your Azure OpenAI instance in the Config page before chatting.")
    st.stop()

# Show instance and deployment info
with st.expander("🔍 LLM Info", expanded=False):
    st.markdown(f"**Instance:** `{llm_config.instance_name}`  |  **Deployment:** `{llm_config.deployment_name}`  |  **Model:** `{llm_config.model_name or 'N/A'}`")

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Chat UI layout
chat_container = st.container()
input_container = st.container()

with chat_container:
    # Custom CSS for chat messages
    st.markdown("""
    <style>
        .chat-message {
            padding: 8px 12px;
            border-radius: 6px;
            margin-bottom: 6px;
            color: #fff;
        }
        .user-message {
            background-color: #262730; /* Streamlit's dark theme input background */
            text-align: right;
        }
        .assistant-message {
            background-color: #31333F; /* Slightly lighter for assistant */
            text-align: left;
        }
        .message-sender {
            font-weight: bold;
            margin-bottom: 4px;
            display: block;
        }
    </style>
    """, unsafe_allow_html=True)

    # Chat history display area
    # The outer div for scrolling should be managed by st.container() with height if needed,
    # or let Streamlit handle it. For now, let's remove fixed height to see full history.
    # st.markdown("<div style='height:400px; overflow-y:auto; background:#181c24; border-radius:8px; padding:16px; margin-bottom:8px;'>", unsafe_allow_html=True)

    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"<div class='chat-message user-message'><span class='message-sender'>You:</span>{message['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-message assistant-message'><span class='message-sender'>Assistant:</span>{message['content']}</div>", unsafe_allow_html=True)
    # st.markdown("</div>", unsafe_allow_html=True)

with input_container:
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Your message:", height=80, key="chat_input", placeholder="Type your message here...")
        submitted = st.form_submit_button("Send", type="primary")

    if submitted and user_input.strip():
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})

        # Prepare messages for LLM
        # Langchain expects a list of BaseMessage objects or (role, content) tuples
        # For AzureChatOpenAI, it's typically a list of HumanMessage, AIMessage, SystemMessage
        # The current `agent_system.llm.stream` expects this format.
        history_for_llm = []
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                history_for_llm.append(("human", msg["content"]))
            elif msg["role"] == "assistant":
                 history_for_llm.append(("ai", msg["content"]))

        llm = agent_system.llm if hasattr(agent_system, "llm") else LLMFactory.create_llm(llm_config)

        # Placeholder for the streaming response
        # We need to update the UI dynamically as chunks arrive.
        # A simple way is to rerun and redraw, but for streaming, st.empty() is better.
        assistant_response_area = st.empty()
        full_response = ""

        with st.spinner("Thinking..."):
            try:
                for chunk in llm.stream(history_for_llm): # Pass the formatted history
                    full_response += chunk.content
                    # Update the placeholder with the latest response
                    assistant_response_area.markdown(
                        f"<div class='chat-message assistant-message'><span class='message-sender'>Assistant:</span>{full_response}▌</div>",
                        unsafe_allow_html=True
                    )
            except Exception as e:
                st.error(f"Error: {e}")

        # Once streaming is complete, add the full response to history
        if full_response: # Ensure we don't add empty responses if an error occurred early
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})

        # Clear the temporary streaming area and rerun to draw the final message from history
        assistant_response_area.empty()
        st.rerun()

# Option to clear chat
st.markdown("---")
if st.button("��️ Clear Chat"):
    st.session_state.chat_history = []
    st.rerun() 