from pydantic import BaseModel
from typing import Optional, List

class CustomerSummary(BaseModel):
    id: str
    CustomerID: str
    CreditLimit: float
    UtilisationPct: float
    risk_band: Optional[str] = None
    last_score: Optional[float] = None

class CreditLimitUpdate(BaseModel):
    credit_limit: float

class ControlsUpdate(BaseModel):
    spend_cap: Optional[float] = None
    category_blocks: List[str] = []
    alerts_enabled: Optional[bool] = True
