from typing import List, Optional
from pydantic import BaseModel, EmailStr

class PersonalInfo(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None

class AccountInfo(BaseModel):
    created_at: str
    credit_score: Optional[int] = None
    risk_tier: Optional[str] = None

class BehaviorMetrics(BaseModel):
    lifetime_value: Optional[float] = None
    days_since_last_purchase: Optional[int] = None
    purchase_frequency: Optional[float] = None
    average_order_value: Optional[float] = None

class Order(BaseModel):
    order_id: str
    order_date: str
    total_amount: float
    status: str
    items_count: int

class Predictions(BaseModel):
    churn_probability: float
    churn_risk_level: str
    next_best_offer: Optional[str] = None

class Customer360Response(BaseModel):
    customer_id: str
    personal_info: PersonalInfo
    account_info: AccountInfo
    behavior: Optional[BehaviorMetrics] = None
    recent_orders: Optional[List[Order]] = None
    predictions: Optional[Predictions] = None