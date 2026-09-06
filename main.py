import os
import json
from typing import List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from models import SpendingProfile, CardEvaluationResult, CreditCard, MultiCardWalletResult
from engine import (
    rank_cards_for_profile,
    optimize_wallet_combo,
    optimize_top_wallets,
)

app = FastAPI(title="SpendWise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "SpendWise API is running"}

def load_card_database() -> List[CreditCard]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "cards_seed.json")
    
    if not os.path.exists(json_path):
        json_path = os.path.join(os.getcwd(), "cards_seed.json")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [CreditCard(**card) for card in data]

@app.post("/api/optimize", response_model=List[CardEvaluationResult])
def optimize_cards(
    spending: SpendingProfile,
    include_business: bool = Query(default=False)
):
    try:
        cards = load_card_database()
        return rank_cards_for_profile(cards, spending, include_business=include_business)
    except Exception as e:
        print(f"Error in /api/optimize: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimize-wallet", response_model=MultiCardWalletResult)
def optimize_wallet(
    spending: SpendingProfile,
    wallet_size: int = Query(default=2, ge=2, le=3),
    include_business: bool = Query(default=False)
):
    try:
        cards = load_card_database()
        return optimize_wallet_combo(
            cards, 
            spending, 
            wallet_size=wallet_size, 
            include_business=include_business
        )
    except Exception as e:
        print(f"Error in /api/optimize-wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimize-wallets", response_model=List[MultiCardWalletResult])
def optimize_wallets(
    spending: SpendingProfile,
    wallet_size: int = Query(default=2, ge=2, le=3),
    top_n: int = Query(default=3, ge=1, le=5),
    include_business: bool = Query(default=False)
):
    try:
        cards = load_card_database()
        return optimize_top_wallets(
            cards, 
            spending, 
            wallet_size=wallet_size, 
            top_n=top_n, 
            include_business=include_business
        )
    except Exception as e:
        print(f"Error in /api/optimize-wallets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimize-no-fee", response_model=List[CardEvaluationResult])
def optimize_no_annual_fee_cards(
    spending: SpendingProfile,
    include_business: bool = Query(default=False)
):
    try:
        cards = load_card_database()
        no_fee_cards = [c for c in cards if c.annual_fee == 0.0]
        return rank_cards_for_profile(
            no_fee_cards, 
            spending, 
            include_business=include_business
        )
    except Exception as e:
        print(f"Error in /api/optimize-no-fee: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/optimize-student", response_model=List[CardEvaluationResult])
def optimize_student_cards(
    spending: SpendingProfile,
):
    try:
        cards = load_card_database()
        student_cards = [c for c in cards if c.is_student]
        return rank_cards_for_profile(
            student_cards,
            spending,
            include_business=False,
        )
    except Exception as e:
        print(f"Error in /api/optimize-student: {e}")
        raise HTTPException(status_code=500, detail=str(e))