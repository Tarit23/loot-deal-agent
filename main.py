import time
import asyncio
import schedule
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram.ext import ApplicationBuilder
from telegram.constants import ParseMode

import database
import scraper
import utils
import ai_content
import discovery
from bot import setup_bot_application
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is alive and tracking deals!")

    def log_message(self, format, *args):
        # Silent logging for health checks
        return

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Health check server running on port {port}")
    server.serve_forever()

async def post_deal(app, title, old_price, new_price, product_url):
    """Generates content and posts the deal to the Telegram channel."""
    if not TELEGRAM_CHANNEL_ID or TELEGRAM_CHANNEL_ID == "@your_channel_username":
        print("Telegram Channel ID not set. Cannot post deal.")
        return
        
    # Generate Affiliate link
    affiliate_link = utils.generate_affiliate_link(product_url)
    
    # Generate AI content
    print("Generating AI post content...")
    message = ai_content.generate_deal_post(title, old_price, new_price, affiliate_link)
    
    # Post to channel
    print(f"Posting to channel {TELEGRAM_CHANNEL_ID}...")
    try:
        await app.bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        print("Deal posted successfully!")
    except Exception as e:
        print(f"Failed to post to telegram channel: {e}")

async def check_prices_async(bot_instance):
    """Core logic to check prices and alert if deals are found."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running scheduled price check...")
    products = database.get_all_products()
    
    for pid, product_data in products.items():
        url = product_data.get('url')
        old_price = product_data.get('last_price')
        target_price = product_data.get('target_price')
        highest_price = product_data.get('highest_price', old_price)
        list_price = product_data.get('list_price')
        title = product_data.get('title', "Product")
        
        # Add slight delay to avoid bot detection
        await asyncio.sleep(2)
        
        print(f"Scraping {pid}...")
        new_title, new_price, new_list_price = scraper.scrape_product(url)
        
        if new_price is None:
            print(f"Skipping {pid} (Failed to scrape price)")
            continue
            
        # Update everything in DB: price, title, and list price
        database.update_product_metadata(pid, title=new_title, new_price=new_price, new_list_price=new_list_price)
        
        # Determine current title for post (prefer new title if found)
        post_title = new_title or title
        current_list_price = new_list_price or list_price
        
        # Check Deal
        if utils.is_deal(old_price, new_price, target_price, highest_price, current_list_price):
            print(f"✅ Deal found for {pid}! New: ₹{new_price}")
            
            # Generate Affiliate link
            affiliate_link = utils.generate_affiliate_link(url)
            
            # Generate AI content (Fallback to old price if old_price is None, use list_price as baseline)
            baseline = old_price or current_list_price or new_price
            message = ai_content.generate_deal_post(post_title, baseline, new_price, affiliate_link)
            
            try:
                print(f"Attempting to post to {TELEGRAM_CHANNEL_ID}...")
                await bot_instance.send_message(
                    chat_id=TELEGRAM_CHANNEL_ID,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN
                )
                print("Post successful!")
            except Exception as e:
                print(f"❌ Post error for {pid}: {e}")
                # Try one more time without Markdown in case AI generated bad markdown
                try:
                    await bot_instance.send_message(
                        chat_id=TELEGRAM_CHANNEL_ID,
                        text=message
                    )
                    print("Post successful (without Markdown fallback)!")
                except Exception as e2:
                    print(f"❌ Critical Post failure: {e2}")
        else:
            print(f"No deal for {pid}. Target: {target_price}, Current: {new_price}")

async def run_discovery_job(context):
    try:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running automated product discovery...")
        count = discovery.run_all_discovery()
        print(f"Discovery finished. Added {count} new products.")
    except Exception as e:
        print(f"Error in automated discovery: {e}")

async def run_price_check_job(context):
    """Job wrapper for price checks."""
    try:
        await check_prices_async(context.bot)
    except Exception as e:
        print(f"Error in scheduled price check: {e}")

if __name__ == '__main__':
    print("Starting Resilient Loot Deal Tracker with JobQueue...")
    
    # Initialize DB
    database.init_db()
    
    while True:
        try:
            # We import here to allow reloads if needed, though with JobQueue it's less necessary
            from bot import setup_bot_application
            app = setup_bot_application()
            
            # Get the JobQueue
            job_queue = app.job_queue
            
            # Schedule the price checks (Every 2 hours)
            job_queue.run_repeating(run_price_check_job, interval=7200, first=10)
            
            # Schedule the discovery (Every 6 hours)
            job_queue.run_repeating(run_discovery_job, interval=21600, first=30)
            
            print("Price checking (2H) and Discovery (6H) scheduled via JobQueue.")
            
            # Start Render Health Check Server
            threading.Thread(target=run_health_server, daemon=True).start()
            
            # Self-Ping for Render/Cloud persistence
            def self_ping():
                import requests
                time.sleep(15)
                port = os.environ.get("PORT", "10000")
                url = f"http://localhost:{port}"
                while True:
                    try:
                        requests.get(url, timeout=5)
                    except:
                        pass
                    time.sleep(600)

            threading.Thread(target=self_ping, daemon=True).start()

            # Startup Notification
            async def send_startup_msg(application):
                 try:
                     await application.bot.send_message(
                         chat_id=TELEGRAM_CHANNEL_ID, 
                         text="🚀 **Loot Agent is now Online!**\nMonitoring deals 24/7...",
                         parse_mode=ParseMode.MARKDOWN
                     )
                 except Exception as e:
                     print(f"Startup notification failed: {e}. Check if bot is admin in the channel.")

            # Add the startup message to the loop
            # app.post_init = send_startup_msg # PTB way to do things after initialization
            
            # Start bot polling
            print("Bot is polling. Running 24/7 Watchdog...")
            app.run_polling()
            
        except Exception as e:
            print(f"CRITICAL: Bot crashed with error: {e}")
            print("Restarting in 10 seconds...")
            time.sleep(10)
