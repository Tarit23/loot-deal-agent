import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHANNEL_ID")

if token:
    print(f"Token length: {len(token)}")
    print(f"Token starts with: {token[:5]}")
    print(f"Token ends with: {token[-5:]}")
else:
    print("TELEGRAM_BOT_TOKEN is missing!")

if chat_id:
    print(f"Chat ID length: {len(chat_id)}")
    print(f"Chat ID starts with: {chat_id[:4]}")
    print(f"Chat ID value (masked-ish): {chat_id}")
else:
    print("TELEGRAM_CHANNEL_ID is missing!")
