"""
Regression tests for SpendWise's rewards engine.

Each test locks in a bug that was found and fixed:
  1. Pydantic field-alias mismatches silently disabled caps and bonus rates.
  2. Wallet per-card contributions didn't sum to the wallet total.
  3. Variable bonus categories ("highest spending category") always fell
     back to the flat catch-all rate.

Run from the repo root with:  pytest -v
"""
import json
from pathlib import Path

import pytest

from engine import (
    _earn_for_category,
    calculate_card_rewards,
    optimize_top_wallets,
)
from models import CreditCard, SpendingProfile

SEED_PATH = Path(__file__).parent / "cards_seed.json"
TOL = 0.05  # allowance for per-card rounding to cents


# ---------- fixtures ----------

@pytest.fixture(scope="module")
def cards():
    with open(SEED_PATH) as f:
        return [CreditCard(**c) for c in json.load(f)]


@pytest.fixture
def profile():
    return SpendingProfile(
        grocery=6000.0, dining=4000.0, travel=2500.0, gas=2000.0,
        streaming=300.0, catch_all=14000.0,
    )


def make_card(base: CreditCard, **overrides) -> CreditCard:
    """Copy a real seed card and override fields by their Python names,
    so tests don't depend on the JSON alias spellings."""
    defaults = dict(
        point_valuation=0.01,
        cap_cat=None,
        cap_limit=None,
        rate_after_cap=None,
    )
    defaults.update(overrides)
    return base.model_copy(update=defaults)


# ---------- bug 1: alias mismatches ----------

def test_spending_profile_dumps_engine_category_names(profile):
    """The engine looks up categories by these names. If an alias change
    breaks the mapping, every lookup would silently miss."""
    keys = set(profile.model_dump().keys())
    for expected in ["grocery", "dining", "travel", "gas", "catch_all"]:
        assert expected in keys, f"SpendingProfile is missing '{expected}'"


def test_spending_profile_keeps_values(profile):
    """Unknown keyword names are silently dropped by Pydantic, so make sure
    the spending we pass in is actually what the engine sees."""
    assert sum(profile.model_dump().values()) == pytest.approx(28800.0)


def test_spending_profile_accepts_catch_all_alias():
    assert SpendingProfile(catchAll=500.0).catch_all == 500.0


def test_seed_cards_load_cap_fields(cards):
    """When aliases were mismatched, cap fields loaded as None on every card
    and caps were never enforced. At least some cards must have caps."""
    capped = [c for c in cards if c.cap_cat and c.cap_limit]
    assert capped, "No seed card loaded with a spending cap"


def test_seed_cards_load_bonus_rates(cards):
    """Bonus-category rates must survive loading, not collapse to catch-all."""
    has_bonus = [
        c for c in cards
        if any(rate > c.rates.get("catch_all", 0.01)
               for cat, rate in c.rates.items() if cat != "catch_all")
    ]
    assert has_bonus, "No seed card loaded with a bonus-category rate"


def test_single_category_cap_is_enforced(cards):
    card = make_card(
        cards[0],
        rates={"grocery": 0.05, "catch_all": 0.01},
        cap_cat="grocery", cap_limit=1500.0, rate_after_cap=0.01,
    )
    earned = _earn_for_category(card, "grocery", 5000.0, cap_usage={})
    # 1500 at 5% + 3500 at 1%
    assert earned == pytest.approx(75.0 + 35.0)


def test_combined_cap_is_shared_across_categories(cards):
    card = make_card(
        cards[0],
        rates={"grocery": 0.05, "gas": 0.05, "dining": 0.05, "catch_all": 0.01},
        cap_cat="combined_bonus_categories", cap_limit=1000.0, rate_after_cap=0.01,
    )
    usage = {}
    grocery = _earn_for_category(card, "grocery", 800.0, usage)
    gas = _earn_for_category(card, "gas", 800.0, usage)
    assert grocery == pytest.approx(800 * 0.05)
    # only 200 of cap left: 200 at 5% + 600 at 1%
    assert gas == pytest.approx(200 * 0.05 + 600 * 0.01)


# ---------- bug 2: wallet contributions ----------

def test_wallet_per_card_rewards_sum_to_total(cards, profile):
    wallets = optimize_top_wallets(cards, profile, wallet_size=2, top_n=10)
    assert wallets
    for w in wallets:
        per_card = sum(c.annual_rewards for c in w.cards)
        assert per_card == pytest.approx(w.total_annual_rewards, abs=TOL)


def test_wallet_per_card_net_sums_to_total(cards, profile):
    wallets = optimize_top_wallets(cards, profile, wallet_size=2, top_n=10)
    for w in wallets:
        per_card = sum(c.net_first_year_value for c in w.cards)
        assert per_card == pytest.approx(w.total_net_value, abs=TOL)


def test_each_category_earns_on_only_its_assigned_card(cards, profile):
    wallets = optimize_top_wallets(cards, profile, wallet_size=2, top_n=10)
    for w in wallets:
        for c in w.cards:
            for cat, earned in c.breakdown.items():
                if w.best_category_assignments[cat] != c.card_id:
                    assert earned == 0.0


# ---------- bug 3: variable bonus categories ----------

def test_highest_spending_category_gets_bonus_rate(cards, profile):
    card = make_card(
        cards[0],
        rates={"highest_spending_category": 0.05, "catch_all": 0.01},
        cap_cat="highest_spending_category",
    )
    spend = profile.model_dump()
    top_cat = max((c for c in spend if c != "catch_all"), key=spend.get)

    result = calculate_card_rewards(card, profile)
    assert result.breakdown[top_cat] == pytest.approx(spend[top_cat] * 0.05, abs=0.01)


def test_other_categories_keep_flat_rate(cards, profile):
    card = make_card(
        cards[0],
        rates={"highest_spending_category": 0.05, "catch_all": 0.01},
        cap_cat="highest_spending_category",
    )
    spend = profile.model_dump()
    top_cat = max((c for c in spend if c != "catch_all"), key=spend.get)

    result = calculate_card_rewards(card, profile)
    for cat, amount in spend.items():
        if cat != top_cat:
            assert result.breakdown[cat] == pytest.approx(amount * 0.01, abs=0.01)