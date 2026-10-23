import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from database import get_encrypted_connection

# Load environment variables from .env file
load_dotenv()

# Initialize the Gemini Client (detects GEMINI_API_KEY from .env)
client = genai.Client()

GLOBAL_NEGATIVE_KEYWORDS = [
    "baby food", "puree", "pouch", "toddler",
    "cat food", "dog food", "pet",
    "seasoning mix", "gravy mix", "dressing", "dip",
    "chips", "snack", "candy"
]

def get_cheapest_product(cursor, search_term, exclude_keywords):
    """
    Finds the lowest priced product for a given category that:
    1. Does not contain any user-specified allergy/dislike keywords.
    2. Does not contain junk matches (baby food, pet food, etc).
    """
    # Check if image_url exists in product_cache columns, or select standard columns
    cursor.execute("""
        SELECT upc, brand, description, price 
        FROM product_cache 
        WHERE search_term = ? AND price IS NOT NULL AND price > 0
        ORDER BY price ASC
    """, (search_term,))
    
    rows = cursor.fetchall()
    all_exclusions = [k.lower() for k in exclude_keywords] + GLOBAL_NEGATIVE_KEYWORDS

    for row in rows:
        description_lower = (row[2] or "").lower()
        brand_lower = (row[1] or "").lower()
        full_text = f"{brand_lower} {description_lower}"
        
        if any(keyword in full_text for keyword in all_exclusions):
            continue
        
        upc = row[0]
        # Standard Kroger CDN URL format by UPC; if an image URL column exists in cache, use that instead
        fallback_image_url = f"https://www.kroger.com/product/images/medium/front/{upc}"
            
        return {
            "upc": upc,
            "brand": row[1] if row[1] else "Store Brand",
            "description": row[2],
            "price": float(row[3]),
            "category": search_term,
            "image_url": fallback_image_url
        }
    return None

def fetch_affordable_ingredients(exclude_keywords):
    """Pulls a list of the 50 absolute cheapest raw ingredients from the encrypted database."""
    with get_encrypted_connection() as conn:
        cursor = conn.cursor()
        
        # Grab distinct categories to provide a diverse palette
        cursor.execute("SELECT DISTINCT search_term FROM product_cache")
        categories = [row[0] for row in cursor.fetchall()]
        
        available_palette = []
        for cat in categories:
            best = get_cheapest_product(cursor, cat, exclude_keywords)
            if best:
                available_palette.append(best)
                
        # Sort by price and cap at 50 to keep the LLM prompt lean
        available_palette.sort(key=lambda x: x["price"])
        return available_palette[:50]

def generate_ai_meal_plan(budget, target_meals, pantry_items, dislikes_allergies, misc_preferences=None):
    if misc_preferences is None:
        misc_preferences = []
        
    # 1. Fetch available data palette from encrypted local cache
    available_ingredients = fetch_affordable_ingredients(dislikes_allergies)
    
    # 2. Format palette into prompt context
    store_inventory_text = "\n".join(
        [f"- {item['category']} ({item['brand']} {item['description']}): ${item['price']:.2f}" for item in available_ingredients]
    )
    
    # Format the new constraints
    constraints_text = ", ".join(misc_preferences) if misc_preferences else "None"

    # 3. Construct prompt
    prompt = f"""
    You are an expert, budget-conscious meal planner. 
    A user needs a meal plan consisting of exactly {target_meals} meals.
    Their maximum budget for groceries is ${budget:.2f}.
    
    They already have these items in their pantry (cost is $0):
    {', '.join(pantry_items)}
    
    They dislike or are allergic to:
    {', '.join(dislikes_allergies)}
    
    Cooking Style & Equipment Constraints:
    {constraints_text}
    
    Here is the live inventory available at their local store with exact prices:
    {store_inventory_text}
    
    Instructions:
    1. Create exactly {target_meals} delicious, creative recipes.
    2. Prioritize using their pantry items to reduce grocery costs.
    3. For all missing ingredients, you MUST ONLY select items from the provided "live inventory" list. Do not invent ingredients.
    4. Calculate the total cost of the items you selected. The total MUST be strictly less than ${budget:.2f}.
    5. STRICTLY ADHERE to the Cooking Style & Equipment Constraints. If 'Microwave Only' or 'College Student (No Oven)' is listed, you must not suggest recipes requiring an oven. If 'Quick Meal' is listed, keep prep and cook times strictly under 15 minutes. If 'Good for Leftovers' is listed, suggest meals that scale well and reheat easily.
    """
# ... (The rest of your function remains exactly the same)

    print("Thinking... consulting Gemini to assemble the perfect meal plan...")

    # 4. Generate structured JSON response with Config
    config = types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
        response_schema={
            "type": "OBJECT",
            "properties": {
                "recipes": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "instructions": {"type": "STRING"},
                            "ingredients_used": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                                "description": "Category names of ingredients used (e.g., 'chicken breast', 'rice')"
                            }
                        },
                        "required": ["name", "instructions", "ingredients_used"]
                    }
                },
                "shopping_list_categories": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "List of ingredient categories that need to be purchased from the store."
                },
                "estimated_total_cost": {"type": "NUMBER"}
            },
            "required": ["recipes", "shopping_list_categories", "estimated_total_cost"]
        }
    )

    # Time-based retry loop for 503 capacity spikes
    max_retries = 3
    response = None

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=config
            )
            break # Exit the loop immediately if successful
            
        except Exception as e:
            if "503" in str(e):
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt # Pauses for 1s, then 2s
                    print(f"Warning: Gemini is experiencing peak traffic. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
            # If it's not a 503, or we ran out of retries, raise the error
            raise e

    if not response:
        raise RuntimeError("Google AI endpoints are currently unavailable. Please try again in a moment.")

    # 5. Parse output
    ai_plan = json.loads(response.text)
    
    # 6. Map requested shopping categories back to database records
    final_shopping_list = []
    actual_total = 0.0
    for cat in ai_plan["shopping_list_categories"]:
        item = next((i for i in available_ingredients if i["category"] == cat), None)
        if item:
            final_shopping_list.append(item)
            actual_total += item["price"]

    return {
        "recipes": ai_plan["recipes"],
        "shopping_list": final_shopping_list,
        "ai_estimated_cost": ai_plan["estimated_total_cost"],
        "actual_calculated_cost": round(actual_total, 2),
        "budget": budget
    }

if __name__ == "__main__":
    USER_BUDGET = 35.00
    TARGET_MEALS = 4
    USER_PANTRY = ["rice", "butter", "garlic"]
    USER_EXCLUSIONS = ["peanut butter", "peanuts"]

    plan = generate_ai_meal_plan(
        budget=USER_BUDGET,
        target_meals=TARGET_MEALS,
        pantry_items=USER_PANTRY,
        dislikes_allergies=USER_EXCLUSIONS
    )

    print(f"\n✅ Plan Generated Successfully!")
    print(f"Target Budget: ${plan['budget']:.2f}")
    print(f"Calculated Cart Cost: ${plan['actual_calculated_cost']:.2f}\n")

    print("=== AI GENERATED RECIPES ===")
    for idx, r in enumerate(plan["recipes"], 1):
        print(f"{idx}. {r['name']}")
        print(f"   Ingredients: {', '.join(r['ingredients_used'])}")
        print(f"   How to cook: {r['instructions']}\n")

    print("=== FINAL SHOPPING LIST ===")
    for item in plan["shopping_list"]:
        print(f"- {item['brand']} {item['description']} — ${item['price']:.2f} (UPC: {item['upc']})")