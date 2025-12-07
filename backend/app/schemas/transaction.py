from pydantic import BaseModel, Field
from typing import Optional

class TransactionCreate(BaseModel):
    amount: float = Field(gt=0)
    category: str
    description: Optional[str] = None
