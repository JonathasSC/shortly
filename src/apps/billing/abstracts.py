from abc import ABC, abstractmethod


class PaymentAbstract(ABC):
    def __init__(self, sdk):
        self.sdk = sdk
        super().__init__()

    @abstractmethod
    def create_checkout_preference(self, **kwargs):
        pass
