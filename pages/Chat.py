import streamlit as st
from llm_config import LLMFactory

st.set_page_config(page_title="Azure OpenAI Chat", page_icon="💬")

# Sidebar navigation
with st.sidebar:
    st.header("Navigation")
    st.page_link("main.py", label="🏠 Main")
    st.page_link("pages/Chat.py", label="💬 Chat", disabled=True)
    st.page_link("pages/Config.py", label="⚙️ Config")
    st.page_link("pages/TaskProcessor.py", label="📝 Task Processor")

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
    st.markdown("<div style='height:400px; overflow-y:auto; background:#181c24; border-radius:8px; padding:16px; margin-bottom:8px;'>", unsafe_allow_html=True)
    # Only show the last user message and the last assistant response
    if len(st.session_state.chat_history) >= 1:
        last_user_msg = next((msg for msg in reversed(st.session_state.chat_history) if msg["role"] == "user"), None)
        if last_user_msg:
            st.markdown(f"<div style='background:#262730; color:#fff; border-radius:6px; padding:8px 12px; margin-bottom:6px; text-align:right;'><b>You:</b> {last_user_msg['content']}</div>", unsafe_allow_html=True)
    if len(st.session_state.chat_history) >= 2:
        last_assistant_msg = next((msg for msg in reversed(st.session_state.chat_history) if msg["role"] == "assistant"), None)
        if last_assistant_msg:
            st.markdown(f"<div style='background:#31333f; color:#fff; border-radius:6px; padding:8px 12px; margin-bottom:6px; text-align:left;'><b>Assistant:</b> {last_assistant_msg['content']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with input_container:
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Your message:", height=80, key="chat_input")
        submitted = st.form_submit_button("Send", type="primary")

    if submitted and user_input.strip():
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
        messages = [(msg["role"], msg["content"]) for msg in st.session_state.chat_history]
        llm = agent_system.llm if hasattr(agent_system, "llm") else LLMFactory.create_llm(llm_config)
        response = ""
        with st.spinner("Thinking..."):
            try:
                for chunk in llm.stream(messages):
                    response += chunk.content
                    st.markdown(f"<div style='background:#31333f; color:#fff; border-radius:6px; padding:8px 12px; margin-bottom:6px; text-align:left;'><b>Assistant:</b> {response}▌</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

# Option to clear chat
st.markdown("---")
if st.button("��️ Clear Chat"):
    st.session_state.chat_history = []
    st.rerun() 