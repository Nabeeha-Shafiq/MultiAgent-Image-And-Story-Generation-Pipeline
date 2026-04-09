import os
from dotenv import load_dotenv

load_dotenv()

import time
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
IMAGE_MODE = os.getenv("IMAGE_MODE", "pollinations")  # mock | pollinations | comfyui
MAX_RETRIES = 3
MODEL_NAME = "llama-3.3-70b-versatile"
CHROMA_PERSIST_DIR = "./memory/chroma_db"
from datetime import datetime
now = datetime.now()
fallback_id = f"RUN_{now.day}_{now.strftime('%B').upper()}_{now.strftime('%I:%M%p').lstrip('0')}"
RUN_ID = os.getenv("RUN_ID", fallback_id)
OUTPUT_DIR = os.path.join(".", "outputs", RUN_ID)
MCP_SERVER_URL = "http://localhost:8000"
