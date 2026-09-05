from itertools import combinations
from typing import List, Dict, Optional

from models import CreditCard, SpendingProfile, CardEvaluationResult, MultiCardWalletResult

# Categories that share a single combined spending cap on some cards
# (e.g. one card that caps 5% across grocery + gas + dining together,
# rather than capping each category separately).
# KNOWN LIMITATION: this is a fixed guess, not derived per-card from the
# seed data's "note" field. It's a reasonable approximation but won't be
# exactly right for every combined-cap card (e.g. Bank of America's combined
# cap actually spans grocery + a chosen category, not grocery+gas+dining).
COMBINED_CAP_GROUPS = {
    "combined_bonus_categories": ["grocery", "gas", "dining"],
}

# cap_cat values that don't name a fixed category directly -- instead the
# real-world card pays its bonus rate on "whichever category you spend the
# most in" (Citi Custom Cash) or "a category of your choice" (BofA, US
# Bank). The app has no UI for a user to pick a category, so we resolve
# these by assuming the cardholder makes the optimal choice: whichever
# tracked category (other than catch_all) has the highest spend.
DYNAMIC_CATEGORY_KEYS = {
    "highest_spending_category",
    "custom_choice_category",
    "custom_choice_five_percent_tier",
}


def _base_rate(card: CreditCard, cat: str) -> float:
    if cat in card.rates:
        return card.rates[cat]
    # KNOWN SIMPLIFICATION: the app doesn't distinguish "travel booked
    # through the issuer's portal" from general travel spend, so a card
    # whose only travel rate is portal-specific is treated as if that rate
    # applies to all travel. This slightly overstates value for cardholders
    # who don't book through the portal.
    if cat == "travel" and "travel_portal_booking" in card.rates:
        return card.rates["travel_portal_booking"]
    return card.rates.get("catch_all", 0.01)


def _resolve_dynamic_bonus_category(card: CreditCard, spend_map: Dict[str, float]) -> Optional[str]:
    if card.cap_cat not in DYNAMIC_CATEGORY_KEYS:
        return None
    eligible = {c: s for c, s in spend_map.items() if c != "catch_all"}
    if not eligible:
        return None
    return max(eligible, key=eligible.get)


def _nominal_effective_rate(card: CreditCard, cat: str, dynamic_cat: Optional[str] = None) -> float:
    """
    Rate used only for *comparing* cards when deciding which card should
    "own" a category in a wallet. Ignores whether a cap has already been
    exhausted -- see note in evaluate_single_wallet.
    """
    if card.cap_cat in DYNAMIC_CATEGORY_KEYS and cat == dynamic_cat:
        rate = card.rates.get(card.cap_cat, _base_rate(card, cat))
    else:
        rate = _base_rate(card, cat)
    return rate * (card.point_valuation / 0.01)


def _earn_for_category(
    card: CreditCard,
    cat: str,
    spend: float,
    cap_usage: Dict[str, float],
    dynamic_cat: Optional[str] = None,
) -> float:
    """
    Dollar rewards earned by `card` on `spend` in category `cat`, respecting
    single-category caps, combined-category caps, and dynamic "top/chosen
    category" bonuses.

    `cap_usage` is a running total of dollars already counted against this
    card's cap, keyed by card.id. Pass the SAME dict across every category
    you evaluate for a given card (or wallet containing that card) so a
    combined cap is correctly shared instead of being reset per category.
    """
    is_dynamic_target = card.cap_cat in DYNAMIC_CATEGORY_KEYS and cat == dynamic_cat
    if is_dynamic_target:
        rate = card.rates.get(card.cap_cat, _base_rate(card, cat))
    else:
        rate = _base_rate(card, cat)

    if not (card.cap_cat and card.cap_limit):
        return spend * rate * (card.point_valuation / 0.01)

    group = COMBINED_CAP_GROUPS.get(card.cap_cat)
    in_capped_group = (
        is_dynamic_target
        or cat == card.cap_cat
        or (group is not None and cat in group)
    )

    if not in_capped_group:
        return spend * rate * (card.point_valuation / 0.01)

    post_rate = card.rate_after_cap if card.rate_after_cap is not None else rate
    cap = card.cap_limit

    used = cap_usage.get(card.id, 0.0)
    elig = min(spend, max(0.0, cap - used))
    over = spend - elig
    cap_usage[card.id] = used + elig

    return (elig * rate + over * post_rate) * (card.point_valuation / 0.01)


