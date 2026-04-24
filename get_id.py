import asyncio
import requests
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def get_updates():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    print(f"Fetching updates from: {url}")
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if not data.get("ok"):
            print(f"Error: {data}")
            return

        results = data.get("result", [])
        if not results:
            print("No recent updates found. Please send /status to the bot in Telegram!")
            return

        print("\n--- Recent Bot Activity ---")
        for update in results:
            if "message" in update:
                msg = update["message"]
                chat = msg["chat"]
                print(f"Chat: {chat.get('title', 'Private')} | ID: {chat['id']} | Type: {chat['type']} | Text: {msg.get('text', 'No text')}")
            elif "my_chat_member" in update:
                member = update["my_chat_member"]
                chat = member["chat"]
                print(f"ADDED TO CHAT: {chat.get('title', 'Unknown')} | ID: {chat['id']} | Status: {member['new_chat_member']['status']}")
        print("---------------------------\n")

    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(get_updates())
