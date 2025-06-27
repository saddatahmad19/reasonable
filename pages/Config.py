import streamlit as st
from utils import load_llm_config_from_json, save_llm_config_to_json

# Sidebar navigation
with st.sidebar:
    st.header("Navigation")
    st.page_link("main.py", label="🏠 Main")
    st.page_link("pages/Chat.py", label="💬 Chat")
    st.page_link("pages/Config.py", label="⚙️ Config", disabled=True)
    st.page_link("pages/TaskProcessor.py", label="📝 Task Processor")

st.set_page_config(page_title="LLM Configuration", page_icon="⚙️")
st.title("⚙️ LLM Configuration")

config = load_llm_config_from_json()

provider_options = ["Azure OpenAI", "OpenAI", "Gemini", "Anthropic"]
provider_env_map = {
    "Azure OpenAI": "azure_openai",
    "OpenAI": "openai",
    "Gemini": "gemini",
    "Anthropic": "anthropic"
}
field_map = {
    "azure_openai": {
        "api_key": "AZURE_OPENAI_API_KEY",
        "endpoint": "AZURE_OPENAI_ENDPOINT",
        "deployment_name": "AZURE_OPENAI_DEPLOYMENT_NAME",
        "api_version": "AZURE_OPENAI_API_VERSION"
    },
    "openai": {
        "api_key": "OPENAI_API_KEY",
        "model_name": "OPENAI_MODEL_NAME"
    },
    "gemini": {
        "api_key": "GEMINI_API_KEY",
        "model_name": "GEMINI_MODEL_NAME"
    },
    "anthropic": {
        "api_key": "ANTHROPIC_API_KEY",
        "model_name": "ANTHROPIC_MODEL_NAME"
    }
}

default_provider = config.get("PROVIDER", "azure_openai")
default_provider_ui = next((k for k, v in provider_env_map.items() if v == default_provider), provider_options[0])

st.markdown("Configure your LLM provider below. This configuration is required before using chat or task features.")

with st.form("llm_config_form"):
    api_provider = st.selectbox(
        "Select API Provider",
        provider_options,
        index=provider_options.index(default_provider_ui)
    )
    provider_key = provider_env_map[api_provider]
    fields = field_map[provider_key]
    input_values = {}
    for field, env_key in fields.items():
        label = field.replace("_", " ").title()
        default = config.get(env_key, "")
        if "key" in field:
            val = st.text_input(label, value=default, type="password")
        else:
            val = st.text_input(label, value=default)
        input_values[field] = val
    temperature = st.number_input(
        "Temperature",
        min_value=0.0, max_value=2.0, value=float(config.get("TEMPERATURE", 0.7)), step=0.01
    )
    max_tokens = st.number_input(
        "Max Tokens",
        min_value=1, max_value=32768, value=int(config.get("MAX_TOKENS", 4000)), step=1
    )
    submitted = st.form_submit_button("Save Configuration", type="primary")

    if submitted:
        # Validate required fields
        required_fields = [f for f in fields if "key" in f or f in ("endpoint", "deployment_name")]
        if not all(input_values.get(f) for f in required_fields):
            st.error("Please fill in all required fields.")
        else:
            save_dict = {"PROVIDER": provider_key, "TEMPERATURE": str(temperature), "MAX_TOKENS": str(max_tokens)}
            for field, env_key in fields.items():
                save_dict[env_key] = input_values[field]
            save_llm_config_to_json(save_dict)
            st.success("✅ Configuration saved! You can now use the app.")
            st.rerun()

# Show current config summary
st.markdown("---")
st.subheader("Current Configuration")
config = load_llm_config_from_json()
if config:
    st.json(config)
else:
    st.info("No configuration found. Please fill out the form above.") 