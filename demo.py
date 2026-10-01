"""Quick demo: rank the top 5 cards for a sample spending profile."""
import json

from models import CreditCard, SpendingProfile
from engine import rank_cards_for_profile

with open("cards_seed.json", "r") as f:
    cards_data = json.load(f)

cards = [CreditCard(**c) for c in cards_data]

sample_spending = SpendingProfile(
    grocery=6000.0,
    dining=4000.0,
    travel=2500.0,
    gas=2000.0,
    streaming=300.0,
    catch_all=14000.0,
)

ranked = rank_cards_for_profile(cards, sample_spending)

print(f"\n{'Rank':<5} {'Card Name':<35} {'Rewards':<10} {'Bonus':<8} {'Fee':<8} {'Net Y1 Value'}")
print("-" * 75)
for idx, res in enumerate(ranked[:5], start=1):
    print(
        f"{idx:<5} {res.card_name:<35} ${res.annual_rewards:<9.2f} "
        f"${res.signup_bonus_earned:<7.2f} ${res.effective_annual_fee:<7.2f} "
        f"${res.net_first_year_value:.2f}"
    )