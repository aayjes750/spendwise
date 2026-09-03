import os
import json
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException

from models import SpendingProfile, CardEvaluationResult, CreditCard, MultiCardWalletResult
from engine import rank_cards_for_profile, optimize_wallet_combo

app = FastAPI(title="SpendWise API")

# Health check root route
@app.get("/")
def health_check():
    return {"status": "ok", "message": "SpendWise API is running"}

# Enable universal CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_card_database() -> List[CreditCard]:
    json_path = os.path.join(os.path.dirname(__file__), "cards_seed.json")
    with open(json_path, "r") as f:
        data = json.load(f)
    return [CreditCard(**card) for card in data]

@app.post("/api/optimize", response_model=List[CardEvaluationResult])
def optimize_cards(spending: SpendingProfile):
    cards = load_card_database()
    return rank_cards_for_profile(cards, spending)

@app.post("/api/optimize-wallet", response_model=MultiCardWalletResult)
def optimize_wallet(spending: SpendingProfile):
    cards = load_card_database()
    return optimize_wallet_combo(cards, spending, wallet_size=2)
@app.post("/api/optimize-no-fee", response_model=List[CardEvaluationResult])
def optimize_no_annual_fee_cards(spending: SpendingProfile):
    try:
        cards = load_card_database()
        # Filter cards where annual_fee is 0
        no_fee_cards = [c for c in cards if c.annual_fee == 0.0]
        return rank_cards_for_profile(no_fee_cards, spending)
    except Exception as e:
        print(f"Error in /api/optimize-no-fee: {e}")
        raise HTTPException(status_code=500, detail=str(e))