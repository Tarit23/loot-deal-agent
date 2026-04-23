import asyncio
import time
from telegram import Bot
from telegram.constants import ParseMode

import database
import scraper
import utils
import ai_content
import discovery
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

async def run_tracker():
    print("🚀 Starting GitHub Actions Deal Tracker...")
    
    # Initialize DB
    database.init_db()
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        return

    # Initialize Bot (Stateless)
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # 1. Run Discovery
    print("🔍 Running Discovery...")
    try:
        discovery.run_all_discovery()
    except Exception as e:
        print(f"Error in discovery: {e}")

    # 2. Run Price Checks
    print("💰 Checking Prices and Posting Deals...")
    products = database.get_all_products()
    
    for pid, product_data in products.items():
        url = product_data.get('url')
        old_price = product_data.get('last_price')
        target_price = product_data.get('target_price')
        highest_price = product_data.get('highest_price', old_price)
        list_price = product_data.get('list_price')
        title = product_data.get('title', "Product")
        
        # Add delay to avoid blocking
        time.sleep(2)
        
        print(f"Scraping {pid}...")
        new_title, new_price, new_list_price = scraper.scrape_product(url)
        
        if new_price is None:
            print(f"Skipping {pid} (Failed to scrape price)")
            continue
            
        # Update DB
        database.update_product_price(pid, new_price)
        if new_list_price and not list_price:
             database.add_product(pid, url, list_price=new_list_price)
        
        # Check if it's a deal
        if utils.is_deal(old_price, new_price, target_price, highest_price, new_list_price or list_price):
            print(f"✅ Deal found for {pid}! Posting...")
            affiliate_link = utils.generate_affiliate_link(url)
            message = ai_content.generate_deal_post(new_title or title, old_price or (new_list_price or list_price), new_price, affiliate_link)
            
            try:
                await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message, parse_mode=ParseMode.MARKDOWN)
                print(f"Post successful for {pid}")
            except Exception as e:
                print(f"Failed to post {pid}: {e}")
        else:
            print(f"No deal for {pid}. Current: {new_price}")

    print("✅ Tracker run complete.")

if __name__ == "__main__":
    asyncio.run(run_tracker())
