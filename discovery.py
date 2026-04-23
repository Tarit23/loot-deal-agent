import requests
from bs4 import BeautifulSoup
import time
import random
import re
from urllib.parse import urljoin
import database
import utils
from scraper import get_headers

# Categories to search for discoveries
CATEGORIES = ["mobiles", "electronics", "laptops", "shoes", "watches", "kitchen", "home decor", "headphones"]

def discover_amazon():
    """Finds high-discount products on Amazon India using search filters."""
    print("Running Amazon Discovery...")
    discovered_urls = []
    
    for category in CATEGORIES:
        # Search URL with 50% or more discount filter (rh=p_8_50-)
        search_url = f"https://www.amazon.in/s?k={category}&rh=p_8_50-"
        
        try:
            response = requests.get(search_url, headers=get_headers(), timeout=15)
            if response.status_code != 200:
                print(f"Amazon search failed for {category}: {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.content, "html.parser")
            # Find product cards
            # Amazon search results usually have class 's-result-item'
            items = soup.find_all("div", {"data-component-type": "s-search-result"})
            
            for item in items[:10]: # Limit to top 10 products per category
                link_tag = item.find("a", {"class": "a-link-normal s-no-outline"})
                if link_tag and 'href' in link_tag.attrs:
                    full_url = urljoin("https://www.amazon.in", link_tag['href'])
                    # Clean the URL to be a standard product URL
                    if '/dp/' in full_url:
                        clean_url = full_url.split('?')[0]
                        discovered_urls.append(clean_url)
            
            # Rate limiting delay
            time.sleep(random.uniform(2, 5))
            
        except Exception as e:
            print(f"Error in Amazon discovery for {category}: {e}")
            
    return list(set(discovered_urls))

def discover_flipkart():
    """Finds high-discount products on Flipkart using search filters."""
    print("Running Flipkart Discovery...")
    discovered_urls = []
    
    for category in CATEGORIES:
        # Search URL with 50% or more discount filter
        search_url = f"https://www.flipkart.com/search?q={category}&p[]=facets.discount_range%3D50%25%2Bor%2Bmore"
        
        try:
            response = requests.get(search_url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                print(f"Flipkart search failed for {category}: {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find product links
            # Flipkart uses different structures for different categories
            # One common one is <a> tags with 'VpYofL' or similar, but checking for 'p/' in href is safer
            links = soup.find_all("a", href=re.compile(r'/p/'))
            
            for link in links[:10]: # Limit to top 10
                if 'href' in link.attrs:
                    full_url = urljoin("https://www.flipkart.com", link['href'])
                    # Clean to base product URL
                    clean_url = full_url.split('?')[0]
                    # We might need the 'pid' which is in params, so keep the ID relevant parts if needed
                    # For simplicity in MVP, we track the base product
                    discovered_urls.append(clean_url)
            
            # Rate limiting delay
            time.sleep(random.uniform(2, 5))
            
        except Exception as e:
            print(f"Error in Flipkart discovery for {category}: {e}")
            
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
