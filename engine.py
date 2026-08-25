from itertools import combinations
from typing import List, Dict
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

def rank_cards_for_profile(cards: List[CreditCard], spd: SpendingProfile) -> List[CardEvaluationResult]:
    results = [calculate_card_rewards(c, spd) for c in cards]
    return sorted(results, key=lambda x: x.net_first_year_value, reverse=True)

def optimize_wallet_combo(cards: List[CreditCard], spd: SpendingProfile, wallet_size: int = 2) -> MultiCardWalletResult:
    spend_map = spd.model_dump()
    best_combo = None
    best_net_yield = -float("inf")
    best_assignments = {}

    card_evals = {c.id: calculate_card_rewards(c, spd) for c in cards}

    for combo in combinations(cards, wallet_size):
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

        total_fee = sum(card_evals[c.id].effective_annual_fee for c in combo)
        total_sub = sum(card_evals[c.id].signup_bonus_earned for c in combo)
        net_yield = total_rewards + total_sub - total_fee

        if net_yield > best_net_yield:
            best_net_yield = net_yield
            best_combo = combo
            best_assignments = category_assignment

    chosen_evals = [card_evals[c.id] for c in best_combo]
    return MultiCardWalletResult(
        cards=chosen_evals,
        total_net_value=round(best_net_yield, 2),
        total_annual_rewards=round(sum(c.annual_rewards for c in chosen_evals), 2),
        total_effective_fee=round(sum(c.effective_annual_fee for c in chosen_evals), 2),
        total_signup_bonus=round(sum(c.signup_bonus_earned for c in chosen_evals), 2),
        best_category_assignments=best_assignments
    )