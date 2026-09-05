"""
Regression test for the wallet-optimizer cap bug:
evaluate_single_wallet used to ignore cap_cat/cap_limit entirely,
so a capped card would earn its bonus rate on unlimited spend when
picked in a multi-card wallet. This pins down the fixed behavior.

Drop this next to test_run.py and run with: pytest test_cap_bug.py -v
"""
from models import CreditCard, SpendingProfile
from engine import calculate_card_rewards, evaluate_single_wallet


def make_capped_grocery_card():
    # 5% groceries capped at $1,500/yr, 1% after that. 0 fee to isolate the cap math.
    return CreditCard(
        name="Test Capped Grocery Card",
        annual_fee=0.0,
        reward_rates={"grocery": 0.05, "catch_all": 0.01},
        cap_cat="grocery",
        cap_limit=1500.0,
        rate_after_cap=0.01,
    )


def make_flat_catch_all_card():
    # Boring 1.5% flat card, 0 fee -- used as the "second" wallet card.
    return CreditCard(
        name="Test Flat Card",
        annual_fee=0.0,
        reward_rates={"catch_all": 0.015},
    )


def test_single_card_respects_cap():
    card = make_capped_grocery_card()
    spend = SpendingProfile(grocery=6000.0)
    result = calculate_card_rewards(card, spend)

    # First $1500 at 5% ($75) + remaining $4500 at 1% ($45) = $120
    assert result.breakdown["grocery"] == 120.00


def test_wallet_also_respects_cap():
    """
    This is the case that used to fail before the fix: with the old code,
    evaluate_single_wallet ignored cap_cat/cap_limit and paid 5% on the
    full $6000 of grocery spend ($300) instead of the capped $120.
    """
    capped = make_capped_grocery_card()
    flat = make_flat_catch_all_card()
    spend_map = SpendingProfile(grocery=6000.0).model_dump()

    card_evals = {
        capped.id: calculate_card_rewards(capped, SpendingProfile(**spend_map)),
        flat.id: calculate_card_rewards(flat, SpendingProfile(**spend_map)),
    }

    wallet = evaluate_single_wallet((capped, flat), card_evals, spend_map)

    # Grocery gets assigned to the capped card (5% nominal beats 1.5% flat),
    # but earnings must reflect the cap: $120, not $300.
    assert wallet.total_annual_rewards == 120.00
    assert wallet.best_category_assignments["grocery"] == capped.id