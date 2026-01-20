from __future__ import annotations

from gym.gym import ValidationError
from abc import ABC, abstractmethod

from dataclasses import dataclass

class PricePolicy(ABC):
    @abstractmethod
    def apply(self, base_price: float) -> float:
        ...

@dataclass(frozen=True)
class NoDiscount(PricePolicy):
    def apply(self, base_price: float) -> float:
        return base_price
    
@dataclass(frozen=True)
class PercentOff(PricePolicy):
    discount: float

    def __post_init__(self) -> None:
        if not (0 < self.discount < 1):
            raise ValidationError ("Discount must be between 0 and 1, For Example: 20% Discount is 0.20")
        
    def apply(self, base_price: float) -> float:
        return base_price * (1 - self.discount)
    
@dataclass(frozen=True)
class FixedPrice(PricePolicy):
    price: float

    def __post_init__(self) -> None:
        if not self.price > 0:
            raise ValidationError ("Price must be greater than $0.")
        
    def apply(self, base_price) -> float:
        return self.price
    