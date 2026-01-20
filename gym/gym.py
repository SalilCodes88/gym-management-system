from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from gym.people import Member, Trainer
from gym.payments import BasePaymentProcessor, FakePaymentProcessor, InMemoryPaymentLedger, PaymentRecord
from gym.workouts import WorkoutCatalog, WorkoutPlan, Exercise

from enum import Enum
from uuid import uuid4

class GymError(Exception):
    """Base Error for gym domain"""

class ValidationError(GymError):
    """Raised when states are invalid"""

class NotFoundError(GymError):
    """Raised when an entity cannot be found"""

class PaymentError(GymError):
    """"Raised for payment related failures"""

class MembershipStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"

def new_id(prefix: str) -> str:
    if not prefix or not prefix.strip():
        raise ValidationError ("Prefix must be a non empty string.")
    return f"{prefix}_{uuid4().hex}"

@dataclass
class Gym():
    name: str
    members: Dict[str, Member] = field(default_factory=dict)
    trainers: Dict[str, Trainer] = field(default_factory=dict)
    members_by_email: Dict[str,str] = field(default_factory=dict)
    trainers_by_email: Dict[str,str] = field(default_factory=dict)
    payment_processor: BasePaymentProcessor = field(default_factory=FakePaymentProcessor)
    payment_ledger: InMemoryPaymentLedger = field(default_factory=InMemoryPaymentLedger)
    workouts: WorkoutCatalog = field(default_factory=WorkoutCatalog)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValidationError ("Gym name cannot be empty")
        
    def add_member(self, member: Member) -> None:
        if not isinstance(member,Member):
            raise ValidationError ("Must be a member object.")
        
        if member.membership.status == MembershipStatus.CANCELLED:
            raise ValidationError ("Cannot add a member with cancelled status.")
        
        if member.id in self.members:
            raise ValidationError ("This member already exists in the system.")
        
        email_key = member.email.lower().strip()

        if email_key in self.members_by_email:
            raise ValidationError ("Member with this email already exists in the system.")

        self.members[member.id] = member
        self.members_by_email[email_key] = member.id

    def get_member(self, member_id: str) -> Member:
        try:
            return self.members[member_id.strip()]
        except KeyError:
            raise NotFoundError (f"Member with '{member_id}' member id not found in the system.")
        
    def find_member_by_email(self, email: str) -> Optional[Member]:
        email_key = email.lower().strip()
        member_id = self.members_by_email.get(email_key)

        if member_id is None:
            return None
        
        return self.members[member_id]

    def remove_member(self, member_id: str) -> None:
        if member_id not in self.members:
            raise NotFoundError ("This member does not exist in the system.")
        
        member = self.members[member_id]
        email_key = member.email.lower().strip()

        self.members.pop(member_id)

        if self.members_by_email.get(email_key) == member_id:
            self.members_by_email.pop(email_key)

        else:
            raise ValidationError ("Inconsistent email index for member.")
        
    def cancel_member_membership(self, member_id: str) -> None:
        member = self.get_member(member_id=member_id)
        member.cancel_membership()

    def pause_membership(self, member_id: str) -> None:
        member = self.get_member(member_id=member_id)
        member.pause_membership()
        
    def list_members(self) -> List[Member]:
        return list(self.members.values())
    
    def charge_member(self, member_id: str, amount: float | None = None) -> PaymentRecord:
        member = self.get_member(member_id=member_id)

        if not member.is_active:
            raise ValidationError ("Cannot charge an inactive member.")
        
        charge_amount = member.monthly_price if amount is None else amount
        if charge_amount < 0:
            raise ValidationError ("Charge amount cannot be negative.")
        record = self.payment_processor.charge(
            member_id= member.id,
            member_name= member.full_name,
            amount= charge_amount
        )

        self.payment_ledger.add(record)
        return record
    
    def list_all_payments_for_member(self, member_id: str) -> List[PaymentRecord]:
        self.get_member(member_id=member_id)
        return self.payment_ledger.list_all_for_member(member_id=member_id)
    
    def total_paid_by_member(self, member_id: str) -> float:
        self.get_member(member_id=member_id)
        return self.payment_ledger.total_success_for_member(member_id=member_id)
    
    def total_revenue(self) -> float:
        return self.payment_ledger.total_success_for_all()
    
    def create_workout_plan(self, member_id: str, title: str) -> WorkoutPlan:
        member= self.get_member(member_id)
        plan = WorkoutPlan(member_id=member.id, title=title)
        self.workouts.add_plan(plan)
        return plan
    
    def add_exercise_to_plan(self, plan_id: str, exercise: Exercise) -> None:
        plan= self.workouts.get_plan(plan_id=plan_id)
        plan.add_exercise(exercise=exercise)

    def remove_exercise_from_plan(self, plan_id: str, number: int) -> None:
        plan = self.workouts.get_plan(plan_id=plan_id)
        plan.remove_exercise_by_number(number)

    def remove_exercise_by_name(self, plan_id: str, name: str) -> None:
        plan = self.workouts.get_plan(plan_id=plan_id)
        plan.remove_exercise_by_name(name=name)

    def list_plans_for_member(self, member_id: str) -> List[WorkoutPlan]:
        member = self.get_member(member_id=member_id)
        return self.workouts.list_all_plans_for_member(member.id)
    
    def get_workout_plan(self, plan_id: str) -> WorkoutPlan:
        return self.workouts.get_plan(plan_id=plan_id)
    
    def remove_workout_plan(self, plan_id: str) -> None:
        self.workouts.remove_plan(plan_id=plan_id)

    def add_trainer(self, trainer: Trainer) -> None:
        if not isinstance(trainer, Trainer):
            raise ValidationError ("Must be a trainer object.")
        
        if trainer.id in self.trainers:
            raise ValidationError ("This trainer already exists in the system.")
        
        email_key = trainer.email.lower().strip()

        if email_key in self.trainers_by_email:
            raise ValidationError ("Trainer with this email already exists in the system.")
        self.trainers[trainer.id] = trainer
        self.trainers_by_email[email_key] = trainer.id

    def get_trainer(self, trainer_id: str) -> Trainer:
        try:
            return self.trainers[trainer_id]
        except KeyError:
            raise NotFoundError ("This trainer does not exist in the system.")
        
    def find_trainer_by_email(self, email: str) -> Optional[Trainer]:
        email_key = email.lower().strip()
        trainer_id = self.trainers_by_email.get(email_key)

        if trainer_id is None:
            return None
        
        return self.trainers[trainer_id]
    
    def remove_trainer(self, trainer_id: str) -> None:
        if trainer_id not in self.trainers:
            raise NotFoundError ("This trainer does not exist in the system.")
        
        trainer = self.trainers[trainer_id]
        email_key = trainer.email.lower().strip()

        self.trainers.pop(trainer_id)

        if self.trainers_by_email.get(email_key) == trainer_id:
            self.trainers_by_email.pop(email_key)

        else:
            raise ValidationError ("Inconsistent email index for trainer.")
        
    def list_trainers(self) -> List[Trainer]:
        return list(self.trainers.values())
    
    def total_member_count(self) -> int:
        return len(self.members)
    
    def total_trainer_count(self) -> int:
        return len(self.trainers)
    
    def summary(self) -> str:
        active_members = sum(1 for m in self.members.values() if m.is_active)
        inactive_members = self.total_member_count() - active_members

        revenue = self.total_revenue()

        return(
            f"Gym: {self.name}\n",
            f"Members: {self.total_member_count()}\n",
            f"{active_members} active, {inactive_members} inactive\n",
            f"{self.total_trainer_count()} Trainers\n",
            f"Monthly Revenue: {revenue:.2f}",
        )
    
    def __str__(self):
        return self.summary()
    