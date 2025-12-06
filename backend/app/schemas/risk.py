from pydantic import BaseModel
from typing import List

class RuleTrigger(BaseModel):
    rule_name: str
    reason: str
    suggested_outreach: str

class CustomerFeatures(BaseModel):
    credit_limit: float
    utilisation_pct: float
    avg_payment_ratio: float
    min_due_paid_freq: float
    merchant_mix_index: float
    cash_withdrawal_pct: float
    recent_spend_change_pct: float

class RiskSummary(BaseModel):
    ml_probability: float
    ensemble_probability: float
    risk_band: str
    top_features: List[dict]
    rules: List[RuleTrigger] | None = None
