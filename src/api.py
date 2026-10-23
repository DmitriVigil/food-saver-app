import base64
import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # Add this import
from pydantic import BaseModel
from typing import List
import uvicorn
from planner import generate_ai_meal_plan

app = FastAPI(title="Food Saver API", version="1.0")

# --- ADD THIS BLOCK ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows your phone to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ----------------------

class MealPlanRequest(BaseModel):
    budget: float
    target_meals: int
    pantry_items: List[str]
    dislikes_allergies: List[str]
    misc_preferences: List[str] = [] # New field

@app.post("/api/generate-plan")
def create_meal_plan(request: MealPlanRequest):
    try:
        plan = generate_ai_meal_plan(
            budget=request.budget,
            target_meals=request.target_meals,
            pantry_items=request.pantry_items,
            dislikes_allergies=request.dislikes_allergies,
            misc_preferences=request.misc_preferences # Pass to planner
        )
        return {"status": "success", "data": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 1. Define the incoming payload structure for the Cart
class CartItem(BaseModel):
    upc: str
    quantity: int

class AddToCartRequest(BaseModel):
    items: List[CartItem]
    auth_code: str

# 2. Create the Checkout Endpoint
@app.post("/api/add-to-cart")
def add_to_kroger_cart(request: AddToCartRequest):
    # Ensure your backend .env has these variables
    client_id = os.getenv("KROGER_CLIENT_ID")
    client_secret = os.getenv("KROGER_CLIENT_SECRET")
    
    # 1. Base64 encode the Client ID and Secret (Kroger Requirement)
    auth_string = f"{client_id}:{client_secret}"
    auth_base64 = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    
    # 2. Exchange the Auth Code for a Customer Access Token
    token_url = "https://api.kroger.com/v1/connect/oauth2/token"
    token_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_base64}"
    }
    
    # Note: redirect_uri must EXACTLY match what the frontend printed
    token_data = {
        "grant_type": "authorization_code",
        "code": request.auth_code,
        "redirect_uri": "http://localhost:8081" 
    }
    
    token_response = requests.post(token_url, headers=token_headers, data=token_data)
    
    if not token_response.ok:
        print(f"Token Error: {token_response.text}")
        raise HTTPException(status_code=400, detail="Could not authorize Kroger account.")
        
    access_token = token_response.json().get("access_token")
    
    # 3. Push the items to the Kroger Cart
    cart_url = "https://api.kroger.com/v1/cart/add"
    cart_headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    kroger_payload = {
        "items": [{"upc": item.upc, "quantity": item.quantity} for item in request.items]
    }
    
    cart_response = requests.put(cart_url, headers=cart_headers, json=kroger_payload)
    print("Kroger Cart Response Status:", cart_response.status_code)
    print("Kroger Cart Response Body:", cart_response.text)

    if not cart_response.ok:
        print(f"Cart Error: {cart_response.text}")
        raise HTTPException(status_code=400, detail="Failed to add items to Kroger cart.")
        
    return {"status": "success", "message": "Items successfully added to Kroger cart!"}
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)