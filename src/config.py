import os
from dotenv import load_dotenv
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment file if present (don't error if missing during tests)
dotenv_path = BASE_DIR / "env_files" / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)
else:
    load_dotenv()

ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY", "")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "")

# SenseVoice Configuration
SENSEVOICE_MODEL_PATH = os.getenv("SENSEVOICE_MODEL_PATH", str(BASE_DIR / "models" / "SenseVoiceSmall"))

# Audio Configuration
AUDIO_RATE = 16000
AUDIO_CHANNELS = 1
CHUNK = 1024
VAD_MODE = 3
NO_SPEECH_THRESHOLD = 1.0

# Logging Configuration
AUDIO_LOGS_DIR = BASE_DIR / "audio_logs"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
CONVERSATIONS_DIR = LOGS_DIR / "conversations"

# Ensure directories exist
for directory in [AUDIO_LOGS_DIR, OUTPUT_DIR, LOGS_DIR, CONVERSATIONS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)