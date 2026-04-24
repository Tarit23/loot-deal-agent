import json
import os

DB_FILE = 'products.json'

def init_db():
    """Initializes the database file if it doesn't exist."""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({"products": {}}, f, indent=4)

def load_data():
    """Loads product data from the database with basic validation."""
    init_db()
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            if "products" not in data:
                return {"products": {}}
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"Warning: {DB_FILE} is corrupt or missing. Resetting...")
        return {"products": {}}

def save_data(data):
    """Saves product data to the database atomically."""
    temp_file = DB_FILE + ".tmp"
    try:
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=4)
        # Atomic swap
        os.replace(temp_file, DB_FILE)
    except Exception as e:
        print(f"❌ Error saving database: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)

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

def update_product_metadata(product_id, title=None, new_price=None, new_list_price=None):
    """Updates multiple fields of a product and tracks the highest price seen."""
    data = load_data()
    if product_id in data["products"]:
        product = data["products"][product_id]
        
        if title:
            product["title"] = title
            
        if new_price is not None:
            # update highest price if needed
            highest = product.get("highest_price")
            if highest is None or new_price > highest:
                product["highest_price"] = new_price
            product["last_price"] = new_price
            
        if new_list_price is not None:
            product["list_price"] = new_list_price
            
        save_data(data)
        return True
    return False
