import requests
from bs4 import BeautifulSoup
import re

# Generic headers to mask simple scraping
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
}

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
    """Scrapes title and price from Amazon India."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        # Amazon might return 503 if blocked, just log it or retry in production
        if response.status_code != 200:
            print(f"Failed to fetch Amazon page: {response.status_code}")
            return None, None, None
            
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Title
        title_element = soup.find(id="productTitle")
        title = title_element.text.strip() if title_element else None
        
        # Price (Multiple selectors depending on Amazon's layout changes)
        price = None
        
        # Try the most reliable 'a-offscreen' within 'a-price' first
        price_container = soup.find("span", {"class": "a-price"})
        if price_container:
            offscreen = price_container.find("span", {"class": "a-offscreen"})
            if offscreen:
                price = clean_price(offscreen.text)
        
        # List Price (MRP) - often crossed out
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
                ("span", {"class": "a-offscreen"}),
                ("span", {"class": "a-color-price"})
            ]
            
            for tag, attrs in price_selectors:
                price_elem = soup.find(tag, attrs)
                if price_elem:
                    price = clean_price(price_elem.text)
                    if price:
                        break
                    
        return title, price, list_price
    except Exception as e:
        print(f"Error scraping Amazon: {e}")
        return None, None, None

def scrape_flipkart(url):
    """Scrapes title and price from Flipkart."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"Failed to fetch Flipkart page: {response.status_code}")
            return None, None, None
            
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
        
        return title, price, list_price
    except Exception as e:
        print(f"Error scraping Flipkart: {e}")
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
