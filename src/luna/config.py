import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
CRM_URL = os.environ["CRM_URL"]
CRM_BEARER = os.environ["CRM_BEARER"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
