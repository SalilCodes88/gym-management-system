from __future__ import annotations

from gym.gym import new_id, ValidationError, MembershipStatus
from pricing import PricePolicy, NoDiscount
from typing import List

from dataclasses import dataclass, field
from abc import abstractmethod, ABC

@dataclass
class BaseMembership(ABC):
    id: str = field(init=False)

    status: MembershipStatus = field(init=False)
    price_policy: PricePolicy = field(default_factory= NoDiscount)

    def __post_init__(self):
        self.id = new_id("ms")
        self.status = MembershipStatus.ACTIVE

    @abstractmethod
    @property
    def name(self):
        ...

    @abstractmethod
    @property
    def base_monthly_price(self):
        ...

    @property
    def monthly_price(self):
        return round(self.price_policy.apply(self.base_monthly_price), 2)
    
    @property
    def is_active(self):
        return self.status == MembershipStatus.ACTIVE
    
    def pause(self):
        if self.status == MembershipStatus.CANCELLED:
            raise ValidationError ("Cannot pause a cancelled membership.")
        self.status = MembershipStatus.PAUSED

    def resume(self):
        if self.status == MembershipStatus.CANCELLED:
            raise ValidationError ("Cannot resume a cancelled membership.")
        self.status = MembershipStatus.ACTIVE

    def cancel(self):
        self.status = MembershipStatus.CANCELLED

    def benefits(self) -> List[str]:
        return ["24/7 Gym Access", "Pool", "Sauna"]
    
class BasicMembership(BaseMembership):
    @property
    def name(self):
        return "Basic"
    
    @property
    def base_monthly_price(self):
        return 29.99
    
class PremiumMembership(BaseMembership):
    @property
    def name(self):
        return "Premium"
    
    @property
    def base_monthly_price(self):
        return 59.99
    
    def benefits(self):
        return super().benefits() + ["Group Fitness Classes", "Recovery Room"]
    