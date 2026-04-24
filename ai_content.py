import google.generativeai as genai
from config import GEMINI_API_KEY

def generate_deal_post(title, old_price, new_price, affiliate_link):
    """
    Uses Google Gemini free tier to generate an engaging Telegram deal post.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        # Fallback if API key is not set
        return (
            "PRICE DROP ALERT!\n\n"
            f"Product: {title}\n"
            f"Old Price: {old_price}\n"
            f"New Price: {new_price}!!\n\n"
            f"Grab the Deal: {affiliate_link}\n\n"
            "#deals #loot"
        )
        
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Try different model name variations
        model_names = ['gemini-flash-latest', 'gemini-pro-latest', 'gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
        response = None
        
        for mname in model_names:
            try:
                model = genai.GenerativeModel(mname)
                prompt = (
                    f"Write a high-converting Telegram deal post with urgency and short format. "
                    f"Include emojis and relevant hashtags. "
                    f"Product: {title}\n"
                    f"Previous Price: {old_price}\n"
                    f"Current Deal Price: {new_price}\n"
                    f"Link to buy: {affiliate_link}\n"
                    f"\nKeep it under 150 words. Do not use placeholders, use the exact link provided. Keep the markdown link format Telegram friendly."
                )
                response = model.generate_content(prompt)
                if response:
                    return response.text
            except Exception as model_err:
                print(f"Model {mname} failed: {model_err}")
                continue
        
        if not response:
            raise Exception("All Gemini models failed.")
            
    except Exception as e:
        print(f"Error generating AI message: {e}")
        # Fallback message
        return (
            "PRICE DROP ALERT!\n\n"
            f"Product: {title}\n"
            f"Price dropped to {new_price} (was {old_price})\n\n"
            f"Buy here: {affiliate_link}\n\n"
            "#shopping #deals"
        )
