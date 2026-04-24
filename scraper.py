import requests
from bs4 import BeautifulSoup
import re
import random
import time

# List of many user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0"
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Connection": "keep-alive"
    }

# Keep HEADERS for backward compatibility but encourage get_headers()
HEADERS = get_headers()

def expand_url(url):
    """Expands shortened URLs like amzn.to, fktr.in, bit.ly, etc."""
    # List of known shorteners that we should expand
    shorteners = ["amzn.to", "fktr.in", "bit.ly", "t.co", "tinyurl.com"]
    if any(s in url.lower() for s in shorteners):
        try:
            # Use a head request first to avoid downloading full content if possible
            response = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=5)
            return response.url
        except Exception as e:
            print(f"Error expanding URL {url}: {e}")
            # Fallback to get request if head fails
            try:
                response = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=10)
                return response.url
            except Exception as e2:
                print(f"Fallback expansion failed: {e2}")
    return url

def clean_amazon_url(url):
    """Cleans an Amazon URL to its base form (DP) or (GP)."""
    # Use regex to find the ASIN and keep only the necessary part
    match = re.search(r'(?:/dp/|/gp/product/)([A-Z0-9]{10})', url)
    if match:
        asin = match.group(1)
        return f"https://www.amazon.in/dp/{asin}/"
    return url

def clean_flipkart_url(url):
    """Cleans a Flipkart URL by keeping only the product path and PID."""
    if 'flipkart.com' in url:
        # Split by query params but keep pid if present
        base_url = url.split('?')[0]
        # Check if pid is in original URL
        if 'pid=' in url:
            pid = re.search(r'pid=([^&]+)', url)
            if pid:
                return f"{base_url}?pid={pid.group(1)}"
        return base_url
    return url

def clean_price(price_str):
    """Removes currency symbols and commas to return a float."""
    if not price_str:
        return None
    # Remove everything except digits and dots
    cleaned = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(cleaned)
    except ValueError:
        return None

def scrape_amazon(url):
    """Scrapes title and price from Amazon India with retries."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=get_headers(), timeout=15)
            
            if response.status_code == 503:
                print(f"Amazon 503 (Busy/Bot Detected). Attempt {attempt+1}/{max_retries}. Waiting...")
                time.sleep(random.uniform(5, 10))
                continue
            elif response.status_code != 200:
                print(f"❌ Failed to fetch Amazon page: {response.status_code}")
                return None, None, None
                
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Title
            title_element = (
                soup.find(id="productTitle") or 
                soup.find("span", {"id": "productTitle"}) or 
                soup.find("h1", {"id": "title"}) or
                soup.select_one(".product-title-word-break")
            )
            title = title_element.text.strip() if title_element else None
            
            # Price
            price = None
            price_container = soup.find("span", {"class": "a-price"})
            if price_container:
                offscreen = price_container.find("span", {"class": "a-offscreen"})
                if offscreen:
                    price = clean_price(offscreen.text)
            
            # List Price
            list_price_element = soup.find("span", {"class": "a-price a-text-price"})
            list_price = None
            if list_price_element:
                offscreen_list = list_price_element.find("span", {"class": "a-offscreen"})
                if offscreen_list:
                    list_price = clean_price(offscreen_list.text)

            if not price:
                # Fallback selectors
                price_selectors = [
                    ("span", {"class": "a-price-whole"}),
                    ("span", {"id": "priceblock_ourprice"}),
                    ("span", {"id": "priceblock_dealprice"}),
                    ("span", {"id": "priceblock_saleprice"}),
                    ("span", {"class": "a-offscreen"}),
                    ("span", {"class": "a-color-price"}),
                    ("span", {"class": "apexPriceToPay"}),
                    ("span", {"class": "a-size-medium a-color-price"})
                ]
                for tag, attrs in price_selectors:
                    price_elem = soup.find(tag, attrs)
                    if price_elem:
                        price = clean_price(price_elem.text)
                        if price: break
                        
            if price:
                return title, price, list_price
            else:
                print(f"Price not found on Amazon for {url}. Attempt {attempt+1}/{max_retries}")
                time.sleep(2)

        except Exception as e:
            print(f"Error scraping Amazon (Attempt {attempt+1}): {e}")
            time.sleep(random.uniform(2, 5))
            
    return None, None, None

def scrape_flipkart(url):
    """Scrapes title and price from Flipkart with retries."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=get_headers(), timeout=15)
            if response.status_code != 200:
                print(f"❌ Failed to fetch Flipkart page: {response.status_code}. Attempt {attempt+1}")
                time.sleep(2)
                continue
                
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Title
            title_element = soup.find("span", {"class": "B_NuCI"}) or soup.find("h1", {"class": "yhB1nd"})
            title = title_element.text.strip() if title_element else None
            
            # Price
            price_element = soup.find("div", {"class": "_30jeq3 _16Jk6d"}) or soup.find("div", {"class": "Nx9bqj CxhGGd"})
            price = clean_price(price_element.text) if price_element else None
            
            # List Price
            list_price_element = soup.find("div", {"class": "_3I9_re _2G6_Y9"}) or soup.find("div", {"class": "yYUr8F"})
            list_price = clean_price(list_price_element.text) if list_price_element else None
            
            if price:
                return title, price, list_price
            else:
                print(f"⚠️ Price not found on Flipkart for {url}. Attempt {attempt+1}")
                time.sleep(2)
        except Exception as e:
            print(f"Error scraping Flipkart (Attempt {attempt+1}): {e}")
            time.sleep(random.uniform(2, 5))
            
    return None, None, None

def scrape_product(url):
    """Routes the URL to the correct scraper."""
    domain = url.lower()
    if 'amazon' in domain:
        return scrape_amazon(url)
    elif 'flipkart' in domain:
        return scrape_flipkart(url)
    else:
        print(f"Unsupported URL domain: {url}")
        return None, None, None
