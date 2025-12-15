from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class CheckoutPreferenceDTO:
    title: str
    price: float
    quantity: int
    back_urls: Dict[str, str]

    auto_return: str = "approved"
    metadata: Dict[str, str] = field(default_factory=dict)
    notification_url: Optional[str] = None
    external_reference: Optional[str] = None


@dataclass
class PaymentDataDTO:
    user_id: int
    payment_type: str
    amount: int = None
    plan_id: int = None
    payment_id: str = None
