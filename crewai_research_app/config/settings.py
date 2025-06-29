import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_KEY_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
# Example: FIREBASE_SERVICE_ACCOUNT_KEY_PATH = "path/to/your/firebase-service-account-key.json"

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Other settings
TEMP_UPLOAD_DIR_NAME = "temp_uploads"
# Path should be relative to the project root.
# __file__ is crewai_research_app/config/settings.py
# os.path.dirname(__file__) is crewai_research_app/config
# os.path.join(os.path.dirname(__file__), '..') is crewai_research_app (project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEMP_UPLOAD_PATH = os.path.join(PROJECT_ROOT, TEMP_UPLOAD_DIR_NAME)

# Ensure the temp directory exists
if not os.path.exists(TEMP_UPLOAD_PATH):
    os.makedirs(TEMP_UPLOAD_PATH)

# Logging Configuration (Basic)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
