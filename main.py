import time
import asyncio
import schedule
import threading
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
        
        # Add slight delay
        time.sleep(2)
        
        print(f"Scraping {pid}...")
        new_title, new_price, new_list_price = scraper.scrape_product(url)
        
        if new_price is None:
            print(f"Skipping {pid} (Failed to scrape price)")
            continue
            
        # Update price and list price in DB
        database.update_product_price(pid, new_price)
        if new_list_price:
             database.add_product(pid, url, list_price=new_list_price)
        
        # Check Deal
        if utils.is_deal(old_price, new_price, target_price, highest_price, new_list_price or list_price):
            print(f"Deal found for {pid}! New: {new_price}")
            # Ensure we use the bot instance correctly
            affiliate_link = utils.generate_affiliate_link(url)
            message = ai_content.generate_deal_post(title, old_price or (new_list_price or list_price), new_price, affiliate_link)
            try:
                await bot_instance.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                print(f"Post error: {e}")
        else:
            print(f"No deal for {pid}. Target: {target_price}, Current: {new_price}")

def job_check(bot_instance):
    """Synchronous job wrapper."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(check_prices_async(bot_instance))

def job_discovery():
    """Scheduled job to find new loot deals."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running automated product discovery...")
    discovery.run_all_discovery()

if __name__ == '__main__':
    print("Starting Telegram Deal Tracker bot & Scheduler MVP...")
    
    # Initialize DB
    database.init_db()
    
    try:
        app = setup_bot_application()
    except ValueError as e:
        print(f"Error: {e}. Please check your .env file.")
        exit(1)
        
    # Schedule the price checks (Every 2 hours)
    schedule.every(2).hours.do(job_check, app.bot)
    
    # Schedule the discovery (Every 6 hours)
    schedule.every(6).hours.do(job_discovery)
    print("Price checking (2H) and Discovery (6H) scheduled.")
    
    # Initial manual run trigger
    print("Running initial discovery and price check...")
    threading.Thread(target=job_discovery).start()
    threading.Thread(target=lambda: job_check(app.bot)).start()
    
    # In a real production setup, bot polling and scheduler would run in separate threads
    # or use Asyncio schedule tools to be non-blocking. 
    # For MVP, we run the scheduler in background thread or we can run schedule via a loop.
    import threading
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)

    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()
    
    # Start Render Health Check Server
    h = threading.Thread(target=run_health_server, daemon=True)
    h.start()
    
    # Start bot polling (blocking)
    print("Bot is polling. Send commands in Telegram!")
    app.run_polling()
