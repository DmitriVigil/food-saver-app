import os
import time
import requests
import base64
from dotenv import load_dotenv
from database import init_db, save_products

load_dotenv()

class KrogerClient:
    def __init__(self):
        self.client_id = os.getenv("KROGER_CLIENT_ID")
        self.client_secret = os.getenv("KROGER_CLIENT_SECRET")
        self.base_url = "https://api.kroger.com/v1"
        self.access_token = None
        self._authenticate()

    def _authenticate(self):
        print("Authenticating with Kroger API...")
        url = f"{self.base_url}/connect/oauth2/token"
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }
        data = {
            "grant_type": "client_credentials",
            "scope": "product.compact"
        }

        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            self.access_token = response.json().get("access_token")
        else:
            print("Fatal Error: Authentication failed.")

    def _get_headers(self):
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

    def get_nearest_store_id(self, zip_code):
        url = f"{self.base_url}/locations?filter.zipCode.near={zip_code}&filter.limit=1"
        
        response = requests.get(url, headers=self._get_headers())
        if response.status_code == 200:
            locations = response.json().get("data", [])
            if locations:
                return locations[0].get("locationId")
        return None

    def search_products(self, location_id, search_term, limit=50):
        url = f"{self.base_url}/products?filter.term={search_term}&filter.locationId={location_id}&filter.limit={limit}"
        
        response = requests.get(url, headers=self._get_headers())
        results = []
        
        if response.status_code == 200:
            products = response.json().get("data", [])
            for item in products:
                brand = item.get("brand", "Unknown")
                description = item.get("description", "No Description")
                upc = item.get("upc", "No UPC")
                
                price = None
                items_list = item.get("items", [])
                if items_list:
                    price_data = items_list[0].get("price", {})
                    price = price_data.get("regular")
                
                results.append({
                    "brand": brand,
                    "description": description,
                    "price": price,
                    "upc": upc
                })
        return results

if __name__ == "__main__":
    init_db()
    client = KrogerClient()
    
    if client.access_token:
        store_id = client.get_nearest_store_id("43420")
        
        if store_id:
            popular_items = [
                "milk", "eggs", "bread", "butter", "cheese", 
                "chicken breast", "ground beef", "pasta", "rice", 
                "beans", "onions", "garlic", "potatoes", "apples", 
                "bananas", "spinach", "tomatoes", "cereal", "coffee", "peanut butter"
            ]
            
            print(f"Seeding database with {len(popular_items)} popular items. This will take a moment...\n")
            
            total_saved = 0
            
            for item in popular_items:
                product_data = client.search_products(store_id, item, limit=50)
                
                if product_data:
                    save_products(product_data, store_id, item)
                    total_saved += len(product_data)
                
                time.sleep(1)
                
            print(f"\nDatabase Seeding Complete! {total_saved} items are now stored in priceplace_cache.db")