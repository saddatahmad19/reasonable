import streamlit as st
# Assuming execution from project root: `streamlit run main_streamlit_app.py` (when inside crewai_research_app dir)
# or `streamlit run crewai_research_app/main_streamlit_app.py` (when outside)
# Python path will include the directory containing `crewai_research_app` or `crewai_research_app` itself.

from app.firebase_init import initialize_firebase, signup_user, login_user, logout_user, get_current_user
from config import settings
import os
import zipfile
from utils.file_handler import list_files_in_repo # This function will be implemented later

# Initialize Firebase
# This should ideally be called once. Streamlit's execution model can rerun scripts.
# We use session_state to track initialization.
if 'firebase_initialized' not in st.session_state:
    initialize_firebase()

def main():
    st.title("CrewAI Powered Deep Research App")

    # --- Authentication UI ---
    st.sidebar.header("User Authentication")
    if get_current_user():
        st.sidebar.write(f"Logged in as: {get_current_user()}")
        if st.sidebar.button("Logout"):
            logout_user()
            st.experimental_rerun() # Rerun to update UI after logout
    else:
        auth_choice = st.sidebar.selectbox("Choose Action", ["Login", "Sign Up"])
        email = st.sidebar.text_input("Email", key="auth_email")
        password = st.sidebar.text_input("Password", type="password", key="auth_password")

        if auth_choice == "Login":
            if st.sidebar.button("Login"):
                if email and password:
                    login_user(email, password)
                    if st.session_state.get('logged_in'):
                        st.experimental_rerun()
                else:
                    st.sidebar.error("Email and password are required.")
        elif auth_choice == "Sign Up":
            if st.sidebar.button("Sign Up"):
                if email and password:
                    signup_user(email, password)
                else:
                    st.sidebar.error("Email and password are required.")

    # Main app, only accessible if logged in (basic protection)
    if not get_current_user():
        st.warning("Please login or sign up to use the app.")
        return

    st.header("1. Upload Repository (as .zip)")
    uploaded_file = st.file_uploader("Choose a .zip file", type="zip")

    repo_path = None
    if uploaded_file is not None:
        # Use the corrected TEMP_UPLOAD_PATH from settings
        if not os.path.exists(settings.TEMP_UPLOAD_PATH):
            os.makedirs(settings.TEMP_UPLOAD_PATH) # Should be created by settings.py, but good to double check

        zip_path = os.path.join(settings.TEMP_UPLOAD_PATH, uploaded_file.name)
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"Uploaded {uploaded_file.name}")

        # Extract the zip file
        extracted_path = os.path.join(settings.TEMP_UPLOAD_PATH, uploaded_file.name.replace(".zip", ""))
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extracted_path)
            st.success(f"Extracted repository to: {extracted_path}")
            # Usually, a git repo has a single top-level folder after extraction from a typical zip.
            # We need to find that folder.
            extracted_items = os.listdir(extracted_path)
            if len(extracted_items) == 1 and os.path.isdir(os.path.join(extracted_path, extracted_items[0])):
                repo_path = os.path.join(extracted_path, extracted_items[0])
            else:
                # The zip might not have a single root folder, or might have multiple.
                # For simplicity, assume the extracted_path itself is the root if no single subfolder.
                repo_path = extracted_path
            st.info(f"Repository path set to: {repo_path}")

            try:
                all_files = list_files_in_repo(repo_path)
                st.success(f"Found {len(all_files)} non-ignored files in the repository.")
                if all_files:
                    st.write("First 10 files found (relative to repo root):")
                    for f_abs_path in all_files[:10]:
                        st.text(os.path.relpath(f_abs_path, repo_path))
            except Exception as e:
                st.error(f"Error listing files from repository: {e}")

        except zipfile.BadZipFile:
            st.error("Invalid zip file.")
            repo_path = None
        except Exception as e:
            st.error(f"Error extracting zip file: {e}")
            repo_path = None


    st.header("2. Define Prompts")
    system_prompt = st.text_area("System Prompt (Optional)", key="system_prompt",
                                 help="Overall guidance for the AI agents. E.g., 'You are a master software architect.'")
    user_prompt = st.text_area("Your Research Prompt", key="user_prompt",
                               help="The main question or task for the AI. E.g., 'Analyze this codebase and suggest improvements for scalability.'")

    if st.button("Start Research", key="start_research_button"):
        if not get_current_user():
            st.error("Please login to start research.")
            return
        if not repo_path:
            st.error("Please upload a repository zip file first.")
            return
        if not user_prompt:
            st.error("Please enter a research prompt.")
            return

        st.info("Research process starting...")

        # TODO: Trigger CrewAI logic here
        # from app.crew_logic import run_crew  # Example
        # result = run_crew(repo_path, system_prompt, user_prompt)

        # Simulate output for now
        st.subheader("Research Plan (Large Steps)")
        st.markdown("- Step 1: Codebase Ingestion and Initial Analysis.")
        st.markdown("- Step 2: Deep Dive into Core Modules based on Prompt.")
        st.markdown("- Step 3: Architecture and Solution Design.")

        st.subheader("Detailed Steps (Example for Large Step 1)")
        st.markdown("  - Sub-step 1.1: Parsing file structures and dependencies.")
        st.markdown("  - Sub-step 1.2: Identifying key classes and functions.")

        st.subheader("Final Output")
        st.text_area("Research Results", "This is where the final research output from CrewAI will be displayed.", height=300, key="final_output")

if __name__ == "__main__":
    # To run this: streamlit run crewai_research_app/app.py (from the root directory of the project)
    # Ensure that crewai_research_app, config, utils are in python path.
    # This often means running from the parent directory of crewai_research_app.
    # For simplicity in Streamlit, we often put helper modules in the same dir or use relative paths carefully.

    # Adjusting current working directory for imports if necessary, or ensuring PYTHONPATH is set.
    # If script is in `crewai_research_app/app.py` and run from `crewai_research_app` parent:
    # sys.path.append(os.path.dirname(os.path.abspath(__file__))) # Adds current dir of app.py
    # sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')) # Adds parent dir

    main()
