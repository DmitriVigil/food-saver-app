from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn
from planner import generate_ai_meal_plan

# Initialize the FastAPI application
app = FastAPI(title="Food Saver API", version="1.0")

# 1. Define the exact JSON structure we expect the mobile app to send us
class MealPlanRequest(BaseModel):
    budget: float
    target_meals: int
    pantry_items: List[str]
    dislikes_allergies: List[str]

# 2. Create the web endpoint (URL) that the mobile app will talk to
@app.post("/api/generate-plan")
def create_meal_plan(request: MealPlanRequest):
    try:
        # Call your existing Gemini engine with the data from the web request
        plan = generate_ai_meal_plan(
            budget=request.budget,
            target_meals=request.target_meals,
            pantry_items=request.pantry_items,
            dislikes_allergies=request.dislikes_allergies
        )
        # Send the finalized plan back to the mobile app as JSON
        return {"status": "success", "data": plan}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Start the live web server on port 8000
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)