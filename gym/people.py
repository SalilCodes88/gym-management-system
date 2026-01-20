from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from gym.gym import new_id, ValidationError, MembershipStatus
from gym.memberships import BaseMembership

@dataclass
class Person:
    id: str = field(init=False)
    full_name: str
    email: str

    def __post_init__(self) -> None:
        self.id = new_id("per")
        if not self.full_name or not self.full_name.strip():
            raise ValidationError ("Name field cannot be empty.")
        self.full_name = self.full_name.strip()

        if not self.email or not self.email.strip():
            raise ValidationError ("Email must be provided.")
        self.email = self.email.strip()

        if "@" not in self.email or "." not in self.email:
            raise ValidationError ("Please enter a valid email.")

@dataclass        
class Member(Person):
    membership: BaseMembership
    join_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.id = new_id("mem")
        if not isinstance(self.membership, BaseMembership):
            raise ValidationError ("Must be a Base Membership object.")
        
    @property
    def membership_id(self) -> str:
        return self.membership.id
    
    @property
    def membership_name(self) -> str:
        return self.membership.name
    
    @property
    def membership_status(self) -> MembershipStatus:
        return self.membership.status
    
    @property
    def is_active(self) -> bool:
        return self.membership.is_active
    
    @property
    def monthly_price(self) -> float:
        return self.membership.monthly_price
    
    def cancel_membership(self) -> None:
        self.membership.cancel()
    
    def pause_membership(self) -> None:
        self.membership.pause()

@dataclass    
class Trainer(Person):
    specialty: Optional[str] = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self.id = new_id("trn")

        if self.specialty is not None:
            if not self.specialty.strip():
                raise ValidationError ("Speciality cannot be just empty space.")
            
            self.specialty = self.specialty.title()
