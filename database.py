import json
import os

DB_FILE = 'products.json'

def init_db():
    """Initializes the database file if it doesn't exist."""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({"products": {}}, f, indent=4)

def load_data():
    """Loads product data from the database."""
    init_db()
    with open(DB_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"products": {}}

def save_data(data):
    """Saves product data to the database."""
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def add_product(product_id, url, title=None, current_price=None, target_price=None, list_price=None):
    """Adds or updates a product in the database."""
    data = load_data()
    
    if product_id not in data["products"]:
        data["products"][product_id] = {
            "url": url,
            "title": title or "Pending Title...",
            "last_price": current_price,
            "target_price": target_price,
            "highest_price": current_price,
            "list_price": list_price
        }
    else:
        # Update existing
        if title: data["products"][product_id]["title"] = title
        if current_price is not None:
             data["products"][product_id]["last_price"] = current_price
        if target_price is not None:
             data["products"][product_id]["target_price"] = target_price
        if list_price is not None:
             data["products"][product_id]["list_price"] = list_price
             
    save_data(data)

def get_product(product_id):
    """Retrieves a single product."""
    data = load_data()
    return data["products"].get(product_id)

def get_all_products():
    """Retrieves all tracked products."""
    data = load_data()
    return data["products"]

def remove_product(product_id):
    """Removes a product from tracking."""
    data = load_data()
    if product_id in data["products"]:
        del data["products"][product_id]
        save_data(data)
        return True
    return False

def update_product_price(product_id, new_price):
    """Updates the price of a product and tracks the highest price seen."""
    data = load_data()
    if product_id in data["products"]:
        product = data["products"][product_id]
        old_price = product.get("last_price")
        
        # update highest price if needed
        highest = product.get("highest_price")
        if highest is None or (new_price is not None and new_price > highest):
            product["highest_price"] = new_price
            
        product["last_price"] = new_price
        save_data(data)
        return True
    return False
