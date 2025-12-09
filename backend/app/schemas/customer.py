from typing import Optional, List

from pydantic import BaseModel


class CustomerSummary(BaseModel):
    id: str
    CustomerID: str
    CreditLimit: float
    UtilisationPct: float
    CashWithdrawalPct: float | None = None
    username: Optional[str] = None
    risk_band: Optional[str] = None
    last_score: Optional[float] = None


class CreditLimitUpdate(BaseModel):
    credit_limit: float


class ControlsUpdate(BaseModel):
    spend_cap: Optional[float] = None
    category_blocks: List[str] = []
    alerts_enabled: Optional[bool] = True
