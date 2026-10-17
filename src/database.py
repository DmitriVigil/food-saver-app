import os
import json
import csv
from datetime import datetime
from dotenv import load_dotenv
from sqlcipher3 import dbapi2 as sqlite3

# Load environment variables (including DB_PASSWORD)
load_dotenv()

DB_PATH = "priceplace_cache.db"

def get_encrypted_connection():
    """Helper to return an encrypted database connection."""
    conn = sqlite3.connect(DB_PATH)
    db_key = os.getenv("DB_PASSWORD")
    if not db_key:
        raise ValueError("DB_PASSWORD environment variable is missing.")
    
    # Unlock the database using the encryption key
    conn.execute(f"PRAGMA key = '{db_key}'")
    return conn

def init_db():
    """Initializes the cache table."""
    with get_encrypted_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_cache (
                upc TEXT PRIMARY KEY,
                brand TEXT,
                description TEXT,
                price REAL,
                location_id TEXT,
                search_term TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def save_products(products, location_id, search_term):
    """Saves or updates products in the local cache."""
    with get_encrypted_connection() as conn:
        cursor = conn.cursor()
        for p in products:
            cursor.execute("""
                INSERT INTO product_cache (upc, brand, description, price, location_id, search_term, cached_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(upc) DO UPDATE SET
                    price=excluded.price,
                    cached_at=excluded.cached_at
            """, (
                p.get("upc"),
                p.get("brand"),
                p.get("description"),
                p.get("price"),
                location_id,
                search_term,
                datetime.utcnow()
            ))
        conn.commit()

def export_to_json(output_path="exports/products.json"):
    """Exports all cached products to a JSON file."""
    with get_encrypted_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product_cache")
        rows = [dict(row) for row in cursor.fetchall()]
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=4)
    print(f"Exported {len(rows)} products to {output_path}")

def export_to_csv(output_path="exports/products.csv"):
    """Exports all cached products to a standard CSV file."""
    with get_encrypted_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT upc, brand, description, price, location_id, search_term, cached_at FROM product_cache")
        rows = cursor.fetchall()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["UPC", "Brand", "Description", "Price", "Location ID", "Search Term", "Cached At"])
        writer.writerows(rows)
    print(f"Exported {len(rows)} products to {output_path}")