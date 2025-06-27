import streamlit as st
import os
from typing import List, Dict, Any
import tempfile
from pathlib import Path
from src.app_logic.utils import load_llm_config_from_json
from src.app_logic.agent_system import AgentSystem
from src.app_logic.llm_config import LLMConfig

from src.app_logic.ui_utils import create_sidebar_nav_v2

# Sidebar navigation
create_sidebar_nav_v2("main")

st.set_page_config(
    page_title="LangChain Autonomous Task Processor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("assets/styles.css")

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
        try:
            st.session_state.agent_system = AgentSystem(llm_config)
            # If successful, update status message if needed, though it's already optimistic.
        except ValueError as e:
            st.error(f"Failed to initialize LLM Agent: {e}. Please check your settings on the Config page or choose a supported LLM provider.")
            # Prevent access to other pages if agent system fails to load
            st.session_state.agent_system = None # Ensure it's None
            config_status = "⚠️ Error" # Update status
            st.markdown(f"**LLM Status:** {config_status}") # Re-render status
            # Potentially disable links or stop the app here if critical
        except Exception as e: # Catch any other unexpected errors during AgentSystem init
            st.error(f"An unexpected error occurred while setting up the LLM Agent: {e}. Please check your configuration.")
            st.session_state.agent_system = None
            config_status = "⚠️ Error"
            st.markdown(f"**LLM Status:** {config_status}")


# Update config_status based on whether agent_system was successfully created
if "agent_system" in st.session_state and st.session_state.agent_system is not None:
    config_status = "✅ Configured & Agent Ready"
elif config is None: # No config file
    config_status = "❌ Not Configured"
    # Warning about no config is already handled above
else: # Config file exists, but agent creation failed
    config_status = f"⚠️ LLM Configured, but Agent Error (see message above)"

# Display LLM Status again in case it was updated by error handling
# This might be slightly redundant if no error, but ensures correct status if error.
# Consider placing this status update more strategically if it causes UI flicker.
# For now, let's update it once after attempt.
st.markdown(f"**LLM Status:** {config_status}")


st.markdown("---")
st.markdown("**Quick Links:**")
st.page_link("pages/TaskProcessor.py", label="📝 Go to Task Processor")
st.page_link("pages/Chat.py", label="💬 Go to Chat")
st.page_link("pages/Config.py", label="⚙️ Go to Config")

# (Optional) Add more main page content or app description here.