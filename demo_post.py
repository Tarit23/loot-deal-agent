import asyncio
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
import ai_content
import utils

async def send_demo():
    print("Starting Demo Post...")
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        print("Error: Bot token or Channel ID missing.")
        return
        
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Fake product data for demo
    title = "Apple iPhone 15 (128 GB) - Blue"
    old_price = 79900.0
    new_price = 39990.0 # 50% drop
    product_url = "https://www.amazon.in/dp/B0C781GC3V"
    affiliate_link = utils.generate_affiliate_link(product_url)
    
    print("Generating AI content...")
    message = ai_content.generate_deal_post(title, old_price, new_price, affiliate_link)
    
    print(f"Sending to channel {TELEGRAM_CHANNEL_ID}...")
    try:
        await app.bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID, 
            text=message, 
            parse_mode=ParseMode.MARKDOWN
        )
        print("Demo post sent successfully! Check your channel.")
    except Exception as e:
        print(f"Failed to send: {e}")

if __name__ == "__main__":
    asyncio.run(send_demo())
