import os
import json
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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