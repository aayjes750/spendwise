from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Dict, List, Optional

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
    annual_fee: float = Field(default=0.0, alias="annual_fee")
    annual_fee_waived_first_year: bool = Field(default=False, alias="annual_fee_waived_first_year")
    credits: float = 0.0
    signup_bonus_value: float = Field(default=0.0, alias="signup_bonus_value")
    signup_bonus_spend_req: float = Field(default=0.0, alias="signup_bonus_spend_requirement")
    point_valuation: float = Field(default=0.01, alias="pointValuation")
    rates: Dict[str, float] = Field(default_factory=dict, alias="reward_rates")
    cap_cat: Optional[str] = Field(default=None, alias="capCat")
    cap_limit: Optional[float] = Field(default=None, alias="capLimit")
    rate_after_cap: Optional[float] = Field(default=None, alias="rateAfterCap")
    note: Optional[str] = None

    @model_validator(mode="after")
    def set_defaults(self):
        if not self.id:
            self.id = self.card_name.lower().replace(" ", "_")
        if not self.issuer or self.issuer == "Generic":
            first_word = self.card_name.split()[0] if self.card_name else "Unknown"
            self.issuer = first_word
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