from scraper import scrape_product

# Testing with a known live Amazon India URL
test_url = "https://www.amazon.in/dp/B0CHX1W1XY"
print(f"Testing scraper with URL: {test_url}")

title, price = scrape_product(test_url)

print(f"Scraped Title: {title}")
print(f"Scraped Price: {price}")

if price:
    print("✅ Scraper is working for live URLs!")
else:
    print("❌ Scraper failed to fetch price for a live URL. May need better headers or bot-bypass.")
