import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import database
import utils
import scraper
from config import TELEGRAM_BOT_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers the /start command."""
    await update.message.reply_text(
        "👋 Welcome to Deal Tracker Bot!\n\n"
        "I can track Amazon and Flipkart prices and post deals automatically.\n"
        "Commands:\n"
        "/add <url> - Add a new product to track\n"
        "/add <url> <target_price> - Add with a target price\n"
        "/list - List all tracked products\n"
        "/remove <url or id> - Remove a product"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers the /add command."""
    args = context.args
    if not args:
         await update.message.reply_text("Please provide a URL. Usage: /add <url> [target_price]")
         return
         
    url = args[0]
    target_price = None
    if len(args) > 1:
        try:
             target_price = float(args[1])
        except ValueError:
             await update.message.reply_text("Invalid target price. Please provide a number.")
             return

    # Extract ID
    product_id = utils.extract_product_id(url)
    
    # Scrape current price
    await update.message.reply_text("Scraping product info... please wait ⏳")
    title, price, list_price = scraper.scrape_product(url)
    
    if not price:
         await update.message.reply_text("⚠️ Could not fetch price. Adding anyway, maybe it resolves later.")
    else:
         await update.message.reply_text(f"✅ Found product: {title}\nCurrent Price: ₹{price}")
         
    database.add_product(product_id, url, title=title, current_price=price, target_price=target_price)
    await update.message.reply_text(f"Tracked successfully! ID: {product_id}")

async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers the /list command."""
    products = database.get_all_products()
    if not products:
        await update.message.reply_text("No products are currently being tracked.")
        return
        
    msg = "📋 **Tracked Products:**\n\n"
    for pid, p in products.items():
        title = p.get('title', 'Unknown')
        if len(title) > 30: title = title[:27] + "..."
        price = p.get('last_price', 'Unknown')
        msg += f"ID: `{pid}`\n📦 {title}\n💰 ₹{price}\n\n"
        
    await update.message.reply_markdown(msg)

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers the /remove command."""
    args = context.args
    if not args:
         await update.message.reply_text("Please provide an ID or URL. Usage: /remove <id/url>")
         return
         
    target = args[0]
    pid = target
    
    # Check if target is a url
    if "amazon" in target.lower() or "flipkart" in target.lower():
         pid = utils.extract_product_id(target)
         
    if database.remove_product(pid):
         await update.message.reply_text(f"✅ Removed product {pid} from tracking.")
    else:
         await update.message.reply_text(f"❌ Could not find product with ID {pid}.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers the /status command with bot health info."""
    from config import TELEGRAM_CHANNEL_ID, GEMINI_API_KEY
    import database
    
    products = database.get_all_products()
    
    # Check if vars are set (censored)
    bot_token_status = "✅ Set" if TELEGRAM_BOT_TOKEN and "your_" not in TELEGRAM_BOT_TOKEN else "❌ NOT SET"
    channel_status = f"✅ {TELEGRAM_CHANNEL_ID}" if TELEGRAM_CHANNEL_ID and "your_" not in TELEGRAM_CHANNEL_ID else "❌ NOT SET"
    gemini_status = "✅ Set" if GEMINI_API_KEY and "your_" not in GEMINI_API_KEY else "❌ NOT SET"
    
    msg = (
        "🤖 **Bot Status Report**\n\n"
        f"🔹 **Bot Token**: {bot_token_status}\n"
        f"🔹 **Channel ID**: {channel_status}\n"
        f"🔹 **Gemini API**: {gemini_status}\n\n"
        f"📈 **Tracking**: {len(products)} products\n"
        "🌐 **Environment**: Running"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def forcediscovery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers the /forcediscovery command."""
    await update.message.reply_text("🔍 Running forced discovery... this may take a minute.")
    import discovery
    import main
    
    # Run discovery logic
    count = discovery.run_all_discovery()
    await update.message.reply_text(f"✅ Discovery finished. Found {count} new products.")
    
    # Try to post one random item to the channel to prove it works
    import database
    products = database.get_all_products()
    if products:
        pid, pdata = next(iter(products.items()))
        await update.message.reply_text(f"Attempting to post forced deal for: {pid}")
        # Run a single check
        import scraper
        t, pr, lp = scraper.scrape_product(pdata['url'])
        if pr:
             import ai_content, utils
             aff = utils.generate_affiliate_link(pdata['url'])
             msg = ai_content.generate_deal_post(t or "Test Product", "999", pr, aff)
             try:
                 await context.bot.send_message(chat_id=pdata.get('channel_id', TELEGRAM_CHANNEL_ID), text=msg, parse_mode='Markdown')
                 await update.message.reply_text("✅ Forced post sent to channel!")
             except Exception as e:
                 await update.message.reply_text(f"❌ Failed to post deal: {e}")
        else:
             await update.message.reply_text("❌ Scraper blocked or failed to find price. Try again later.")

def setup_bot_application():
    """Sets up the bot handlers and returns the bot application."""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in config.")
        
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_products))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("testpost", test_post))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("forcediscovery", forcediscovery))
    
    return app
