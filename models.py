from pydantic import BaseModel, ConfigDict, Field
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
    model_config = ConfigDict(populate_by_name=True)

    id: str
    card_name: str = Field(alias="cardName")
    issuer: str
    annual_fee: float = Field(alias="annualFee")
    credits: float = 0.0
    signup_bonus_value: float = Field(default=0.0, alias="signupBonusValue")
    signup_bonus_spend_req: float = Field(default=0.0, alias="signupBonusSpendReq")
    point_valuation: float = Field(default=0.01, alias="pointValuation")
    rates: Dict[str, float]
    cap_cat: Optional[str] = Field(default=None, alias="capCat")
    cap_limit: Optional[float] = Field(default=None, alias="capLimit")
    rate_after_cap: Optional[float] = Field(default=None, alias="rateAfterCap")

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