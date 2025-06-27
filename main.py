import streamlit as st
import os
from typing import List, Dict, Any
import tempfile
from pathlib import Path
from utils import load_llm_config_from_json
from agent_system import AgentSystem
from llm_config import LLMConfig

# Sidebar navigation
with st.sidebar:
    st.header("Navigation")
    st.page_link("main.py", label="🏠 Main", disabled=True)
    st.page_link("pages/TaskProcessor.py", label="📝 Task Processor")
    st.page_link("pages/Chat.py", label="💬 Chat")
    st.page_link("pages/Config.py", label="⚙️ Config")

st.set_page_config(
    page_title="LangChain Autonomous Task Processor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 LangChain Autonomous Task Processor")
st.markdown("Welcome! Use the sidebar to navigate to the Task Processor, Chat, or Config pages.")

# Status panel
st.header("📊 Status Panel")

# Configuration status
config = load_llm_config_from_json()
config_status = "✅ Configured" if config else "❌ Not Configured"
st.markdown(f"**LLM Status:** {config_status}")

# Instructions
if not config:
    st.warning("Please go to the Config page to set up your LLM provider before using the app.")
else:
    st.success("LLM is configured. You can now use the Task Processor or Chat features.")

    # Only create agent_system if not already in session_state
    if "agent_system" not in st.session_state:
        llm_config = LLMConfig(
            provider=config.get("PROVIDER"),
            api_key=config.get("AZURE_OPENAI_API_KEY"),
            endpoint=config.get("AZURE_OPENAI_ENDPOINT"),
            deployment_name=config.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version=config.get("AZURE_OPENAI_API_VERSION"),
            temperature=float(config.get("TEMPERATURE", 1.0)),
            max_tokens=int(config.get("MAX_TOKENS", 32768)),
            model_name=None  # or set if you have a model_name field
        )
        st.session_state.agent_system = AgentSystem(llm_config)

st.markdown("---")
st.markdown("**Quick Links:**")
st.page_link("pages/TaskProcessor.py", label="📝 Go to Task Processor")
st.page_link("pages/Chat.py", label="💬 Go to Chat")
st.page_link("pages/Config.py", label="⚙️ Go to Config")

# (Optional) Add more main page content or app description here.