import json

from models import CreditCard, SpendingProfile
from engine import rank_cards_for_profile

with open("cards_seed.json", "r") as f:
    cards_data = json.load(f)

cards = [CreditCard(**c) for c in cards_data]

# NOTE: these keyword args previously used abbreviations (groc, dine, trav,
# stream, ent, catch) that didn't match any real SpendingProfile field name
# (grocery, dining, travel, gas, streaming, catch_all). Pydantic silently
# drops unrecognized keywords instead of erroring, so every category except
# "gas" (which matched by coincidence) was quietly defaulting to $0. There's
# also no dedicated "entertainment" field in the model, so that spend is
# folded into catch_all here instead of just being dropped.
sample_spending = SpendingProfile(
    grocery=6000.0,
    dining=4000.0,
    travel=2500.0,
    gas=2000.0,
    streaming=300.0,
    catch_all=14000.0 + 1200.0,  # includes what was previously "ent"
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