import os
from dotenv import load_dotenv
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

dotenv_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=dotenv_path)

ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

if not ZHIPUAI_API_KEY:
    raise ValueError("ZHIPUAI_API_KEY not found in .env file")
if not ALPHAVANTAGE_API_KEY:
    raise ValueError("ALPHAVANTAGE_API_KEY not found in .env file")