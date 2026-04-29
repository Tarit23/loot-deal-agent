import requests
from bs4 import BeautifulSoup
import time
import random
import re
from urllib.parse import urljoin
import database
import utils
from scraper import get_headers

# A massive list of categories to ensure all types of products appear
ALL_CATEGORIES = [
    "mobiles", "smartwatches", "laptops", "tablets", "monitors", "storage devices", 
    "earbuds", "headphones", "bluetooth speakers", "power banks", "chargers",
    "shoes", "sneakers", "sports shoes", "casual shoes", "sandals",
    "watches", "sunglasses", "backpacks", "luggage", "wallets", "belts",
    "t-shirts", "jeans", "jackets", "activewear", "kurti", "sarees",
    "kitchen appliances", "cookware", "gas stoves", "water purifiers", "mixer grinders",
    "home decor", "bedsheets", "curtains", "clocks", "lamps", "furniture",
    "groceries", "dry fruits", "chocolates", "snacks", "detergents",
    "beauty products", "skincare", "perfumes", "makeup", "hair care", "trimmers",
    "fitness equipment", "dumbbells", "yoga mats", "protein powder",
    "toys", "board games", "action figures", "baby products", "diapers",
    "books", "stationery", "pens", "notebooks", "car accessories", "bike accessories",
    "tools", "drills", "home improvement", "smart home devices"
]

def get_random_categories(num=8):
    import random
    return random.sample(ALL_CATEGORIES, min(num, len(ALL_CATEGORIES)))

def discover_amazon():
    """Finds high-discount products on Amazon India using search filters."""
    print("Running Amazon Discovery...")
    discovered_urls = []
    
    for category in get_random_categories():
        # Search URL with 50% or more discount filter (rh=p_8_50-)
        search_url = f"https://www.amazon.in/s?k={category}&rh=p_8_50-"
        
        for attempt in range(2):
            try:
                response = requests.get(search_url, headers=get_headers(), timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")
                    # Find product cards
                    items = soup.find_all("div", {"data-component-type": "s-search-result"})
                    
                    for item in items[:10]:
                        link_tag = item.find("a", {"class": "a-link-normal s-no-outline"})
                        if link_tag and 'href' in link_tag.attrs:
                            full_url = urljoin("https://www.amazon.in", link_tag['href'])
                            if '/dp/' in full_url:
                                clean_url = full_url.split('?')[0]
                                discovered_urls.append(clean_url)
                    break
                print(f"Amazon search attempt {attempt+1} failed: {response.status_code}")
                time.sleep(5)
            except Exception as e:
                print(f"Error in Amazon attempt {attempt+1}: {e}")
                time.sleep(5)
            
    return list(set(discovered_urls))

def discover_flipkart():
    """Finds high-discount products on Flipkart using search filters."""
    print("Running Flipkart Discovery...")
    discovered_urls = []
    
    for category in get_random_categories():
        # Search URL with 50% or more discount filter
        search_url = f"https://www.flipkart.com/search?q={category}&p[]=facets.discount_range%3D50%25%2Bor%2Bmore"
        
        for attempt in range(2):
            try:
                response = requests.get(search_url, headers=get_headers(), timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")
                    links = soup.find_all("a", href=re.compile(r'/p/'))
                    for link in links[:10]:
                        if 'href' in link.attrs:
                            full_url = urljoin("https://www.flipkart.com", link['href'])
                            clean_url = full_url.split('?')[0]
                            discovered_urls.append(clean_url)
                    break
                print(f"Flipkart search attempt {attempt+1} failed: {response.status_code}")
                time.sleep(5)
            except Exception as e:
                print(f"Error in Flipkart attempt {attempt+1}: {e}")
                time.sleep(5)
            
    return list(set(discovered_urls))

def run_all_discovery():
    """Runs discovery on all platforms and adds new products to the database."""
    all_discovered = []
    
    # Run Amazon
    amz_urls = discover_amazon()
    all_discovered.extend(amz_urls)
    print(f"Discovered {len(amz_urls)} products from Amazon.")
    
    # Run Flipkart
    flp_urls = discover_flipkart()
    all_discovered.extend(flp_urls)
    print(f"Discovered {len(flp_urls)} products from Flipkart.")
    
    count = 0
    for url in all_discovered:
        product_id = utils.extract_product_id(url)
        # Only add if not already tracked
        if not database.get_product(product_id):
            database.add_product(product_id, url)
            count += 1
            
    print(f"Added {count} NEW products to watchlist.")
    return count

if __name__ == "__main__":
    # Test run
    database.init_db()
    run_all_discovery()