def calculate_card_rewards(card: CreditCard, spd: SpendingProfile) -> CardEvaluationResult:
    spend_map = spd.model_dump()
    cap_usage: Dict[str, float] = {}
    breakdown: Dict[str, float] = {}
    tot_rewards = 0.0

    dynamic_cat = _resolve_dynamic_bonus_category(card, spend_map)

    for cat, spend in spend_map.items():
        earned = _earn_for_category(card, cat, spend, cap_usage, dynamic_cat)
        breakdown[cat] = round(earned, 2)
        tot_rewards += earned

    tot_spend = sum(spend_map.values())
    sub_earned = card.signup_bonus_value if tot_spend >= card.signup_bonus_spend_req else 0.0
    # Year 1 fee should be $0 if the card waives its annual fee for the
    # first year -- this field existed on the model but was never read.
    base_fee = 0.0 if card.annual_fee_waived_first_year else card.annual_fee
    eff_fee = max(0.0, base_fee - card.credits)
    net_val = tot_rewards + sub_earned - eff_fee

    return CardEvaluationResult(
        card_id=card.id,
        card_name=card.card_name,
        issuer=card.issuer,
        annual_fee=card.annual_fee,
        effective_annual_fee=round(eff_fee, 2),
        signup_bonus_earned=round(sub_earned, 2),
        annual_rewards=round(tot_rewards, 2),
        net_first_year_value=round(net_val, 2),
        breakdown=breakdown,
    )


def rank_cards_for_profile(
    cards: List[CreditCard],
    spd: SpendingProfile,
    include_business: bool = False,
) -> List[CardEvaluationResult]:
    filtered_cards = [c for c in cards if include_business or not c.is_business]
    results = [calculate_card_rewards(c, spd) for c in filtered_cards]
    return sorted(results, key=lambda x: x.net_first_year_value, reverse=True)


def evaluate_single_wallet(
    combo: tuple,
    card_evals: Dict[str, CardEvaluationResult],
    spend_map: Dict[str, float],
) -> MultiCardWalletResult:
    category_assignment: Dict[str, str] = {}
    total_rewards = 0.0
    # Shared across every category in this wallet so a combined cap on one
    # card is tracked correctly no matter how many categories land on it.
    cap_usage: Dict[str, float] = {}
    # Each card's dynamic "top category" only depends on the spend profile,
    # not on the wallet combo, so resolve it once per card up front.
    dynamic_cats = {card.id: _resolve_dynamic_bonus_category(card, spend_map) for card in combo}

    for cat, spend in spend_map.items():
        # NOTE: we still pick the "best" card per category using the nominal
        # (pre-cap-exhaustion) rate. A fully optimal assignment would need to
        # jointly solve category assignment + cap exhaustion (e.g. an ILP);
        # this greedy approach is a documented simplification. What it no
        # longer does is silently ignore caps when computing the payout for
        # whichever card gets picked -- that was the actual bug.
        best_rate = -1.0
        best_card = combo[0]
        for card in combo:
            rate = _nominal_effective_rate(card, cat, dynamic_cats[card.id])
            if rate > best_rate:
                best_rate = rate
                best_card = card

        category_assignment[cat] = best_card.id
        total_rewards += _earn_for_category(
            best_card, cat, spend, cap_usage, dynamic_cats[best_card.id]
        )

    chosen_evals = [card_evals[c.id] for c in combo]
    total_fee = sum(c.effective_annual_fee for c in chosen_evals)
    total_sub = sum(c.signup_bonus_earned for c in chosen_evals)
    net_yield = total_rewards + total_sub - total_fee

    return MultiCardWalletResult(
        cards=chosen_evals,
        total_net_value=round(net_yield, 2),
        total_annual_rewards=round(total_rewards, 2),
        total_effective_fee=round(total_fee, 2),
        total_signup_bonus=round(total_sub, 2),
        best_category_assignments=category_assignment,
    )


def optimize_top_wallets(
    cards: List[CreditCard],
    spd: SpendingProfile,
    wallet_size: int = 2,
    top_n: int = 3,
    include_business: bool = False,
) -> List[MultiCardWalletResult]:
    filtered_cards = [c for c in cards if include_business or not c.is_business]
    spend_map = spd.model_dump()
    card_evals = {c.id: calculate_card_rewards(c, spd) for c in filtered_cards}

    evaluated_wallets = [
        evaluate_single_wallet(combo, card_evals, spend_map)
        for combo in combinations(filtered_cards, wallet_size)
    ]
    evaluated_wallets.sort(key=lambda w: w.total_net_value, reverse=True)
    return evaluated_wallets[:top_n]


def optimize_wallet_combo(
    cards: List[CreditCard],
    spd: SpendingProfile,
    wallet_size: int = 2,
    include_business: bool = False,
) -> MultiCardWalletResult:
    top_wallets = optimize_top_wallets(
        cards, spd, wallet_size=wallet_size, top_n=1, include_business=include_business
    )
    if not top_wallets:
        raise ValueError("No eligible cards found to form a wallet.")
    return top_wallets[0]