# Price & Deal Tracker AI Agent MVP

A fully automated Telegram bot system that tracks e-commerce product prices, detects deals, and automatically posts high-converting, AI-generated deal messages using your affiliate links.

## Overview
- Scrapes prices from **Amazon** and **Flipkart**.
- Stores data locally in `products.json`.
- Detects drops (>= 20% compared to highest known price) or drops below a custom target price.
- Uses **Google Gemini API (Free)** to write engaging deal alerts.
- Runs a Telegram bot accepting commands like `/start`, `/add`, `/list`, and `/remove`.
- Includes a scheduler to run checks every 2 hours.

## Setup Instructions

**1. Create a Telegram Bot:**
- Open Telegram and message `@BotFather`.
- Send `/newbot`, choose a name and username.
- Copy your `BOT_TOKEN`.

**2. Setup a Telegram Channel:**
- Create a public/private Telegram channel.
- Add your newly created Bot as an **Admin** to that channel.
- Make note of your channel username (e.g., `@mylootdeals`).

**3. Get Gemini API Key:**
- Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
- Create a new API key.

**4. Install Dependencies:**
```sh
pip install -r requirements.txt
```

**5. Environment Variables:**
- Copy `.env.example` and name it `.env`
- Fill in the required values:
```env
TELEGRAM_BOT_TOKEN="your_bot_token"
TELEGRAM_CHANNEL_ID="@your_channel_username" # Or the numeric ID
GEMINI_API_KEY="your_gemini_api_key_here"
AMAZON_AFFILIATE_TAG="your_tag-21"
FLIPKART_AFFILIATE_ID="your_flp_id"
```

## Running the MVP

Start the application:
```sh
python main.py
```

The system will now wait for your commands. 
Go to Telegram and start your bot:
- Type `/add https://www.amazon.in/dp/...` to start tracking a product.
- It will scrape the price and store tracking data in `products.json`.
- The background threaded scheduler will re-check prices every 2 hours. If a deal is found, an AI-generated message will be posted to your channel alongside an affiliate link!

## Developer Notes
- E-commerce scrapers are fragile. `requests` and `BeautifulSoup` are simple but can be blocked easily. If it starts failing, explore using `Selenium` or `Playwright`.
- The affiliate link logic is foundational. You can expand `utils.py` to correctly map missing tracking parameters for advanced affiliate networks.
