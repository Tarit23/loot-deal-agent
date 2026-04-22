import os
from dotenv import load_dotenv

# Load env variables from .env file if it exists
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AMAZON_AFFILIATE_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "")
FLIPKART_AFFILIATE_ID = os.getenv("FLIPKART_AFFILIATE_ID", "rohanpouri")
EARNKARO_USER_ID = os.getenv("EARNKARO_USER_ID", "")
