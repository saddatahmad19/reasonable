import streamlit as st

def create_sidebar_nav():
    """Creates the standard sidebar navigation for the app."""
    with st.sidebar:
        st.header("Navigation")
        # Get the current page filename
        current_page = st.session_state.get('current_page', 'main.py')

        st.page_link("main.py", label="🏠 Main", disabled=(current_page == "main.py"))
        st.page_link("pages/TaskProcessor.py", label="📝 Task Processor", disabled=(current_page == "pages/TaskProcessor.py"))
        st.page_link("pages/Chat.py", label="💬 Chat", disabled=(current_page == "pages/Chat.py"))
        st.page_link("pages/Config.py", label="⚙️ Config", disabled=(current_page == "pages/Config.py"))

def set_current_page_session_state():
    """
    Sets the current page in session state.
    This function is intended to be called at the beginning of each page script.
    It uses st.query_params to infer the current page, which is a bit of a hack
    as Streamlit doesn't directly expose the current page's script path.
    A more robust way might be needed if this proves unreliable.
    Alternatively, each page can explicitly set its own identifier.
    For now, we rely on the fact that st.page_link navigates to ?page=pagename
    and Streamlit's multipage app structure.

    A simpler approach for now: each page will call this and identify itself.
    This function is not strictly necessary if each page calls create_sidebar_nav
    and we manually determine the 'current_page' or pass it.

    Let's simplify: The `create_sidebar_nav` will take the current page identifier as an argument.
    Each page will be responsible for passing its identifier.
    """
    pass # This function will be removed or rethought.

# Revised approach for create_sidebar_nav:
# Each page will call `create_sidebar_nav(current_page_identifier)`

def create_sidebar_nav_v2(current_page_identifier: str):
    """
    Creates the standard sidebar navigation for the app.
    Args:
        current_page_identifier: A string identifying the current page,
                                 e.g., "main", "task_processor", "chat", "config".
    """
    with st.sidebar:
        st.header("Navigation")
        st.page_link("main.py", label="🏠 Main", disabled=(current_page_identifier == "main"))
        st.page_link("pages/TaskProcessor.py", label="📝 Task Processor", disabled=(current_page_identifier == "task_processor"))
        st.page_link("pages/Chat.py", label="💬 Chat", disabled=(current_page_identifier == "chat"))
        st.page_link("pages/Config.py", label="⚙️ Config", disabled=(current_page_identifier == "config"))

# For simplicity and directness, I'll use v2.
# Each page will need a small modification to pass its identifier.
# Example usage in main.py: create_sidebar_nav_v2("main")
# Example usage in pages/Chat.py: create_sidebar_nav_v2("chat")
