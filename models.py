from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class SpendingProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    grocery: float = Field(default=0.0, ge=0)
    dining: float = Field(default=0.0, ge=0)
    travel: float = Field(default=0.0, ge=0)
    gas: float = Field(default=0.0, ge=0)
    streaming: float = Field(default=0.0, ge=0)
    catch_all: float = Field(default=0.0, ge=0, alias="catchAll")


class CreditCard(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: Optional[str] = None
    card_name: str = Field(default="", alias="name")
    issuer: Optional[str] = "Generic"
    is_business: bool = Field(default=False, alias="is_business")
    is_student: bool = Field(default=False, alias="is_student")
    annual_fee: float = Field(default=0.0, alias="annual_fee")
    annual_fee_waived_first_year: bool = Field(
        default=False, alias="annual_fee_waived_first_year"
    )
    credits: float = 0.0
    signup_bonus_value: float = Field(default=0.0, alias="signup_bonus_value")
    signup_bonus_spend_req: float = Field(
        default=0.0, alias="signup_bonus_spend_requirement"
    )
    point_valuation: float = Field(default=0.01, alias="pointValuation")
    rates: Dict[str, float] = Field(default_factory=dict, alias="reward_rates")

    # NOTE: these three were previously aliased to "capCat" / "capLimit" /
    # "rateAfterCap", which never matched any key actually present in
    # cards_seed.json ("spending_cap_category" / "spending_cap_limit" /
    # "reward_rate_after_cap"). Because the model allows extra fields,
    # Pydantic silently accepted the mismatch instead of erroring, so
    # cap_cat/cap_limit/rate_after_cap were None for every card, and no
    # spending cap was ever actually enforced. Fixed to match the real data.
    cap_cat: Optional[str] = Field(default=None, alias="spending_cap_category")
    cap_limit: Optional[float] = Field(default=None, alias="spending_cap_limit")
    rate_after_cap: Optional[float] = Field(default=None, alias="reward_rate_after_cap")

    note: Optional[str] = None

    @model_validator(mode="after")
    def set_card_defaults(self):
        # Auto-generate a kebab/snake ID if missing
        if not self.id:
            self.id = self.card_name.lower().replace(" ", "_")

        # Infer issuer from the first word if omitted
        if not self.issuer or self.issuer == "Generic":
            self.issuer = self.card_name.split()[0] if self.card_name else "Unknown"

        # Flag business cards automatically based on naming patterns
        name_lower = self.card_name.lower()
        if "business" in name_lower or "ink" in name_lower:
            self.is_business = True

        # Flag student cards automatically if the name says so; cards without
        # "student" in the name can still be marked explicitly in the seed
        # data (e.g. beginner/credit-building cards aimed at the same audience).
        if "student" in name_lower:
            self.is_student = True

        return self


class CardEvaluationResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    card_id: str
    card_name: str
    issuer: str
    annual_fee: float
    effective_annual_fee: float
    signup_bonus_earned: float
    annual_rewards: float
    net_first_year_value: float
    breakdown: Dict[str, float]


class MultiCardWalletResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cards: List[CardEvaluationResult]
    total_net_value: float
    total_annual_rewards: float
    total_effective_fee: float
    total_signup_bonus: float
    best_category_assignments: Dict[str, str]