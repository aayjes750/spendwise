from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json

from models import SpendingProfile, CardEvaluationResult, CreditCard, MultiCardWalletResult
from engine import rank_cards_for_profile, optimize_wallet_combo

app = FastAPI(title="SpendWise API")

# Enable CORS for React dev server
# Enable CORS for React dev server & production Vercel frontend
# Enable CORS for React dev server & production Vercel frontend
origins = [
    "https://spendwise-indol-iota.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_card_database() -> List[CreditCard]:
    with open("cards_seed.json", "r") as f:
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