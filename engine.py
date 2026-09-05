from itertools import combinations
from typing import List, Dict, Optional
from models import CreditCard, SpendingProfile, CardEvaluationResult, MultiCardWalletResult

def calculate_card_rewards(card: CreditCard, spd: SpendingProfile) -> CardEvaluationResult:
    spend_map = spd.model_dump()
    base_rate = card.rates.get("catch_all", 0.01)
    tot_rewards = 0.0
    breakdown: Dict[str, float] = {}

    comb_caps = {
        "combined_bonus_categories": ["grocery", "gas", "dining"],
    }

    if card.cap_cat and card.cap_limit:
        cap = card.cap_limit
        post_rate = card.rate_after_cap or base_rate

        if card.cap_cat in comb_caps:
            target_cats = comb_caps[card.cap_cat]
            acc_spend = 0.0
            for cat, spend in spend_map.items():
                rate = card.rates.get(cat, base_rate)
                if cat in target_cats and spend > 0:
                    elig = min(spend, max(0.0, cap - acc_spend))
                    over = spend - elig
                    acc_spend += elig
                    earned = (elig * rate + over * post_rate) * (card.point_valuation / 0.01)
                else:
                    earned = (spend * rate) * (card.point_valuation / 0.01)
                breakdown[cat] = round(earned, 2)
                tot_rewards += earned
        else:
            for cat, spend in spend_map.items():
                rate = card.rates.get(cat, base_rate)
                if cat == card.cap_cat:
                    elig = min(spend, cap)
                    over = max(0.0, spend - cap)
                    earned = (elig * rate + over * post_rate) * (card.point_valuation / 0.01)
                else:
                    earned = (spend * rate) * (card.point_valuation / 0.01)
                breakdown[cat] = round(earned, 2)
                tot_rewards += earned
    else:
        for cat, spend in spend_map.items():
            rate = card.rates.get(cat, base_rate)
            earned = (spend * rate) * (card.point_valuation / 0.01)
            breakdown[cat] = round(earned, 2)
            tot_rewards += earned

    tot_spend = sum(spend_map.values())
    sub_earned = card.signup_bonus_value if tot_spend >= card.signup_bonus_spend_req else 0.0
    eff_fee = max(0.0, card.annual_fee - card.credits)
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
        breakdown=breakdown
    )

def rank_cards_for_profile(
    cards: List[CreditCard], 
    spd: SpendingProfile, 
    include_business: bool = False
) -> List[CardEvaluationResult]:
    filtered_cards = [c for c in cards if include_business or not c.is_business]
    results = [calculate_card_rewards(c, spd) for c in filtered_cards]
    return sorted(results, key=lambda x: x.net_first_year_value, reverse=True)

def evaluate_single_wallet(
    combo: tuple, 
    card_evals: Dict[str, CardEvaluationResult], 
    spend_map: Dict[str, float]
) -> MultiCardWalletResult:
    category_assignment = {}
    total_rewards = 0.0

    for cat, spend in spend_map.items():
        best_rate = -1.0
        best_card_id = combo[0].id
        for card in combo:
            effective_rate = card.rates.get(cat, card.rates.get("catch_all", 0.01)) * (card.point_valuation / 0.01)
            if effective_rate > best_rate:
                best_rate = effective_rate
                best_card_id = card.id
        
        category_assignment[cat] = best_card_id
        total_rewards += spend * best_rate

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
        best_category_assignments=category_assignment
    )

def optimize_top_wallets(
    cards: List[CreditCard],
    spd: SpendingProfile,
    wallet_size: int = 2,
    top_n: int = 3,
    include_business: bool = False
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
    include_business: bool = False
) -> MultiCardWalletResult:
    top_wallets = optimize_top_wallets(cards, spd, wallet_size=wallet_size, top_n=1, include_business=include_business)
    if not top_wallets:
        raise ValueError("No eligible cards found to form a wallet.")
    return top_wallets[0]