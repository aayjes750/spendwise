# SpendWise

A credit card recommendation engine that ranks cards by **projected Net Year 1 Value** — signup bonus plus category rewards, minus effective annual fee — based on a user's own spending profile, rather than generic "best card" rankings.

**Live app:** [spendwise-aayjes.vercel.app](https://spendwise-aayjes.vercel.app)
**API:** FastAPI backend deployed on Render

---

## What it does

- Ranks 24 credit cards by first-year net value for a custom spending profile across 6 categories (grocery, dining, travel, gas, streaming, and general spend)
- Enforces real-world spending caps (e.g. "5% on groceries up to $6,000/year, 1% after")
- Resolves dynamic bonus categories, like cards that pay a bonus rate on "whichever category you spend the most in"
- Recommends optimal 2-card wallet combinations, splitting spend across categories to maximize combined value

## Tech stack

- **Backend:** Python, FastAPI, Pydantic
- **Frontend:** React, deployed on Vercel
- **Testing:** pytest

## A bug I found and fixed

While reviewing my own reward-calculation logic, I found that `models.py`'s Pydantic field aliases (`capCat`, `capLimit`, `rateAfterCap`) didn't actually match the key names used in `cards_seed.json` (`spending_cap_category`, `spending_cap_limit`, `reward_rate_after_cap`). Because the model allowed extra fields, Pydantic silently discarded the mismatched data instead of raising an error — meaning **no card's spending cap was ever actually enforced**, despite the cap logic in `engine.py` being written correctly.

I traced this by comparing the app's live output against hand-calculated expected values, found the same root-cause pattern (a name mismatch silently swallowed instead of erroring) in two other places — a card's `travel_portal_booking` rate never matching the `travel` spending category, and "top spending category" bonus cards never resolving to an actual category — and fixed all three, plus added regression tests (`test_cap_bug.py`) to lock the fixed behavior in.

**Before fix:** Capital One Venture Rewards (advertised 5% on travel) was silently earning a flat 2% on everything.
**After fix:** it correctly earns 5% on travel spend, verified against the live deployed API.

## Known simplifications

Documented directly in code comments (`engine.py`), not hidden:
- The multi-card wallet optimizer assigns categories using each card's nominal (pre-cap) rate rather than jointly solving assignment and cap exhaustion — a fully optimal solution would need something like an ILP formulation.
- Signup bonus eligibility compares total annual spend against the bonus's spend requirement, without modeling the requirement's actual time window (typically 3 months).
- Effective annual fee assumes full redemption of card credits (e.g. Amex Gold's dining/Uber credits), which overstates value for cardholders who don't use every credit.
- Niche card categories not tracked by the app's 6 spending buckets (e.g. drugstore, office supplies) fall back to the card's catch-all rate.

## Running locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
python test_run.py          # prints a sample ranking to the console
pytest test_cap_bug.py -v   # regression tests for the cap-enforcement fix
```

## Project structure

```
main.py           # FastAPI routes
models.py         # Pydantic models (SpendingProfile, CreditCard, results)
engine.py         # Reward calculation and wallet optimization logic
cards_seed.json   # Card database (rates, caps, signup bonuses)
test_run.py       # Manual sanity-check script
test_cap_bug.py   # Regression tests for the cap-enforcement fix
frontend/         # React frontend
```