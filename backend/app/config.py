import os

from dotenv import load_dotenv


# Load environment variables from backend/.env
load_dotenv()


# ---------------------------------------------------------
# Application
# ---------------------------------------------------------

APP_NAME = "Smart Food Waste Management API"
APP_VERSION = "1.0.0"


# ---------------------------------------------------------
# JWT
# ---------------------------------------------------------

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "change_this_for_local_development",
)

JWT_ALGORITHM = "HS256"


# ---------------------------------------------------------
# Groq
# ---------------------------------------------------------

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY",
    "",
)


# ---------------------------------------------------------
# AI Configuration
# ---------------------------------------------------------

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)