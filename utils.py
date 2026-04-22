import re
import urllib.parse
import datetime
from urllib.parse import urlparse, parse_qs, urlencode
from config import AMAZON_AFFILIATE_TAG, FLIPKART_AFFILIATE_ID, EARNKARO_USER_ID

def generate_affiliate_link(url: str) -> str:
    """
    Converts a standard product URL into an affiliate URL.
    Handles Amazon Tag and EarnKaro (Flipkart/Others) format.
    """
    # 1. Expand it first (in case it's a short link)
    from scraper import expand_url, clean_amazon_url, clean_flipkart_url
    url = expand_url(url)
    
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    
    # --- AMAZON LOGIC ---
    if 'amazon' in domain:
        # Clean the URL first
        clean_url = clean_amazon_url(url)
        # Add tag
        tag = AMAZON_AFFILIATE_TAG or "bfsgdahgoiy-21"
        if '?' in clean_url:
            return f"{clean_url}&tag={tag}"
        else:
            return f"{clean_url}?tag={tag}"
    
    # --- FLIPKART LOGIC (EARNKARO) ---
    elif 'flipkart.com' in domain:
        # Clean URL (base product link)
        clean_url = clean_flipkart_url(url)
        
        # User provided format: affid=rohanpouri&affExtParam2=5210268
        affid = FLIPKART_AFFILIATE_ID or "rohanpouri"
        userid = EARNKARO_USER_ID or "5210268"
        
        # affExtParam1 usually contains a timestamp for tracking
        today = datetime.datetime.now().strftime("%Y%m%d")
        timestamp_param = f"ENKR{today}A{userid}" # Simplified simulation
        
        separator = '&' if '?' in clean_url else '?'
        affiliate_params = (
            f"affid={affid}"
            f"&affExtParam1={timestamp_param}"
            f"&affExtParam2={userid}"
        )
        return f"{clean_url}{separator}{affiliate_params}"
    
    # --- FALLBACK: EARNKARO PROFIT LINK (For other stores) ---
    elif EARNKARO_USER_ID:
        # For Myntra, AJIO, etc., use the EarnKaro redirector
        encoded_url = urllib.parse.quote(url)
        return f"https://topdeal.in/c/{EARNKARO_USER_ID}/?url={encoded_url}"
        
    return url

def extract_product_id(url: str) -> str:
    """
    Extracts a unique identifier from an e-commerce URL.
    """
    # Simple logic: extract ASIN for amazon
    if 'amazon' in url.lower():
        match = re.search(r'/dp/([A-Z0-9]{10})', url)
        if not match:
             match = re.search(r'/gp/product/([A-Z0-9]{10})', url)
        if match:
            return f"amz_{match.group(1)}"
            
    # Simple logic for flipkart (the 'pid' query param)
    elif 'flipkart' in url.lower():
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        if 'pid' in query:
             return f"flp_{query['pid'][0]}"
             
    # Fallback to a hash of the URL if not easily parseable
    import hashlib
    return "oth_" + hashlib.md5(url.encode()).hexdigest()[:10]

def is_deal(old_price: float, new_price: float, target_price: float = None, highest_price: float = None, list_price: float = None) -> bool:
    """
    Deal detection logic:
    1. Returns True if price dropped by >= 20% compared to highest known price.
    2. OR Returns True if new_price <= target_price.
    3. OR (Loot Discovery) Returns True if current price is >= 40% lower than MRP (list_price).
    """
    if new_price is None:
        return False
        
    # Check target price first
    if target_price is not None and new_price <= target_price:
        return True
        
    # Check massive discount from list_price (Loot Discovery Trigger)
    if list_price is not None and list_price > 0:
        loot_drop = ((list_price - new_price) / list_price) * 100
        if loot_drop >= 45.0: # 45% off is usually 'Loot' territory for generic categories
            return True
        
    # Price drop logic (compare against the Highest Price seen so far)
    baseline_price = highest_price if highest_price is not None else old_price
    
    if baseline_price is not None and baseline_price > 0:
        drop_percentage = ((baseline_price - new_price) / baseline_price) * 100
        if drop_percentage >= 20.0:
            return True
            
    return False
