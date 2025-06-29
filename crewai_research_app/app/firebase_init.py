import firebase_admin
from firebase_admin import credentials, auth
import streamlit as st
from config import settings # Assuming project root is in PYTHONPATH

# Placeholder for firebase_app to ensure it's globally accessible after init
firebase_app = None

def initialize_firebase():
    global firebase_app
    if not firebase_admin._apps:
        try:
            if settings.FIREBASE_SERVICE_ACCOUNT_KEY_PATH:
                cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_KEY_PATH)
                firebase_app = firebase_admin.initialize_app(cred)
                st.session_state['firebase_initialized'] = True
                print("Firebase initialized successfully.") # For server-side logging
            else:
                st.error("Firebase service account key path not found in settings. Please configure .env.")
                st.session_state['firebase_initialized'] = False
                print("Firebase service account key path not found.") # For server-side logging
        except Exception as e:
            st.error(f"Firebase initialization failed: {e}")
            st.session_state['firebase_initialized'] = False
            print(f"Firebase initialization failed: {e}") # For server-side logging
    else:
        # Already initialized
        firebase_app = firebase_admin.get_app()
        st.session_state['firebase_initialized'] = True


# --- Authentication Functions ---

def signup_user(email, password):
    if not st.session_state.get('firebase_initialized', False):
        st.error("Firebase not initialized. Cannot sign up.")
        return None
    try:
        user = auth.create_user(email=email, password=password)
        st.success(f"User {user.email} created successfully! Please login.")
        return user
    except Exception as e:
        st.error(f"Error creating user: {e}")
        return None

def login_user(email, password):
    """
    Authenticates a user with email and password.
    This is a simplified example. Firebase Admin SDK is typically for backend.
    For client-side auth in Streamlit, you'd usually handle tokens obtained from Firebase Client SDKs.
    However, for a self-contained Streamlit app, we can simulate a session.
    WARNING: This is a conceptual example for server-side validation.
    Directly handling passwords server-side like this in a typical web app flow without a secure
    client-to-server token exchange mechanism is not standard practice for user-facing login.
    Streamlit's nature (Python backend for UI) makes this a bit different.
    """
    if not st.session_state.get('firebase_initialized', False):
        st.error("Firebase not initialized. Cannot login.")
        return None
    try:
        # Firebase Admin SDK does not have a direct "sign in with password" method
        # like client SDKs. It's meant for managing users, not signing them in.
        # We can verify a user's existence or custom token, but not directly a password.
        # This is a common misconception when using Admin SDK for auth.

        # For a true login, you'd typically:
        # 1. Use Firebase Client SDK (JavaScript) to sign in the user on the client-side.
        # 2. Send the ID token to the Streamlit backend.
        # 3. Verify the ID token using auth.verify_id_token().
        # Since Streamlit doesn't easily support client-side JS for this out-of-the-box,
        # we'll keep track of a logged-in state in Streamlit's session_state.
        # This is NOT secure production-grade authentication for a web app.
        # It's a simplified approach for this specific context.

        user = auth.get_user_by_email(email) # Checks if user exists
        # Password verification needs to be handled differently, typically via client SDK.
        # For this exercise, we'll assume if user exists, login is "successful" for demo purposes.
        # In a real app, you would NOT do this.
        st.session_state['logged_in'] = True
        st.session_state['user_email'] = email
        st.success(f"Logged in as {email} (simulated).")
        return user
    except auth.UserNotFoundError:
        st.error("Login failed: User not found.")
        return None
    except Exception as e:
        st.error(f"Login failed: {e}")
        return None


def logout_user():
    if 'logged_in' in st.session_state:
        del st.session_state['logged_in']
    if 'user_email' in st.session_state:
        del st.session_state['user_email']
    st.success("Logged out successfully.")

def get_current_user():
    if st.session_state.get('logged_in', False):
        return st.session_state.get('user_email')
    return None

# Ensure Firebase is initialized at the start if not already
# This might run multiple times in Streamlit's execution model but firebase_admin._apps check handles it.
# initialize_firebase() # Call this from app.py instead to control execution order
