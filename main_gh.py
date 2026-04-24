import asyncio
import time
import random
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
    print(f"📊 Currently tracking {len(products)} products.")
    
    for pid, product_data in products.items():
        try:
            url = product_data.get('url')
            old_price = product_data.get('last_price')
            target_price = product_data.get('target_price')
            highest_price = product_data.get('highest_price', old_price)
            list_price = product_data.get('list_price')
            title = product_data.get('title', "Product")
            
            # Add delay to avoid blocking
            await asyncio.sleep(random.uniform(2, 5))
            
            print(f"Checking {pid}...")
            new_title, new_price, new_list_price = scraper.scrape_product(url)
            
            if new_price is None:
                print(f"Skipping {pid} (Failed to scrape price or blocked)")
                continue
                
            # Update DB with all metadata
            database.update_product_metadata(pid, title=new_title, new_price=new_price, new_list_price=new_list_price)
            
            # Determine values for post
            post_title = new_title or title
            current_list_price = new_list_price or list_price
            
            # Check if it's a deal
            if utils.is_deal(old_price, new_price, target_price, highest_price, current_list_price):
                print(f"✅ Deal found for {pid}! New: ₹{new_price}")
                affiliate_link = utils.generate_affiliate_link(url)
                
                # Baseline for AI (old price or list price)
                baseline = old_price or current_list_price or new_price
                message = ai_content.generate_deal_post(post_title, baseline, new_price, affiliate_link)
                
                try:
                    await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message, parse_mode=ParseMode.MARKDOWN)
                    print(f"Post successful for {pid}")
                except Exception as e:
                    print(f"❌ Markdown Post failed for {pid}: {e}. Retrying without markdown...")
                    try:
                        await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message)
                        print(f"Post successful (no-markdown fallback) for {pid}")
                    except Exception as e2:
                        print(f"❌ Critical Post failure for {pid}: {e2}")
            else:
                print(f"ℹ️ No deal for {pid}. Current: ₹{new_price}")
        except Exception as e:
            print(f"❌ Unexpected error checking {pid}: {e}")

    print("🏁 GitHub Actions Tracker run complete.")

if __name__ == "__main__":
    asyncio.run(run_tracker())
