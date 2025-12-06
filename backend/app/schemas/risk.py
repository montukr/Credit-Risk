from pydantic import BaseModel
from typing import List

class FeatureContribution(BaseModel):
    feature: str
    value: float

class RiskSummary(BaseModel):
    ml_probability: float
    ensemble_probability: float
    risk_band: str
    top_features: List[FeatureContribution]
