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
